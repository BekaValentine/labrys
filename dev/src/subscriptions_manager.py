import datetime
import json
import os
import re
import random
import requests

from tinydb import TinyDB, Query

import src.public_keys as public_keys


class SubscriptionsManager(object):

    def __init__(self, data_dir, identity_manager, encryption_manager, known_blades_manager):
        self.data_dir = data_dir
        self.identity_manager = identity_manager
        self.encryption_manager = encryption_manager
        self.known_blades_manager = known_blades_manager
        self.subscriptions_db = TinyDB(
            os.path.join(self.data_dir, 'subscriptions.json'))
        self.subscribers_db = TinyDB(
            os.path.join(self.data_dir, 'subscribers.json'))

        self.max_list_items_to_display = 3

    def subscriptions(self, last_seen=None):
        if last_seen is not None:
            found = self.subscriptions_db.search(Query().id == last_seen)
            found.sort(reverse=True, key=lambda s: s['subscribe_datetime'])
            if found:
                subs = self.subscriptions_db.search((Query().subscribe_datetime <= found[0]['subscribe_datetime']) &
                                                    (Query().id != last_seen))
            else:
                subs = self.subscriptions_db.all()
        else:
            subs = self.subscriptions_db.all()

        for sub in subs:
            blade_identity = self.known_blades_manager.cached_blade_identity(
                sub['public_signing_key'])

            if 'avatar_filename' in blade_identity:
                sub['avatar_filename'] = blade_identity['avatar_filename']
            sub['display_name'] = blade_identity['display_name']
            sub['bio'] = blade_identity['bio']

        subs.sort(reverse=True, key=lambda s: s['subscribe_datetime'])

        if len(subs) <= self.max_list_items_to_display:
            next_last_seen = None
        else:
            next_last_seen = subs[self.max_list_items_to_display - 1]['id']

        subs = subs[:self.max_list_items_to_display]

        return subs, next_last_seen

    def add_subscription(self, blade_url):
        match = re.match('^(https?://)?([^/]+)(/.*)?$', blade_url)

        if match is None:
            return

        blade_url = match.group(2)

        blade_identity = self.known_blades_manager.load_and_cache_blade_identity(
            blade_url)

        if blade_identity and not self.subscriptions_db.search(Query().public_signing_key == blade_identity['public_signing_key']):

            requests.post('http://' + blade_identity['url'] + '/api/inbox',
                          data=json.dumps({'url': self.identity_manager.blade_url(),
                                           'public_signing_key': self.identity_manager.public_signing_key(),
                                           'type': 'new_subscriber'}))

            self.subscriptions_db.insert({
                'id': public_keys.encode_public_key(blade_identity['public_signing_key']),
                'subscribe_datetime': datetime.datetime.utcnow().isoformat(),
                'url': blade_url,
                'public_signing_key': blade_identity['public_signing_key'],
                'last_seen': None
            })

    def remove_subscription(self, sub_id):
        public_signing_key = public_keys.decode_public_key(sub_id)

        self.subscriptions_db.remove(
            Query().public_signing_key == public_signing_key)

    def update_subscriptions(self):
        local_messages = []

        for sub in self.subscriptions_db.all():
            resp_data = self.encryption_manager.encrypted_client_request(
                sub['public_signing_key'],
                requests.get,
                'http://' + sub['url'] + '/api/feed',
                {'last_seen': sub['last_seen']})

            if resp_data is not None:
                messages = json.loads(resp_data)
                most_recent_datetime = None
                most_recent_id = None
                for msg in messages:
                    if most_recent_datetime is None or (most_recent_datetime is not None and most_recent_datetime < msg['publish_datetime']):
                        most_recent_id = msg['id']

                    local_messages += [{
                        'id': ''.join([random.choice('0123456789abcdef')
                                       for i in range(30)]),
                        'retrieve_datetime': datetime.datetime.utcnow().isoformat(),
                        'url': sub['url'],
                        'public_signing_key': sub['public_signing_key'],
                        'origin_id': msg['id'],
                        'publish_datetime': msg['publish_datetime'],
                        'type': msg['type'],
                        'content': msg['content']
                    }]

                if most_recent_id:
                    self.subscriptions_db.update({'last_seen': most_recent_id}, Query(
                    ).public_signing_key == sub['public_signing_key'])

        return local_messages

    def all_subscribers(self):
        return self.subscribers_db.all()

    def add_subscriber(self, sub_public_signing_key, sub_url):
        print('ADDING NEW SUBSCRIBER')
        match = re.match('^(https?://)?([^/]+)(/.*)?$', sub_url)

        if match is None:
            return

        sub_url = match.group(2)

        sub_identity = self.known_blades_manager.load_and_cache_blade_identity(
            sub_url)

        self.subscribers_db.insert({
            'id': public_keys.encode_public_key(sub_identity['public_signing_key']),
            'subscribe_datetime': datetime.datetime.utcnow().isoformat(),
            'public_signing_key': sub_identity['public_signing_key'],
        })
