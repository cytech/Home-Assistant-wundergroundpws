"""
Support for WUndergroundPWS weather service.
For more details about this platform, please refer to the documentation at
https://github.com/cytech/Home-Assistant-wundergroundpws/tree/v1.X.X
"""
from .const import (
    DOMAIN,
    MANUFACTURER,
    NAME,

    ENTRY_PWS_ID,
    ENTRY_WEATHER_COORDINATOR,

    TEMPUNIT,
    LENGTHUNIT,
    SPEEDUNIT,
    PRESSUREUNIT,

    FIELD_CONDITION_HUMIDITY,
    FIELD_CONDITION_PRESSURE,
    FIELD_CONDITION_TEMP,
    FIELD_CONDITION_WINDDIR,
    FIELD_CONDITION_WINDSPEED,

    FIELD_FORECAST_VALIDTIMEUTC,
    FIELD_FORECAST_PRECIPCHANCE,
    FIELD_FORECAST_QPF,
    FIELD_FORECAST_TEMPERATUREMAX,
    FIELD_FORECAST_TEMPERATUREMIN,
    FIELD_FORECAST_WINDDIRECTIONCARDINAL,
    FIELD_FORECAST_WINDSPEED,
    FIELD_FORECAST_ICONCODE,
)

import logging

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_WIND_SPEED,
    WeatherEntity,
    Forecast,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from .wunderground_data import WUndergroundData

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None
) -> None:
    """Set up WeatherUnderground weather entity based on a config entry."""
    domain_data = hass.data[DOMAIN]
    rest = domain_data[ENTRY_WEATHER_COORDINATOR]

    unique_id = hass.data[DOMAIN][ENTRY_PWS_ID]

    wu_weather = WUWeather(unique_id, unique_id, rest)
    async_add_entities([wu_weather], False)


class WUWeather(WeatherEntity):

    def __init__(
        self,
        name: str,
        unique_id: str,
        wunderground_data: WUndergroundData
    ) -> None:
        """Initialize the sensor."""
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, unique_id)},
            manufacturer=MANUFACTURER,
            name=NAME,
        )
        self._rest = wunderground_data

    @property
    def native_temperature(self) -> float:
        """
        Return the platform temperature in native units
        (i.e. not converted).
        """
        return self._rest.get_condition(FIELD_CONDITION_TEMP)

    @property
    def native_temperature_unit(self) -> str:
        """Return the native unit of measurement for temperature."""
        return self._rest.units_of_measurement[TEMPUNIT]

    @property
    def native_pressure(self) -> float:
        """Return the pressure in native units."""
        pressure = self._rest.get_condition(FIELD_CONDITION_PRESSURE)
        if pressure is not None:
            return self._rest.get_condition(FIELD_CONDITION_PRESSURE)

    @property
    def native_pressure_unit(self) -> str:
        """Return the native unit of measurement for pressure."""
        return self._rest.units_of_measurement[PRESSUREUNIT]

    @property
    def humidity(self) -> float:
        """Return the humidity in native units."""
        return self._rest.get_condition(FIELD_CONDITION_HUMIDITY)

    @property
    def native_wind_speed(self) -> float:
        """Return the wind speed in native units."""
        return self._rest.get_condition(FIELD_CONDITION_WINDSPEED)

    @property
    def native_wind_speed_unit(self) -> str:
        """Return the native unit of measurement for wind speed."""
        return self._rest.units_of_measurement[SPEEDUNIT]

    @property
    def wind_bearing(self) -> str:
        """Return the wind bearing."""
        return self._rest.get_condition(FIELD_CONDITION_WINDDIR)

    @property
    def ozone(self) -> float:
        """Return the ozone level."""
        return self._attr_ozone

    @property
    def native_visibility(self) -> float:
        """Return the visibility in native units."""
        return self._attr_visibility

    @property
    def native_visibility_unit(self) -> str:
        """Return the native unit of measurement for visibility."""
        return self._attr_visibility_unit

    @property
    def forecast(self) -> list[Forecast]:
        """Return the forecast in native units."""
        days = [0, 2, 4, 6, 8]
        if self._rest.get_forecast('temperature', 0) is None:
            days[0] += 1

        forecast = [
            Forecast({
                ATTR_FORECAST_CONDITION:
                self._rest._iconCode_to_condition(
                    self._rest.get_forecast(
                        FIELD_FORECAST_ICONCODE, period)
                ),
                ATTR_FORECAST_PRECIPITATION:
                self._rest.get_forecast(FIELD_FORECAST_QPF, period),
                ATTR_FORECAST_PRECIPITATION_PROBABILITY:
                self._rest.get_forecast(FIELD_FORECAST_PRECIPCHANCE, period),

                ATTR_FORECAST_TEMP:
                self._rest.get_forecast(FIELD_FORECAST_TEMPERATUREMAX, period),
                # Use the min temperature from the next prediction,
                # as otherwise it is too similar to the current max
                # and is not as useful
                ATTR_FORECAST_TEMP_LOW:
                self._rest.get_forecast(
                    FIELD_FORECAST_TEMPERATUREMIN, period+1),

                ATTR_FORECAST_TIME:
                self._rest.get_forecast(
                    FIELD_FORECAST_VALIDTIMEUTC, period) * 1000,

                ATTR_FORECAST_WIND_BEARING:
                self._rest.get_forecast(
                    FIELD_FORECAST_WINDDIRECTIONCARDINAL, period),
                ATTR_FORECAST_WIND_SPEED: self._rest.get_forecast(
                    FIELD_FORECAST_WINDSPEED, period)
            })
            for period in days
        ]
        # _LOGGER.debug(f'{forecast=}')
        return forecast

    @property
    def native_precipitation_unit(self) -> str:
        """
        Return the native unit of measurement for accumulated precipitation.
        """
        return self._rest.units_of_measurement[LENGTHUNIT]

    @property
    def condition(self) -> str:
        """Return the current condition."""
        day = self._rest.get_forecast(FIELD_FORECAST_ICONCODE)
        night = self._rest.get_forecast(FIELD_FORECAST_ICONCODE, 1)
        return self._rest._iconCode_to_condition(day or night)
