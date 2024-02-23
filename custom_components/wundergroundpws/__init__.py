"""The wundergroundpws component."""
import logging
from typing import Final
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE, CONF_LONGITUDE, Platform
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.util.unit_system import METRIC_SYSTEM
from .coordinator import WundergroundPWSUpdateCoordinator, WundergroundPWSUpdateCoordinatorConfig
from .const import (
    CONF_LANG,
    CONF_NUMERIC_PRECISION,
    CONF_PWS_ID,
    DOMAIN, API_METRIC, API_IMPERIAL, API_URL_METRIC, API_URL_IMPERIAL, CONF_CALENDARDAYTEMPERATURE,
    CONF_FORECAST_SENSORS
)

PLATFORMS: Final = [Platform.WEATHER, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the WundergroundPWS component."""
    hass.data.setdefault(DOMAIN, {})

    latitude = entry.options[CONF_LATITUDE]
    longitude = entry.options[CONF_LONGITUDE]

    if hass.config.units is METRIC_SYSTEM:
        unit_system_api = API_URL_METRIC
        unit_system = API_METRIC
    else:
        unit_system_api = API_URL_IMPERIAL
        unit_system = API_IMPERIAL

    config = WundergroundPWSUpdateCoordinatorConfig(
        api_key=entry.data[CONF_API_KEY],
        pws_id=entry.data[CONF_PWS_ID],
        numeric_precision=entry.options[CONF_NUMERIC_PRECISION],
        unit_system_api=unit_system_api,
        unit_system=unit_system,
        lang=entry.options[CONF_LANG],
        calendarday=entry.options[CONF_CALENDARDAYTEMPERATURE],
        latitude=latitude,
        longitude=longitude,
        forecast_enable=entry.options.get(CONF_FORECAST_SENSORS, False)
    )

    wupwscoordinator = WundergroundPWSUpdateCoordinator(hass, config)
    await wupwscoordinator.async_config_entry_first_refresh()
    if not wupwscoordinator.last_update_success:
        raise ConfigEntryNotReady

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    hass.data[DOMAIN][entry.entry_id] = wupwscoordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)
