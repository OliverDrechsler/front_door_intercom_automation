# Setup OTP

To store a master password for *totp* *time pased one time password* it must be encoded with base32 as a hash.
You can run the the cli script `encrypt_decrypt_password_with_base32.py` in `tools` diretory.
Command examples see below.  
Than you get a base32 hashed password and now have to store this password in the `config.yaml` under section `otp:` `password:`

This password is you supre secure password for the time based one time password generation.  
For the TOTP genenration it's required that you specify some more config settings in `config.yaml`.  
TOTP section in `config.yaml` section
```
otp:
  password: "KRSXG5CQIASCIVZQOJCA===="
  length: 6
  interval: 30
  hash_type: sha256
```
- The `password` is your generated base32 hashed password
- The `length` is the length of the one time password code.  
  By default mostly used is 6 but it recommended to use a higher value upt to 10.
- The `interval`is the time interval how long the password is valid for your input / sending to app.  
  By default mostly used in the internet is 30 (seconds).
- The `hash_type` is the time based one time password hash algorythm to use.  
  Most broadly used ist `sha256` (equal to sha2) but i recommend to use `sha512` which is equal to sha3.  
  Do not use sha1!  
  
**It is important to remember this this seetings since these will be required to configure on your Mobile OTP / Authenticator App**
The generated otp code will than send via telegram chat channel to `fdia` app to open the door.



## Script command options

The script `tools/encrypt_decrypt_password_with_base32.py` has
following command options:
- `--encrypt <here password to encrypt>`
- `--decrypt <here password to decrypt>`

### Example encrypt command:
Command:
```
tools/encrypt_decrypt_password_with_base32.py --encrypt mySuperSecurePassW0Rd1
```
Output:
```
NV4VG5LQMVZFGZLDOVZGKUDBONZVOMCSMQYQ====
```

### Example decrypt command
Command:
```
tools/encrypt_decrypt_password_with_base32.py --decrypt NV4VG5LQMVZFGZLDOVZGKUDBONZVOMCSMQYQ====
```

Output:
```
mySuperSecurePassW0Rd1
```

