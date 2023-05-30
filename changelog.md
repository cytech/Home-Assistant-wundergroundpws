v2.0.2
fix error on expired sensors - HASS 2023.5 rejecting string "-", change to None (shows as "Unknown) 
corrects issues # 169, 173

v2.0.1
add user-agent to config_flow (error on docker installation)

v2.0.0  
Redesign sensors - BREAKING CHANGE - no upgrade path from earlier versions  
move integration to config_flow
