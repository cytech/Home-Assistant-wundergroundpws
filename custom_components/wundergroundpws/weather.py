"""
Support for WUndergroundPWS weather service.
For more details about this platform, please refer to the documentation at
https://github.com/cytech/Home-Assistant-wundergroundpws/tree/v2.X.X
"""

from . import WundergroundPWSUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from .const import (
    DOMAIN,

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
    FIELD_FORECAST_CALENDARDAYTEMPERATUREMAX,
    FIELD_FORECAST_CALENDARDAYTEMPERATUREMIN,
    FIELD_FORECAST_WINDDIRECTIONCARDINAL,
    FIELD_FORECAST_WINDSPEED,
    FIELD_FORECAST_ICONCODE, CONF_PWS_ID,
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
    WeatherEntityFeature,
    Forecast,
    DOMAIN as WEATHER_DOMAIN
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

ENTITY_ID_FORMAT = WEATHER_DOMAIN + ".{}"


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add weather entity."""
    pws_id: str = entry.data[CONF_PWS_ID]
    coordinator: WundergroundPWSUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WUWeather(pws_id, coordinator)])


class WUWeather(CoordinatorEntity, WeatherEntity):

    def __init__(
            self,
            pws_id: str,
            coordinator: WundergroundPWSUpdateCoordinator
    ):
        super().__init__(coordinator)
        """Initialize the sensor."""
        self._attr_name = pws_id
        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, f"{self._attr_name}", hass=coordinator.hass
        )
        self._attr_unique_id = f"{coordinator.pws_id},{WEATHER_DOMAIN}".lower()

    @property
    def supported_features(self) -> int | None:
        """Flag supported features."""
        # return WeatherEntityFeature.FORECAST_HOURLY if self.coordinator.config.hourly_forecast else WeatherEntityFeature.FORECAST_DAILY
        return WeatherEntityFeature.FORECAST_DAILY

    @property
    def native_temperature(self) -> float:
        """
        Return the platform temperature in native units
        (i.e. not converted).
        """
        return self.coordinator.get_condition(FIELD_CONDITION_TEMP)

    @property
    def native_temperature_unit(self) -> str:
        """Return the native unit of measurement for temperature."""
        return self.coordinator.units_of_measurement[TEMPUNIT]

    @property
    def native_pressure(self) -> float:
        """Return the pressure in native units."""
        pressure = self.coordinator.get_condition(FIELD_CONDITION_PRESSURE)
        if pressure is not None:
            return self.coordinator.get_condition(FIELD_CONDITION_PRESSURE)

    @property
    def native_pressure_unit(self) -> str:
        """Return the native unit of measurement for pressure."""
        return self.coordinator.units_of_measurement[PRESSUREUNIT]

    @property
    def humidity(self) -> float:
        """Return the humidity in native units."""
        return self.coordinator.get_condition(FIELD_CONDITION_HUMIDITY)

    @property
    def native_wind_speed(self) -> float:
        """Return the wind speed in native units."""
        return self.coordinator.get_condition(FIELD_CONDITION_WINDSPEED)

    @property
    def native_wind_speed_unit(self) -> str:
        """Return the native unit of measurement for wind speed."""
        return self.coordinator.units_of_measurement[SPEEDUNIT]

    @property
    def wind_bearing(self) -> str:
        """Return the wind bearing."""
        return self.coordinator.get_condition(FIELD_CONDITION_WINDDIR)

    @property
    def ozone(self) -> float:
        """Return the ozone level."""
        return self._attr_ozone

    # @property
    # def native_visibility(self) -> float:
    #     """Return the visibility in native units."""
    #     return self._attr_visibility
    #
    # @property
    # def native_visibility_unit(self) -> str:
    #     """Return the native unit of measurement for visibility."""
    #     return self._attr_visibility_unit

    @property
    def native_precipitation_unit(self) -> str:
        """
        Return the native unit of measurement for accumulated precipitation.
        """
        return self.coordinator.units_of_measurement[LENGTHUNIT]

    @property
    def condition(self) -> str:
        """Return the current condition."""
        day = self.coordinator.get_forecast(FIELD_FORECAST_ICONCODE)
        night = self.coordinator.get_forecast(FIELD_FORECAST_ICONCODE, 1)
        return self.coordinator._iconcode_to_condition(day or night)


    def _forecast(self) -> list[Forecast]:
        """Return the forecast in native units."""
        days = [0, 2, 4, 6, 8]
        if self.coordinator.get_forecast('temperature', 0) is None:
            days[0] += 1
        if self.coordinator._calendarday is True:
            caldaytempmax = FIELD_FORECAST_CALENDARDAYTEMPERATUREMAX
            caldaytempmin = FIELD_FORECAST_CALENDARDAYTEMPERATUREMIN
        else:
            caldaytempmax = FIELD_FORECAST_TEMPERATUREMAX
            caldaytempmin = FIELD_FORECAST_TEMPERATUREMIN

        forecast = []
        for period in days:
            forecast.append(Forecast({
                ATTR_FORECAST_CONDITION:
                    self.coordinator._iconcode_to_condition(
                        self.coordinator.get_forecast(
                            FIELD_FORECAST_ICONCODE, period)
                    ),
                ATTR_FORECAST_PRECIPITATION:
                    self.coordinator.get_forecast(FIELD_FORECAST_QPF, period),
                ATTR_FORECAST_PRECIPITATION_PROBABILITY:
                    self.coordinator.get_forecast(FIELD_FORECAST_PRECIPCHANCE, period),

                ATTR_FORECAST_TEMP:
                    self.coordinator.get_forecast(caldaytempmax, period),
                ATTR_FORECAST_TEMP_LOW:
                    self.coordinator.get_forecast(
                        caldaytempmin, period),

                ATTR_FORECAST_TIME:
                    dt_util.utc_from_timestamp(self.coordinator.get_forecast(
                        FIELD_FORECAST_VALIDTIMEUTC, period)).isoformat(),

                ATTR_FORECAST_WIND_BEARING:
                    self.coordinator.get_forecast(
                        FIELD_FORECAST_WINDDIRECTIONCARDINAL, period),
                ATTR_FORECAST_WIND_SPEED: self.coordinator.get_forecast(
                    FIELD_FORECAST_WINDSPEED, period)
            }))
        # _LOGGER.debug(f'{forecast=}')
        return forecast

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        return self._forecast()
