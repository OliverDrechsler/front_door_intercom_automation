# Time based One Time Password  helper command line interface

This script `tools/totp_helper_cli.py` is a cli helper tool to get  
a one time password based on your provided config `config.yaml` file.  
  
It prints out the TOTP code or it can verify a given input totp code.  

Script help:
```
tools/totp_helper_cli.py --help
Usage: totp_helper_cli.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  get-otp     Generates an OTP based on the configuration.
  verify-otp  Verifies an OTP based on the configuration.
```

## Get a TOTP code

Example command
```
tools/totp_helper_cli.py get-otp
```

Output
```
123456
```


## Verify a TOTP code

Example command
```
tools/totp_helper_cli.py verify-otp 123456
```

Output
```
OTP is valid
```
or 
Output
```
OTP is invalid
```
