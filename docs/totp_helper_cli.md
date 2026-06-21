# TOTP Helper Command-Line Interface

The script `tools/totp_helper_cli.py` is a small CLI utility that reads your `config.yaml` file and either generates or verifies a TOTP code.

## Help Output

```bash
tools/totp_helper_cli.py --help
```

Example:

```text
Usage: totp_helper_cli.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  get-otp     Generate an OTP based on the configuration.
  verify-otp  Verify an OTP based on the configuration.
```

## Generate a TOTP Code

```bash
tools/totp_helper_cli.py get-otp
```

Example output:

```text
123456
```

## Verify a TOTP Code

```bash
tools/totp_helper_cli.py verify-otp 123456
```

Example valid output:

```text
OTP is valid
```

Example invalid output:

```text
OTP is invalid
```
