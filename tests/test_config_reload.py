"""Reload regression tests with fabricated configuration only."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_API_KEY

from custom_components.wundergroundpws import async_setup_entry
from custom_components.wundergroundpws.config_flow import WundergroundPWSFlowHandler
from custom_components.wundergroundpws.const import CONF_PWS_ID


@pytest.mark.asyncio
async def test_setup_does_not_register_redundant_reload_listener():
    hass = MagicMock()
    hass.data = {}
    hass.config.config_dir = "/unused-test-config"
    hass.async_add_executor_job = AsyncMock(return_value={})
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    entry = MagicMock()
    entry.options = {
        "latitude": 0,
        "longitude": 0,
        "numeric_precision": "none",
        "lang": "en-US",
        "calendardaytemp": False,
    }
    # Use the actual option constants, independent of spelling changes.
    from custom_components.wundergroundpws.const import (
        CONF_CALENDARDAYTEMPERATURE,
        CONF_LANG,
        CONF_NUMERIC_PRECISION,
    )

    entry.options.update(
        {
            CONF_CALENDARDAYTEMPERATURE: False,
            CONF_LANG: "en-US",
            CONF_NUMERIC_PRECISION: "none",
        }
    )
    entry.data = {CONF_API_KEY: "fabricated-key", CONF_PWS_ID: "TEST_STATION"}
    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    with patch(
        "custom_components.wundergroundpws.WundergroundPWSUpdateCoordinator",
        return_value=coordinator,
    ):
        await async_setup_entry(hass, entry)
    entry.add_update_listener.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("changed", [False, True])
async def test_reauth_schedules_exactly_one_reload(changed):
    flow = WundergroundPWSFlowHandler()
    flow.hass = MagicMock()
    flow.hass.config_entries.async_update_entry.return_value = changed
    flow.context = {"source": "reauth"}
    entry = MagicMock(entry_id="test-entry", update_listeners=[])
    with patch.object(flow, "_get_reauth_entry", return_value=entry):
        result = await flow.async_step_reauth_confirm(
            {CONF_API_KEY: "fabricated-key", CONF_PWS_ID: "TEST_STATION"}
        )
    assert result["reason"] == "reauth_successful"
    flow.hass.config_entries.async_schedule_reload.assert_called_once_with("test-entry")


@pytest.mark.asyncio
async def test_options_delegate_reload_to_home_assistant():
    entry = MagicMock(options={})
    flow = WundergroundPWSFlowHandler.async_get_options_flow(entry)
    assert flow.automatic_reload is True
    result = await flow.async_step_init({"forecast_enable": True})
    assert result["data"] == {"forecast_enable": True}
