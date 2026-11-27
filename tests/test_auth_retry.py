"""Regression tests using fabricated credentials and mocked HTTP responses."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from homeassistant.config_entries import ConfigEntryState, current_entry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.wundergroundpws.coordinator import (
    WundergroundPWSUpdateCoordinator,
    WundergroundPWSUpdateCoordinatorConfig,
)


@pytest.fixture
def settings():
    config = WundergroundPWSUpdateCoordinatorConfig(
        api_key="fabricated-test-credential",
        pws_id="TEST_STATION",
        numeric_precision="none",
        unit_system_api="m",
        unit_system="metric",
        lang="en-US",
        calendarday=False,
        latitude="0",
        longitude="0",
        forecast_enable=True,
        tranfile={},
    )
    config.entry_id = "test-entry"
    return config


def response(status=200, body=None, content_error=False):
    result = MagicMock()
    result.status = status
    error = aiohttp.ClientResponseError(
        MagicMock(
            real_url="https://example.invalid/?apiKey=fabricated-test-credential"
        ),
        (),
        status=status,
        message="fabricated upstream error",
    )
    result.raise_for_status.side_effect = error if status >= 400 else None
    result.json = AsyncMock(return_value=body or {"observations": [{}]})
    if content_error:
        result.json.side_effect = aiohttp.ContentTypeError(
            error.request_info, (), status=status, message="unexpected mimetype"
        )
    return result


@pytest.fixture
def environment(tmp_path):
    """Use HA's real coordinator and an in-memory storage backend."""
    saved = {}
    session = MagicMock()
    session.get = AsyncMock()
    clock = [1_800_000_000.0]

    async def load(store):
        return saved.get(store.key)

    async def save(store, data):
        import copy

        saved[store.key] = copy.deepcopy(data)

    with (
        patch("homeassistant.helpers.frame.report_usage"),
        patch(
            "custom_components.wundergroundpws.coordinator.async_get_clientsession",
            return_value=session,
        ),
        patch("homeassistant.helpers.storage.Store.async_load", load),
        patch("homeassistant.helpers.storage.Store.async_save", save),
        patch("time.time", side_effect=lambda: clock[0]),
    ):
        yield tmp_path, session, saved, clock


def create(environment, settings):
    tmp_path, _, _, _ = environment
    entry = MagicMock(
        entry_id=settings.entry_id, state=ConfigEntryState.SETUP_IN_PROGRESS
    )
    token = current_entry.set(entry)
    try:
        return WundergroundPWSUpdateCoordinator(HomeAssistant(str(tmp_path)), settings)
    finally:
        current_entry.reset(token)


@pytest.mark.asyncio
@pytest.mark.parametrize("content_error", [False, True])
async def test_first_401_is_retried(environment, settings, content_error):
    _, session, _, _ = environment
    session.get.return_value = response(401, content_error=content_error)
    with pytest.raises(UpdateFailed):
        await create(environment, settings).get_weather()


@pytest.mark.asyncio
async def test_24_hours_of_rejections_require_reauth(environment, settings):
    _, session, _, clock = environment
    session.get.return_value = response(401, content_error=True)
    coordinator = create(environment, settings)
    for _ in range(96):
        with pytest.raises(UpdateFailed):
            await coordinator.get_weather()
        clock[0] += 900
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator.get_weather()


@pytest.mark.asyncio
async def test_retry_state_survives_recreation(environment, settings):
    _, session, saved, clock = environment
    session.get.return_value = response(401, content_error=True)
    for _ in range(96):
        with pytest.raises(UpdateFailed):
            await create(environment, settings).get_weather()
        clock[0] += 900
    assert saved
    assert "fabricated-test-credential" not in str(saved)
    assert "TEST_STATION" not in str(saved)
    with pytest.raises(ConfigEntryAuthFailed):
        await create(environment, settings).get_weather()


@pytest.mark.asyncio
async def test_retry_wait_prevents_extra_requests(environment, settings):
    _, session, _, clock = environment
    session.get.return_value = response(401, content_error=True)
    with pytest.raises(UpdateFailed):
        await create(environment, settings).get_weather()
    clock[0] += 60
    with pytest.raises(UpdateFailed):
        await create(environment, settings).get_weather()
    assert session.get.await_count == 1


@pytest.mark.asyncio
async def test_errors_do_not_expose_request_url(environment, settings):
    _, session, _, _ = environment
    session.get.return_value = response(503, content_error=True)
    with pytest.raises(UpdateFailed) as caught:
        await create(environment, settings).get_weather()
    assert "fabricated-test-credential" not in str(caught.value)
    assert "example.invalid" not in str(caught.value)
    assert caught.value.__context__ is None or caught.value.__suppress_context__


@pytest.mark.asyncio
async def test_recovery_starts_new_grace_period(environment, settings):
    _, session, _, clock = environment
    coordinator = create(environment, settings)
    session.get.return_value = response(401)
    for _ in range(95):
        with pytest.raises(UpdateFailed):
            await coordinator.get_weather()
        clock[0] += 900
    session.get.return_value = response()
    assert await coordinator.get_weather()
    clock[0] += 900
    session.get.return_value = response(401)
    with pytest.raises(UpdateFailed):
        await coordinator.get_weather()


@pytest.mark.asyncio
async def test_forecast_rejections_not_reset_by_current_success(environment, settings):
    _, session, _, clock = environment
    coordinator = create(environment, settings)
    session.get.side_effect = lambda url, **kwargs: response(
        401 if "/forecast/" in url else 200
    )
    for _ in range(96):
        with pytest.raises(UpdateFailed):
            await coordinator.get_weather()
        clock[0] += 900
    with pytest.raises(ConfigEntryAuthFailed, match="forecast"):
        await coordinator.get_weather()


@pytest.mark.asyncio
async def test_changed_credentials_do_not_inherit_rejections(environment, settings):
    _, session, _, clock = environment
    session.get.return_value = response(401)
    coordinator = create(environment, settings)
    for _ in range(96):
        with pytest.raises(UpdateFailed):
            await coordinator.get_weather()
        clock[0] += 900
    settings.api_key = "different-fabricated-credential"
    with pytest.raises(UpdateFailed):
        await create(environment, settings).get_weather()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [403, 429, 500, 503])
async def test_non_auth_errors_preserve_rejection_streak(environment, settings, status):
    _, session, _, clock = environment
    coordinator = create(environment, settings)
    session.get.return_value = response(401)
    for _ in range(95):
        with pytest.raises(UpdateFailed):
            await coordinator.get_weather()
        clock[0] += 900
    session.get.return_value = response(status)
    with pytest.raises(UpdateFailed):
        await coordinator.get_weather()
    clock[0] += 900
    session.get.return_value = response(401)
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator.get_weather()


@pytest.mark.asyncio
async def test_elapsed_grace_requires_a_fresh_rejection(environment, settings):
    _, session, _, clock = environment
    session.get.return_value = response(401)
    with pytest.raises(UpdateFailed):
        await create(environment, settings).get_weather()
    clock[0] += 86400
    with pytest.raises(ConfigEntryAuthFailed):
        await create(environment, settings).get_weather()


@pytest.mark.asyncio
async def test_entry_state_is_isolated(environment, settings):
    _, session, _, _ = environment
    session.get.return_value = response(401)
    with pytest.raises(UpdateFailed):
        await create(environment, settings).get_weather()
    settings.entry_id = "another-test-entry"
    with pytest.raises(UpdateFailed):
        await create(environment, settings).get_weather()
    assert session.get.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [TimeoutError(), aiohttp.ClientConnectionError("fabricated-test-credential")],
)
async def test_transport_error_is_sanitized_and_not_auth(environment, settings, error):
    _, session, _, _ = environment
    session.get.side_effect = error
    with pytest.raises(UpdateFailed) as caught:
        await create(environment, settings).get_weather()
    assert "fabricated-test-credential" not in str(caught.value)
    assert caught.value.__suppress_context__


@pytest.mark.asyncio
async def test_api_error_payload_is_not_echoed(environment, settings):
    _, session, _, _ = environment
    session.get.return_value = response(
        body={"errors": [{"message": "fabricated-test-credential"}]}
    )
    with pytest.raises(UpdateFailed) as caught:
        await create(environment, settings).get_weather()
    assert "fabricated-test-credential" not in str(caught.value)


@pytest.mark.asyncio
async def test_request_deadline_preserves_auth_streak(environment, settings):
    import asyncio

    _, session, _, clock = environment
    coordinator = create(environment, settings)
    session.get.return_value = response(401)
    for _ in range(95):
        with pytest.raises(UpdateFailed):
            await coordinator.get_weather()
        clock[0] += 900

    async def stalled(*args, **kwargs):
        await asyncio.sleep(1)

    session.get.side_effect = stalled
    with (
        patch("custom_components.wundergroundpws.coordinator.DEFAULT_TIMEOUT", 0.001),
        pytest.raises(UpdateFailed),
    ):
        await coordinator.get_weather()
    session.get.side_effect = None
    clock[0] += 900
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator.get_weather()


@pytest.mark.asyncio
async def test_initial_refresh_keeps_setup_retryable(environment, settings):
    _, session, _, _ = environment
    session.get.return_value = response(401)
    with pytest.raises(ConfigEntryNotReady):
        await create(environment, settings).async_config_entry_first_refresh()


@pytest.mark.asyncio
async def test_response_released_after_rejection(environment, settings):
    _, session, _, _ = environment
    reply = response(401)
    session.get.return_value = reply
    with pytest.raises(UpdateFailed):
        await create(environment, settings).get_weather()
    reply.release.assert_called_once()


@pytest.mark.asyncio
async def test_entry_removal_deletes_retry_metadata(environment, settings):
    from custom_components.wundergroundpws import async_remove_entry

    tmp_path, _, _, _ = environment
    entry = MagicMock(entry_id=settings.entry_id, data={"api_key": settings.api_key})
    with patch(
        "homeassistant.helpers.storage.Store.async_remove", new_callable=AsyncMock
    ) as remove:
        await async_remove_entry(HomeAssistant(str(tmp_path)), entry)
    remove.assert_awaited_once()


@pytest.mark.asyncio
async def test_partial_success_does_not_reset_grace(environment, settings):
    _, session, _, clock = environment
    coordinator = create(environment, settings)
    session.get.return_value = response(401)
    with pytest.raises(UpdateFailed):
        await coordinator.get_weather()
    clock[0] += 900
    session.get.side_effect = [response(), response(503)]
    with pytest.raises(UpdateFailed):
        await coordinator.get_weather()
    clock[0] += 86400
    session.get.side_effect = None
    session.get.return_value = response(401)
    with pytest.raises(ConfigEntryAuthFailed):
        await create(environment, settings).get_weather()
