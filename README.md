# Home-Assistant-Wundergroundpws v1.X.X
Home Assistant custom integration for Weather Underground personal weather station users.  
Includes a native Home Assistant Weather Entity and a variety of weather sensors.  
Current conditions are generated from the wundergroundpws configured pws_id.  
Forecast is generated from the Home Assistant configured latitude/longitude.  
The `wundergroundpws` platform uses [Weather Underground](http://www.wunderground.com) as a source for current weather information.  
Thanks to @shtrom for ALL the work on this update!

:+1: If you find this software useful, feel free to make a donation: [Paypal.me Donation Link](https://paypal.me/cytecheng)  

-------------------

[Prerequisites](#installation-prerequisites)

[Weather Underground PWS API Key](#weather-underground-pws-api-key)

[Installation](#installation)

[Upgrade](#upgrade)

[Description of terms and variables](#description-of-terms-and-variables)

[Sample configuration.yaml](#sample-configurationyaml)

# Installation Prerequisites
Please review the minimum requirements below to determine whether you will be able to
install and use the software.

- Home Assistant Version 2022.11 or greater
- Registered and active Weather Underground personal weather station API key 

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


# Installation
Download the latest release zip file from this repository.
Extract the zip file to a temporary directory.
-------
Stop Home Assistant.  
Copy the custom_components directory from the extracted file into your .homeassistant directory
and the www directory from the extracted file into your .homeassistant directory.  
or  
copy the contents of the custom_components directory from the extracted file into an existing custom_components directory in your .homeassistant directory
and the contents of the www directory from the extracted file into an existing www directory in your .homeassistant directory.  
To add Wundergroundpws to your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
wundergroundpws:
  api_key: YOUR_API_KEY
  pws_id: YOUR_STATION_ID
  numeric_precision: none

weather:
  - platform: wundergroundpws

sensor:
  - platform: wundergroundpws
    monitored_conditions:
      - temp
      - dewpt
      - heatIndex
```
Restart Home Assistant

# Upgrade
UPGRADE NOTE v1.0.0: BREAKING CHANGE -  Requires Home Assistant v 2022.11 or later.  
REQUIRES SIGNIFICANT CHANGES TO CONFIGURATION.YAML.  
See "Example configuration.yaml entry" above.  
TO UPGRADE FROM v0.8.X:
1. Stop Home Assistant.
2. Delete contents of existing "custom_components/wundergroundpws" directory.
3. Download v1.X.X zip file.
4. Extract v1.X.X zip file and copy the contents of the "custom_components/wundergroundpws" directory into the existing "custom_components/wundergroundpws" directory.
5. Modify your configuration.yaml, to resemble the "Example configuration.yaml entry" above.
6. Restart Home Assistant.
7. Existing sensors in any entity cards should be the same.  
8. In lovelace, add a "weather forecast" card selecting the "weather.YOUR_STATION_ID" entity and save.  

        
# Description of terms and variables
```yaml
  wundergroundpws:
    api_key:
      description: The API key for Weather Underground. See above for details.
      required: true
      type: string
    pws_id:
      description: "You must enter a Personal Weather Station ID. The station id will be used to display current weather conditions."
      required: true
      type: string
    numeric_precision:
        description: Required - Show PWS data as integer or decimal
        required: true - Value of 'none' or 'decimal'
        type: string
    lang:
      description: Specify the language that the API returns. The current list of all Wunderground language codes is available  at https://docs.google.com/document/d/13HTLgJDpsb39deFzk_YCQ5GoGoZCO_cRYzIxbwvgJLI/edit#). If not specified, it defaults to English (en-US).
      required: false
      type: string
      default: en-US
    latitude:
      description: Latitude coordinate for weather forecast (required if **longitude** is specified).
      required: false
      type: string
      default: Coordinates defined in your `configuration.yaml`
    longitude:
      description: Longitude coordinate for weather forecast (required if **latitude** is specified).
      required: false
      type: string
      default: Coordinates defined in your `configuration.yaml`
```
```yaml
  monitored_conditions:
#      description: Conditions to display in the frontend. The following conditions can be monitored.
#      required: true
#      type: list
#      default: symbol
     dewpt:
       description: Temperature below which water droplets begin to condense and dew can form
     elev:
       description: Elevation
     heatIndex:
       description: Heat index (combined effects of the temperature and humidity of the air)
     humidity:
       description: Relative humidity                  
     neighborhood:
       description: WU PWS reference name
     obsTimeLocal:
       description: Text summary of local observation time
     precip_1d:
       description: "[<sup>[1d]</sup>](#1d): Forecasted precipitation intensity"
     precip_chance_1d:
       description: "[<sup>[1d]</sup>](#1d): Forecasted precipitation probability in %"      
     precipRate:
       description: Rain intensity
     precipTotal:
       description: Today Total precipitation
     pressure:
       description: Atmospheric air pressure
     solarRadiation:
       description: Current levels of solar radiation
     stationID:
       description: Your personal weather station (PWS) ID
     temp:
       description: Current temperature
     temp_high_1d:
       description: "[<sup>[1d]</sup>](#1d): Forecasted high temperature"
     temp_low_1d:
       description: "[<sup>[1d]</sup>](#1d): Forecasted low temperature"
     uv:
       description: Current levels of UV radiation. See [here](https://www.wunderground.com/resources/health/uvindex.asp) for explanation.
     weather_1d:
       description: "[<sup>[12h]</sup>](#12h): A human-readable weather forecast of Day"
     weather_1n:
       description: "[<sup>[12h]</sup>](#12h): A human-readable weather forecast of Night"
     wind_1d:
       description: "[<sup>[1d]</sup>](#1d): Forecasted wind speed"
     windChill:
       description: Wind Chill (combined effects of the temperature and wind)      
     winddir:
       description: Wind degrees
     windDirectionName:
       description: Wind cardinal direction (N,S,E,W, etc)
     windGust:
       description: Wind gusts speed
     windSpeed:
       description: Current wind speed      
```

All the conditions listed above will be updated every 5 minutes.

Conditions above marked with <a name="1d">[1d]</a> are daily forecasts. To get forecast for different day, replace the number
in `_1d_` part of the sensor name. Valid values are from `1` to `5`.

Conditions above marked with <a name="1n">[1n]</a> are nightly forecasts. To get forecast for different night, replace the number
in `_1n_` part of the sensor name. Valid values are from `1` to `5`.

```yaml
    sensor:
      - platform: wundergroundpws
        monitored_conditions:
          - weather_1d
          - weather_1n
          - weather_2d
          - weather_2n
          - weather_3d
          - weather_3n
          - weather_4d
          - weather_4n
```
<p class='note warning'>
Note: While the platform is called “wundergroundpws” the sensors will show up in Home Assistant as “WUPWS” (eg: sensor.wupws_weather_1d).
</p>

Note that the Weather Underground sensor is added to the entity_registry, so second and subsequent Personal Weather Station ID (pws_id) will have their monitored conditions suffixed with an index number e.g.

```yaml
    - sensor.wupws_weather_1d_metric_2
```
Additional details about the API are available [here](https://docs.google.com/document/d/1eKCnKXI9xnoMGRRzOL1xPCBihNV2rOet08qpE_gArAY/edit).

# Sample configuration.yaml
```yaml
wundergroundpws:
  api_key: YOUR_API_KEY
  pws_id: YOUR_STATION_ID
  numeric_precision: none

weather:
  - platform: wundergroundpws

sensor:
  - platform: wundergroundpws
    monitored_conditions:
      - dewpt
      - elev
      - heatIndex
      - humidity
      - neighborhood
      - obsTimeLocal
      - precip_1d
      - precip_chance_1d
      - precipRate
      - precipTotal
      - pressure
      - solarRadiation
      - stationID
      - temp
      - temp_high_1d
      - temp_low_1d
      - today_summary
      - uv
      - weather_1d
      - weather_1n
      - weather_2d
      - weather_2n
      - weather_3d
      - weather_3n
      - weather_4d
      - weather_4n
      - weather_5d
      - weather_5n
      - wind_1d
      - windChill
      - winddir
      - windDirectionName
      - windGust
      - windSpeed
```