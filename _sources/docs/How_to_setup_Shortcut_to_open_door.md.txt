# How to setup Apple IOS Shortcut App to open door via REST-API call

It is required that you have setup beforehand the OTP App on your mobile.  
see [How_to_setup_OTP_App_on_mobile_phone](How_to_setup_OTP_App_on_mobile_phone.md)  
  
1. Open on iPhone Apple Shortcut app.  
2. Create or navigate to a folder of your choice.  
3. Select `+` to add a new shortcut  
    ![1](_static/Sortcut_setup_1.PNG)  

4. name/rename your new shortcut.  
    ![2](_static/Sortcut_setup_2.PNG)  

5. type in search `otp` and select `copy a code`  
    ![3](_static/Sortcut_setup_3.PNG)  
    ![4](_static/Sortcut_setup_4.PNG) 
    ![5](_static/Sortcut_setup_5.PNG)  

6. Now search another function in search bar `inhalte abrufen` or `request content`  
    ![6](_static/Sortcut_setup_6.PNG)  
  
7. Insert:
   - your RPi URL / IP = `http://<RPi hostname or IP in your local wifi net>:<Port e.g. 5001>/open`  
   - Method: POST
   - Header  = add Key -> KeyName = `Authorization` Value = `Basic <here your base64 encoded WebUsername:Password>`
   - Content `JSON`
   - Add key = `totp` and value = `code` > otp code from previous step.
    ![7](_static/Sortcut_setup_7.PNG)  
    ![8](_static/Sortcut_setup_8.PNG)  
    ![9](_static/Sortcut_setup_9.PNG)  
  
8. Finished. Try to run it.   
  ![10](_static/Sortcut_setup_10.PNG)  
