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

