# How to Set Up an Apple iOS Shortcut to Open the Door

This guide shows how to create an Apple Shortcuts workflow that sends a TOTP code to the FDIA REST API.

Prerequisite:

- Set up your OTP app first. See [How_to_setup_OTP_App_on_mobile_phone.md](./How_to_setup_OTP_App_on_mobile_phone.md).

## Create the Shortcut

1. Open the Apple Shortcuts app on your iPhone.
2. Create a new shortcut or open a folder where you want to store it.
3. Tap `+` to create a new shortcut.

![Step 1](_static/Sortcut_setup_1.PNG)

4. Name or rename the shortcut.

![Step 2](_static/Sortcut_setup_2.PNG)

5. Search for `OTP` and add the action that copies a code from your OTP app.

![Step 3](_static/Sortcut_setup_3.PNG)
![Step 4](_static/Sortcut_setup_4.PNG)
![Step 5](_static/Sortcut_setup_5.PNG)

6. Search for the action to fetch web content, for example `Get Contents of URL`.

![Step 6](_static/Sortcut_setup_6.PNG)

7. Configure the request:

- URL: `http://<RPi-hostname-or-IP>:<port>/open`
- Method: `POST`
- Header key: `Authorization`
- Header value: `Basic <base64-encoded-username:password>`
- Content type: `JSON`
- JSON field: `totp`
- JSON value: the OTP code from the previous step

![Step 7](_static/Sortcut_setup_7.PNG)
![Step 8](_static/Sortcut_setup_8.PNG)
![Step 9](_static/Sortcut_setup_9.PNG)

8. Save the shortcut and test it.

![Step 10](_static/Sortcut_setup_10.PNG)

## Notes

- This shortcut works with the FDIA Flask REST API.
- It is intended for local network use or access over VPN.
- Do not expose the FDIA web service directly to the public internet.
