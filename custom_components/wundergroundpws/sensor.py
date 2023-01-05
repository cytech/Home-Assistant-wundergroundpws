"""
Support for WUndergroundPWS weather service.
For more details about this platform, please refer to the documentation at
https://github.com/cytech/Home-Assistant-wundergroundpws/tree/v1.X.X
"""

from .const import (
    CONF_ATTRIBUTION,
    DOMAIN,
    ENTRY_PWS_ID,
    ENTRY_WEATHER_COORDINATOR,
    TEMPUNIT,
    LENGTHUNIT,
    ALTITUDEUNIT,
    SPEEDUNIT,
    PRESSUREUNIT,
    RATE,
    PERCENTAGEUNIT, ENTRY_TRAN_FILE,
)

import logging
import re

import voluptuous as vol

from homeassistant.helpers.typing import HomeAssistantType, ConfigType
from homeassistant.components import sensor
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    CONF_MONITORED_CONDITIONS,
    ATTR_ATTRIBUTION, DEGREE, UnitOfIrradiance)

import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)


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
                 device_class=None, state_class=None):
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
        self.state_class = state_class


class WUCurrentConditionsSensorConfig(WUSensorConfig):
    """Helper for defining sensor configurations for current conditions."""

    def __init__(self, friendly_name, field, icon="mdi:gauge",
                 unit_of_measurement=None, device_class=None, state_class=None):
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
            value=lambda wu: wu.data['observations'][0][wu.unit_system][field],
            icon=icon,
            unit_of_measurement=lambda wu: wu.units_of_measurement[unit_of_measurement],
            device_state_attributes={
                'date': lambda wu: wu.data['observations'][0]['obsTimeLocal']
            },
            device_class=device_class,
            state_class=state_class
        )


class WUDailyTextForecastSensorConfig(WUSensorConfig):
    """Helper for defining sensor configurations for daily text forecasts.
    Wunderground API caveat: The daypart object as well as the temperatureMax field OUTSIDE of the daypart object
    will appear as null in the API after 3:00pm Local Apparent Time. """

    def __init__(self, period):
        """Constructor.
        Args:
            period (int): forecast period number
        """
        super().__init__(
            friendly_name=lambda wu: wu.data['daypart'][0]['daypartName'][period]
            if (wu.data['daypart'][0]['daypartName'][period] is not None) else 'N/A',
            feature='forecast',
            value=lambda wu: wu.data['daypart'][0]['narrative'][period]
            if (wu.data['daypart'][0]['narrative'][period] is not None) else 'N/A',
            entity_picture=lambda wu: '/local/wupws_icons/' +
                                      str(wu.data['daypart'][0]['iconCode'][period]) + '.png',
            device_state_attributes={
                'date': lambda wu: wu.data['observations'][0]['obsTimeLocal']
            }
        )


class WUDailySimpleForecastSensorConfig(WUSensorConfig):
    """Helper for defining sensor configurations for daily simpleforecasts.
    Wunderground API caveat: The daypart object as well as the temperatureMax field OUTSIDE of the daypart object
    will appear as null in the API after 3:00pm Local Apparent Time. """

    def __init__(self, friendly_name, period, field,
                 unit_of_measurement=None, icon=None, device_class=None, state_class=None):
        """Constructor.
        Args:
            period (int): forecast period number
            field (string): field name to use as value
            unit_of_measurement (string): corresponding unit in home assistant
        """
        super().__init__(
            friendly_name=friendly_name,
            feature='forecast',
            value=lambda wu: wu.data['daypart'][0][field][period]
            if (wu.data['daypart'][0][field][period] is not None) else 'N/A',
            unit_of_measurement=lambda wu: wu.units_of_measurement[unit_of_measurement]
            if (wu.data['daypart'][0][field][period] is not None) else '',
            entity_picture=lambda wu: str(
                wu.data['daypart'][0]['iconCode'][period]) if not icon else None,
            icon=icon,
            device_state_attributes={
                'date': lambda wu: wu.data['observations'][0]['obsTimeLocal']
            },
            device_class=device_class,
            state_class=state_class
        )


# Declaration of supported WU sensors
# (see above helper classes for argument explanation)

SENSOR_TYPES = {
    # current
    'neighborhood': WUSensorConfig(
        'Neighborhood', 'observations',
        value=lambda wu: wu.data['observations'][0]['neighborhood'],
        icon="mdi:map-marker"),
    'obsTimeLocal': WUSensorConfig(
        'Local Observation Time', 'observations',
        value=lambda wu: wu.data['observations'][0]['obsTimeLocal'],
        icon="mdi:clock"),
    'humidity': WUSensorConfig(
        'Relative Humidity', 'observations',
        value=lambda wu: int(wu.data['observations'][0]['humidity'] or 0),
        unit_of_measurement='%',
        icon="mdi:water-percent",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT),
    'stationID': WUSensorConfig(
        'Station ID', 'observations',
        value=lambda wu: wu.data['observations'][0]['stationID'],
        icon="mdi:home"),
    'solarRadiation': WUSensorConfig(
        'Solar Radiation', 'observations',
        value=lambda wu: str(wu.data['observations'][0]['solarRadiation']),
        unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
        icon="mdi:weather-sunny",
        device_class=SensorDeviceClass.IRRADIANCE,
        state_class=SensorStateClass.MEASUREMENT),
    'uv': WUSensorConfig(
        'UV Index', 'observations',
        value=lambda wu: str(wu.data['observations'][0]['uv']),
        unit_of_measurement='',
        icon="mdi:sunglasses",
        state_class=SensorStateClass.MEASUREMENT),
    'winddir': WUSensorConfig(
        'Wind Direction - Degrees', 'observations',
        value=lambda wu: int(wu.data['observations'][0]['winddir'] or 0),
        unit_of_measurement=DEGREE,
        icon="mdi:weather-windy",
        state_class=SensorStateClass.MEASUREMENT),
    'windDirectionName': WUSensorConfig(
        'Wind Direction - Cardinal', 'observations',
        value=lambda wu: wind_direction_to_friendly_name(
            int(wu.data['observations'][0]['winddir'] or -1)),
        unit_of_measurement='',
        icon="mdi:weather-windy"),
    'today_summary': WUSensorConfig(
        'Today Summary', 'observations',
        value=lambda wu: str(wu.data['narrative'][0]),
        unit_of_measurement='',
        icon="mdi:gauge"),
    # current conditions
    'elev': WUCurrentConditionsSensorConfig(
        'Elevation', 'elev', 'mdi:elevation-rise', ALTITUDEUNIT),
    'dewpt': WUCurrentConditionsSensorConfig(
        'Dewpoint', 'dewpt', 'mdi:water', TEMPUNIT, device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT),
    'heatIndex': WUCurrentConditionsSensorConfig(
        'Heat index', 'heatIndex', "mdi:thermometer", TEMPUNIT, device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT),
    'windChill': WUCurrentConditionsSensorConfig(
        'Wind chill', 'windChill', "mdi:thermometer", TEMPUNIT, device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT),
    'precipRate': WUCurrentConditionsSensorConfig(
        'Precipitation Rate', 'precipRate', "mdi:umbrella", RATE,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY, state_class=SensorStateClass.MEASUREMENT),
    'precipTotal': WUCurrentConditionsSensorConfig(
        'Precipitation Today', 'precipTotal', "mdi:umbrella", LENGTHUNIT, device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL_INCREASING),
    'pressure': WUCurrentConditionsSensorConfig(
        'Pressure', 'pressure', "mdi:gauge", PRESSUREUNIT,
        device_class=SensorDeviceClass.PRESSURE, state_class=SensorStateClass.MEASUREMENT),
    'temp': WUCurrentConditionsSensorConfig(
        'Temperature', 'temp', "mdi:thermometer", TEMPUNIT,
        device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    'windGust': WUCurrentConditionsSensorConfig(
        'Wind Gust', 'windGust', "mdi:weather-windy", SPEEDUNIT, device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT),
    'windSpeed': WUCurrentConditionsSensorConfig(
        'Wind Speed', 'windSpeed', "mdi:weather-windy", SPEEDUNIT, device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT),
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
        "mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE),
    'temp_high_2d': WUDailySimpleForecastSensorConfig(
        "High Temperature Tomorrow", 2, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE),
    'temp_high_3d': WUDailySimpleForecastSensorConfig(
        "High Temperature in 3 Days", 4, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE),
    'temp_high_4d': WUDailySimpleForecastSensorConfig(
        "High Temperature in 4 Days", 6, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE),
    'temp_high_5d': WUDailySimpleForecastSensorConfig(
        "High Temperature in 5 Days", 8, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE),
    'temp_low_1d': WUDailySimpleForecastSensorConfig(
        "Low Temperature Today", 1, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE),
    'temp_low_2d': WUDailySimpleForecastSensorConfig(
        "Low Temperature Tomorrow", 3, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE),
    'temp_low_3d': WUDailySimpleForecastSensorConfig(
        "Low Temperature in 3 Days", 5, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE),
    'temp_low_4d': WUDailySimpleForecastSensorConfig(
        "Low Temperature in 4 Days", 7, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE),
    'temp_low_5d': WUDailySimpleForecastSensorConfig(
        "Low Temperature in 5 Days", 9, "temperature", TEMPUNIT,
        "mdi:thermometer", device_class=SensorDeviceClass.TEMPERATURE),
    'wind_1d': WUDailySimpleForecastSensorConfig(
        "Avg. Wind Today", 0, "windSpeed", SPEEDUNIT,
        "mdi:weather-windy", device_class=SensorDeviceClass.WIND_SPEED),
    'wind_2d': WUDailySimpleForecastSensorConfig(
        "Avg. Wind Tomorrow", 2, "windSpeed", SPEEDUNIT,
        "mdi:weather-windy", device_class=SensorDeviceClass.WIND_SPEED),
    'wind_3d': WUDailySimpleForecastSensorConfig(
        "Avg. Wind in 3 Days", 4, "windSpeed", SPEEDUNIT,
        "mdi:weather-windy", device_class=SensorDeviceClass.WIND_SPEED),
    'wind_4d': WUDailySimpleForecastSensorConfig(
        "Avg. Wind in 4 Days", 6, "windSpeed", SPEEDUNIT,
        "mdi:weather-windy", device_class=SensorDeviceClass.WIND_SPEED),
    'wind_5d': WUDailySimpleForecastSensorConfig(
        "Avg. Wind in 5 Days", 8, "windSpeed", SPEEDUNIT,
        "mdi:weather-windy", device_class=SensorDeviceClass.WIND_SPEED),
    'precip_1d': WUDailySimpleForecastSensorConfig(
        "Precipitation Amount Today", 0, 'qpf', LENGTHUNIT,
        "mdi:umbrella", device_class=SensorDeviceClass.PRECIPITATION),
    'precip_2d': WUDailySimpleForecastSensorConfig(
        "Precipitation Amount Tomorrow", 2, 'qpf', LENGTHUNIT,
        "mdi:umbrella", device_class=SensorDeviceClass.PRECIPITATION),
    'precip_3d': WUDailySimpleForecastSensorConfig(
        "Precipitation Amount in 3 Days", 4, 'qpf', LENGTHUNIT,
        "mdi:umbrella", device_class=SensorDeviceClass.PRECIPITATION),
    'precip_4d': WUDailySimpleForecastSensorConfig(
        "Precipitation Amount in 4 Days", 6, 'qpf', LENGTHUNIT,
        "mdi:umbrella", device_class=SensorDeviceClass.PRECIPITATION),
    'precip_5d': WUDailySimpleForecastSensorConfig(
        "Precipitation Amount in 5 Days", 8, 'qpf', LENGTHUNIT,
        "mdi:umbrella", device_class=SensorDeviceClass.PRECIPITATION),
    'precip_chance_1d': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability Today", 0, "precipChance", PERCENTAGEUNIT,
        "mdi:umbrella"),
    'precip_chance_2d': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability Tomorrow (Day)", 2, "precipChance", PERCENTAGEUNIT,
        "mdi:umbrella"),
    'precip_chance_3d': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability in 3 Days (Day)", 4, "precipChance", PERCENTAGEUNIT,
        "mdi:umbrella"),
    'precip_chance_4d': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability in 4 Days (Day)", 6, "precipChance", PERCENTAGEUNIT,
        "mdi:umbrella"),
    'precip_chance_5d': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability in 5 Days (Day)", 8, "precipChance", PERCENTAGEUNIT,
        "mdi:umbrella"),
    'precip_chance_1n': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability Tonight", 1, "precipChance", PERCENTAGEUNIT,
        "mdi:umbrella"),
    'precip_chance_2n': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability Tomorrow Night", 3, "precipChance", PERCENTAGEUNIT,
        "mdi:umbrella"),
    'precip_chance_3n': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability in 3 Days (Night)", 5, "precipChance", PERCENTAGEUNIT,
        "mdi:umbrella"),
    'precip_chance_4n': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability in 4 Days (Night)", 7, "precipChance", PERCENTAGEUNIT,
        "mdi:umbrella"),
    'precip_chance_5n': WUDailySimpleForecastSensorConfig(
        "Precipitation Probability in 5 Days (Night)", 9, "precipChance", PERCENTAGEUNIT,
        "mdi:umbrella"),
}


def wind_direction_to_friendly_name(argument):
    if (argument < 0):
        return ""
    if 348.75 <= argument or 11.25 > argument:
        return "N"
    if 11.25 <= argument < 33.75:
        return "NNE"
    if 33.75 <= argument < 56.25:
        return "NE"
    if 56.25 <= argument < 78.75:
        return "ENE"
    if 78.75 <= argument < 101.25:
        return "E"
    if 101.25 <= argument < 123.75:
        return "ESE"
    if 123.75 <= argument < 146.25:
        return "SE"
    if 146.25 <= argument < 168.75:
        return "SSE"
    if 168.75 <= argument < 191.25:
        return "S"
    if 191.25 <= argument < 213.75:
        return "SSW"
    if 213.75 <= argument < 236.25:
        return "SW"
    if 236.25 <= argument < 258.75:
        return "WSW"
    if 258.75 <= argument < 281.25:
        return "W"
    if 281.25 <= argument < 303.75:
        return "WNW"
    if 303.75 <= argument < 326.25:
        return "NW"
    if 326.25 <= argument < 348.75:
        return "NNW"
    return ""


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MONITORED_CONDITIONS):
        vol.All(cv.ensure_list, vol.Length(min=1), [vol.In(SENSOR_TYPES)])
})


async def async_setup_platform(hass: HomeAssistantType, config: ConfigType,
                               async_add_entities, discovery_info=None):
    rest = hass.data[DOMAIN][ENTRY_WEATHER_COORDINATOR]

    #     unique_id_base = "@{:06f},{:06f}".format(longitude, latitude)
    # else:
    #     # Manually specified weather station, use that for unique_id
    #     unique_id_base = pws_id
    unique_id_base = hass.data[DOMAIN][ENTRY_PWS_ID]
    sensors = []

    for variable in config[CONF_MONITORED_CONDITIONS]:
        sensors.append(WUndergroundSensor(hass, rest, variable,
                                          unique_id_base))

    async_add_entities(sensors, True)


class WUndergroundSensor(SensorEntity):
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
        self._state_class = self._cfg_expand("state_class")

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
        if self._condition in self.hass.data[DOMAIN][ENTRY_TRAN_FILE].keys():
            return self.hass.data[DOMAIN][ENTRY_TRAN_FILE][self._condition]
        return self._cfg_expand("friendly_name")

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
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

    @property
    def state_class(self):
        """Return the state class."""
        return self._state_class

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

