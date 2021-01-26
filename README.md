[![CodeFactor](https://www.codefactor.io/repository/github/oliverdrechsler/front_door_intercom_automation/badge)](https://www.codefactor.io/repository/github/oliverdrechsler/front_door_intercom_automation)
![CI pipeline](https://github.com/OliverDrechsler/front_door_intercom_automation/workflows/FDIa/badge.svg)
[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)
[![Updates](https://pyup.io/repos/github/OliverDrechsler/front_door_intercom_automation/shield.svg)](https://pyup.io/repos/github/OliverDrechsler/front_door_intercom_automation/)
[![Python 3](https://pyup.io/repos/github/OliverDrechsler/front_door_intercom_automation/python-3-shield.svg)](https://pyup.io/repos/github/OliverDrechsler/front_door_intercom_automation/)
[![Known Vulnerabilities](https://snyk.io/test/github/OliverDrechsler/front_door_intercom_automation/badge.svg)](https://snyk.io/test/github/OliverDrechsler/front_door_intercom_automation)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=OliverDrechsler_front_door_intercom_automation&metric=alert_status)](https://sonarcloud.io/dashboard?id=OliverDrechsler_front_door_intercom_automation)
# front door intercom automation
## Ring at front door receive photo notification and open via telegram one-time password

**Under development see `dev` branch**

***It works but dev is still in progress***

## Short - description

One Raspberry Pi is connected to a BTCino front-door intercom.  
It detects when the door bell rings.  
Requests either from a Raspberry PI (Zero) with Camera a photo  
or from a Blink Cam (depends on defined configuration in config.yaml).  
Sends a door bell ring notification via telegram message to a privat  
group and attachs the photo.  
The house owner can respond with a time-based one time password in the  
privat chat to open the door.  

## Long - description

This Project consists of 

- one Raspberry Pi B+ which runs this project files
  
either one of these camera or both
- one Paspberry Pi Zero with Camera see git project [https://github.com/OliverDrechsler/PiCam_API](https://github.com/OliverDrechsler/PiCam_API)
- one Blink Camera

The main Raspberry Pi is connected via wire to the BTCino front-door intercom.   
When the front door bell rings the RPi detects it and starts  
to take a photo (depens on config file) either from PiCam API or from Blink cam.  
Then the RPi sends a telegram message about the door bell to a privat chat.  
Also it sends in a second step the photo to the telegram privat group.  
The RPi run in an additional thread a telegram bot.  
  
The bot is only reacting on defined (see config file) privat chat group as well  
on known defined chat person id's!  

The bot reacts on receiving commands:
-  for opening the door, 
-  taking a snapshot/photo or 
-  adding blink cam 2 factor authentication code
  
If the bot receives a time-based one-time-password  
it will open the frond door via wire through the BTCino intercom.  
The totp (time-based one time password) is compatible to each public available TOTP provider.  
It also support sha256 (sha2) and sha512 (sha3). I recommend to use sha512.  
In future there will be an additional AES encrytption added.  

Because Blink renews frequently their 2FA token via mail    
the bot has a command feature,  
where you can send the actual 2FA token to system  
(if not already provided in an additional blink_config.json file).  


## ToDo's: 

- [ ] write unit tests
- [ ] documentation
- [ ] generate code api docu via sphinx and add it to readthedocs.org
- [ ] docu and pictures about circurit layout and wiring
- [ ] pictures how i build the hardware
- [ ] pictures and docu how i mounted RPi Zero with Cam
- [ ] pictures and docu how i mounted blink cam
- [ ] pictures and docu how mounted the RPi close to BTCino frond-door intercom in the control cabinet

**other repo ToDo's**

- [ ] PiCam API had some ToDo's [https://github.com/OliverDrechsler/PiCam_API](https://github.com/OliverDrechsler/PiCam_API)

- [ ] develop an iPhone and an Apple Watch App to:
  - open door through one button via  
        telegram message with AES + totp code encryption  
  - geofencing feature for asking to open the door 


