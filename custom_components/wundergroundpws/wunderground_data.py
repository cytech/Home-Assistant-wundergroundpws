import asyncio
from datetime import timedelta
import logging

import async_timeout
import aiohttp
from homeassistant.const import (
    PERCENTAGE, UnitOfPressure, UnitOfTemperature, UnitOfLength, UnitOfSpeed, UnitOfVolumetricFlux)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

from .const import (
    FIELD_LATITUDE,
    FIELD_LONGITUDE,
    FIELD_OBSERVATIONS,
    FIELD_CONDITION_HUMIDITY,
    FIELD_CONDITION_WINDDIR,
    FIELD_DAYPART,
    FIELD_FORECAST_VALIDTIMEUTC,
    FIELD_FORECAST_TEMPERATUREMAX,
    FIELD_FORECAST_TEMPERATUREMIN,
    FIELD_FORECAST_CALENDARDAYTEMPERATUREMAX,
    FIELD_FORECAST_CALENDARDAYTEMPERATUREMIN
)

_RESOURCESHARED = '&format=json&apiKey={apiKey}&units={units}'
_RESOURCECURRENT = ('https://api.weather.com/v2/pws/observations/current'
                    '?stationId={stationId}')
_RESOURCEFORECAST = ('https://api.weather.com/v3/wx/forecast/daily/5day'
                     '?geocode={latitude},{longitude}')
_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)


class WUndergroundData:
    """Get data from WUnderground."""
    # icon map supporting document TWC_Icon_Map.ods in repository
    icon_condition_map: dict = {
        'clear-night': [31, 33],
        'cloudy': [26, 27, 28],
        'exceptional': [0, 1, 2, 19, 21, 22, 36, 43],  # 44 is Not Available (N/A)
        'fog': [20],
        'hail': [17],
        'lightning': [],
        'lightning-rainy': [3, 4, 37, 38, 47],
        'partlycloudy': [29, 30],
        'pouring': [40],
        'rainy': [9, 11, 12, 39, 45],
        'snowy': [13, 14, 15, 16, 41, 42, 46],
        'snowy-rainy': [5, 6, 7, 8, 10, 18, 25, 35],
        'sunny': [32, 34],
        'windy': [23, 24],
        'windy-variant': []
    }

    def __init__(self, hass, api_key, pws_id,
                 numeric_precision, unit_system_api, unit_system, lang,
                 latitude, longitude):
        """Initialize the data object."""
        self._hass = hass
        self._api_key = api_key
        self._pws_id = pws_id
        self._numeric_precision = numeric_precision
        self._unit_system_api = unit_system_api
        self.unit_system = unit_system
        self.units_of_measurement = None
        self._lang = lang
        self._latitude = latitude
        self._longitude = longitude
        self._features = set()
        self.data = None
        self._session = async_get_clientsession(self._hass)

        if unit_system_api == 'm':
            self.units_of_measurement = (UnitOfTemperature.CELSIUS, UnitOfLength.MILLIMETERS, UnitOfLength.METERS,
                                         UnitOfSpeed.KILOMETERS_PER_HOUR, UnitOfPressure.MBAR,
                                         UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR, PERCENTAGE)
        else:
            self.units_of_measurement = (UnitOfTemperature.FAHRENHEIT, UnitOfLength.INCHES, UnitOfLength.FEET,
                                         UnitOfSpeed.MILES_PER_HOUR, UnitOfPressure.INHG,
                                         UnitOfVolumetricFlux.INCHES_PER_HOUR, PERCENTAGE)

    def request_feature(self, feature):
        """Register feature to be fetched from WU API."""
        self._features.add(feature)

    def get_condition(self, field):
        if field in [
            FIELD_CONDITION_HUMIDITY,
            FIELD_CONDITION_WINDDIR,
        ]:
            # Those fields are unit-less
            return self.data[FIELD_OBSERVATIONS][0][field] or 0
        return self.data[FIELD_OBSERVATIONS][0][self.unit_system][field]

    def get_forecast(self, field, period=0):
        try:
            if field in [
                FIELD_FORECAST_TEMPERATUREMAX,
                FIELD_FORECAST_TEMPERATUREMIN,
                FIELD_FORECAST_CALENDARDAYTEMPERATUREMAX,
                FIELD_FORECAST_CALENDARDAYTEMPERATUREMIN,
                FIELD_FORECAST_VALIDTIMEUTC,
            ]:
                # Those fields exist per-day, rather than per dayPart, so the period is halved
                return self.data[field][int(period / 2)]
            return self.data[FIELD_DAYPART][0][field][period]
        except IndexError:
            return None

    @classmethod
    def _iconCode_to_condition(cls, icon_code):
        for condition, iconcodes in cls.icon_condition_map.items():
            if icon_code in iconcodes:
                return condition
        _LOGGER.warning(f'Unmapped iconCode from TWC Api. (44 is Not Available (N/A)) "{icon_code}". ')
        return None

    def _build_url(self, baseurl):
        if baseurl == _RESOURCECURRENT:
            if self._numeric_precision != 'none':
                baseurl += '&numericPrecision={numericPrecision}'
        elif baseurl == _RESOURCEFORECAST:
            baseurl += '&language={language}'

        baseurl += _RESOURCESHARED

        return baseurl.format(
            apiKey=self._api_key,
            language=self._lang,
            latitude=self._latitude,
            longitude=self._longitude,
            numericPrecision=self._numeric_precision,
            stationId=self._pws_id,
            units=self._unit_system_api
        )

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Get the latest data from WUnderground."""
        headers = {'Accept-Encoding': 'gzip'}
        try:
            with async_timeout.timeout(10):
                url = self._build_url(_RESOURCECURRENT)
                response = await self._session.get(url, headers=headers)
            result_current = await response.json()
            if result_current is None:
                raise ValueError('NO CURRENT RESULT')
            self._check_errors(url, result_current)

            if not self._longitude:
                self._longitude = (result_current[FIELD_OBSERVATIONS][0][FIELD_LONGITUDE])
            if not self._latitude:
                self._latitude = (result_current[FIELD_OBSERVATIONS][0][FIELD_LATITUDE])

            with async_timeout.timeout(10):
                url = self._build_url(_RESOURCEFORECAST)
                response = await self._session.get(url, headers=headers)
            result_forecast = await response.json()

            if result_forecast is None:
                raise ValueError('NO FORECAST RESULT')
            self._check_errors(url, result_forecast)

            result = {**result_current, **result_forecast}

            self.data = result
            # manual test responses
            # before 3:00 pm
            # self.data = {}
            # after 3:00 pm
            # self.data = {}

        except ValueError as err:
            _LOGGER.error("Check WUnderground API %s", err.args)
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error("Error fetching WUnderground data: %s", repr(err))
        # _LOGGER.debug(f'WUnderground data {self.data}')

    def _check_errors(self, url: str, response: dict):
        # _LOGGER.debug(f'Checking errors from {url} in {response}')
        if 'errors' not in response:
            return
        if errors := response['errors']:
            raise ValueError(
                f'Error from {url}: '
                '; '.join([
                    e['message']
                    for e in errors
                ])
            )
