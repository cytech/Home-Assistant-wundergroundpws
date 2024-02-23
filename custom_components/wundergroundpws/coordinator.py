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
    FIELD_FORECAST_CALENDARDAYTEMPERATUREMIN, DOMAIN, FIELD_LONGITUDE, FIELD_LATITUDE,
    DEFAULT_TIMEOUT
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
    calendarday: bool
    latitude: str
    longitude: str
    forecast_enable: bool
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
        self._calendarday = config.calendarday
        self._latitude = config.latitude
        self._longitude = config.longitude
        self.forecast_enable = config.forecast_enable
        self._features = set()
        self.data = None
        self._session = async_get_clientsession(self._hass)
        self._tranfile = self.get_tran_file()

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

    @property
    def pws_id(self):
        """Return the location used for data."""
        return self._pws_id

    async def _async_update_data(self) -> dict[str, Any]:
        return await self.get_weather()

    async def get_weather(self):
        """Get weather data."""
        headers = {
            'Accept-Encoding': 'gzip',
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }
        try:
            with async_timeout.timeout(DEFAULT_TIMEOUT):
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

            with async_timeout.timeout(DEFAULT_TIMEOUT):
                url = self._build_url(_RESOURCEFORECAST)
                response = await self._session.get(url, headers=headers)
                result_forecast = await response.json()

                if result_forecast is None:
                    raise ValueError('NO FORECAST RESULT')
                self._check_errors(url, result_forecast)

            result = {**result_current, **result_forecast}

            self.data = result

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
        tfiledir = f'{self._hass.config.config_dir}/custom_components/{DOMAIN}/wupws_translations/'
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
