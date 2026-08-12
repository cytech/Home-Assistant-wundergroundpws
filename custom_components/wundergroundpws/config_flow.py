"""Config Flow to configure WundergrounPWS Integration."""

from asyncio import timeout
from collections.abc import Mapping
from http import HTTPStatus
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlowResult
from .exceptions import InvalidApiKeyError, InvalidStationIdError, InvalidApiResponseError

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.config_validation import latitude, longitude

from .const import (
    CONF_CALENDARDAYTEMPERATURE,
    CONF_FORECAST_SENSORS,
    CONF_LANG,
    CONF_NUMERIC_PRECISION,
    CONF_PWS_ID,
    CONF_UPDATE_INTERVAL,
    DEFAULT_CALENDARDAYTEMPERATURE,
    DEFAULT_FORECAST_SENSORS,
    DEFAULT_LANG,
    DEFAULT_NUMERIC_PRECISION,
    DEFAULT_TIMEOUT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    FIELD_LATITUDE,
    FIELD_LONGITUDE,
    FIELD_OBSERVATIONS,
    LANG_CODES,
    MIN_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class WundergroundPWSFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a WundergrounPWS config flow."""

    VERSION = 1

    def __init__(self):
        self._entry_data = None

    async def async_step_reauth(
            self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        self._entry_data = entry_data
        """Handle a flow for reauth."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
            self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by reauthentication."""
        errors = {}

        if user_input is not None:
            # Update the existing entry and abort
            existing_entry = self._get_reauth_entry()
            return self.async_update_reload_and_abort(
                existing_entry,
                data={
                    CONF_API_KEY: user_input[CONF_API_KEY],
                    CONF_PWS_ID: user_input[CONF_PWS_ID]
                },
                reason="reauth_successful",
            )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY, default=self._entry_data.get('api_key')): str,
                    vol.Required(CONF_PWS_ID, default=self._entry_data.get('pws_id')): str,
                }
            ),
            errors=errors or {},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def _validate_user_input(self, user_input: dict) -> dict:
        """Validate user input and fetch data from API.

        Returns:
            Dictionary with response data if successful, empty dict on error.

        Raises:
            InvalidApiKeyError: If API key is invalid or missing.
            InvalidStationIdError: If station ID is invalid or missing.
            Exception: For other unexpected errors.
        """
        if user_input[CONF_API_KEY] is None or user_input[CONF_API_KEY] == "":
            raise InvalidApiKeyError("Invalid API key")

        if user_input[CONF_PWS_ID] is None or user_input[CONF_PWS_ID] == "":
            raise InvalidStationIdError("Invalid Station ID")

        session = async_create_clientsession(self.hass)
        pws_id = user_input[CONF_PWS_ID]
        api_key = user_input[CONF_API_KEY]
        headers = {
            "Accept-Encoding": "gzip",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        }

        async with timeout(DEFAULT_TIMEOUT):
            url = (
                f"https://api.weather.com/v2/pws/observations/current?stationId={pws_id}&format=json&units=e"
                f"&apiKey={api_key}"
            )
            response = await session.get(url, headers=headers)

        if response.status != HTTPStatus.OK:
            if response.status == HTTPStatus.UNAUTHORIZED:
                _LOGGER.error(
                    "WundergroundPWS config responded with HTTP error %s: %s",
                    response.status,
                    response.reason,
                )
                raise InvalidApiKeyError("Invalid API key")
            if response.status == HTTPStatus.NO_CONTENT:
                _LOGGER.error(
                    "WundergroundPWS config responded with HTTP error %s: %s",
                    response.status,
                    response.reason,
                )
                raise InvalidStationIdError("Invalid Station ID")
            _LOGGER.error(
                "WundergroundPWS config responded with HTTP error %s: %s",
                response.status,
                response.reason,
            )
            raise InvalidApiResponseError("Unknown API Error")

        return await response.json()

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if user_input is not None:
            try:
                result_current = await self._validate_user_input(user_input)
            except InvalidApiKeyError:
                return await self._show_setup_form(errors={"base": "invalid_api_key"})
            except InvalidStationIdError:
                return await self._show_setup_form(errors={"base": "invalid_station_id"})
            except InvalidApiResponseError:
                return await self._show_setup_form(errors={"base": "unknown_error"})

            station_id = result_current[FIELD_OBSERVATIONS][0]["stationID"]

            unique_id = str(f"{DOMAIN}-{station_id}")
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Extract latitude and longitude from the API response, overwriting hass defaults if available
            longitude = result_current[FIELD_OBSERVATIONS][0][FIELD_LONGITUDE]
            latitude = result_current[FIELD_OBSERVATIONS][0][FIELD_LATITUDE]

            return self.async_create_entry(
                title=station_id,
                data={
                    CONF_API_KEY: user_input[CONF_API_KEY],
                    CONF_PWS_ID: user_input[CONF_PWS_ID],
                },
                options={
                    CONF_LATITUDE: latitude,
                    CONF_LONGITUDE: longitude,
                    CONF_NUMERIC_PRECISION: DEFAULT_NUMERIC_PRECISION,
                    CONF_LANG: DEFAULT_LANG,
                    CONF_CALENDARDAYTEMPERATURE: DEFAULT_CALENDARDAYTEMPERATURE,
                    CONF_FORECAST_SENSORS: DEFAULT_FORECAST_SENSORS,
                    CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
                },
            )

        return await self._show_setup_form(user_input)

    async def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(CONF_PWS_ID): str,
                }
            ),
            errors=errors or {},
        )

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_FORECAST_SENSORS,
                        default=self._config_entry.options.get(
                            CONF_FORECAST_SENSORS, DEFAULT_FORECAST_SENSORS
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_NUMERIC_PRECISION,
                        default=self._config_entry.options.get(
                            CONF_NUMERIC_PRECISION, DEFAULT_NUMERIC_PRECISION
                        ),
                    ): vol.All(vol.In(["none", "decimal"])),
                    vol.Optional(
                        CONF_LANG,
                        default=self._config_entry.options.get(CONF_LANG, DEFAULT_LANG),
                    ): vol.All(vol.In(LANG_CODES)),
                    vol.Optional(
                        CONF_CALENDARDAYTEMPERATURE,
                        default=self._config_entry.options.get(
                            CONF_CALENDARDAYTEMPERATURE, DEFAULT_CALENDARDAYTEMPERATURE
                        ),
                    ): bool,
                    vol.Inclusive(
                        CONF_LATITUDE,
                        "coordinates",
                        "Latitude and longitude must exist together",
                        default=self._config_entry.options.get(CONF_LATITUDE),
                    ): latitude,
                    vol.Inclusive(
                        CONF_LONGITUDE,
                        "coordinates",
                        "Latitude and longitude must exist together",
                        default=self._config_entry.options.get(CONF_LONGITUDE),
                    ): longitude,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_UPDATE_INTERVAL)),
                }
            ),
        )
