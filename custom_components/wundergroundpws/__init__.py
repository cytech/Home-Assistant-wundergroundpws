"""The wundergroundpws component."""
import json
import logging
from typing import Final
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE, CONF_LONGITUDE, Platform
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util.unit_system import METRIC_SYSTEM
from .coordinator import WundergroundPWSUpdateCoordinator, WundergroundPWSUpdateCoordinatorConfig
from .const import (
    CONF_LANG,
    CONF_NUMERIC_PRECISION,
    CONF_PWS_ID,
    DOMAIN,
    ENTRY_LANG,
)

PLATFORMS: Final = [Platform.WEATHER, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


# def get_tran_file(hass: HomeAssistantType):
#     """get translation file for wupws sensor friendly_name"""
#     tfiledir = f'{hass.config.config_dir}/custom_components/{DOMAIN}/wupws_translations/'
#     tfilename = hass.data[DOMAIN][ENTRY_LANG].split('-', 1)[0]
#     try:
#         tfile = open(f'{tfiledir}{tfilename}.json')
#         tfiledata = json.load(tfile)
#     except Exception:  # pylint: disable=broad-except
#         tfile = open(f'{tfiledir}en.json')
#         tfiledata = json.load(tfile)
#         _LOGGER.warning(f'Sensor translation file {tfilename}.json does not exist. Defaulting to en-US.')
#
#     return tfiledata


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the WundergroundPWS component."""
    hass.data.setdefault(DOMAIN, {})

    latitude = entry.options[CONF_LATITUDE]
    longitude = entry.options[CONF_LONGITUDE]

    if hass.config.units is METRIC_SYSTEM:
        unit_system_api = 'm'
        unit_system = 'metric'
    else:
        unit_system_api = 'e'
        unit_system = 'imperial'

    config = WundergroundPWSUpdateCoordinatorConfig(
        api_key=entry.data[CONF_API_KEY],
        pws_id=entry.data[CONF_PWS_ID],
        numeric_precision=entry.options[CONF_NUMERIC_PRECISION],
        unit_system_api=unit_system_api,
        unit_system=unit_system,
        lang=entry.options[CONF_LANG],
        latitude=latitude,
        longitude=longitude,

    )

    wupwscoordinator = WundergroundPWSUpdateCoordinator(hass, config)
    await wupwscoordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    hass.data[DOMAIN][entry.entry_id] = wupwscoordinator
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

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
