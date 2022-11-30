'''
Support for WUndergroundPWS weather service.

For more details about this platform, please refer to the documentation at
https://github.com/cytech/Home-Assistant-wundergroundpws
'''

DOMAIN = 'wundergroundpws'
MANUFACTURER = 'WeatherUnderground'
NAME = 'WeatherUnderground'

CONF_ATTRIBUTION = 'Data provided by the WUnderground weather service'
CONF_PWS_ID = 'pws_id'
CONF_NUMERIC_PRECISION = 'numeric_precision'
CONF_LANG = 'lang'

ENTRY_PWS_ID = 'pws_id'
ENTRY_WEATHER_COORDINATOR = 'weather_coordinator'

# Language Supported Codes
LANG_CODES = [
    'ar-AE', 'az-AZ', 'bg-BG', 'bn-BD', 'bn-IN', 'bs-BA', 'ca-ES', 'cs-CZ', 'da-DK', 'de-DE', 'el-GR', 'en-GB', 'en-IN',
    'en-US', 'es-AR', 'es-ES', 'es-LA', 'es-MX', 'es-UN', 'es-US', 'et-EE', 'fa-IR', 'fi-FI', 'fr-CA', 'fr-FR', 'gu-IN',
    'he-IL', 'hi-IN', 'hr-HR', 'hu-HU', 'in-ID', 'is-IS', 'it-IT', 'iw-IL', 'ja-JP', 'jv-ID', 'ka-GE', 'kk-KZ', 'kn-IN',
    'ko-KR', 'lt-LT', 'lv-LV', 'mk-MK', 'mn-MN', 'ms-MY', 'nl-NL', 'no-NO', 'pl-PL', 'pt-BR', 'pt-PT', 'ro-RO', 'ru-RU',
    'si-LK', 'sk-SK', 'sl-SI', 'sq-AL', 'sr-BA', 'sr-ME', 'sr-RS', 'sv-SE', 'sw-KE', 'ta-IN', 'ta-LK', 'te-IN', 'tg-TJ',
    'th-TH', 'tk-TM', 'tl-PH', 'tr-TR', 'uk-UA', 'ur-PK', 'uz-UZ', 'vi-VN', 'zh-CN', 'zh-HK', 'zh-TW'
]

DEFAULT_LANG = 'en-US'

TEMPUNIT = 0
LENGTHUNIT = 1
ALTITUDEUNIT = 2
SPEEDUNIT = 3
PRESSUREUNIT = 4
RATE = 5
PERCENTAGEUNIT = 6

FIELD_CONDITION_HUMIDITY = 'humidity'
FIELD_CONDITION_PRESSURE = 'pressure'
FIELD_CONDITION_TEMP = 'temp'
FIELD_CONDITION_WINDDIR = 'winddir'
FIELD_CONDITION_WINDSPEED = 'windSpeed'

FIELD_FORECAST_PRECIPCHANCE = 'precipChance'
FIELD_FORECAST_QPF = 'qpf'
FIELD_FORECAST_TEMPERATUREMAX = 'temperatureMax'
FIELD_FORECAST_TEMPERATUREMIN = 'temperatureMin'
FIELD_FORECAST_VALIDTIMEUTC = 'validTimeUtc'
FIELD_FORECAST_WINDDIRECTIONCARDINAL = 'windDirectionCardinal'
FIELD_FORECAST_WINDSPEED = 'windSpeed'
FIELD_FORECAST_WXPHRASESHORT = 'wxPhraseShort'
