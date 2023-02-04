v1.1.1  
Remove +1 adjustment to forecast temperatureMin for weather entity.  
This caused current day forecast temp min to jump to next day temp min after 3:00pm.  

Set config numeric_precision to optional and default 'none'.

Added optional "calendarday_temp" to wundergroundpws configuration.  
If set true, retrieves main Forecast temperature max/min (NOT daypart) relative to calendar day (12:00am -> 11:59pm)  
as opposed to API period (~7:00am -> ~6:59am).  
Only affects the weather entity forecast values, not the sensors.   
This field is undocumented in The Weather Company PWS API, so it is subject to change and if removed from  
the API response in the future, will crash the integration if set true.  

moved translations directory to wupws_translations.  
updated nl.json per PR#152.

v1.1.0  
Replace condition mapping from wxPhraseShort to iconCode
- wxPhraseShort is not documented and subject to change by the API and iconCode is not
  - response from weather company API email after request of wxPhraseShort list:
        The wxPhraseShort values are not available to be shared externally.
        These strings are possible to be changed, and mapping these strings can lead to issues for client apps in the
        future.
- this also allows for the wundergroundpws lang to be set and functional
  - Note: Only the TWC  5-day forecast API handles the translation of phrases for values of the following data.
        dayOfWeek, daypartName, moonPhase, narrative, qualifierPhrase, uvDescription, windDirectionCardinal, windPhrase, wxPhraseLong

Added localization mechanism for wupws sensor friendly names.
Fix/rework sensor device_class and state_class for statistics  
update wunderground language codes

v1.0.3  
add "Foggy" to fog condition_map
add "Ice" to snowy condition map
add "Snw Shwrs" to snowy condition map
add "Snow Showers" to snowy condition map
add "Snow" to snowy condition map
add "Rn/Snw" to snowy-rainy condition map
add "T-Showers" to rainy condition map
add "Drizzle" to rainy condition map
add "P Cldy/Wind" to windy-variant condition map
add "Iso" to condition_modifiers

v1.0.2  
Add state_class to sensors for automatic stats/graphs
add "Lgt Rain" to condition_map
add "Early" to condition_modifiers
added - precip_chance_  1n thru 5n sensors for nighttime
return 'Expired' instead of 'unknown' for daypart sensors from the API after 3:00pm Local Apparent Time
Wunderground API caveat: 
PLEASE NOTE: The daypart object as well as the temperatureMax field OUTSIDE of the daypart object will appear as null in the API after 3:00pm Local Apparent Time.



v1.0.1  
merge weather entity fixes from @shtrom
correct pressure reporting in weather entity

v1.0.0  
complete rework by @shtrom to add weather entity.  
Pull Request #114 - https://github.com/shtrom/Home-Assistant-wundergroundpws/tree/weather-entity  
BREAKING CHANGE for upgrades

v0.8.3  
merge PR #100 Add sensor for wind direction as friendly name

v0.8.2  
2022-11-03
fix for HASS 2023.1 deprecation is_metric

v0.8.1  
2021-12-16
fixes for 2022.X deprecations:  
apply pr #75 - Drop loop= kwarg from async_timeout.timeout  
replace device_state_attributes with extra_state_attributes in sensor.py  

v0.8.0  
2021-08-03  
v0.8.0 requires Home Assistant 2021.8 or later  
fix missing forecast unit_of_measure, issue #70  

2021-02-24  

copies of weathericons (PR#30)

2021-02-21  

merge PR#50

2021-02-11  

updated readme - PR#36
added config item for numeric_precision  PR#12
fixed icon issue - PR#30
fixed error when winddir, humidity is null

