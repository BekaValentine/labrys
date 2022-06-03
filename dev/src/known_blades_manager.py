import os
import requests

from tinydb import TinyDB, Query

import src.public_keys as public_keys


class KnownBladesManager(object):

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.known_blades_db = TinyDB(
            os.path.join(self.data_dir, 'known_blades.json'))
        self.known_blades_avatars_dir = os.path.join(
            self.data_dir, 'known_blades_avatars')

    def all_known_blades(self):
        return self.known_blades_db.all()

    def load_and_cache_blade_identity(self, blade_url):
        blade_identity = {'url': blade_url}

        try:
            resp = requests.get('http://' + blade_url +
                                '/api/identity/public_signing_key')
        except requests.exceptions.ConnectionError:
            return None

        if resp.status_code != 200:
            return None

        blade_identity['public_signing_key'] = resp.text

        previous = self.known_blades_db.search(
            Query().public_signing_key == blade_identity['public_signing_key'])
        if previous:
            return previous[0]

        resp = requests.get('http://' + blade_url +
                            '/api/identity/display_name')
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
                blade_identity['avatar_filename'] = public_keys.encode_public_key(
                    blade_identity['public_signing_key']) + '.' + ext
                with open(os.path.join(self.known_blades_avatars_dir, blade_identity['avatar_filename']), 'wb') as fd:
                    for chunk in resp.iter_content(chunk_size=128):
                        fd.write(chunk)

        self.known_blades_db.insert(blade_identity)

        return blade_identity

    def cached_blade_identity(self, public_signing_key):
        previous = self.known_blades_db.search(
            Query().public_signing_key == public_signing_key)

        if previous:
            return previous[0]
        else:
            return None

    def blade(self, blade_url):
        blade_id = self.blade_identity(blade_url)

        response = requests.get('http://' + blade_url + '/api/feed')
        if response.status_code == 200:
            messages = response.json().get('messages')
        else:
            messages = []

        messages.sort(reverse=True, key=lambda m: m['publish_datetime'])

        found = self.subscriptions_db.search(Query().url == blade_url)
        if len(found) != 0:
            subscription_id = found[0]['id']
        else:
            subscription_id = None

        return blade_id, messages, subscription_id
