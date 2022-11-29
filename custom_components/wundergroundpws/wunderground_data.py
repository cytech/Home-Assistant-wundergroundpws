import asyncio
from datetime import timedelta
import logging

import async_timeout
import aiohttp
from homeassistant.const import (
    TEMP_FAHRENHEIT, TEMP_CELSIUS, LENGTH_INCHES,
    LENGTH_FEET, LENGTH_MILLIMETERS, LENGTH_METERS, SPEED_MILES_PER_HOUR, SPEED_KILOMETERS_PER_HOUR,
    PERCENTAGE, PRESSURE_INHG, PRESSURE_MBAR, PRECIPITATION_INCHES_PER_HOUR, PRECIPITATION_MILLIMETERS_PER_HOUR)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

from .const import (
    FIELD_CONDITION_HUMIDITY,
    FIELD_CONDITION_PRESSURE,
    FIELD_CONDITION_TEMP,
    FIELD_CONDITION_WINDDIR,
    FIELD_CONDITION_WINDSPEED,

    FIELD_FORECAST_WXPHRASESHORT,
    FIELD_FORECAST_VALIDTIMEUTC,
    FIELD_FORECAST_PRECIPCHANCE,
    FIELD_FORECAST_QPF,
    FIELD_FORECAST_TEMPERATUREMAX,
    FIELD_FORECAST_TEMPERATUREMIN,
    FIELD_FORECAST_WINDDIRECTIONCARDINAL,
    FIELD_FORECAST_WINDSPEED,
)

_RESOURCECURRENT = 'https://api.weather.com/v2/pws/observations/current?stationId={}&format=json&units={}&apiKey={}'
_RESOURCEFORECAST = 'https://api.weather.com/v3/wx/forecast/daily/5day?geocode={},{}&units={}&{}&format=json&apiKey={}'
_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)

class WUndergroundData:
    """Get data from WUnderground."""

    condition_map: dict = {
        'clear-night': [
            "Clear",
        ],
        'cloudy': [
            "Cloudy",
            "Flurries",
        ],
        'exceptional': [
            "Fair",
        ],
        'fog': [
            "Fog",
        ],
        'hail': [
            "Frz Rain",
        ],
        'lightning': [
            'T-Storms',
        ],
        'lightning-rainy': [
            "Rain/Thunder",
        ],
        'partlycloudy': [
        ],
        'pouring': [
            "Heavy Rain",
        ],
        'rainy': [
            "Light Rain",
            "Rain Shower",
            "Rain/Wind",
            "Rn/Snw/Wind",
            "Shower/Wind",
            "Showers",
            "Showers/Wind",
        ],
        'snowy': [
            "Ice/Snow",
            "Light Snow",
            "Snow Shower",
            "Snow/Wind",
        ],
        'snowy-rainy': [
            "Rain/Snow",
        ],
        'sunny': [
            "Sunny",
        ],
        'windy': [
            "Fair/Wind",
            "Sun/Wind"
        ],
        'windy-variant': [
            "Cldy/Wind",
            "Cloudy/Wind",
        ],
    }
    condition_modifiers: list = (
        'AM ',
        'Few ',
        'Late',
        'M ',
        'Near',
        'P',
        'PM ',
        'Sct',
    )

    def __init__(self, hass, api_key, pws_id, numeric_precision, unit_system_api, unit_system, lang, latitude,
                 longitude):
        """Initialize the data object."""
        self._hass = hass
        self._api_key = api_key
        self._pws_id = pws_id
        self._numeric_precision = numeric_precision
        self._unit_system_api = unit_system_api
        self.unit_system = unit_system
        self.units_of_measurement = None
        self._lang = 'language={}'.format(lang)
        self._latitude = latitude
        self._longitude = longitude
        self._features = set()
        self.data = None
        self._session = async_get_clientsession(self._hass)

        if unit_system_api == 'm':
            self.units_of_measurement = (TEMP_CELSIUS, LENGTH_MILLIMETERS, LENGTH_METERS, SPEED_KILOMETERS_PER_HOUR,
                                         PRESSURE_MBAR, PRECIPITATION_MILLIMETERS_PER_HOUR, PERCENTAGE)
        else:
            self.units_of_measurement = (TEMP_FAHRENHEIT, LENGTH_INCHES, LENGTH_FEET, SPEED_MILES_PER_HOUR,
                                         PRESSURE_INHG, PRECIPITATION_INCHES_PER_HOUR, PERCENTAGE)

    def request_feature(self, feature):
        """Register feature to be fetched from WU API."""
        self._features.add(feature)

    def get_condition(self, field):
        if field in [
                FIELD_CONDITION_HUMIDITY,
                FIELD_CONDITION_WINDDIR,
        ]:
            # Those fields are unit-less
            return self.data['observations'][0][field] or 0
        return self.data['observations'][0][self.unit_system][field]

    def get_forecast(self, field, period=0):
        try:
            if field in [
                    FIELD_FORECAST_TEMPERATUREMAX,
                    FIELD_FORECAST_TEMPERATUREMIN,
                    FIELD_FORECAST_VALIDTIMEUTC,
            ]:
                # Those fields exist per-day, rather than per dayPart, so the period is halved
                return self.data[field][int(period/2)]
            return self.data['daypart'][0][field][period]
        except IndexError:
            return None

    @classmethod
    def _wxPhraseShort_to_conditio(cls, wx_phrase_short):
        '''
        Based on data at [0]

        [0] https://wiki.webcore.co/TWC_Weather
        '''
        for s in cls.condition_modifiers:
            wx_phrase_short = wx_phrase_short.replace(s, '')
        wx_phrase_short = wx_phrase_short.strip()
        for condition, phrases in cls.condition_map.items():
            if wx_phrase_short in phrases:
                return condition
        _LOGGER.warn(f'Unsupported condition string "{wx_phrase_short}". Please update WUndergroundData.condition_map.')
        return None

    def _build_url(self, baseurl):
        if baseurl is _RESOURCECURRENT:
            if self._numeric_precision == 'none':
                url = baseurl.format(
                    self._pws_id, self._unit_system_api, self._api_key)
            else:
                url = baseurl.format(
                    self._pws_id, self._unit_system_api, self._api_key) + '&numericPrecision=decimal'
        else:
            url = baseurl.format(self._latitude, self._longitude,
                                 self._unit_system_api, self._lang, self._api_key)

        return url

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Get the latest data from WUnderground."""
        headers = {'Accept-Encoding': 'gzip'}
        try:
            with async_timeout.timeout(10):
                response = await self._session.get(self._build_url(_RESOURCECURRENT), headers=headers)
            result_current = await response.json()

            # need to check specific new api errors
            # if "error" in result['response']:
            #     raise ValueError(result['response']["error"]["description"])
            # _LOGGER.debug('result_current' + str(result_current))

            if result_current is None:
                raise ValueError('NO CURRENT RESULT')
            with async_timeout.timeout(10):
                response = await self._session.get(self._build_url(_RESOURCEFORECAST), headers=headers)
            result_forecast = await response.json()

            if result_forecast is None:
                raise ValueError('NO FORECAST RESULT')

            result = {**result_current, **result_forecast}

            self.data = result
        except ValueError as err:
            _LOGGER.error("Check WUnderground API %s", err.args)
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error("Error fetching WUnderground data: %s", repr(err))
        _LOGGER.debug(f'WUnderground data {self.data}')
