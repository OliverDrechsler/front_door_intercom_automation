# How to install fresh Image and FDIA code on RPi

## Prepare SD Card

1. open RPi Imager
2. Select RPi hardware , Image RPI OS Lite, choose your SD Card
3. Select next and choose configure settings.
4. Enter Hostname
5. Enter Username and password
6. Add your ssh public key in ther `service` section `authentication via public key`
7. Click next and procceed with imaging.

8. Insert SD Card in RPi1 b+ (or above Hardware) and power on
9. System will start up and after a while it reboots automatically.
10. After second boot you can try to login
11. `sudo su`  switch to root user
12. `nmcli -p connection show` show network interface config
13. `nmcli c mod "Wired connection 1" ipv4.addresses 10.0.0.220/24 ipv4.method manual`  set static ip
14. `nmcli con mod "Wired connection 1" ipv4.gateway 10.0.0.1` set gateway ip
15. `nmcli con mod "Wired connection 1" ipv4.dns 10.0.0.1`set dns to your home local network router (most use cases)
16. If using multiple DNS Servers set like this `nmcli con mod "Wired connection 1" ipv4.dns "8.8.8.8,8.8.4.4"`
17. If you want to use multiple IP's you can set `nmcli c mod "Wired connection 1" ipv4.addresses "10.0.0.220/24, 10.0.0.221/24, 10.0.0.222/24" ipv4.method manual` like this
18. shutdown interface and up again to activate settings `nmcli c down "Wired connection 1" && sudo nmcli c up "Wired connection 1"`
19. show network config run `nmcli -p connection show "Wired connection 1"`
20. Now it's time to install required base software `sudo apt install mc git screen curl python3-pip python3.11-venv direnv`
21. `cd /usr/local/bin`
22. `git clone https://github.com/OliverDrechsler/front_door_intercom_automation.git` clone repo.
23. `cd front_door_intercom_automation`
24. `python3 -m venv .venv` create a python virtualenv.
25. `chmod +x .venv/bin/activate`
26. `.venv/bin/activate`
27. add `eval "$(direnv hook bash)"`  to `~/.bashrc`
28. run `source ~/.bashrc`
29. create `.envrc`  in fdia dir and add lines 
    ```
    export VIRTUAL_ENV=./.venv
    layout python-venv $VIRTUAL_ENV
    ```
31.  now run `direnv allow`
32.  `.venv/bin/pip3 install -r requirements.txt`to install required libs.
33.    configure now `config.yaml`
34. `.venv/bin/python3 -m fdia.py` test run
35. Edit file `fdia.service` and adjust to your path to `ExecStart=/usr/local/bin/fdia/.venv/bin/python3 /usr/local/bin/fdia/fdia.py`  because python fdia code runs in python virtualenv therefore we've to call this python3 executable before.
36. To run fdia as a service on startup with root permissions  
    copy `fdia.service`to `/etc/systemd/system/`to your RPi systemd deamon folder.  
37. Run `systemctl daemon-reload` and `systemctl start fdia`to start it as a service.
38. check log output `journalctl -xu fdia -f`