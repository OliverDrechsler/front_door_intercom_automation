from __future__ import annotations
import onetimepass as otp
import hashlib
from passlib.totp import TOTP


def verify_otp(to_verify: int, my_secret: str, length: int, interval: int, hash_type: str) -> bool:
    """
    Verify given onetimepassword  matches

    :param to_verify: given time-based one time password 
    :type to_verify: int
    :param my_secret: my local stored secret
    :type my_secret: str
    :param length: time-based one time password length 
    :type length: int
    :param interval: totp interval in sec
    :type interval: int
    :return: result of totp matches
    :rtype: bool
    """
    return otp.valid_totp(
        token=to_verify, secret=my_secret, token_length=length, interval_length=interval,
        digest_method=hash_type)


def verify_totp_code(to_verify: str, my_secret: str, length: int, interval: int, hash_type: str) -> bool:
    """
    Verify given time-based one time password with passlib

    :param to_verify: given time-based one time password 
    :type to_verify: str
    :param my_secret: my local stored secret
    :type my_secret: str
    :param length: time-based one time password length 
        Caution Due to a limitation of the HOTP algorithm, 
        the 10th digit can only take on values 0 .. 2, 
        and thus offers very little extra security.
        Please use maxim lenght of 9 instead 10 
        limitation see here https://passlib.readthedocs.io/en/stable/lib/passlib.totp.html#totptoken        
    :type length: int
    :param interval: totp interval in sec
    :type interval: int
    :param hash_type: hash code type to be used sha1, sha256 or sha512
    :type hash_type: str
    :return: result of totp matches
    :rtype: bool
    """
    totp = TOTP(key=my_secret, digits=length, period=interval, alg=hash_type)
    if totp.generate().token == str(to_verify):
        return True
    else:
        return False
