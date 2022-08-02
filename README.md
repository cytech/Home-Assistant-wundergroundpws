# Home-Assistant-wundergroundpws
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![Validate with hassfest](https://github.com/cytech/Home-Assistant-wundergroundpws/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/cytech/Home-Assistant-wundergroundpws/actions/workflows/hassfest.yaml)

Home Assistant custom component sensor for Weather Underground personal weather station users

:+1: If you find this product useful, feel free to buy me a beer: https://paypal.me/cytecheng

UPGRADE NOTE v0.8.X: Requires Home Assistant v 2021.8 or later  

UPGRADE NOTE: numeric_precision must be added to your exisiting configuration.yaml for this sensor.
This adds the ability to display PWS data as integer or decimal. Valid options are 'none' or 'decimal'.
See example below.


The `wundergroundpws` platform uses [Weather Underground](http://www.wunderground.com) as a source for current weather information.

<p class='note warning'>
Free API keys are only issued to registered and active Weather Underground personal weather station users.

To use this sensor, you need to enter your personal weather station API key and Station ID in configuration.yaml.

To get a free API key:
1) You must have a personal weather station registered and uploading data to Weather Underground
    
    a) Join weather Underground
    
    b) Sign In
    
    c) My Profile -> My Weather Stations
    
    d) Add a New PWS
2) get API key at  https://www.wunderground.com/member/api-keys

Please consider this when using the following information.

To install, add this repository as custom repository for HACS and install the Weather Underground Personal Weather Station integration and copy the www directory into your .homeassistant directory.

or 

copy the custom_components directory into your .homeassistant directory
and the www directory into your .homeassistant directory.

or

copy the contents of the custom_components into an existing custom_components directory in your .homeassistant directory
and the contents of the www directory into an existing www directory in your .homeassistant directory.

Current conditions are generated from the wundergroundpws configured pws_id.

The forecast is generated from the HA configured latitude/longitude.
</p>


To add Wunderground to your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: wundergroundpws
    api_key: YOUR_API_KEY
    pws_id: YOUR_STATION_ID
    numeric_precision: none
    monitored_conditions:
      - temp
      - dewpt
      - heatIndex
```        
Description of terms and variables
```yaml
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
    monitored_conditions:
      description: Conditions to display in the frontend. The following conditions can be monitored.
      required: true
      type: list
      default: symbol
      keys:
        (generated from PWS)
        stationID:
          description: Your personal weather station (PWS) ID
        solarRadiation:
          description: Current levels of solar radiation
        neighborhood:
          description: WU PWS reference name
        obsTimeLocal:
          description: Text summary of local observation time
        uv:
          description: Current levels of UV radiation. See [here](https://www.wunderground.com/resources/health/uvindex.asp) for explanation.
        winddir:
          description: Wind degrees
        humidity:
          description: Relative humidity                  
        dewpt:
          description: Temperature below which water droplets begin to condense and dew can form
        heatIndex:
          description: Heat index (combined effects of the temperature and humidity of the air)
        windChill:
          description: Wind Chill (combined effects of the temperature and wind)      
        elev:
          description: Elevation
        precipTotal:
          description: Today Total precipitation
        precipRate:
          description: Rain intensity
        pressure:
          description: Atmospheric air pressure
        temp:
          description: Current temperature
        windGust:
          description: Wind gusts speed
        windSpeed:
          description: Current wind speed
        (generated from lat/lon forecast)        
        precip_1d:
          description: "[<sup>[1d]</sup>](#1d): Forecasted precipitation intensity"
        precip_chance_1d:
          description: "[<sup>[1d]</sup>](#1d): Forecasted precipitation probability in %"      
        temp_high_1d:
          description: "[<sup>[1d]</sup>](#1d): Forecasted high temperature"
        temp_low_1d:
          description: "[<sup>[1d]</sup>](#1d): Forecasted low temperature"
        wind_1d:
          description: "[<sup>[1d]</sup>](#1d): Forecasted wind speed"
        weather_1d:
          description: "[<sup>[12h]</sup>](#12h): A human-readable weather forecast of Day"
        weather_1n:
          description: "[<sup>[12h]</sup>](#12h): A human-readable weather forecast of Night"      
```

All the conditions listed above will be updated every 5 minutes.

Conditions above marked with <a name="1d">[1d]</a> are daily forecasts. To get forecast for different day, replace the number
in `_1d_` part of the sensor name. Valid values are from `1` to `5`.

Conditions above marked with <a name="1n">[1n]</a> are nightly forecasts. To get forecast for different night, replace the number
in `_1n_` part of the sensor name. Valid values are from `1` to `5`.

```yaml
    sensor:
      - platform: wundergroundpws
        api_key: YOUR_API_KEY
        pws_id: YOUR_STATION_ID
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
