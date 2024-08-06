# ChangeLog
## Release 1.0.2
- add: door bell gpio button bouncer time 
- add: enable option for door bell detection 
- add: enable option for door opening relais board 
- add: enable option for flask web ui and rest-api 
- refactor: web log messages 
- refactor fdia.service 
- updated: README.md 
- updated: How_to_install_fresh_RPi_with_Code.md 
- bump: version updates for:
  - Update requests from 2.32.2 to 2.32.3 
  - Update pyTelegramBotAPI from 4.21.0 to 4.22.0. 
  - Update aiohttp from 3.9.5 to 3.10.1.

## Release 1.0.1 
- LICENSE change from GPLv2 to MIT
- small refactor, 
- fix camera async
- migrated from GPIOZERO to RPI.GPIO library
- web ui add flask host ip
- added more unit tests
- updated documentation

## Release 1.0.0  - CODE REFACTORED - DOCU UPDATED
- New version with new feature like:
  python 3.10, 3.11, 3.12 support (deprecated 3.9 and below)
- WebApp, with browser page and rest api for opening 
- migrated to pyTelegramBotAPI 
- updated blinkpy to asyncio 
- daylight and night vision detect to choose camera 
- multi threading 
- using pyOTP instead passlib 
- detecting Pi Hardware native

## Release 0.0.5 and below uses and supports
- python below 3.8 and therefore older OS'es
- telepot library
- blinkpy library below 0.20.0

By default older version are not recommended to use because of vulnerabilities.
Use always latest version.


## Previous Python Version releases

**If you want use a release which works with python below 3.8 take a look at [0.0.5](https://github.com/OliverDrechsler/front_door_intercom_automation/releases/tag/v0.0.5)** 
