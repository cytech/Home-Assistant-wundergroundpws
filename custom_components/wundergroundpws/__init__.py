'''The wundergroundpws component.'''

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

    DOMAIN,
    NAME,

    ENTRY_PWS_ID,
    ENTRY_WEATHER_COORDINATOR,

    LANG_CODES,
    DEFAULT_LANG,
)
from .wunderground_data import WUndergroundData

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {
            vol.Required(CONF_API_KEY): cv.string,
            vol.Required(CONF_PWS_ID): cv.string,
            vol.Required(CONF_NUMERIC_PRECISION):
                vol.All(vol.In(['none', 'decimal'])),

            vol.Optional(CONF_LANG, default=DEFAULT_LANG):
                vol.All(vol.In(LANG_CODES)),
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


async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    '''Set up the WUnderground sensor.'''

    platform_config = config.get(DOMAIN)

    api_key = platform_config.get(CONF_API_KEY)
    pws_id = platform_config.get(CONF_PWS_ID)
    # XXX: Could get the lat/long from the PWS
    latitude = platform_config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = platform_config.get(CONF_LONGITUDE, hass.config.longitude)

    numeric_precision = platform_config.get(CONF_NUMERIC_PRECISION)

    lang = platform_config.get(CONF_LANG)

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
    }

    return True
