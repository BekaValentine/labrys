import base64
import flask
import json
import os
import requests
from tinydb import TinyDB, Query


def encode_public_key(s):
    return str(base64.urlsafe_b64encode(bytes(s, encoding='ascii')), encoding='ascii')


def decode_public_key(s):
    return str(base64.urlsafe_b64decode(bytes(s, encoding='ascii')), encoding='ascii')


def load_and_cache_blade_identity(known_blades_avatars_dir, known_blades_db, blade_url):

    blade_identity = {'url': blade_url}

    try:
        resp = requests.get('http://' + blade_url +
                            '/api/identity/public_signing_key')
    except requests.exceptions.ConnectionError:
        return None

    if resp.status_code != 200:
        return None

    blade_identity['public_signing_key'] = resp.text

    previous = known_blades_db.search(
        Query().public_signing_key == blade_identity['public_signing_key'])
    if previous:
        return previous[0]

    resp = requests.get('http://' + blade_url + '/api/identity/display_name')
    if resp.status_code == 200:
        blade_identity['display_name'] = resp.text

    resp = requests.get('http://' + blade_url + '/api/identity/bio')
    if resp.status_code == 200:
        blade_identity['bio'] = resp.text

    resp = requests.get('http://' + blade_url + '/api/identity/avatar')
    if resp.status_code == 200:
        ct = resp.headers['Content-Type']
        if ct == 'image/jpeg':
            ext = 'jpg'
        elif ct == 'image/gif':
            ext = 'gif'
        elif 'image/svg+xml' in ct:
            ext = 'svg'
        else:
            ext = None

        if ext:
            blade_identity['avatar_filename'] = encode_public_key(
                blade_identity['public_signing_key']) + '.' + ext
            with open(os.path.join(known_blades_avatars_dir, blade_identity['avatar_filename']), 'wb') as fd:
                for chunk in resp.iter_content(chunk_size=128):
                    fd.write(chunk)

    known_blades_db.insert(blade_identity)

    return blade_identity


def cached_blade_identity(known_blades_db, public_signing_key):

    previous = known_blades_db.search(
        Query().public_signing_key == public_signing_key)

    if previous:
        return previous[0]
    else:
        return None
