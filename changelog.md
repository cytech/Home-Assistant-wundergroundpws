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
