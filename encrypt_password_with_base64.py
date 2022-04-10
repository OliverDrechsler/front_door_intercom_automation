#!/usr/bin/env python3
import base64
import click


@click.command()
@click.option(
    "--encrypt",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="encrypt a given password with base32 from input",
)
def encrypt(encrypt):
    print(base64.b32encode(bytes(encrypt, "ascii")))
