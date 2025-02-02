# ChangeLog
# Release 1.0.6
## What's Changed
### Exciting New Features 🎉
* add changelog generator pipeline by @OliverDrechsler in https://github.com/OliverDrechsler/front_door_intercom_automation/pull/194
### 🏕 Features
* Update CHANGELOG.md by @OliverDrechsler in https://github.com/OliverDrechsler/front_door_intercom_automation/pull/195
* Scheduled weekly dependency update for week 48 by @pyup-bot in https://github.com/OliverDrechsler/front_door_intercom_automation/pull/196
* Scheduled weekly dependency update for week 50 by @pyup-bot in https://github.com/OliverDrechsler/front_door_intercom_automation/pull/198
* Scheduled weekly dependency update for week 52 by @pyup-bot in https://github.com/OliverDrechsler/front_door_intercom_automation/pull/200
* Scheduled weekly dependency update for week 02 by @pyup-bot in https://github.com/OliverDrechsler/front_door_intercom_automation/pull/201
* Fix/picam request exceptions by @OliverDrechsler in https://github.com/OliverDrechsler/front_door_intercom_automation/pull/203
* Breaking change fix daylight detection from timezone utc to local timezone needs adjustment in config file by @OliverDrechsler in https://github.com/OliverDrechsler/front_door_intercom_automation/pull/204

**Full Changelog**: https://github.com/OliverDrechsler/front_door_intercom_automation/compare/1.0.5...1.0.6




# Release 1.0.5
## What's Changed
### Exciting New Features 🎉
* add release notes pipeline by @OliverDrechsler in https://github.com/OliverDrechsler/front_door_intercom_automation/pull/193
### 👒 Dependencies
* Scheduled weekly dependency update for week 39 https://github.com/OliverDrechsler/front_door_intercom_automation/pull/183
* Scheduled weekly dependency update for week 40 https://github.com/OliverDrechsler/front_door_intercom_automation/pull/184
* Scheduled weekly dependency update for week 42 https://github.com/OliverDrechsler/front_door_intercom_automation/pull/186
* Scheduled weekly dependency update for week 44 https://github.com/OliverDrechsler/front_door_intercom_automation/pull/189
* Scheduled weekly dependency update for week 45 https://github.com/OliverDrechsler/front_door_intercom_automation/pull/190
* Scheduled weekly dependency update for week 46 https://github.com/OliverDrechsler/front_door_intercom_automation/pull/191
* Scheduled weekly dependency update for week 47 https://github.com/OliverDrechsler/front_door_intercom_automation/pull/192
**Full Changelog**: https://github.com/OliverDrechsler/front_door_intercom_automation/compare/1.0.4...1.0.5

## Release 1.0.4
- bumped lib versions
- updated doc readme.md
- added unit tests for tools scripts
- translated static web-ui page from german to english

## Release 1.0.3
- fix camera PiCam_API download filename

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
