---
layout: page
title: "Weather UndergroundPWS (WUndergroundPWS)"
description: "Instructions on how to integrate Weather Underground (WUnderground) Personal Weather Station within Home Assistant."
date: 2019-03-19
sidebar: true
comments: false
sharing: true
footer: true
logo: wunderground.png
ha_category: Weather
ha_release: 0.89
ha_iot_class: "Cloud Polling"
---

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

Current conditions are generated from the wundergroundpws configured pws_id.

Forecast is generated from the HA configured latitude/longitude.
</p>

{% linkable_title Configuration %}

To add Wunderground to your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: wundergroundpws
    api_key: YOUR_API_KEY
    pws_id: YOUR_STATION_ID
    monitored_conditions:
      - temp
      - dewpt
      - heatIndex
```

{% configuration %}
api_key:
  description: The API key for Weather Underground. See above for details.
  required: true
  type: string
pws_id:
  description: "You must enter a Personal Weather Station ID. The station id will be used to display current weather conditions."
  required: true
  type: string
lang:
  description: Specify the language that the API returns. The current list of all Wunderground language codes is available [here](https://docs.google.com/document/d/13HTLgJDpsb39deFzk_YCQ5GoGoZCO_cRYzIxbwvgJLI/edit#). If not specified, it defaults to English (en-US).
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
    UV:
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
{% endconfiguration %}

All the conditions listed above will be updated every 5 minutes.

## {% linkable_title Forecasts %}

### {% linkable_title Daily forecasts %}

Conditions above marked with <a name="1d">[1d]</a> are daily forecasts. To get forecast for different day, replace the number
in `_1d_` part of the sensor name. Valid values are from `1` to `5`.

Conditions above marked with <a name="1n">[1n]</a> are nightly forecasts. To get forecast for different night, replace the number
in `_1n_` part of the sensor name. Valid values are from `1` to `5`.

## {% linkable_title Additional examples %}

### {% linkable_title Daily forecast %}

```yaml
sensor:
  - platform: wunderground
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

group:
  daily_forecast:
    name: Daily Forecast
    entities:
      - sensor.pws_weather_1d
      - sensor.pws_weather_1n
      - sensor.pws_weather_2d
      - sensor.pws_weather_2n
      - sensor.pws_weather_3d
      - sensor.pws_weather_3n
      - sensor.pws_weather_4d
      - sensor.pws_weather_4n
```


### {% linkable_title Weather overview %}

<p class='note warning'>
Note: While the platform is called “wundergroundpws” the sensors will show up in Home Assistant as “WUPWS” (eg: sensor.wupws_weather_1d).
</p>

Note that the Weather Underground sensor is added to the entity_registry, so second and subsequent Personal Weather Station ID (pws_id) will have their monitored conditions suffixed with an index number e.g.

```yaml
- sensor.wupws_weather_1d_metric_2
```

Additional details about the API are available [here](https://docs.google.com/document/d/1eKCnKXI9xnoMGRRzOL1xPCBihNV2rOet08qpE_gArAY/edit).