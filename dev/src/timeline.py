import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet
import datetime
import json
import nacl
import random
import requests
from tinydb import Query

import src.dh_sessions as dh_sessions


def update_subscriptions(private_signing_key_file, public_signing_key_file, subscriptions_db, timeline_cache_db):

    local_messages = []

    for sub in subscriptions_db.all():
        resp_data = dh_sessions.encrypted_client_request(
            private_signing_key_file,
            public_signing_key_file,
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
                subscriptions_db.update({'last_seen': most_recent_id},
                                        Query().public_signing_key == sub['public_signing_key'])

    for msg in local_messages:
        timeline_cache_db.insert(msg)

    return local_messages
