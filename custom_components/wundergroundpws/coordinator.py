"""The WundergroundPWS data coordinator."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import json
from homeassistant.util.unit_system import METRIC_SYSTEM
from homeassistant.const import (
    PERCENTAGE, UnitOfPressure, UnitOfTemperature, UnitOfLength, UnitOfSpeed, UnitOfVolumetricFlux)
from .const import (
    ICON_CONDITION_MAP,
    FIELD_OBSERVATIONS,
    FIELD_CONDITION_HUMIDITY,
    FIELD_CONDITION_WINDDIR,
    FIELD_DAYPART,
    FIELD_FORECAST_VALIDTIMEUTC,
    FIELD_FORECAST_TEMPERATUREMAX,
    FIELD_FORECAST_TEMPERATUREMIN,
    FIELD_FORECAST_CALENDARDAYTEMPERATUREMAX,
    FIELD_FORECAST_CALENDARDAYTEMPERATUREMIN, DOMAIN, FIELD_LONGITUDE, FIELD_LATITUDE
)

_LOGGER = logging.getLogger(__name__)

_RESOURCESHARED = '&format=json&apiKey={apiKey}&units={units}'
_RESOURCECURRENT = ('https://api.weather.com/v2/pws/observations/current'
                    '?stationId={stationId}')
_RESOURCEFORECAST = ('https://api.weather.com/v3/wx/forecast/daily/5day'
                     '?geocode={latitude},{longitude}')

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)


@dataclass
class WundergroundPWSUpdateCoordinatorConfig:
    """Class representing coordinator configuration."""

    api_key: str
    pws_id: str
    numeric_precision: str
    unit_system_api: str
    unit_system: str
    lang: str
    latitude: str
    longitude: str
    update_interval = MIN_TIME_BETWEEN_UPDATES


class WundergroundPWSUpdateCoordinator(DataUpdateCoordinator):
    """The WundergroundPWS update coordinator."""

    icon_condition_map = ICON_CONDITION_MAP

    def __init__(
            self, hass: HomeAssistant, config: WundergroundPWSUpdateCoordinatorConfig
    ) -> None:
        """Initialize."""
        self._hass = hass
        self._api_key = config.api_key
        self._pws_id = config.pws_id
        self._numeric_precision = config.numeric_precision
        self._unit_system_api = config.unit_system_api
        self.unit_system = config.unit_system
        self._lang = config.lang
        self._latitude = config.latitude
        self._longitude = config.longitude
        self._features = set()
        self.data = None
        self._session = async_get_clientsession(self._hass)

        if self._unit_system_api == 'm':
            self.units_of_measurement = (UnitOfTemperature.CELSIUS, UnitOfLength.MILLIMETERS, UnitOfLength.METERS,
                                         UnitOfSpeed.KILOMETERS_PER_HOUR, UnitOfPressure.MBAR,
                                         UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR, PERCENTAGE)
        else:
            self.units_of_measurement = (UnitOfTemperature.FAHRENHEIT, UnitOfLength.INCHES, UnitOfLength.FEET,
                                         UnitOfSpeed.MILES_PER_HOUR, UnitOfPressure.INHG,
                                         UnitOfVolumetricFlux.INCHES_PER_HOUR, PERCENTAGE)

        super().__init__(
            hass,
            _LOGGER,
            name="WundergroundPWSUpdateCoordinator",
            update_interval=config.update_interval,
        )

    @property
    def is_metric(self):
        """Determine if this is the metric unit system."""
        return self._hass.config.units is METRIC_SYSTEM

    async def _async_update_data(self) -> dict[str, Any]:
        return await self.get_weather()

    async def get_weather(self):
        """Get weather data."""
        headers = {'Accept-Encoding': 'gzip'}
        try:
            # with async_timeout.timeout(10):
            #     url = self._build_url(_RESOURCECURRENT)
            #     response = await self._session.get(url, headers=headers)
            # result_current = await response.json()
            # if result_current is None:
            #     raise ValueError('NO CURRENT RESULT')
            # self._check_errors(url, result_current)
            #
            # if not self._longitude:
            #     self._longitude = (result_current[FIELD_OBSERVATIONS][0][FIELD_LONGITUDE])
            # if not self._latitude:
            #     self._latitude = (result_current[FIELD_OBSERVATIONS][0][FIELD_LATITUDE])
            #
            # with async_timeout.timeout(10):
            #     url = self._build_url(_RESOURCEFORECAST)
            #     response = await self._session.get(url, headers=headers)
            # result_forecast = await response.json()
            #
            # if result_forecast is None:
            #     raise ValueError('NO FORECAST RESULT')
            # self._check_errors(url, result_forecast)
            #
            # result = {**result_current, **result_forecast}
            #
            # self.data = result
            # manual test responses todo
            # before 3:00 pm
            result = {'observations': [{'stationID': 'KAZBISBE8', 'obsTimeUtc': '2022-12-05T18:28:46Z', 'obsTimeLocal': '2022-12-05 11:28:46', 'neighborhood': 'PalominasEast', 'softwareType': 'AMBWeatherV4.2.9', 'country': 'US', 'solarRadiation': 579.1, 'lon': -110.039001, 'realtimeFrequency': None, 'epoch': 1670264926, 'lat': 31.386, 'uv': 5.0, 'winddir': 190, 'humidity': 60.0, 'qcStatus': 1, 'imperial': {'temp': 67.1, 'heatIndex': 67.1, 'dewpt': 52.9, 'windChill': 67.1, 'windSpeed': 6.7, 'windGust': 8.1, 'pressure': 29.77, 'precipRate': 0.0, 'precipTotal': 0.0, 'elev': 4465.0}}], 'calendarDayTemperatureMax': [67, 64, 60, 59, 62, 63], 'calendarDayTemperatureMin': [46, 40, 37, 31, 32, 30], 'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'], 'expirationTimeUtc': [1670265785, 1670265785, 1670265785, 1670265785, 1670265785, 1670265785], 'moonPhase': ['Waxing Gibbous', 'Waxing Gibbous', 'Full Moon', 'Full Moon', 'Waning Gibbous', 'Waning Gibbous'], 'moonPhaseCode': ['WXG', 'WXG', 'F', 'F', 'WNG', 'WNG'], 'moonPhaseDay': [12, 13, 14, 15, 16, 17], 'moonriseTimeLocal': ['2022-12-05T15:40:13-0700', '2022-12-06T16:16:05-0700', '2022-12-07T16:56:08-0700', '2022-12-08T17:41:13-0700', '2022-12-09T18:31:56-0700', '2022-12-10T19:25:39-0700'], 'moonriseTimeUtc': [1670280013, 1670368565, 1670457368, 1670546473, 1670635916, 1670725539], 'moonsetTimeLocal': ['2022-12-05T04:43:16-0700', '2022-12-06T05:43:07-0700', '2022-12-07T06:43:35-0700', '2022-12-08T07:41:45-0700', '2022-12-09T08:37:28-0700', '2022-12-10T09:27:21-0700'], 'moonsetTimeUtc': [1670240596, 1670330587, 1670420615, 1670510505, 1670600248, 1670689641], 'narrative': ['Times of sun and clouds. Highs in the upper 60s and lows in the low 40s.', 'Abundant sunshine. Highs in the mid 60s and lows in the upper 30s.', 'Mostly sunny. Highs in the low 60s and lows in the low 30s.', 'More sun than clouds. Highs in the upper 50s and lows in the low 30s.', 'Partly cloudy. Highs in the low 60s and lows in the low 30s.', 'Abundant sunshine. Highs in the low 60s and lows in the low 30s.'], 'qpf': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'qpfSnow': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'sunriseTimeLocal': ['2022-12-05T07:04:43-0700', '2022-12-06T07:05:29-0700', '2022-12-07T07:06:14-0700', '2022-12-08T07:06:58-0700', '2022-12-09T07:07:41-0700', '2022-12-10T07:08:24-0700'], 'sunriseTimeUtc': [1670249083, 1670335529, 1670421974, 1670508418, 1670594861, 1670681304], 'sunsetTimeLocal': ['2022-12-05T17:16:40-0700', '2022-12-06T17:16:45-0700', '2022-12-07T17:16:51-0700', '2022-12-08T17:17:00-0700', '2022-12-09T17:17:10-0700', '2022-12-10T17:17:21-0700'], 'sunsetTimeUtc': [1670285800, 1670372205, 1670458611, 1670545020, 1670631430, 1670717841], 'temperatureMax': [67, 64, 60, 59, 62, 63], 'temperatureMin': [40, 37, 31, 32, 30, 31], 'validTimeLocal': ['2022-12-05T07:00:00-0700', '2022-12-06T07:00:00-0700', '2022-12-07T07:00:00-0700', '2022-12-08T07:00:00-0700', '2022-12-09T07:00:00-0700', '2022-12-10T07:00:00-0700'], 'validTimeUtc': [1670248800, 1670335200, 1670421600, 1670508000, 1670594400, 1670680800], 'daypart': [{'cloudCover': [10, 11, 18, 10, 15, 17, 28, 56, 41, 21, 10, 6], 'dayOrNight': ['D', 'N', 'D', 'N', 'D', 'N', 'D', 'N', 'D', 'N', 'D', 'N'], 'daypartName': ['Today', 'Tonight', 'Tomorrow', 'Tomorrow night', 'Wednesday', 'Wednesday night', 'Thursday', 'Thursday night', 'Friday', 'Friday night', 'Saturday', 'Saturday night'], 'iconCode': [30, 33, 32, 31, 34, 33, 34, 29, 30, 29, 32, 31], 'iconCodeExtend': [3000, 3300, 3200, 3100, 3400, 3300, 3400, 2900, 3000, 2900, 3200, 3100], 'narrative': ['Some clouds this morning will give way to generally sunny skies for the afternoon. High 67F. Winds WSW at 10 to 15 mph.', 'Generally clear. Low around 40F. Winds light and variable.', 'Sunny skies. High 64F. Winds SW at 10 to 20 mph.', 'Clear. Low 37F. Winds SSW at 5 to 10 mph.', 'Generally sunny. High around 60F. Winds SW at 10 to 20 mph.', 'Partly cloudy. Low 31F. Winds WNW at 5 to 10 mph.', 'Sun and a few passing clouds. High 59F. Winds light and variable.', 'A few clouds. Low 32F. Winds light and variable.', 'Sunshine and clouds mixed. High 62F. Winds SW at 5 to 10 mph.', 'Partly cloudy. Low around 30F. Winds light and variable.', 'Sunny. High 63F. Winds WSW at 5 to 10 mph.', 'A mostly clear sky. Low 31F. Winds WSW at 5 to 10 mph.'], 'precipChance': [1, 7, 7, 7, 6, 8, 8, 4, 3, 3, 2, 2], 'precipType': ['rain', 'rain', 'rain', 'precip', 'rain', 'precip', 'rain', 'precip', 'rain', 'precip', 'rain', 'precip'], 'qpf': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'qpfSnow': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'qualifierCode': [None, None, None, None, None, None, None, None, None, None, None, None], 'qualifierPhrase': [None, None, None, None, None, None, None, None, None, None, None, None], 'relativeHumidity': [52, 78, 57, 74, 56, 75, 54, 59, 42, 57, 33, 48], 'snowRange': ['', '', '', '', '', '', '', '', '', '', '', ''], 'temperature': [67, 40, 64, 37, 60, 31, 59, 32, 62, 30, 63, 31], 'temperatureHeatIndex': [67, 54, 64, 51, 60, 48, 59, 47, 62, 48, 63, 48], 'temperatureWindChill': [56, 40, 39, 37, 38, 31, 32, 32, 33, 30, 31, 31], 'thunderCategory': ['No thunder', 'No thunder', 'No thunder', 'No thunder', 'No thunder', 'No thunder', 'No thunder', 'No thunder', 'No thunder', 'No thunder', 'No thunder', 'No thunder'], 'thunderIndex': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'uvDescription': ['Moderate', 'Low', 'Moderate', 'Low', 'Moderate', 'Low', 'Moderate', 'Low', 'Moderate', 'Low', 'Moderate', 'Low'], 'uvIndex': [4, 0, 4, 0, 4, 0, 3, 0, 3, 0, 3, 0], 'windDirection': [240, 212, 214, 202, 225, 302, 6, 71, 225, 281, 247, 246], 'windDirectionCardinal': ['WSW', 'SSW', 'SW', 'SSW', 'SW', 'WNW', 'N', 'ENE', 'SW', 'W', 'WSW', 'WSW'], 'windPhrase': ['Winds WSW at 10 to 15 mph.', 'Winds light and variable.', 'Winds SW at 10 to 20 mph.', 'Winds SSW at 5 to 10 mph.', 'Winds SW at 10 to 20 mph.', 'Winds WNW at 5 to 10 mph.', 'Winds light and variable.', 'Winds light and variable.', 'Winds SW at 5 to 10 mph.', 'Winds light and variable.', 'Winds WSW at 5 to 10 mph.', 'Winds WSW at 5 to 10 mph.'], 'windSpeed': [13, 6, 15, 7, 14, 6, 5, 5, 6, 4, 9, 6], 'wxPhraseLong': ['Partly Cloudy', 'Mostly Clear', 'Sunny', 'Clear', 'Mostly Sunny', 'Mostly Clear', 'Mostly Sunny', 'Partly Cloudy', 'Partly Cloudy', 'Partly Cloudy', 'Sunny', 'Clear'], 'wxPhraseShort': ['P Cloudy', 'M Clear', 'Sunny', 'Clear', 'M Sunny', 'M Clear', 'M Sunny', 'P Cloudy', 'P Cloudy', 'P Cloudy', 'Sunny', 'Clear']}]}
            self.data = result
            # after 3:00 pm
            # self.data = {}
            return result

        except ValueError as err:
            _LOGGER.error("Check WUnderground API %s", err.args)
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error("Error fetching WUnderground data: %s", repr(err))
        # _LOGGER.debug(f'WUnderground data {self.data}')

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
    def _iconcode_to_condition(cls, icon_code):
        for condition, iconcodes in cls.icon_condition_map.items():
            if icon_code in iconcodes:
                return condition
        _LOGGER.warning(f'Unmapped iconCode from TWC Api. (44 is Not Available (N/A)) "{icon_code}". ')
        return None

    def get_tran_file(self):
        """get translation file for wupws sensor friendly_name"""
        tfiledir = f'{self.hass.config.config_dir}/custom_components/{DOMAIN}/wupws_translations/'
        tfilename = self._lang.split('-', 1)[0]
        try:
            tfiledata = json.load_json(f'{tfiledir}{tfilename}.json')
        except Exception:  # pylint: disable=broad-except
            tfiledata = json.load_json(f'{tfiledir}en.json')
            _LOGGER.warning(f'Sensor translation file {tfilename}.json does not exist. Defaulting to en-US.')
        return tfiledata


class InvalidApiKey(HomeAssistantError):
    """Error to indicate there is an invalid api key."""


class InvalidStationId(HomeAssistantError):
    """Error to indicate there is an invalid api key."""
