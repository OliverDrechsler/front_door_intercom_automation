#!/usr/bin/env python3
import base64
import click


@click.command()
@click.option(
    "--encrypt",
    prompt=False,
    hide_input=True,
    confirmation_prompt=True,
    help="encrypt a given password with base32 from input",
)
@click.option(
    "--decrypt",
    prompt=False,
    help="decrypt a given password with from base32 input code",
)
def program_start(encrypt, decrypt):
    if encrypt is not None:
        encryption(encrypt)
    if decrypt is not None:
        decryption(decrypt)


def encryption(encrypt):
    print(base64.b32encode(bytes(encrypt, "ascii")).decode("ascii"))

def decryption(decrypt):
    print(base64.b32decode(bytes(decrypt, "ascii")).decode("ascii"))


if __name__ == '__main__':
    program_start()
