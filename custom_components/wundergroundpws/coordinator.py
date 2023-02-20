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
# MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1) todo


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
            # manual test responses todo
            # before 3:00 pm
            # en-US  imperial
            # result = {"observations": [{"stationID": "KAZBISBE8", "obsTimeUtc": "2023-02-19T13:39:42Z", "obsTimeLocal": "2023-02-19 06:39:42", "neighborhood": "PalominasEast", "softwareType": "AMBWeatherV4.2.9", "country": "US", "solarRadiation": 0.0, "lon": -110.039001, "realtimeFrequency": None, "epoch": 1676813982, "lat": 31.386, "uv": 0.0, "winddir": 121, "humidity": 59.0, "qcStatus": 1, "imperial": {"temp": 51.1, "heatIndex": 51.1, "dewpt": 37.2, "windChill": 51.1, "windSpeed": 4.0, "windGust": 5.8, "pressure": 29.80, "precipRate": 0.00, "precipTotal": 0.00, "elev": 4465.0}}], "calendarDayTemperatureMax": [56, 64, 57, 46, 57, 62], "calendarDayTemperatureMin": [45, 42, 41, 39, 35, 33], "dayOfWeek": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "expirationTimeUtc": [1676812577, 1676812577, 1676812577, 1676812577, 1676812577, 1676812577], "moonPhase": ["New Moon", "New Moon", "Waxing Crescent", "Waxing Crescent", "Waxing Crescent", "Waxing Crescent"], "moonPhaseCode": ["N", "N", "WXC", "WXC", "WXC", "WXC"], "moonPhaseDay": [29, 0, 2, 3, 4, 5], "moonriseTimeLocal": ["2023-02-19T06:51:16-0700", "2023-02-20T07:30:42-0700", "2023-02-21T08:06:00-0700", "2023-02-22T08:38:21-0700", "2023-02-23T09:09:05-0700", "2023-02-24T09:40:36-0700"], "moonriseTimeUtc": [1676814676, 1676903442, 1676991960, 1677080301, 1677168545, 1677256836], "moonsetTimeLocal": ["2023-02-19T17:42:50-0700", "2023-02-20T18:55:17-0700", "2023-02-21T20:04:14-0700", "2023-02-22T21:10:21-0700", "2023-02-23T22:15:08-0700", "2023-02-24T23:18:04-0700"], "moonsetTimeUtc": [1676853770, 1676944517, 1677035054, 1677125421, 1677215708, 1677305884], "narrative": ["Cloudy. Highs in the mid 50s and lows in the low 40s.", "Mostly cloudy. Highs in the mid 60s and lows in the low 40s.", "Showers. Highs in the upper 50s and lows in the upper 30s.", "Showers early, windy. Highs in the mid 40s and lows in the mid 30s.", "Plenty of sun. Highs in the upper 50s and lows in the low 30s.", "Mix of sun and clouds. Highs in the low 60s and lows in the low 30s."], "qpf": [0.0, 0.04, 0.2, 0.04, 0.0, 0.0], "qpfSnow": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "sunriseTimeLocal": ["2023-02-19T06:57:54-0700", "2023-02-20T06:56:54-0700", "2023-02-21T06:55:54-0700", "2023-02-22T06:54:53-0700", "2023-02-23T06:53:51-0700", "2023-02-24T06:52:48-0700"], "sunriseTimeUtc": [1676815074, 1676901414, 1676987754, 1677074093, 1677160431, 1677246768], "sunsetTimeLocal": ["2023-02-19T18:10:39-0700", "2023-02-20T18:11:28-0700", "2023-02-21T18:12:16-0700", "2023-02-22T18:13:04-0700", "2023-02-23T18:13:52-0700", "2023-02-24T18:14:39-0700"], "sunsetTimeUtc": [1676855439, 1676941888, 1677028336, 1677114784, 1677201232, 1677287679], "temperatureMax": [56, 64, 57, 46, 57, 62], "temperatureMin": [42, 41, 39, 35, 33, 33], "validTimeLocal": ["2023-02-19T07:00:00-0700", "2023-02-20T07:00:00-0700", "2023-02-21T07:00:00-0700", "2023-02-22T07:00:00-0700", "2023-02-23T07:00:00-0700", "2023-02-24T07:00:00-0700"], "validTimeUtc": [1676815200, 1676901600, 1676988000, 1677074400, 1677160800, 1677247200], "daypart": [{"cloudCover": [98, 98, 80, 72, 78, 71, 78, 75, 34, 48, 55, 53], "dayOrNight": ["D", "N", "D", "N", "D", "N", "D", "N", "D", "N", "D", "N"], "daypartName": ["Today", "Tonight", "Tomorrow", "Tomorrow night", "Tuesday", "Tuesday night", "Wednesday", "Wednesday night", "Thursday", "Thursday night", "Friday", "Friday night"], "iconCode": [26, 26, 26, 11, 11, 24, 39, 27, 34, 29, 30, 29], "iconCodeExtend": [2600, 2600, 2600, 1100, 1100, 2710, 6113, 2700, 3400, 2900, 3000, 2900], "narrative": ["Cloudy skies. Slight chance of a rain shower. High 56F. Winds S at 10 to 20 mph.", "Cloudy. Slight chance of a rain shower. Low 42F. Winds light and variable.", "Cloudy. Slight chance of a rain shower. High 64F. Winds S at 5 to 10 mph.", "Cloudy with occasional rain showers. Low 41F. Winds light and variable. Chance of rain 40%.", "Overcast with rain showers at times. High 57F. Winds SSW at 10 to 20 mph. Chance of rain 50%.", "Partly cloudy skies in the evening followed by cloudy and windy conditions late. Low 39F. Winds SW at 25 to 35 mph.", "Rain showers early, then remaining overcast and windy later in the day. High 46F. Winds SW at 25 to 35 mph. Chance of rain 40%.  Winds could occasionally gust over 50 mph.", "Mostly cloudy skies. Low near 35F. Winds SW at 10 to 20 mph.", "A few clouds early, otherwise mostly sunny. High 57F. Winds SSW at 15 to 25 mph.", "Partly cloudy. Low 33F. Winds SSW at 5 to 10 mph.", "Intervals of clouds and sunshine. High 62F. Winds SSW at 10 to 20 mph.", "A few clouds. Low 33F. Winds SSW at 5 to 10 mph."], "precipChance": [24, 18, 16, 43, 50, 24, 42, 20, 6, 6, 5, 6], "precipType": ["rain", "rain", "rain", "rain", "rain", "precip", "rain", "precip", "rain", "precip", "rain", "precip"], "qpf": [0.0, 0.0, 0.0, 0.04, 0.18, 0.0, 0.04, 0.0, 0.0, 0.0, 0.0, 0.0], "qpfSnow": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "qualifierCode": ["Q5015", "Q5015", "Q5015", None, None, None, "Q1022", None, None, None, None, None], "qualifierPhrase": ["Slight chance of a rain shower.", "Slight chance of a rain shower.", "Slight chance of a rain shower.", None, None, None, "Winds could occasionally gust over 50 mph.", None, None, None, None, None], "relativeHumidity": [63, 83, 54, 80, 69, 76, 69, 70, 49, 68, 39, 59], "snowRange": ["", "", "", "", "", "", "", "", "", "", "", ""], "temperature": [56, 42, 64, 41, 57, 39, 46, 35, 57, 33, 62, 33], "temperatureHeatIndex": [56, 50, 64, 53, 57, 45, 46, 41, 57, 47, 62, 49], "temperatureWindChill": [44, 41, 40, 41, 41, 30, 29, 30, 29, 29, 29, 30], "thunderCategory": ["No thunder", "No thunder", "No thunder", "No thunder", "No thunder", "No thunder", "No thunder", "No thunder", "No thunder", "No thunder", "No thunder", "No thunder"], "thunderIndex": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "uvDescription": ["Low", "Low", "Moderate", "Low", "Moderate", "Low", "Moderate", "Low", "High", "Low", "Moderate", "Low"], "uvIndex": [2, 0, 4, 0, 4, 0, 5, 0, 6, 0, 5, 0], "windDirection": [177, 108, 188, 144, 201, 215, 224, 225, 209, 195, 206, 201], "windDirectionCardinal": ["S", "ESE", "S", "SE", "SSW", "SW", "SW", "SW", "SSW", "SSW", "SSW", "SSW"], "windPhrase": ["Winds S at 10 to 20 mph.", "Winds light and variable.", "Winds S at 5 to 10 mph.", "Winds light and variable.", "Winds SSW at 10 to 20 mph.", "Winds SW at 25 to 35 mph.", "Winds SW at 25 to 35 mph.", "Winds SW at 10 to 20 mph.", "Winds SSW at 15 to 25 mph.", "Winds SSW at 5 to 10 mph.", "Winds SSW at 10 to 20 mph.", "Winds SSW at 5 to 10 mph."], "windSpeed": [16, 6, 10, 5, 13, 25, 31, 16, 18, 9, 15, 9], "wxPhraseLong": ["Cloudy", "Cloudy", "Cloudy", "Showers", "Showers", "Mostly Cloudy/Wind", "AM Showers/Wind", "Mostly Cloudy", "Mostly Sunny", "Partly Cloudy", "Partly Cloudy", "Partly Cloudy"], "wxPhraseShort": ["Cloudy", "Cloudy", "Cloudy", "Showers", "Showers", "M Cldy/Wind", "Showers/Wind", "M Cloudy", "M Sunny", "P Cloudy", "P Cloudy", "P Cloudy"]}]}
            # de-DE  metric
            # result = {"observations": [{"stationID": "KAZBISBE8", "obsTimeUtc": "2023-02-19T13:37:50Z", "obsTimeLocal": "2023-02-19 06:37:50", "neighborhood": "PalominasEast", "softwareType": "AMBWeatherV4.2.9", "country": "US", "solarRadiation": 0.0, "lon": -110.039001, "realtimeFrequency": None, "epoch": 1676813870, "lat": 31.386, "uv": 0.0, "winddir": 135, "humidity": 61.0, "qcStatus": 1, "metric": {"temp": 10.6, "heatIndex": 10.6, "dewpt": 3.4, "windChill": 10.6, "windSpeed": 0.0, "windGust": 0.0, "pressure": 1009.11, "precipRate": 0.00, "precipTotal": 0.00, "elev": 1360.9}}], "calendarDayTemperatureMax": [13, 18, 14, 8, 14, 17], "calendarDayTemperatureMin": [8, 6, 5, 4, 2, 1], "dayOfWeek": ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"], "expirationTimeUtc": [1676815635, 1676815635, 1676815635, 1676815635, 1676815635, 1676815635], "moonPhase": ["Neumond", "Neumond", "zunehmender Sichelmond", "zunehmender Sichelmond", "zunehmender Sichelmond", "zunehmender Sichelmond"], "moonPhaseCode": ["N", "N", "WXC", "WXC", "WXC", "WXC"], "moonPhaseDay": [29, 0, 2, 3, 4, 5], "moonriseTimeLocal": ["2023-02-19T06:51:16-0700", "2023-02-20T07:30:42-0700", "2023-02-21T08:06:00-0700", "2023-02-22T08:38:21-0700", "2023-02-23T09:09:05-0700", "2023-02-24T09:40:36-0700"], "moonriseTimeUtc": [1676814676, 1676903442, 1676991960, 1677080301, 1677168545, 1677256836], "moonsetTimeLocal": ["2023-02-19T17:42:50-0700", "2023-02-20T18:55:17-0700", "2023-02-21T20:04:14-0700", "2023-02-22T21:10:21-0700", "2023-02-23T22:15:08-0700", "2023-02-24T23:18:04-0700"], "moonsetTimeUtc": [1676853770, 1676944517, 1677035054, 1677125421, 1677215708, 1677305884], "narrative": ["Bedeckt. Höchsttemperaturen 12 bis 14C und Tiefsttemperaturen 5 bis 7C.", "Bedeckt. Höchsttemperaturen 17 bis 19C und Tiefsttemperaturen 4 bis 6C.", "Schauer. Höchsttemperaturen 13 bis 15C und Tiefsttemperaturen 3 bis 5C.", "Windig, vormittags Schauer. Höchsttemperaturen 7 bis 9C und Tiefsttemperaturen 1 bis 3C.", "Meistens klar. Höchsttemperaturen 13 bis 15C und Tiefsttemperaturen 0 bis 2C.", "Teilweise bedeckt. Höchsttemperaturen 16 bis 18C und Tiefsttemperaturen 0 bis 2C."], "qpf": [0.0, 1.1, 5.08, 0.8, 0.0, 0.0], "qpfSnow": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "sunriseTimeLocal": ["2023-02-19T06:57:54-0700", "2023-02-20T06:56:54-0700", "2023-02-21T06:55:54-0700", "2023-02-22T06:54:53-0700", "2023-02-23T06:53:51-0700", "2023-02-24T06:52:48-0700"], "sunriseTimeUtc": [1676815074, 1676901414, 1676987754, 1677074093, 1677160431, 1677246768], "sunsetTimeLocal": ["2023-02-19T18:10:39-0700", "2023-02-20T18:11:28-0700", "2023-02-21T18:12:16-0700", "2023-02-22T18:13:04-0700", "2023-02-23T18:13:52-0700", "2023-02-24T18:14:39-0700"], "sunsetTimeUtc": [1676855439, 1676941888, 1677028336, 1677114784, 1677201232, 1677287679], "temperatureMax": [13, 18, 14, 8, 14, 17], "temperatureMin": [6, 5, 4, 2, 1, 1], "validTimeLocal": ["2023-02-19T07:00:00-0700", "2023-02-20T07:00:00-0700", "2023-02-21T07:00:00-0700", "2023-02-22T07:00:00-0700", "2023-02-23T07:00:00-0700", "2023-02-24T07:00:00-0700"], "validTimeUtc": [1676815200, 1676901600, 1676988000, 1677074400, 1677160800, 1677247200], "daypart": [{"cloudCover": [98, 98, 79, 71, 79, 72, 79, 75, 35, 48, 56, 55], "dayOrNight": ["D", "N", "D", "N", "D", "N", "D", "N", "D", "N", "D", "N"], "daypartName": ["Heute", "Heute Abend", "Morgen", "Morgen Abend", "Dienstag", "Dienstagnacht", "Mittwoch", "Mittwochnacht", "Donnerstag", "Donnerstagnacht", "Freitag", "Freitagnacht"], "iconCode": [26, 26, 26, 11, 11, 24, 39, 27, 34, 29, 30, 29], "iconCodeExtend": [2600, 2600, 2600, 1100, 1100, 2710, 6113, 2700, 3400, 2900, 3000, 2900], "narrative": ["Bedeckt. Eventuell Regenschauer. Höchsttemperatur 13C. Wind aus S mit 15 bis 30 km/h.", "Bedeckt. Eventuell Regenschauer. Tiefsttemperatur 6C. Wind aus OSO und wechselhaft.", "Bedeckt. Eventuell Regenschauer. Höchsttemperatur 18C. Wind aus S mit 10 bis 15 km/h.", "Schauer. Tiefsttemperatur 5C. Wind aus SO und wechselhaft. Regenrisiko 40 %.", "Schauer. Höchsttemperatur 14C. Wind aus SSW mit 15 bis 30 km/h. Regenrisiko 50 %.", "Meistens bedeckt und windig. Tiefsttemperatur 4C. Wind aus SW mit 15 bis 30 km/h, zunehmend auf 30 bis 50 km/h.", "Windig, vormittags Schauer. Höchsttemperatur 8C. Wind aus SW mit 40 bis 55 km/h. Regenrisiko 40 %.  Windböen mit einer Stärke von stellenweise über 80 km/h.", "Meistens bedeckt. Tiefsttemperatur 2C. Wind aus SW mit 15 bis 30 km/h.", "Meistens klar. Höchsttemperatur 14C. Wind aus SSW mit 25 bis 40 km/h.", "Teilweise bedeckt. Tiefsttemperatur 1C. Wind aus SSW mit 10 bis 15 km/h.", "Teilweise bedeckt. Höchsttemperatur 17C. Wind aus SSW mit 15 bis 30 km/h.", "Teilweise bedeckt. Tiefsttemperatur 1C. Wind aus SSW mit 10 bis 15 km/h."], "precipChance": [24, 18, 16, 40, 52, 24, 41, 20, 6, 6, 5, 7], "precipType": ["rain", "rain", "rain", "rain", "rain", "precip", "rain", "precip", "rain", "precip", "rain", "precip"], "qpf": [0.0, 0.0, 0.0, 1.1, 4.78, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0], "qpfSnow": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "qualifierCode": ["Q5015", "Q5015", "Q5015", None, None, None, "Q1022", None, None, None, None, None], "qualifierPhrase": ["Eventuell Regenschauer.", "Eventuell Regenschauer.", "Eventuell Regenschauer.", None, None, None, "Windböen mit einer Stärke von stellenweise über 80 km/h.", None, None, None, None, None], "relativeHumidity": [62, 83, 54, 80, 68, 76, 69, 70, 49, 69, 39, 60], "snowRange": ["", "", "", "", "", "", "", "", "", "", "", ""], "temperature": [13, 6, 18, 5, 14, 4, 8, 2, 14, 1, 17, 1], "temperatureHeatIndex": [13, 10, 18, 11, 14, 7, 8, 5, 14, 8, 17, 9], "temperatureWindChill": [8, 5, 5, 5, 5, -1, -2, -1, -2, -2, -2, -1], "thunderCategory": [None, None, None, None, None, None, None, None, None, None, None, None], "thunderIndex": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "uvDescription": ["Niedrig", "Niedrig", "Mittel", "Niedrig", "Mittel", "Niedrig", "Mittel", "Niedrig", "Hoch", "Niedrig", "Mittel", "Niedrig"], "uvIndex": [2, 0, 4, 0, 4, 0, 5, 0, 6, 0, 5, 0], "windDirection": [182, 108, 188, 141, 201, 215, 223, 224, 209, 195, 205, 200], "windDirectionCardinal": ["S", "OSO", "S", "SO", "SSW", "SW", "SW", "SW", "SSW", "SSW", "SSW", "SSW"], "windPhrase": ["Wind aus S mit 15 bis 30 km/h.", "Wind aus OSO und wechselhaft.", "Wind aus S mit 10 bis 15 km/h.", "Wind aus SO und wechselhaft.", "Wind aus SSW mit 15 bis 30 km/h.", "Wind aus SW mit 15 bis 30 km/h, zunehmend auf 30 bis 50 km/h.", "Wind aus SW mit 40 bis 55 km/h.", "Wind aus SW mit 15 bis 30 km/h.", "Wind aus SSW mit 25 bis 40 km/h.", "Wind aus SSW mit 10 bis 15 km/h.", "Wind aus SSW mit 15 bis 30 km/h.", "Wind aus SSW mit 10 bis 15 km/h."], "windSpeed": [26, 9, 16, 9, 22, 40, 50, 26, 28, 15, 25, 14], "wxPhraseLong": ["Bedeckt", "Bedeckt", "Bedeckt", "Schauer", "Schauer", "Meist bedeckt/Wind", "Vorm. Schauer/Wind", "Stark bewölkt", "Meist sonnig", "Wolkig", "Wolkig", "Wolkig"], "wxPhraseShort": ["", "", "", "", "", "", "", "", "", "", "", ""]}]}
            # self.data = result
            _LOGGER.warning("LEAVING GET_WEATHER")
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
        _LOGGER.debug("IN GETTRAN")
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
