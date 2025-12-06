# How to install fresh Image and FDIA code on RPi

## Prepare SD Card

1. open RPi Imager
2. Select RPi hardware , Image RPI OS (Debian "Bookworm") Lite, choose your SD Card
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
21. For Raspberry PI 1 with less Ram disable RAM /tmp filesystem `systemctl mask tmp.mount` and `reboot`
22. `cd /usr/local/bin`
23. `git clone https://github.com/OliverDrechsler/front_door_intercom_automation.git` clone repo.
24. `cd front_door_intercom_automation`
25. `python3 -m venv .venv` create a python virtualenv.
26. `chmod +x .venv/bin/activate`
27. `.venv/bin/activate`
28. add `eval "$(direnv hook bash)"`  to `~/.bashrc`
29. run `source ~/.bashrc`
30. create `.envrc`  in fdia dir and add lines 
    ```
    export VIRTUAL_ENV=./.venv
    layout python-venv $VIRTUAL_ENV
    ```
31.  now run `direnv allow`
32.  for pillow on python 3.13+ on RPi1 (armv6 old system install upo max version 12.0) 
    ```
    apt install -y \
        python3-dev python3-pip python3-setuptools python3-wheel \
        libjpeg-dev zlib1g-dev libtiff5-dev libfreetype6-dev \
        liblcms2-dev libwebp-dev libopenjp2-7-dev libjpeg62-turbo-dev \
        tk-dev tcl-dev

    /usr/local/bin/front_door_intercom_automation/.venv/bin/pip3 install --no-cache-dir --force-reinstall Pillow
    ```
33.  `.venv/bin/pip3 install -r requirements.txt`to install required libs.
34.    configure now `config.yaml`
35. `.venv/bin/python3 -m fdia` test run
36. Edit file `fdia.service` and adjust to your path to `ExecStart=/usr/local/bin/front_door_intercom_automation/.venv/bin/python3 /usr/local/bin/front_door_intercom_automation/fdia.py`  because python fdia code runs in python virtualenv therefore we've to call this python3 executable before.
37. To run fdia as a service on startup with root permissions  
    copy `fdia.service`to `/etc/systemd/system/`to your RPi systemd deamon folder.  
38. Run `systemctl daemon-reload` and `systemctl start fdia`to start it as a service.
39. check log output `journalctl -xu fdia -f`
40. activate new service `systemctl enable fdia.service`



## Hint for direnv error

In case you get an error with direnv, you can try to run the following command to fix it:
Command:
```bash
direnv allow
```

Error:
```
direnv: loading front_door_intercom_automation/.envrc
environment:747: layout_python-venv: command not found
direnv: export +VIRTUAL_ENV
```

- create a new file in `~/.config/direnv/direnvrc` with content:
  ```bash
  layout_python-venv() {
    local python=${1:-python3}
    [[ $# -gt 0 ]] && shift
    unset PYTHONHOME
    if [[ -n $VIRTUAL_ENV ]]; then
        VIRTUAL_ENV=$(realpath "${VIRTUAL_ENV}")
    else
        local python_version
        python_version=$("$python" -c "import platform; print(platform.python_version())")
        if [[ -z $python_version ]]; then
        log_error "Could not detect Python version"
        return 1
        fi
        VIRTUAL_ENV=$PWD/.direnv/python-venv-$python_version
    fi
    export VIRTUAL_ENV
    if [[ ! -d $VIRTUAL_ENV ]]; then
        log_status "no venv found; creating $VIRTUAL_ENV"
        "$python" -m venv "$VIRTUAL_ENV"
    fi
    PATH="${VIRTUAL_ENV}/bin:${PATH}"
    export PATH
  }
  ```
- run now `source ~/.bashrc` and than 
  ```
  cd /usr/local/bin/front_door_intercom_automation
  direnv allow
  ```

