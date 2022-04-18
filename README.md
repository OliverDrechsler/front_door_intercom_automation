[![CodeFactor](https://www.codefactor.io/repository/github/oliverdrechsler/front_door_intercom_automation/badge)](https://www.codefactor.io/repository/github/oliverdrechsler/front_door_intercom_automation)
![CI pipeline](https://github.com/OliverDrechsler/front_door_intercom_automation/workflows/FDIa/badge.svg)
[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)
[![Updates](https://pyup.io/repos/github/OliverDrechsler/front_door_intercom_automation/shield.svg)](https://pyup.io/repos/github/OliverDrechsler/front_door_intercom_automation/)
[![Known Vulnerabilities](https://snyk.io/test/github/OliverDrechsler/front_door_intercom_automation/badge.svg)](https://snyk.io/test/github/OliverDrechsler/front_door_intercom_automation)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=OliverDrechsler_front_door_intercom_automation&metric=alert_status)](https://sonarcloud.io/dashboard?id=OliverDrechsler_front_door_intercom_automation)
[![codecov](https://codecov.io/gh/OliverDrechsler/front_door_intercom_automation/branch/master/graph/badge.svg)](https://codecov.io/gh/OliverDrechsler/front_door_intercom_automation)
    
# Front-door intercom automation

**While ring at front door receive photo message and open the door via telegram one-time password**

*Under development see `dev` branch*

***It works but dev is still in progress also see todos list***  

**[📚 View on Github Pages](https://oliverdrechsler.github.io/front_door_intercom_automation/)**  

***[📚 API Docu on Github Pages](https://oliverdrechsler.github.io/front_door_intercom_automation/modules.html)***  

- [Front-door intercom automation](#front-door-intercom-automation)
  - [Short description](#short-description)
  - [Long description](#long-description)
  - [Mobile Device Apps](#mobile-device-apps)
  - [Hardware](#hardware)
    - [Hardware circuit components](#hardware-circuit-components)
    - [RPi Hardware](#rpi-hardware)
    - [How to build circuit](#how-to-build-circuit)
      - [selfmade circuit board connected to BTIcino Intercom](#selfmade-circuit-board-connected-to-bticino-intercom)
      - [2 channel relay board for door opener](#2-channel-relay-board-for-door-opener)
    - [My build pictures](#my-build-pictures)
  - [Code tree structure](#code-tree-structure)
  - [Config Files](#config-files)
    - [Main config file description](#main-config-file-description)
    - [Blink Cam config file description](#blink-cam-config-file-description)
  - [Installation](#installation)
    - [How to install / python requirements](#how-to-install--python-requirements)
    - [How to run project code as a systemd service](#how-to-run-project-code-as-a-systemd-service)
  - [How to](#how-to)
    - [How to run unit-tests](#how-to-run-unit-tests)
    - [Build pipeline checks](#build-pipeline-checks)
  - [Telegram](#telegram)
    - [How to setup a telegram bot](#how-to-setup-a-telegram-bot)
    - [Telegram Bot Commands](#telegram-bot-commands)
  - [Time-based one time passwords info and recommendations](#time-based-one-time-passwords-info-and-recommendations)
  - [ToDo's:](#todos)
  
## Short description

One Raspberry Pi is connected to a BTIcino front-door intercom.  
It detects when the door bell rings.  
Requests either from a Raspberry PI (Zero) with Camera a photo  
or from a Blink Cam (depends on defined configuration in config.yaml).  
Sends a door bell ring photo notification via telegram message to a privat  
group and attachs the photo.  
The house owner can respond with a time-based one time password in the  
privat chat to open the door.  

## Long description

Starting point was an article [Überallkingel at heise.de](https://www.heise.de/select/ct/2017/17/1502995489716437).  
At beginning i startet it with RPi's (one as a Cam and one connected to BTIcino house intercom).  
Later i decided to have infra red cam for night vison and i got during an amazon black week sale a cheap blink cam. That's why i support my own small [Flask API - PiCam API](https://github.com/OliverDrechsler/PiCam_API) Project as well the Blink Cams in general. 

This Project consists of 

- one Raspberry Pi B+ which runs this project files
  
either use one of these camera or both
- one Paspberry Pi Zero with Camera see git project [https://github.com/OliverDrechsler/PiCam_API](https://github.com/OliverDrechsler/PiCam_API)
- one Blink Camera

The main Raspberry Pi is connected via wire to the BTIcino front-door intercom.   
When the front door rings, the RPi detects it and starts  
to take a photo (depends on config file) either from PiCam API or from a Blink Cam.  
Then the RPi sends a telegram message about the door ringing to a privat chat.  
Also it sends in a second step the photo to the telegram privat group.  
The RPi runs a telegram bot. You can now respond with a one time password  
message to open the door.
  
The bot is only reacting on defined (see config file) privat chat group as well  
on known defined chat person id's!  

The bot reacts on following received commands:
-  opening the door
-  taking a snapshot/photo
-  adding blink cam 2 factor authentication code
  
The totp (time-based one time password) is compatible to each public available TOTP provider.  
It also support sha1(not recommended), sha256 (sha2) and sha512 (sha3).  
I recommend to use sha512.  
In future there will be an additional AES encrytption added.  

The telegram bot has a command feature, where you can send the new 2FA token to system. In case of first time login or renew/relogin required.  

## Mobile Device Apps

* [Telegram Messagenger for free in AppStore](https://apps.apple.com/de/app/telegram-messenger/id686449807) 
* [OTP Auth App for free in AppStore](https://apps.apple.com/de/app/otp-auth/id659877384) 
## Hardware
### Hardware circuit components

- door bell detection board:

  * Strip grid circuit board of Epoxy – 100 x 100 mit 2,54mm
  * Optocoupler (PC817)
  * to get correct voltage of 1,2V for Optocoupler, a resistor of 330 Ohm (8 Volt), 560 Ohm (12 Volt) or 1,2 Kiloohm (24 Volt) 
  * Raspberry Pi Hutschienen-Netzteil (Mean Well MDR-20-15) für den Einbau in den Sicherungskasten

- door opener board with relais:

  * saintsmart 2 channel 5V 

### RPi Hardware

- Raspberry Pi B+ with both circuits connected
- Raspberry Pi Zero with camera

### How to build circuit 

t.b.d.
#### selfmade circuit board connected to BTIcino Intercom

to describe  
***BTICino wiring diagram***  
![BTICino wiring diagram](docs/img/RPi-BTIcino.jpg)

#### 2 channel relay board for door opener

to describe  
***saintsmart 2-Channel 5V Relay Module***  
![saintsmart 2-Channel 5V Relay Module](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTD36-cHUnlLZT-B6s4C5KsQBCRfhxt5Cjqxg&usqp=CAU)
  
[shop where to buy saintsmart relay](https://www.sainsmart.com/products/2-channel-5v-relay-module)

***Jumper and wiring layout***
[wiring layout at stackexchange](https://raspberrypi.stackexchange.com/questions/39348/jumper-function-on-relay-modules)

### My build pictures 

t.b.d.

## Code tree structure

```
│
├── camera                   # Camera's package folder
│   ├── __init__.py
│   ├── blink_cam.py         # Amazon's Blink Camera modules
│   ├── cam_common.py        # a common module and to decide which cam gets used
│   └── picam.py             # a module to access my PiCam API Project vi REST-API
├── common                   # Common package folder for configuration modules
│   ├── __init__.py
│   └── config_util.py       # Common config module / class 
├── docs                     # Github Pages sphinx docu better read here https://oliverdrechsler.github.io/front_door_intercom_automation/
├── door                     # door package folder
│   ├── __init__.py
│   ├── bell.py              # bell monitoring module
│   └── opener.py            # door opening module
├── fdia.py                  # Main Script / Program
├── fdia.service             # sample systemd service config file
├── get_otp_token.py         # OLD: generate a totp password with otp lib and sha1
├── messaging                # telegram package folder
│   ├── __init__.py
│   ├── otp.py               # verify totp password module
│   ├── receive_msg.py       # telegram bot module to receive messages
│   └── send_msg.py          # telegram send message module
├── LICENSE                  # Software LICENSE
├── requirements_licenses.txt # used libraries licenes
├── README.md                # This readme file
├── blink_config.json        # Blink Camera config file. If not exist it be will created.
├── config.yaml              # main config file if not found it will use config_template.yaml
├── config_template.yaml     # a config template file to build your on config file
├── telegram_bot_setup.md    # quick guid to setup a telegram bot
└── requirements.txt         # required python libraries to install 
```

## Config Files

config_template.yaml is a template config file and must be adjusted to your needs.
Copy config_template.yaml to config.yaml into project root folder
### Main config file description

t.b.d.
Also see inside config_template.yaml

### Blink Cam config file description

t.b.d.

## Installation

### How to install / python requirements

FDIA needs root permission to access GPIO Pin.
If this is not wanted you have to adjust right to:
- /dev/gpiomem
- /sys/class/gpio...
but its you consult google for it...  

Python 3, pip3 and git cli is required.  
Clone repo to your RPi.
```git clone git@github.com:OliverDrechsler/front_door_intercom_automation.git```

now run pip3 to install python requirments
```pip3 install requirements.txt```

### How to run project code as a systemd service

Adjust file `fdia.service` to your path.
To run fdia as a service on startup with root permissions  
copy `fdia.service`to `/etc/systemd/system/`to your RPi systemd deamon folder. 
Run `systemctl daemon-reload` and `systemctl start fdia`to start it as a service

## How to

### How to run unit-tests

t.b.d.
`python3 -m pytest`

### Build pipeline checks

t.b.d.
## Telegram
### How to setup a telegram bot

see [telegram_bot_setup](telegram_bot_setup.md)
### Telegram Bot Commands

t.b.d.
## Time-based one time passwords info and recommendations

t.b.d.

## ToDo's: 

- [ ] write full documentation
- [ ] added aes encryption to send otp password with aes encrypt additionally
- [ ] add precommit checks (lint,bandit and pytest)
- [ ] add setup.py install script
- [ ] add fdia.py command line args to generate config and set new password
- [ ] pictures how i build the hardware
- [ ] pictures and docu how i mounted RPi Zero with Cam
- [ ] pictures and docu how i mounted blink cam
- [ ] pictures and docu how mounted the RPi close to BTIcino frond-door intercom in the control cabinet
- [ ] pictures door bell photo notification
- [ ] picture door bell open message

**other repo ToDo's**

- [ ] PiCam API had some ToDo's [https://github.com/OliverDrechsler/PiCam_API](https://github.com/OliverDrechsler/PiCam_API)

- [ ] develop an iPhone and an Apple Watch App to:
  - open door through one button via  
        telegram message with AES + totp code encryption  
  - geofencing feature for asking to open the door 

