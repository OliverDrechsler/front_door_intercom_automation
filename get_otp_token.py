#!/usr/bin/env python3

import onetimepass as otp
import os
import click
import yaml
import hashlib
# import time
# import six
# import hmac
# import struct
# import base64


def read_config(config_file):
    """
    Reads config.yaml file into variables.

    params: none
    return: config: variable
    """
    with open(file=config_file, mode='r') as file:
        return yaml.load(file, Loader=yaml.SafeLoader)

def define_config_file():
    """
    Checks and defines Config yaml path.

    Defines a new class path atrribute.
    """
    if os.path.isfile(os.path.dirname(__file__) + '/config.yaml'):
        return (os.path.dirname(__file__) + '/config.yaml')
    else:
        return (os.path.dirname(
            __file__) + '/config_template.yaml')


def verify_otp(to_verify, my_secret, length, interval):
    return otp.valid_totp(
        token=to_verify, secret=my_secret, token_length=length, interval_length=interval,
        digest_method=hashlib.sha1)


def create_otp_tocken(my_secret, length, interval):
    my_token = otp.get_totp(my_secret, token_length=length, interval_length=interval, as_string=True)
    # print(my_token)
    return my_token


@click.command()
@click.argument('params')
def main(params):
    if params == "create":
        conf_file = define_config_file()
        config = read_config(conf_file)
        otp = create_otp_tocken(config["otp"]["password"],config["otp"]["length"],config["otp"]["interval"])
        print(otp.decode("ASCII"))

    elif params == "verify":
        conf_file = define_config_file()
        config = read_config(conf_file)
        verify_otp("token", config["otp"]["password"],config["otp"]["length"],config["otp"]["interval"])


if __name__ == '__main__':
    main()
