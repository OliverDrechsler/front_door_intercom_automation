# Blink Camera setup

## First time setup (no blink_config.json) available

1. Follow Blink installtion guide to setup your camera in your mobile app.
2. Give your cam a name. Be careful with the camera name in Blink. The Blink library only supports ASCII characters and no language-specific special characters.
3. Test your camera with the mobile app.
4. Start configure now your blink camera in the `config.yaml` file  under section `blink:`.  
- Set `enabled` to `True`if want to use the blink.
- Set `username` and `password`.
- Set `name`for the camera name in Blink App.
- choose `night_vision` to set to `True`or `False`
- specify your blink camera json config file in `config_file`: "blink_config.json"

5. Before you start *FDIA* the first time setup please check, that  
   in `config.yaml` under `GPIO`: `testing_msg` is set to `False`
6. Start FDIA and check your log output.
7. Blink will directly send you a second factor authentication request (one time password)
   to your mobile phone or e-mail address of your account.
8. Take the 6 digit security code and send it in telegram to your `Front Door Intercom Automation` Bot.
   The message request to authenticate against blink must look like this  
   `/blink_auth <6 digit security code here>`   (without <> chars)
9. The `FDIA` will now authenticate against blink and log something like this:
```
2024-07-01 00:00:00 - blinkpy.blinkpy - Thread-1 (thread_cameras) - setup_camera_list : network = {
  "network_id": 12345,
  "name": "MyBlinkCameraGruppenSettingsName",
  "cameras": []
}
```
10. After that it will store the blink config to your defined `blink: config_file` (normally `blink_config.json`)
11. Check now your blink config file. It should contain your *credentials*, *uid*, *device_id*, *user_id* 
    and at least a **token** and some more fields.
12. Now you can test to take a foto via telegram chat group message. Just send `/Blink` and you should receive a new snapshot foto.

## Setup / configure again blink after first time setup was made

In case you want to reconfigure your blink or you issues something else or login issues,
just delete your blink `config_file` (name defined in the config.yaml).  
Double check your credentials there as well under the `blink` section.
Now follow the first time setup.

## Troubleshooting

### Known issues

#### Camera name

Actually the blink library which i use does not really support language specific special characters.  
Therefore just use standard ASCII chars and in best case no spaces in the camera name.  

#### Connecting to the right camera

When `FDIA` starts up it logs in to blink and logs
your camera like this:
```
2024-07-01 00:00:00 - blinkpy.blinkpy - Thread-1 (thread_cameras) - setup_camera_list : network = {
  "network_id": 12345,
  "name": "MyBlinkCameraGruppenSettingsName",
  "cameras": []
}
```

### Debugging

Enable debug mode for `FDIA` 

Edit `fdia.py` file  and in top of the file line 22 (after imports)  
there you'll find the section
```
"""Define logging LEVEL"""
default_log_level = logging.INFO
```

Here you can modify *logging.INFO* level to *logging.DEBUG* and store the file.

Now start up the `FDIA` again and try to read log output.

If nothing really occurs try to send from your mobile phone a `/Blink` telegram message in the chat group.

Stop the `FDIA`.  
Check again detail log output.  
In detail check all log output of the thread where teh camera code runs.  
You'll find the tread number when you search for `thread-1 (thread_cameras)`.  
Here you'll in this case it's `thread-1`. Now read all log output from *thread-1*.

If you can solve it by sour self raise a issue request in github.  

