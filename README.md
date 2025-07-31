# Home-Assistant-Wundergroundpws v2.X.X
  

Home Assistant custom integration for Weather Underground personal weather station users.  
Includes a native Home Assistant Weather Entity and a variety of weather sensors.  
Current conditions are generated from the wundergroundpws configured station ID.  
Forecast is generated from the latitude/longitude retrieved from the wundergroundpws configured station ID.  
The `wundergroundpws` platform uses [Weather Underground](http://www.wunderground.com) as a source for current weather information.  

:+1: If you find this software useful, feel free to make a donation: [Paypal.me Donation Link](https://paypal.me/cytecheng)  

**v2.0.4 Upgrade notes:**  
_requires Home Assistant version 2023.9 or greater._  
_If the forecast is not displayed in the weather card after upgrading from v2.x.x to v2.0.4, edit the weather card in the dashboard and re-save it._  

-------------------

[Prerequisites](#installation-prerequisites)

[Weather Underground PWS API Key](#weather-underground-pws-api-key)

[Installation](#installation)

[Upgrade](#upgrade)

[Configure](#configure)

[Description of terms and variables](#description-of-terms-and-variables)

[Weather Entity](#weather-entity)

[Statistics Card](#sensors-available-in-statistics)

[Localization](#localization)

# Installation Prerequisites
Please review the minimum requirements below to determine whether you will be able to
install and use the software.

- **_wundergroundpws v2.X.X is a redesigned integration and not an upgrade to earlier versions._**  
  SEE [Upgrade](#upgrade) section for instructions.
- wundergroundpws v2.X.X requires Home Assistant Version 2023.1 or greater
- Registered and active Weather Underground personal weather station API key  
[Back to top](#top) 

# Weather Underground PWS API Key
Free API keys are only issued to registered and active Weather Underground personal weather station users.  
To use this integration, you need a Weather Underground personal weather station API key and Station ID.  
To get a free API key:  
1) You must have a personal weather station registered and uploading data to Weather Underground.  
    a) Join weather Underground  
    b) Sign In  
    c) My Profile -> My Weather Stations  
    d) Add a New PWS  
2) get API key at  https://www.wunderground.com/member/api-keys.  

Please consider this when using the following information.  
[Back to top](#top)


# Installation

Download the latest v2.X.X release zip file from this repository.
Extract the zip file to a temporary directory.
-------
Copy the custom_components directory from the extracted file into your .homeassistant directory.  
or  
Copy the contents of the custom_components directory from the extracted file into an existing custom_components directory in your .homeassistant directory.

1. In Home Assistant Settings, select DEVICES & SERVICES, then ADD INTEGRATION.  
2. Select the "wundergroundpws" integration.  
3. Enter your Weather Underground API key and your Station ID (Case Sensitive. Must match the ID of your Wunderground device)  
and submit.  
4. After the integration setup is complete, you can select "Configure" to change:  

* Create Forecast Sensors, numeric_precision (none or decimal), language, calendarday_temp, and override latitude and longitude for forecast.  
* Observation and condition sensors will be created and enabled.  
* Forecast sensors are not created by default. They will be created if you enable "Create Forecast Sensors" in the integration "Configure".  
* Forecast sensors will then be created but are disabled. To enable, goto the integration - entities and select the sensors you would like and enable them.

Multiple instances can be created by repeating the above steps with a different StationID and or/API Key.  
Note that every instance requires it's own set of API calls, so be aware of exceeding the Weather Underground Personal API rate limit.  
Each instance calls every 5 minutes or 288 times a day.  
[Back to top](#top)

# Upgrade
There is no upgrade to v2.x.x from earlier versions.  
You must:  
Delete the existing custom_components/wundergroundpws directory.  
Remove all configuration items for v1.1.x and earlier from configuration.yaml:  
```yaml
# REMOVE configuration.yaml entry
wundergroundpws:
  api_key: YOUR_API_KEY
  pws_id: YOUR_STATION_ID

weather:
  - platform: wundergroundpws

sensor:
  - platform: wundergroundpws
    monitored_conditions:
      - temp
      - dewpt
      - heatIndex
      - etc.. 
```
Restart home assistant.  
In home assistant - settings - entities, search for "wundergroundpws" and select all filtered entities and "remove selected".  
Restart home assistant.  
Install v2.x.x (See [Install](#installation) above).  
Reconfigure any lovelace cards, automations, scripts, etc to reflect new sensor names.  
[Back to top](#top) 

# Configure
Wundergroundpws integration configuration options available at:  
Settings-Devices & Services-Wundergroundpws-Configure  

**OPTIONS:**  
**Create Forecast Sensors?**  
Forecast sensors are not created by default. They will be created if you enable "Create Forecast Sensors" in the integration "Configure".  
Forecast sensors will then be created but are disabled. To enable, goto the integration - entities and select the sensors you would like and enable them.  

**Numeric Precision**  
none (integer) or decimal (single).  
Only applies to PWS current values (not forecast) in sensors (not weather entity).

**Language**  
Specify the language that the API returns.  
The default is English (en-US).

**Temperature by Calendar Day?** (experimental)  
**_USE AT YOUR OWN RISK_** - Undocumented in The Weather Company PWS observations API.  
If checked, retrieves Forecast temperature max/min relative to calendar day (12:00am -> 11:59pm) as opposed to API period (~7:00am -> ~6:59am).      
Only affects the weather entity forecast values, not the sensors.  
This field is undocumented in The Weather Company PWS API, so it is subject to change and if removed from API response in the future, will crash the integration if set true.

**Latitude** - Default is retrieved from StationID  
Override Latitude coordinate for weather forecast.

**Longitude** - Default is retrieved from StationID  
Override Longitude coordinate for weather forecast.  
[Back to top](#top) 
        
# Description of terms and variables
```yaml
api_key:
  description: The API key for Weather Underground. See above for details.
  required: true
  type: string
pws_id:
  description: You must enter a Personal Weather Station ID. 
               The station id will be used to display current weather conditions.  
               Note - Case Sensitive. Must match the ID of your Wunderground device in member settings.
  required: true
  type: string
numeric_precision:
  description: Optional - Show PWS data as integer or decimal.
               Only applies to PWS current values (not forecast) in sensors (not weather entity).
  required: false - Value of 'none' or 'decimal'
  type: string
  default: none
calendarday_temp:
  USE AT YOUR OWN RISK - Undocumented in The Weather Company PWS observations API:
  description: Optional - if true, retrieve Forecast temperature max/min relative  
               to calendar day (12:00am -> 11:59pm) as opposed to API period (~7:00am -> ~6:59am).    
               Only affects the weather entity forecast values, not the sensors.  
               This field is undocumented in The Weather Company PWS API,  
               so it is subject to change and if removed from API response in the future, will crash the integration if set true.
  required: false - Value of 'true' or 'false'
  type: boolean
  default: false
lang:
  description: Specify the language that the API returns. The current list of all 
               Wunderground language codes is available  at 
               https://docs.google.com/document/d/13HTLgJDpsb39deFzk_YCQ5GoGoZCO_cRYzIxbwvgJLI/edit
               or at the Localization bookmark below. 
               If not specified, it defaults to English (en-US).
  required: false
  type: string
  default: en-US
latitude:
  description: Latitude coordinate for weather forecast (required if **longitude** is specified).
  required: false
  type: string
  default: WU API lat of stationId
longitude:
  description: Longitude coordinate for weather forecast (required if **latitude** is specified).
  required: false
  type: string
  default: WU API lon of stationId
```
# Available Sensors
```yaml
# description: Conditions to display in the frontend. The following conditions can be monitored.
# See https://www.wunderground.com/about/data) for Weather Underground data information.
#
# Observations (current)
 neighborhood:
   unique_id: <pws_id>,neighborhood
   entity_id: sensor.<pws_id>_neighborhood
   description: WU PWS reference name
 obsTimeLocal:
   unique_id: <pws_id>,obstimelocal
   entity_id: sensor.<pws_id>_local_observation_time   
   description: Text summary of local observation time
 humidity:
   unique_id: <pws_id>,humidity
   entity_id: sensor.<pws_id>_relative_humidity   
   description: Relative humidity    
 stationID:
   unique_id: <pws_id>,stationid
   entity_id: sensor.<pws_id>_station_id   
   description: Your personal weather station (PWS) ID
 solarRadiation:
   unique_id: <pws_id>,solarradiation
   entity_id: sensor.<pws_id>_solar_radiation   
   description: Current levels of solar radiation
 uv:
   unique_id: <pws_id>,uv
   entity_id: sensor.<pws_id>_uv_index   
   description: Current levels of UV radiation.
 winddir:
   unique_id: <pws_id>,winddir
   entity_id: sensor.<pws_id>_wind_direction_degrees   
   description: Wind degrees
 windDirectionCardinal:
   unique_id: <pws_id>,winddirectioncardinal
   entity_id: sensor.<pws_id>_wind_direction_cardinal   
   description: Wind cardinal direction (N, NE, NNE, S, E, W, etc)
# conditions (current)       
 dewpt:
   unique_id: <PWS_ID>,dewpt
   entity_id: sensor.<pws_id>_dewpoint
   description: Temperature below which water droplets begin to condense and dew can form
 elev:
   unique_id: <pws_id>,elev
   entity_id: sensor.<pws_id>_elevation   
   description: Elevation
 heatIndex:
   unique_id: <pws_id>,heatindex
   entity_id: sensor.<pws_id>_heat_index   
   description: Heat index (combined effects of the temperature and humidity of the air)
 precipRate:
   unique_id: <pws_id>,preciprate
   entity_id: sensor.<pws_id>_precipitation_rate   
   description: Rain intensity
 precipTotal:
   unique_id: <pws_id>,preciptotal
   entity_id: sensor.<pws_id>_precipitation_today   
   description: Today Total precipitation
 pressure:
   unique_id: <pws_id>,pressure
   entity_id: sensor.<pws_id>_pressure   
   description: Atmospheric air pressure
 temp:
   unique_id: <pws_id>,temp
   entity_id: sensor.<pws_id>_temperature   
   description: Current temperature
 windChill:
   unique_id: <pws_id>,windchill
   entity_id: sensor.<pws_id>_wind_chill   
   description: Wind Chill (combined effects of the temperature and wind)      
 windGust:
   unique_id: <pws_id>,windgust
   entity_id: sensor.<pws_id>_wind_gust   
   description: Wind gusts speed
 windSpeed:
   unique_id: <pws_id>,windspeed
   entity_id: sensor.<pws_id>_wind_speed   
   description: Current wind speed      
#   Forecast
 narrative:
   unique_id: <PWS_ID>,narrative_<day>f
   entity_id: sensor.<pws_id>_weather_summary_<day>
   description: A human-readable weather forecast for Day. (<day> Variations 0, 1, 2, 3, 4)
 qpfSnow:
   unique_id: <pws_id>,qpfsnow_<day>f
   entity_id: sensor.<pws_id>_snow_amount_<day>
   description: Forecasted snow intensity. (<day> Variations 0, 1, 2, 3, 4)
#   Forecast daypart
 narrative:
   unique_id: <PWS_ID>,narrative_<daypart>fdp
   entity_id: sensor.<pws_id>_forecast_summary_<suffix>
   description: A human-readable weather forecast for Day. (suffix Variations 0d, 1n, 2d, 3n, 4d, 5n, 6d, 7n, 8d, 9n)
 qpf:
   unique_id: <pws_id>,qpf_<daypart>fdp
   entity_id: sensor.<pws_id>_precipitation_amount_<suffix>
   description: Forecasted precipitation intensity. (suffix Variations 0d, 1n, 2d, 3n, 4d, 5n, 6d, 7n, 8d, 9n)
 precipChance:
   unique_id: <pws_id>,precipchance_<daypart>fdp
   entity_id: sensor.<pws_id>_precipitation_probability_<suffix>
   description: Forecasted precipitation probability in %. (suffix Variations 0d, 1n, 2d, 3n, 4d, 5n, 6d, 7n, 8d, 9n)      
 temperature:
   unique_id: <pws_id>,temperature<daypart>fdp
   entity_id: sensor.<pws_id>_forecast_temperature_<suffix>
   description: Forecasted temperature. (suffix Variations 0d, 1n, 2d, 3n, 4d, 5n, 6d, 7n, 8d, 9n)
 windSpeed:
   unique_id: <pws_id>,windspeed_<daypart>fdp
   entity_id: sensor.<pws_id>_average_wind_<suffix>
   description: Forecasted wind speed. (suffix Variations 0d, 1n, 2d, 3n, 4d, 5n, 6d, 7n, 8d, 9n)
```

All the conditions listed above will be updated every 5 minutes.  

**_Wunderground API caveat:   
The daypart object as well as the temperatureMax field OUTSIDE of the daypart object will appear as null in the API after 3:00pm Local Apparent Time.  
The affected sensors will return as "Today Expired" with a value of "Unknown" when this condition is met._**


Variations above marked with "#d" are daily forecasts.
Variations above marked with "#n" are nightly forecasts.


Note: While the platform is called “wundergroundpws” the sensors will show up in Home Assistant as  
```sensor.<pws_id>_forecast_temperature_<suffix>```  
(eg: sensor.samplepwsid_forecast_temperature_0d).


[//]: # (Note that the Weather Underground sensor is added to the entity_registry, so second and subsequent Personal Weather Station ID &#40;pws_id&#41; will have their monitored conditions suffixed with an index number e.g.)

[//]: # ()
[//]: # (```yaml)

[//]: # (    - sensor.wupws_weather_1d_metric_2)

[//]: # (```)
Additional details about the API are available [here](https://docs.google.com/document/d/1eKCnKXI9xnoMGRRzOL1xPCBihNV2rOet08qpE_gArAY/edit).  
[Back to top](#top)

# Weather Entity
wundergroundpws data returned to weather entity (HASS weather forecast card):  
Current:
- temperature
- pressure
- humidity
- wind_speed
- wind_bearing

Forecast:
- datetime
- temperature (max)
- temperature (low)
- condition (icon)
- precipitation
- precipitation_probability
- wind_bearing
- wind_speed

templates can be created to access these values such as:
```
{% for state in states.weather -%}
  {%- if loop.first %}The {% elif loop.last %} and the {% else %}, the {% endif -%}
  {{ state.name | lower }} is {{state.state_with_unit}}
{%- endfor %}.

Wind is {{ states.weather.<STATIONID>.attributes.forecast[0].wind_bearing }} at {{ states.weather.<STATIONID>.attributes.forecast[0].wind_speed }} {{ states.weather.<STATIONID>.attributes.wind_speed_unit }}

```
[Back to top](#top)

# Sensors available in statistics
The following are wundergroundpws sensors exposed to the statistics card in Lovelace.  
Note that only sensors of like units can be combined in a single card.  

* **class NONE**
* sensor.samplepwsid_uv_index
* 
* **class DEGREE**
* sensor.sensor.samplepwsid_wind_direction_degrees

* 
* **class RATE & SPEED**
* sensor.samplepwsid_precipitation_rate
* sensor.samplepwsid_wind_gust
* sensor.samplepwsid_wind_speed
* 
* **class LENGTH**
* sensor.samplepwsid_precipitation_today
* 
* **class PRESSURE**
* sensor.samplepwsid_pressure
* 
* **class HUMIDITY**
* sensor.samplepwsid_relative_humidity
* 
* **class IRRADIANCE**
* sensor.samplepwsid_solar_radiation
* 
* **class TEMPERATURE**
* sensor.samplepwsid_dewpoint
* sensor.samplepwsid_heat_index
* sensor.samplepwsid_wind_chill
* sensor.samplepwsid_temperature

[Back to top](#top)


# Localization

Sensor "friendly names" are set via translation files.  
Wundergroundpws translation files are located in the 'wundergroundpws/wupws_translations' directory.
Files were translated, using 'en.json' as the base, via https://translate.i18next.com.  
Translations only use the base language code and not the variant (i.e. zh-CN/zh-HK/zh-TW uses zh).  
The default is en-US (translations/en.json) if the lang: option is not set in the wundergroundpws config.  
If lang: is set (i.e.  lang: de-DE), then the translations/de.json file is loaded, and the Weather Underground API is queried with de-DE.    
The translation file applies to all sensor friendly names.   
Forecast-narrative, forecast-dayOfWeek, forecast-daypart-narrative and forecast-daypart-daypartName are translated by the api. 
Available lang: options are:  
```
'am-ET', 'ar-AE', 'az-AZ', 'bg-BG', 'bn-BD', 'bn-IN', 'bs-BA', 'ca-ES', 'cs-CZ', 'da-DK', 'de-DE', 'el-GR', 'en-GB',
'en-IN', 'en-US', 'es-AR', 'es-ES', 'es-LA', 'es-MX', 'es-UN', 'es-US', 'et-EE', 'fa-IR', 'fi-FI', 'fr-CA', 'fr-FR',
'gu-IN', 'he-IL', 'hi-IN', 'hr-HR', 'hu-HU', 'in-ID', 'is-IS', 'it-IT', 'iw-IL', 'ja-JP', 'jv-ID', 'ka-GE', 'kk-KZ',
'km-KH', 'kn-IN', 'ko-KR', 'lo-LA', 'lt-LT', 'lv-LV', 'mk-MK', 'mn-MN', 'mr-IN', 'ms-MY', 'my-MM', 'ne-IN', 'ne-NP',
'nl-NL', 'no-NO', 'om-ET', 'pa-IN', 'pa-PK', 'pl-PL', 'pt-BR', 'pt-PT', 'ro-RO', 'ru-RU', 'si-LK', 'sk-SK', 'sl-SI',
'sq-AL', 'sr-BA', 'sr-ME', 'sr-RS', 'sv-SE', 'sw-KE', 'ta-IN', 'ta-LK', 'te-IN', 'ti-ER', 'ti-ET', 'tg-TJ', 'th-TH',
'tk-TM', 'tl-PH', 'tr-TR', 'uk-UA', 'ur-PK', 'uz-UZ', 'vi-VN', 'zh-CN', 'zh-HK', 'zh-TW'
```
Weather Entity (hass weather card) translations are handled by Home Assistant and configured under the user -> language setting.  
[Back to top](#top)