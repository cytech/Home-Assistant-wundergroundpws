"""Persist a bounded grace period for intermittent authentication failures."""

import time
from hashlib import sha256
from math import ceil, isfinite

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import UpdateFailed

AUTH_RETRY_SECONDS = 15 * 60
AUTH_GRACE_SECONDS = 24 * 60 * 60


class AuthRetry:
    """Track failures separately for each endpoint without storing credentials."""

    def __init__(self, hass, entry_id: str, api_key: str) -> None:
        self._store = Store(hass, 1, f"wundergroundpws.auth_retry.{entry_id}")
        self._fingerprint = sha256(api_key.encode()).hexdigest()
        self._failures: dict[str, dict[str, float]] = {}
        self._loaded = False

    async def _async_load(self) -> None:
        if self._loaded:
            return
        saved = await self._store.async_load()
        if isinstance(saved, dict) and saved.get("fingerprint") == self._fingerprint:
            failures = saved.get("failures", {})
            if isinstance(failures, dict):
                for endpoint in ("current", "forecast"):
                    item = failures.get(endpoint)
                    if (
                        isinstance(item, dict)
                        and all(
                            isinstance(item.get(key), (float, int))
                            and isfinite(item[key])
                            for key in ("first", "last")
                        )
                        and 0 <= item["first"] <= item["last"] <= time.time()
                    ):
                        self._failures[endpoint] = item
        self._loaded = True

    async def _async_save(self) -> None:
        await self._store.async_save(
            {"fingerprint": self._fingerprint, "failures": self._failures}
        )

    async def async_check_retry(self, endpoint: str) -> None:
        """Respect the retry delay even across setup retries or restarts."""
        await self._async_load()
        if item := self._failures.get(endpoint):
            wait = ceil(item["last"] + AUTH_RETRY_SECONDS - time.time())
            if wait > 0:
                raise UpdateFailed(
                    f"Waiting to retry authentication for {endpoint}", retry_after=wait
                )

    async def async_rejected(self, endpoint: str) -> None:
        """Only repeated rejections spanning the grace period require reauth."""
        await self._async_load()
        now = time.time()
        item = self._failures.get(endpoint)
        # Like Tedee, retain the first failure until a full update succeeds.
        # https://github.com/home-assistant/core/pull/192058
        if item is None:
            item = {"first": now, "last": now}
        item["last"] = now
        self._failures[endpoint] = item
        await self._async_save()
        if now - item["first"] >= AUTH_GRACE_SECONDS:
            raise ConfigEntryAuthFailed(
                f"Weather API rejected authentication for {endpoint} after the 24-hour grace period"
            ) from None
        raise UpdateFailed(
            f"Temporary HTTP 401 for {endpoint}; retrying with stored credentials",
            retry_after=AUTH_RETRY_SECONDS,
        ) from None

    async def async_reset(self, endpoint: str) -> None:
        """Clear this endpoint's history after a complete successful update."""
        await self._async_load()
        if self._failures.pop(endpoint, None) is not None:
            await self._async_save()

    async def async_remove(self) -> None:
        """Remove persisted retry state when the configuration entry is deleted."""
        await self._store.async_remove()
