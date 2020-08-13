import argparse
import base64
import bcrypt
import nacl.signing
import os
import src.passwords as passwords
import sys
import time


def noninteractive(data_dir, canonical_url, display_name, bio, password):
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'secrets'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'identity'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'permissions'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'known_blades_avatars'), exist_ok=True)

    with open(os.path.join(data_dir, 'blade_url.txt'), 'w') as f:
        f.write(canonical_url)

    with open(os.path.join(data_dir, 'identity', 'display_name.txt'), 'w') as f:
        f.write(display_name)

    with open(os.path.join(data_dir, 'identity', 'bio.txt'), 'w') as f:
        f.write(bio)

    with open(os.path.join(data_dir, 'secrets', 'password_hash.txt'), 'w') as f:
        f.write(passwords.get_hashed_password(password).decode('ascii'))

    # generate signing keys
    private_signing_key = nacl.signing.SigningKey.generate()
    public_signing_key = private_signing_key.verify_key.encode(
        encoder=nacl.encoding.Base64Encoder).decode('ascii')

    # save the private signing key
    with open(os.path.join(data_dir, 'secrets', 'private_signing_key.txt'), 'w') as f:
        f.write(private_signing_key.encode(
            encoder=nacl.encoding.Base64Encoder).decode('ascii'))

    # save the public signing key
    with open(os.path.join(data_dir, 'identity', 'public_signing_key.txt'), 'w') as f:
        f.write(public_signing_key)

    # session key
    with open('/dev/urandom', 'rb') as f:
        session_key = f.read(32)

    with open(os.path.join(data_dir, 'secrets', 'session_secret_key.txt'), 'w') as f:
        f.write(base64.b64encode(session_key).decode('ascii'))


def interactive():

    SLEEP_TIME = 0.75

    time.sleep(SLEEP_TIME)

    print()
    print('******************************')
    print('*                            *')
    print('*   Labrys Setup Assistant   *')
    print('*                            *')
    print('******************************')

    # data dir
    time.sleep(SLEEP_TIME)
    print()
    print()
    data_dir = input(
        'What directory should be used to store your labrys data?\n\n> ')

    # blade_url
    time.sleep(SLEEP_TIME)
    print()
    print()
    canonical_url = input(
        'What is the canonical url to use for this blade?\n\n> ')

    # display name
    time.sleep(SLEEP_TIME)
    print()
    print()
    display_name = input(
        'What display name should this blade use for you?\n\n> ')
    if '' == display_name:
        display_name = 'AnonymousUser'

    # bio
    time.sleep(SLEEP_TIME)
    print()
    print()
    bio = input('What bio text should this blade use for you?\n\n> ')
    if '' == bio:
        bio = 'No bio.'

    # password_hash
    time.sleep(SLEEP_TIME)
    print()
    print()
    password = input(
        'What password would you like to use to log in to this blade?\n\n> ')

    # signing keys
    time.sleep(SLEEP_TIME)
    print()
    print()
    print('Generating signing keys...')

    # session secret key
    time.sleep(SLEEP_TIME)
    print()
    print()
    print('Generating session keys...')

    noninteractive(canonical_url, display_name, bio, password)

    time.sleep(SLEEP_TIME)
    print()
    print()
    print('Setup complete.')
    print()
    print()

    time.sleep(SLEEP_TIME)


if len(sys.argv) == 1:
    interactive()
else:
    parser = argparse.ArgumentParser(
        description='A setup utility for labrys blades. Run this program without arguments for interactive mode.')
    parser.add_argument(
        '<data-dir>', help='The directory to store your labrys data in.')
    parser.add_argument('<canonical-url>',
                        help='The canonical URL used to access this blade.')
    parser.add_argument(
        '<display-name>', help='The name to show other people who view your blade info.')
    parser.add_argument(
        '<bio>', help='A short description of who you are to help other people get to know you.')
    parser.add_argument(
        '<password>', help='The password you will use to log into this blade.')
    args = vars(parser.parse_args())
    noninteractive(args['<data-dir>'], args['<canonical-url>'],
                   args['<display-name>'], args['<bio>'], args['<password>'])
