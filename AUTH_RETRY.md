# Recovering from intermittent HTTP 401 responses

Primary report: [WundergroundPWS discussion #330](https://github.com/cytech/Home-Assistant-wundergroundpws/discussions/330).

A cloud service can temporarily reject a valid API key. Previously, a single
HTTP 401 stopped polling and immediately requested reauthentication.

This change retries with the existing credentials after 15 minutes. Each
endpoint has its own failure history, so successful current observations do not
hide repeatedly rejected forecast requests. Repeated 401 responses spanning
24 hours trigger the normal Home Assistant reauthentication flow.

Following the Tedee approach, only a complete successful update of current
observations and forecasts clears the authentication failure history. Partial
success, transport errors, other HTTP errors, and elapsed time alone do not
clear it. The grace period also applies during initial coordinator refresh:
Home Assistant retries setup rather than immediately requesting reauthentication.

The 24 hours are elapsed time since the first rejection, not proof of 24 hours
of continuous rejection. After that deadline, another HTTP 401 is required to
start reauthentication; a timeout or HTTP 503 still remains an update failure.
A successful complete update after downtime clears the history normally.

Retry metadata is stored per config entry using Home Assistant storage. It
contains timestamps and a SHA-256 credential fingerprint, not the API key,
station identifier, coordinates, or response bodies. A changed key starts with
a fresh history. Deleting the config entry removes its retry metadata.

HTTP status is checked before parsing JSON, including text/plain 401 responses.
Reported fetch errors omit request URLs and upstream response messages, which
can contain credentials. Existing validation of new credentials in the setup
form is unchanged.

The 15-minute retry delay and 24-hour grace duration are constants in
`auth_retry.py`. Making them user-configurable can be discussed separately.
Normal successful polling retains its existing interval. A failed refresh still
follows Home Assistant's unavailable-data handling; cached values are not
presented as newly fetched measurements.

## Related upstream work

- Primary WundergroundPWS report: https://github.com/cytech/Home-Assistant-wundergroundpws/discussions/330
- Architecture discussion: https://github.com/home-assistant/architecture/discussions/1505
- Merged Tedee grace period: https://github.com/home-assistant/core/pull/190338
- Merged Tedee setup/reload correction: https://github.com/home-assistant/core/pull/192058

This implementation follows the retry-before-reauth pattern and full-update
reset semantics of those Tedee changes. It deliberately uses a 24-hour grace
period and a 15-minute authentication retry delay for this cloud service,
instead of Tedee's 10-minute grace period for a local bridge. Unlike Tedee's
in-memory per-entry history, local HA storage retains our history across HA
process restarts. Endpoint-specific timestamps prevent unrelated endpoint
failures from being combined into a single rejection period. These policy
choices are proposals for maintainer review, not a shared Home Assistant policy.

## Home Assistant 2026.12 reload compatibility

Discussion #330 also reports a separate deprecated reload pattern: a config
entry update listener reloads the entry while the reauthentication flow calls
`async_update_reload_and_abort`. Home Assistant disallows this combination
starting with 2026.12.

The integration now removes that redundant listener and uses
`OptionsFlowWithReload` to handle changed options. Reauthentication retains
`async_update_reload_and_abort`, including its default behavior of reloading
when the same credentials are submitted. No config entry migration is needed.

Reference: https://contributors.home-assistant.io/core/integrations/options-flow/

Validation: 27 tests pass on each of Home Assistant 2026.11.3 and 2026.12.0b0
with Python 3.14.7. Tests cover retry behavior, setup without the duplicate
listener, reauth reload scheduling with changed and unchanged credentials,
and the options flow's automatic-reload contract. HTTP responses and HA
configuration/storage boundaries are mocked. This is a focused regression
check, not a full running-HA integration test or certification of the final
2026.12 release. The live installation has not been changed.
