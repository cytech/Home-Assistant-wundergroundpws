# Authentication retry regression tests

Run on Linux with Python 3.14.2 or later:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/python -m pytest -q
```

Tests use the real Home Assistant coordinator classes with mocked HTTP and
storage boundaries, and a controlled clock. They make no API requests and use
fabricated credentials, a placeholder station, and zero coordinates.

Coverage includes JSON and non-JSON 401 responses, the 24-hour boundary,
15-minute retry throttling, coordinator recreation, independent forecast failures,
credential changes, recovery, non-authentication errors, request deadlines,
response cleanup, initial setup retries, and secret-free exception messages.

This is not a full running-Home-Assistant end-to-end test or a live provider test.
