"""The wundergroundpws component."""
import json
import logging

import voluptuous as vol

from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE, CONF_LONGITUDE,
)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.typing import HomeAssistantType, ConfigType
from homeassistant.util.unit_system import METRIC_SYSTEM
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_LANG,
    CONF_NUMERIC_PRECISION,
    CONF_PWS_ID,
    CONF_CALENDARDAYTEMPERATURE,

    DOMAIN,

    ENTRY_PWS_ID,
    ENTRY_WEATHER_COORDINATOR,

    LANG_CODES,
    DEFAULT_LANG, ENTRY_LANG, ENTRY_TRAN_FILE,
    DEFAULT_CALENDARDAYTEMPERATURE, ENTRY_CALENDARDAYTEMPERATURE, DEFAULT_NUMERIC_PRECISION
)
from .wunderground_data import WUndergroundData

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {
            vol.Required(CONF_API_KEY): cv.string,
            vol.Required(CONF_PWS_ID): cv.string,
            vol.Optional(CONF_NUMERIC_PRECISION, default=DEFAULT_NUMERIC_PRECISION):
                vol.All(vol.In(['none', 'decimal'])),
            vol.Optional(CONF_LANG, default=DEFAULT_LANG):
                vol.All(vol.In(LANG_CODES)),
            vol.Optional(CONF_CALENDARDAYTEMPERATURE, default=DEFAULT_CALENDARDAYTEMPERATURE):
                cv.boolean,
            vol.Inclusive(CONF_LATITUDE, 'coordinates',
                          'Latitude and longitude must exist together'):
                cv.latitude,
            vol.Inclusive(CONF_LONGITUDE, 'coordinates',
                          'Latitude and longitude must exist together'):
                cv.longitude,
        },
    },
    extra=vol.ALLOW_EXTRA,
)


"""get translation file for wupws sensor friendly_name"""
def get_tran_file(hass: HomeAssistantType):
    tfiledir = f'{hass.config.config_dir}/custom_components/{DOMAIN}/wupws_translations/'
    tfilename = hass.data[DOMAIN][ENTRY_LANG].split('-', 1)[0]
    try:
        tfile = open(f'{tfiledir}{tfilename}.json')
        tfiledata = json.load(tfile)
    except:
        tfile = open(f'{tfiledir}en.json')
        tfiledata = json.load(tfile)
        _LOGGER.warning(f'Sensor translation file {tfilename}.json does not exist. Defaulting to en-US.')
    return tfiledata


async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    """Set up the WUnderground sensor."""

    platform_config = config.get(DOMAIN)

    api_key = platform_config.get(CONF_API_KEY)
    pws_id = platform_config.get(CONF_PWS_ID)
    # XXX: Could get the lat/long from the PWS
    latitude = platform_config.get(CONF_LATITUDE)
    longitude = platform_config.get(CONF_LONGITUDE)

    numeric_precision = platform_config.get(CONF_NUMERIC_PRECISION)

    lang = platform_config.get(CONF_LANG)
    caldaytemp = platform_config.get(CONF_CALENDARDAYTEMPERATURE)

    if hass.config.units is METRIC_SYSTEM:
        unit_system_api = 'm'
        unit_system = 'metric'
    else:
        unit_system_api = 'e'
        unit_system = 'imperial'

    rest = WUndergroundData(
        hass,
        api_key, pws_id, numeric_precision,
        unit_system_api, unit_system,
        lang,
        latitude, longitude)

    await rest.async_update()
    if not rest.data:
        raise PlatformNotReady

    hass.data[DOMAIN] = {
        ENTRY_WEATHER_COORDINATOR: rest,
        ENTRY_PWS_ID: pws_id,
        ENTRY_LANG: lang,
        ENTRY_CALENDARDAYTEMPERATURE: caldaytemp
    }

    hass.data[DOMAIN].update({ENTRY_TRAN_FILE: get_tran_file(hass)})

    return True
