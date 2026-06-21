# TOTP Setup

FDIA uses a Base32-encoded secret to generate time-based one-time passwords (TOTP). This secret must be stored in the `otp.password` field in `config.yaml`.

Use the helper script `tools/encrypt_decrypt_password_with_base32.py` to encode your secret before storing it.

Example `otp` section:

```yaml
otp:
  password: "KRSXG5CQIASCIVZQOJCA===="
  length: 6
  interval: 30
  hash_type: sha256
```

Field descriptions:

- `password`: your Base32-encoded secret
- `length`: the number of digits in the generated code; values up to 10 are supported
- `interval`: the validity period of each TOTP code in seconds
- `hash_type`: the hash algorithm used for TOTP generation

Recommendations:

- Use at least 9 digits for stronger codes.
- Use `sha512` if you want a stronger hash option.
- Avoid `sha1` unless you need compatibility with older setups.

Important:

- Keep these settings consistent between FDIA and your mobile OTP app.
- FDIA will only accept codes that were generated with the same secret, hash, length, and interval.

The generated code is typically sent to FDIA through the Telegram chat to open the door.

## Script Options

The helper script supports:

- `--encrypt <password>`
- `--decrypt <base32-secret>`

### Example: Encrypt a Password

```bash
tools/encrypt_decrypt_password_with_base32.py --encrypt mySuperSecurePassW0Rd1
```

Example output:

```text
NV4VG5LQMVZFGZLDOVZGKUDBONZVOMCSMQYQ====
```

### Example: Decrypt a Secret

```bash
tools/encrypt_decrypt_password_with_base32.py --decrypt NV4VG5LQMVZFGZLDOVZGKUDBONZVOMCSMQYQ====
```

Example output:

```text
mySuperSecurePassW0Rd1
```
