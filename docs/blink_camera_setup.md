# Blink Camera Setup

## First-Time Setup

Use this procedure if you do not yet have a `blink_config.json` file.

1. Set up your Blink camera in the Blink mobile app.
2. Assign a camera name.
   The Blink library used by FDIA works best with ASCII-only names. Avoid language-specific special characters and, if possible, avoid spaces.
3. Verify that the camera works correctly in the Blink app.
4. Configure the `blink:` section in `config.yaml`:

- Set `enabled` to `True`.
- Set `username` and `password`.
- Set `name` to the exact Blink camera name.
- Set `night_vision` to `True` or `False`.
- Set `config_file`, typically `blink_config.json`.

5. Before starting FDIA for the first time, make sure `GPIO.testing_msg` is set to `False` in `config.yaml`.
6. Start FDIA and watch the logs.
7. Blink should send a second-factor authentication code to your mobile phone or email address.
8. Send the 6-digit code to your FDIA Telegram bot in this format:

```text
/blink_auth <6-digit-code>
```

9. FDIA authenticates with Blink and should log output similar to:

```text
2024-07-01 00:00:00 - blinkpy.blinkpy - Thread-1 (thread_cameras) - setup_camera_list : network = {
  "network_id": 12345,
  "name": "MyBlinkCameraGroupSettingsName",
  "cameras": []
}
```

10. After successful authentication, FDIA stores the Blink session data in the configured `blink.config_file`, usually `blink_config.json`.
11. Check that the file now contains the expected authentication fields such as credentials, `uid`, `device_id`, `user_id`, and at least one token.
12. Test the camera by sending `/Blink` in the Telegram chat. FDIA should return a new snapshot.

## Reconfigure Blink After the Initial Setup

If you need to repeat the setup because of changed credentials or authentication problems:

1. Delete the configured Blink config file, usually `blink_config.json`.
2. Verify the credentials in the `blink:` section of `config.yaml`.
3. Repeat the first-time setup process.

## Troubleshooting

### Camera Name

The Blink library used by this project does not reliably support language-specific special characters. Use ASCII-only camera names for the most stable behavior.

### Verify That FDIA Uses the Correct Camera

When FDIA starts, it logs the Blink network and camera information. A typical log entry looks like this:

```text
2024-07-01 00:00:00 - blinkpy.blinkpy - Thread-1 (thread_cameras) - setup_camera_list : network = {
  "network_id": 12345,
  "name": "MyBlinkCameraGroupSettingsName",
  "cameras": []
}
```

Use this output to confirm that FDIA is connected to the expected Blink account and camera.

### Debugging

Enable debug logging in FDIA and restart the application. Then trigger a `/Blink` command from Telegram and inspect the log output for the camera thread.

If you still cannot resolve the issue, open a GitHub issue with the relevant logs and configuration details.
