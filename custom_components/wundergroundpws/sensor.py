"""
Support for WUndergroundPWS weather service.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.wundergroundpws/
"""
import asyncio
from datetime import timedelta
import logging
import re

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.helpers.typing import HomeAssistantType, ConfigType
from homeassistant.components import sensor
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_MONITORED_CONDITIONS, CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE,
    TEMP_FAHRENHEIT, TEMP_CELSIUS, LENGTH_INCHES,
    LENGTH_FEET, ATTR_ATTRIBUTION)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv
import homeassistant.config as config

_RESOURCECURRENT = 'https://api.weather.com/v2/pws/observations/current?stationId={}&format=json&units={}&apiKey={}'
_RESOURCEFORECAST = 'https://api.weather.com/v3/wx/forecast/daily/5day?geocode={},{}&units={}&{}&format=json&apiKey={}'
_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = "Data provided by the WUnderground weather service"
CONF_PWS_ID = 'pws_id'
CONF_LANG = 'lang'
LENGTH_MILLIMETERS = 'mm'
LENGTH_METERS = 'm'

DEFAULT_LANG = 'en-US'

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)

conf_file = config.get_default_config_dir() + '/configuration.yaml'
load_config = config.load_yaml_config_file(conf_file)

try:
    UNIT_SYSTEM = load_config['homeassistant']['unit_system']
except KeyError as err:
    UNIT_SYSTEM = "metric"

if UNIT_SYSTEM == 'imperial':
    TEMPUNIT = TEMP_FAHRENHEIT
    LENGTHUNIT = LENGTH_INCHES
    ALTITUDEUNIT = LENGTH_FEET
    SPEEDUNIT = 'mph'
    PRESSUREUNIT = 'inHg'
else:
    TEMPUNIT = TEMP_CELSIUS
    LENGTHUNIT = LENGTH_MILLIMETERS
    ALTITUDEUNIT = LENGTH_METERS
    SPEEDUNIT = 'kph'
    PRESSUREUNIT = 'mBar'


# Helper classes for declaring sensor configurations

class WUSensorConfig:
    """WU Sensor Configuration.

    defines basic HA properties of the weather sensor and
    stores callbacks that can parse sensor values out of
    the json data received by WU API.
    """

    def __init__(self, friendly_name, feature, value,
                 unit_of_measurement=None, entity_picture=None,
                 icon="mdi:gauge", device_state_attributes=None,
                 device_class=None):
        """Constructor.

        Args:
            friendly_name (string|func): Friendly name
            feature (string): WU feature. See:
                https://docs.google.com/document/d/1eKCnKXI9xnoMGRRzOL1xPCBihNV2rOet08qpE_gArAY/edit
            value (function(WUndergroundData)): callback that
                extracts desired value from WUndergroundData object
            unit_of_measurement (string): unit of measurement
            entity_picture (string): value or callback returning
                URL of entity picture
            icon (string): icon name
            device_state_attributes (dict): dictionary of attributes,
                or callable that returns it
        """
        self.friendly_name = friendly_name
        self.unit_of_measurement = unit_of_measurement
        self.feature = feature
        self.value = value
        self.entity_picture = entity_picture
        self.icon = icon
        self.device_state_attributes = device_state_attributes or {}
        self.device_class = device_class


class WUCurrentConditionsSensorConfig(WUSensorConfig):
    """Helper for defining sensor configurations for current conditions."""

    def __init__(self, friendly_name, unit_system, field, icon="mdi:gauge",
                 unit_of_measurement=None, device_class=None):
        """Constructor.

        Args:
            friendly_name (string|func): Friendly name of sensor
            field (string): Field name in the "observations[0][unit_system]"
                            dictionary.
            icon (string): icon name , if None sensor
                           will use current weather symbol
            unit_of_measurement (string): unit of measurement
        """
        super().__init__(
            friendly_name,
            "conditions",
            value=lambda wu: wu.data['observations'][0][unit_system][field],
            icon=icon,
            unit_of_measurement=unit_of_measurement,
            device_state_attributes={
                'date': lambda wu: wu.data['observations'][0][
                    'obsTimeLocal']
            },
            device_class=device_class
        )


class WUDailyTextForecastSensorConfig(WUSensorConfig):
    """Helper for defining sensor configurations for daily text forecasts."""

    def __init__(self, period, field=None, unit_of_measurement=None):
        """Constructor.

        Args:
            period (int): forecast period number
            field (string):  field name to use as value
            unit_of_measurement(string): unit of measurement
        """
        super().__init__(
            friendly_name=lambda wu: wu.data['daypart'][0]['daypartName'][period],
            feature='forecast',
            value=lambda wu: wu.data['daypart'][0]['narrative'][period],
            entity_picture=lambda wu: '/local/wupws_icons/' + str(wu.data['daypart'][0]['iconCode'][period]) + '.png',
            unit_of_measurement=unit_of_measurement,
            device_state_attributes={
                'date': lambda wu: wu.data['observations'][0]['obsTimeLocal']
            }
        )


class WUDailySimpleForecastSensorConfig(WUSensorConfig):
    """Helper for defining sensor configurations for daily simpleforecasts."""

    def __init__(self, friendly_name, period, field,
                 ha_unit=None, icon=None, device_class=None):
        """Constructor.

        Args:
            period (int): forecast period number
            field (string): field name to use as value
            ha_unit (string): corresponding unit in home assistant
            title (string): friendly_name of the sensor
        """
        super().__init__(
            friendly_name=friendly_name,
            feature='forecast',
            value=(lambda wu: wu.data['daypart'][0][field][period]),
            unit_of_measurement=ha_unit,
            entity_picture=lambda wu: wu.data['daypart'][0]['iconCode'][period] if not icon else None,
            icon=icon,
            device_state_attributes={
                'date': lambda wu: wu.data['observations'][0]['obsTimeLocal']
            },
            device_class=device_class
        )


# Declaration of supported WU sensors
# (see above helper classes for argument explanation)

SENSOR_TYPES = {
    # current
    'neighborhood': WUSensorConfig(
        'Neighborhood',
        'observations',
        value=lambda wu: wu.data['observations'][0][
            'neighborhood'],
        icon="mdi:map-marker"),
    'obsTimeLocal': WUSensorConfig(
        'Local Observation Time',
        'observations',
        value=lambda wu: wu.data['observations'][0][
            'obsTimeLocal'],
        icon="mdi:clock"),
    'humidity': WUSensorConfig(
        'Relative Humidity',
        'observations',
        value=lambda wu: int(wu.data['observations'][0][
                                 'humidity']),
        unit_of_measurement='%',
        icon="mdi:water-percent",
        device_class="humidity"),
    'stationID': WUSensorConfig(
        'Station ID',
        'observations',
        value=lambda wu: wu.data['observations'][0][
            'stationID'],
        icon="mdi:home"),
    'solarRadiation': WUSensorConfig(
        'Solar Radiation',
        'observations',
        value=lambda wu: str(wu.data['observations'][0][
                                 'solarRadiation']),
        unit_of_measurement='w/m2',
        icon="mdi:weather-sunny"),
    'uv': WUSensorConfig(
        'UV',
        'observations',
        value=lambda wu: str(wu.data['observations'][0][
                                 'uv']),
        unit_of_measurement='',
        icon="mdi:sunglasses", ),
    'winddir': WUSensorConfig(
        'Wind Direction',
        'observations',
        value=lambda wu: int(wu.data['observations'][0][
                                 'winddir']),
        unit_of_measurement='\u00b0',
        icon="mdi:weather-windy"),
    'today_summary': WUSensorConfig(
        'Today Summary',
        'observations',
        value=lambda wu: str(wu.data['narrative'][0]),
        unit_of_measurement='\u00b0',
        icon="mdi:gauge"),
    'elev': WUCurrentConditionsSensorConfig(
        'Elevation', UNIT_SYSTEM, 'elev', 'mdi:elevation-rise', ALTITUDEUNIT),
    'dewpt': WUCurrentConditionsSensorConfig(
        'Dewpoint', UNIT_SYSTEM, 'dewpt', 'mdi:water', TEMPUNIT),
    'heatIndex': WUCurrentConditionsSensorConfig(
        'Heat index', UNIT_SYSTEM, 'heatIndex', "mdi:thermometer", TEMPUNIT),
    'windChill': WUCurrentConditionsSensorConfig(
        'Wind chill', UNIT_SYSTEM, 'windChill', "mdi:thermometer", TEMPUNIT),
    'precipRate': WUCurrentConditionsSensorConfig(
        'Precipitation Rate', UNIT_SYSTEM, 'precipRate', "mdi:umbrella", LENGTHUNIT),
    'precipTotal': WUCurrentConditionsSensorConfig(
        'Precipitation Today', UNIT_SYSTEM, 'precipTotal', "mdi:umbrella", LENGTHUNIT),
    'pressure': WUCurrentConditionsSensorConfig(
        'Pressure', UNIT_SYSTEM, 'pressure', "mdi:gauge", PRESSUREUNIT,
        device_class="pressure"),
    'temp': WUCurrentConditionsSensorConfig(
        'Temperature', UNIT_SYSTEM, 'temp', "mdi:thermometer", TEMPUNIT,
        device_class="temperature"),
    'windGust': WUCurrentConditionsSensorConfig(
        'Wind Gust', UNIT_SYSTEM, 'windGust', "mdi:weather-windy", SPEEDUNIT),
    'windSpeed': WUCurrentConditionsSensorConfig(
        'Wind Speed', UNIT_SYSTEM, 'windSpeed', "mdi:weather-windy", SPEEDUNIT),
    # forecast
    'weather_1d': WUDailyTextForecastSensorConfig(0),
    'weather_1n': WUDailyTextForecastSensorConfig(1),
    'weather_2d': WUDailyTextForecastSensorConfig(2),
    'weather_2n': WUDailyTextForecastSensorConfig(3),
    'weather_3d': WUDailyTextForecastSensorConfig(4),
    'weather_3n': WUDailyTextForecastSensorConfig(5),
    'weather_4d': WUDailyTextForecastSensorConfig(6),
    'weather_4n': WUDailyTextForecastSensorConfig(7),
    'weather_5d': WUDailyTextForecastSensorConfig(8),
    'weather_5n': WUDailyTextForecastSensorConfig(9),
    'temp_high_1d': WUDailySimpleForecastSensorConfig(
        "High Temperature Today", 0, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class="temperature"),
    'temp_high_2d': WUDailySimpleForecastSensorConfig(
        "High Temperature Tomorrow", 2, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class="temperature"),
    'temp_high_3d': WUDailySimpleForecastSensorConfig(
        "High Temperature in 3 Days", 4, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class="temperature"),
    'temp_high_4d': WUDailySimpleForecastSensorConfig(
        "High Temperature in 4 Days", 6, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class="temperature"),
    'temp_high_5d': WUDailySimpleForecastSensorConfig(
        "High Temperature in 5 Days", 8, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class="temperature"),
    'temp_low_1d': WUDailySimpleForecastSensorConfig(
        "Low Temperature Today", 1, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class="temperature"),
    'temp_low_2d': WUDailySimpleForecastSensorConfig(
        "Low Temperature Tomorrow", 3, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class="temperature"),
    'temp_low_3d': WUDailySimpleForecastSensorConfig(
        "Low Temperature in 3 Days", 5, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class="temperature"),
    'temp_low_4d': WUDailySimpleForecastSensorConfig(
        "Low Temperature in 4 Days", 7, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class="temperature"),
    'temp_low_5d': WUDailySimpleForecastSensorConfig(
        "Low Temperature in 5 Days", 9, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class="temperature"),
    'wind_1d': WUDailySimpleForecastSensorConfig(
        "Avg. Wind Today", 0, "windSpeed", SPEEDUNIT,
        "mdi:weather-windy"),
    'wind_2d': WUDailySimpleForecastSensorConfig(
        "Avg. Wind Tomorrow", 2, "windSpeed", SPEEDUNIT,
        "mdi:weather-windy"),
    'wind_3d': WUDailySimpleForecastSensorConfig(
        "Avg. Wind in 3 Days", 4, "windSpeed", SPEEDUNIT,
        "mdi:weather-windy"),
    'wind_4d': WUDailySimpleForecastSensorConfig(
        "Avg. Wind in 4 Days", 6, "windSpeed", SPEEDUNIT,
        "mdi:weather-windy"),
    'wind_5d': WUDailySimpleForecastSensorConfig(
        "Avg. Wind in 5 Days", 8, "windSpeed", SPEEDUNIT,
        "mdi:weather-windy"),
    'precip_1d': WUDailySimpleForecastSensorConfig(
        "Precipitation Intensity Today", 0, 'qpf', LENGTHUNIT,
        "mdi:umbrella"),
    'precip_2d': WUDailySimpleForecastSensorConfig(
        "Precipitation Intensity Tomorrow", 2, 'qpf', LENGTHUNIT,
        "mdi:umbrella"),
    'precip_3d': WUDailySimpleForecastSensorConfig(
        "Precipitation Intensity in 3 Days", 4, 'qpf', LENGTHUNIT,
        "mdi:umbrella"),
    'precip_4d': WUDailySimpleForecastSensorConfig(
        "Precipitation Intensity in 4 Days", 6, 'qpf', LENGTHUNIT,
        "mdi:umbrella"),
    'precip_5d': WUDailySimpleForecastSensorConfig(
        "Precipitation Intensity in 5 Days", 8, 'qpf', LENGTHUNIT,
        "mdi:umbrella"),
    'precip_chance_1d': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability Today", 0, "precipChance", "%",
        "mdi:umbrella"),
    'precip_chance_2d': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability Tomorrow", 2, "precipChance", "%",
        "mdi:umbrella"),
    'precip_chance_3d': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability in 3 Days", 4, "precipChance", "%",
        "mdi:umbrella"),
    'precip_chance_4d': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability in 4 Days", 6, "precipChance", "%",
        "mdi:umbrella"),
    'precip_chance_5d': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability in 5 Days", 8, "precipChance", "%",
        "mdi:umbrella"),
}

# Language Supported Codes
LANG_CODES = [
    'ar-AE', 'az-AZ', 'bg-BG', 'bn-BD', 'bn-IN', 'bs-BA', 'ca-ES', 'cs-CZ', 'da-DK', 'de-DE', 'el-GR', 'en-GB', 'en-IN',
    'en-US', 'es-AR', 'es-ES', 'es-LA', 'es-MX', 'es-UN', 'es-US', 'et-EE', 'fa-IR', 'fi-FI', 'fr-CA', 'fr-FR', 'gu-IN',
    'he-IL', 'hi-IN', 'hr-HR', 'hu-HU', 'in-ID', 'is-IS', 'it-IT', 'iw-IL', 'ja-JP', 'jv-ID', 'ka-GE', 'kk-KZ', 'kn-IN',
    'ko-KR', 'lt-LT', 'lv-LV', 'mk-MK', 'mn-MN', 'ms-MY', 'nl-NL', 'no-NO', 'pl-PL', 'pt-BR', 'pt-PT', 'ro-RO', 'ru-RU',
    'si-LK', 'sk-SK', 'sl-SI', 'sq-AL', 'sr-BA', 'sr-ME', 'sr-RS', 'sv-SE', 'sw-KE', 'ta-IN', 'ta-LK', 'te-IN', 'tg-TJ',
    'th-TH', 'tk-TM', 'tl-PH', 'tr-TR', 'uk-UA', 'ur-PK', 'uz-UZ', 'vi-VN', 'zh-CN', 'zh-HK', 'zh-TW'
]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_PWS_ID): cv.string,
    vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.All(vol.In(LANG_CODES)),
    vol.Inclusive(CONF_LATITUDE, 'coordinates',
                  'Latitude and longitude must exist together'): cv.latitude,
    vol.Inclusive(CONF_LONGITUDE, 'coordinates',
                  'Latitude and longitude must exist together'): cv.longitude,
    vol.Required(CONF_MONITORED_CONDITIONS):
        vol.All(cv.ensure_list, vol.Length(min=1), [vol.In(SENSOR_TYPES)])
})


async def async_setup_platform(hass: HomeAssistantType, config: ConfigType,
                               async_add_entities, discovery_info=None):
    """Set up the WUnderground sensor."""
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    pws_id = config.get(CONF_PWS_ID)

    if hass.config.units.is_metric:
        unit_system_api = 'm'
    else:
        unit_system_api = 'e'

    rest = WUndergroundData(
        hass, config.get(CONF_API_KEY), pws_id, unit_system_api,
        config.get(CONF_LANG), latitude, longitude)

    if pws_id is None:
        unique_id_base = "@{:06f},{:06f}".format(longitude, latitude)
    else:
        # Manually specified weather station, use that for unique_id
        unique_id_base = pws_id
    sensors = []
    for variable in config[CONF_MONITORED_CONDITIONS]:
        sensors.append(WUndergroundSensor(hass, rest, variable,
                                          unique_id_base))

    await rest.async_update()
    if not rest.data:
        raise PlatformNotReady

    async_add_entities(sensors, True)


class WUndergroundSensor(Entity):
    """Implementing the WUnderground sensor."""

    def __init__(self, hass: HomeAssistantType, rest, condition,
                 unique_id_base: str):
        """Initialize the sensor."""
        self.rest = rest
        self._condition = condition
        self._state = None
        self._attributes = {
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
        }
        self._icon = None
        self._entity_picture = None
        self._unit_of_measurement = self._cfg_expand("unit_of_measurement")
        self.rest.request_feature(SENSOR_TYPES[condition].feature)
        # This is only the suggested entity id, it might get changed by
        # the entity registry later.
        self.entity_id = sensor.ENTITY_ID_FORMAT.format('wupws_' + condition)
        self._unique_id = "{},{}".format(unique_id_base, condition)
        self._device_class = self._cfg_expand("device_class")

    def _cfg_expand(self, what, default=None):
        """Parse and return sensor data."""
        cfg = SENSOR_TYPES[self._condition]
        val = getattr(cfg, what)
        if not callable(val):
            return val
        try:
            val = val(self.rest)
        except (KeyError, IndexError, TypeError, ValueError) as err:
            _LOGGER.warning("Failed to expand cfg from WU API."
                            " Condition: %s Attr: %s Error: %s",
                            self._condition, what, repr(err))
            val = default

        return val

    def _update_attrs(self):
        """Parse and update device state attributes."""
        attrs = self._cfg_expand("device_state_attributes", {})

        for (attr, callback) in attrs.items():
            if callable(callback):
                try:
                    self._attributes[attr] = callback(self.rest)
                except (KeyError, IndexError, TypeError, ValueError) as err:
                    _LOGGER.warning("Failed to update attrs from WU API."
                                    " Condition: %s Attr: %s Error: %s",
                                    self._condition, attr, repr(err))
            else:
                self._attributes[attr] = callback

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._cfg_expand("friendly_name")

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Return icon."""
        return self._icon

    @property
    def entity_picture(self):
        """Return the entity picture."""
        return self._entity_picture

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Return the units of measurement."""
        return self._device_class

    async def async_update(self):
        """Update current conditions."""
        await self.rest.async_update()

        if not self.rest.data:
            # no data, return
            return

        self._state = self._cfg_expand("value")
        self._update_attrs()
        self._icon = self._cfg_expand("icon", super().icon)
        url = self._cfg_expand("entity_picture")
        if isinstance(url, str):
            self._entity_picture = re.sub(r'^http://', 'https://',
                                          url, flags=re.IGNORECASE)

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id


class WUndergroundData:
    """Get data from WUnderground."""

    def __init__(self, hass, api_key, pws_id, unit_system_api, lang, latitude, longitude):
        """Initialize the data object."""
        self._hass = hass
        self._api_key = api_key
        self._pws_id = pws_id
        self._unit_system_api = unit_system_api
        self._lang = 'language={}'.format(lang)
        self._latitude = latitude
        self._longitude = longitude
        self._features = set()
        self.data = None
        self._session = async_get_clientsession(self._hass)

    def request_feature(self, feature):
        """Register feature to be fetched from WU API."""
        self._features.add(feature)

    def _build_url(self, baseurl):
        if baseurl is _RESOURCECURRENT:
            url = baseurl.format(self._pws_id, self._unit_system_api, self._api_key)
        else:
            url = baseurl.format(self._latitude, self._longitude, self._unit_system_api, self._lang, self._api_key)

        return url

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Get the latest data from WUnderground."""
        headers = {'Accept-Encoding': 'gzip'}
        try:
            with async_timeout.timeout(10, loop=self._hass.loop):
                response = await self._session.get(self._build_url(_RESOURCECURRENT), headers=headers)
            result_current = await response.json()

            # need to check specific new api errors
            # if "error" in result['response']:
            #     raise ValueError(result['response']["error"]["description"])
            # _LOGGER.debug('result_current' + str(result_current))

            if result_current is None:
                raise ValueError('NO CURRENT RESULT')
            with async_timeout.timeout(10, loop=self._hass.loop):
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
