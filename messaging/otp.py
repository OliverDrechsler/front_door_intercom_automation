from __future__ import annotations
import onetimepass as otp
import hashlib

def verify_otp(to_verify, my_secret, length, interval):
    return otp.valid_totp(
        token=to_verify, secret=my_secret, token_length=length, interval_length=interval,
        digest_method=hashlib.sha1)
