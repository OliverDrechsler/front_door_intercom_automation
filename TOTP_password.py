#!/usr/bin/env python3
import base64
import click

@click.command()
@click.option('--encrypt', 
    prompt=True, 
    hide_input=True,
    confirmation_prompt=True, 
    help='encrypt a given password with base32 from input')
def encrypt(encrypt):
    print(base64.b32encode(bytes(encrypt, 'ascii')))

# @click.command()
# @click.option('--decrypt', prompt=True, hide_input=True,
#               confirmation_prompt=True, 
#               help='decrypt a given password with base32 from input')
# def encrypt(decrypt):
#     click.echo(base64.b32decode(bytes(decrypt, 'ascii')))
