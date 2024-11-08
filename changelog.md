v2.0.9  
replace removed python async_timeout.timeout with asyncio.timeout  
addresses issues in discussion #s  [260](https://github.com/cytech/Home-Assistant-wundergroundpws/discussions/260) and [261](https://github.com/cytech/Home-Assistant-wundergroundpws/discussions/261)

v2.0.8  
modify Forecast Summary sensor initialization.  
when integration was loaded after 3:00 pm apparent time, None was set as value type instead of string, causing failure.  
addresses issues in discussion #s  [248](https://github.com/cytech/Home-Assistant-wundergroundpws/discussions/248) and [246](https://github.com/cytech/Home-Assistant-wundergroundpws/discussions/246)  


v2.0.7  
Move sensor translation file initialization to WundergroundPWSUpdateCoordinatorConfig in `__init__.py`    
Fixes "Detected blocking call to open with args" warning

v2.0.6  
Increase default rest timeout from 10 seconds to 30 seconds  
Starting with home assistant 2024, rest availability on Home Assistant Operating System (on Raspberry Pi ?) after restart is delayed and causing setup failure.  
If you still get a WUPWS setup error after restarting Home Assistant, you can try and change the DEFAULT_TIMEOUT in const.py to 60 seconds. 

v2.0.5  
fix error in cardinal wind direction when api returns None


v2.0.4  
requires Home Assistant version 2023.9 or greater  
address weather entity forecast deprecation for 2024.3  
return forecast date of weather entity in UTC RFC 3339  (issue #183)  
note: If the forecast is not displayed in the weather card after upgrading from v2.x.x to v2.0.4, edit the weather card in the dashboard and re-save it.  


v2.0.3  
fix load failure on hass 2023.9.0 _attr_visibility  
does not address deprecation of forecast  
"this is deprecated and will be unsupported from Home Assistant 2024.3"  

v2.0.2  
fix error on expired sensors - HASS 2023.5 rejecting string "-", change to None (shows as "Unknown)   
corrects issues # 169, 173  

v2.0.1  
add user-agent to config_flow (error on docker installation)  

v2.0.0    
Redesign sensors - BREAKING CHANGE - no upgrade path from earlier versions    
move integration to config_flow  
