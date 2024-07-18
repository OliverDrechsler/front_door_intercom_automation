#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import click
import yaml
import pyotp

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

    Defines a new class path attribute.
    """
    # Get the current directory of the script
    current_dir = os.path.dirname(__file__)

    # Get the parent directory
    parent_dir = os.path.dirname(current_dir)

    # Construct the path to config.yaml in the parent directory
    config_path = os.path.join(parent_dir, 'config.yaml')

    if os.path.isfile(current_dir + "/config.yaml"):
        return current_dir + "/config.yaml"
    elif os.path.isfile(parent_dir + "/config.yaml"):
        return parent_dir + "/config.yaml"
    if os.path.isfile(current_dir + "/config_template.yaml"):
        return current_dir + "/config_template.yaml"
    elif os.path.isfile(parent_dir + "/config_template.yaml"):
        return parent_dir + "/config_templat.yaml"
    else:
        raise (NameError("No config file found!"))


@click.group()
def cli():
    pass

@click.command()
def get_otp():
    """
    Generates an OTP based on the configuration.
    """
    config_file = define_config_file()
    config_data = read_config(config_file)
    otp = pyotp.TOTP(
        s=config_data["otp"]["password"],
        digits=config_data["otp"]["length"],
        interval=config_data["otp"]["interval"],
        digest=config_data["otp"]["hash_type"]
    )
    click.echo(otp.now())

@click.command()
@click.argument('otp')
def verify_otp(otp):
    """
    Verifies an OTP based on the configuration.
    """
    config_file = define_config_file()
    config_data = read_config(config_file)
    totp = pyotp.TOTP(
        s=config_data["otp"]["password"],
        digits=config_data["otp"]["length"],
        interval=config_data["otp"]["interval"],
        digest=config_data["otp"]["hash_type"]
    )
    if totp.verify(otp):
        click.echo("OTP is valid")
    else:
        click.echo("OTP is invalid")

cli.add_command(get_otp)
cli.add_command(verify_otp)

if __name__ == '__main__':
    cli()
