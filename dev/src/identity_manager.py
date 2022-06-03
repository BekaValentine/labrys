import os
import re

import src.passwords as passwords


class IdentityManager(object):

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.blade_url_file = os.path.join(self.data_dir, 'blade_url.txt')
        self.identity_dir = os.path.join(self.data_dir, 'identity')
        self.secrets_dir = os.path.join(self.data_dir, 'secrets')
        self.display_name_file = os.path.join(
            self.identity_dir, 'display_name.txt')
        self.bio_file = os.path.join(self.identity_dir, 'bio.txt')
        self.private_signing_key_file = os.path.join(
            self.secrets_dir, 'private_signing_key.txt')
        self.public_signing_key_file = os.path.join(
            self.identity_dir, 'public_signing_key.txt')
        self.password_hash_file = os.path.join(
            self.secrets_dir, 'password_hash.txt')
        self.session_secret_key_file = os.path.join(
            self.secrets_dir, 'session_secret_key.txt')

    def blade_url(self):
        with open(self.blade_url_file, 'r') as f:
            return f.read().strip()

    def avatar_file_name(self):
        avatar_candidates =\
            [f for f in os.listdir(self.identity_dir)
             if re.search('^avatar\.(png|PNG|jpg|JPG|jpeg|JPEG|gif|GIF|svg|SVG)$', f)]

        if avatar_candidates:
            avatar_file_name = avatar_candidates[0]
        else:
            avatar_file_name = None

        return avatar_file_name

    def display_name(self):
        with open(self.display_name_file, 'r') as f:
            return f.read()

    def bio(self):
        with open(self.bio_file, 'r') as f:
            return f.read()

    def unsafe_private_signing_key(self):
        with open(self.private_signing_key_file, 'r') as f:
            return f.read()

    def public_signing_key(self):
        with open(self.public_signing_key_file, 'r') as f:
            return f.read()

    def unsafe_session_secret_key(self):
        with open(self.session_secret_key_file, 'r') as f:
            return f.read().strip()

    def sign(self, message):
        with open(self.private_signing_key_file, 'r') as f:
            signing_key = nacl.signing.SigningKey(f.read().encode(
                encoding='ascii'), encoder=nacl.encoding.Base64Encoder)
            signed = signing_key.sign(message.encode(encoding='ascii'))
            return base64.b64encode(signed.signature)

    def check_password(self, submitted_password):
        with open(self.password_hash_file, 'r') as f:
            return passwords.check_password(submitted_password, f.read())
