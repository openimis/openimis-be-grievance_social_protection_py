# openIMIS Backend Grievance Social Protection reference module
This repository holds the files of the openIMIS Backend grievance social protection reference module.
It is dedicated to be deployed as a module of [openimis-be_py](https://github.com/openimis/openimis-be_py).

## Configuration options (can be changed via core.ModuleConfiguration)
Rights required:
* `resolution_times`: time to resolution in form of CRON timedelta: {days},{hours} where days are values between <0, 99) and hours are between 0 and 24. 
(default: `5,0`)
* `default_resolution`: The field will be in form of the JSON dictionary with pairs like: 
Key - type of the grievance, 
Value - time to resolution in form of CRON timedelta: `{days},{hours}` where days are values between <0, 99) and hours are between 0 and 24.
(default: `{Default: '5,0'}`)
Note: If for given type of the grievance time is not provided then default value is used from `resolution_times`. 
