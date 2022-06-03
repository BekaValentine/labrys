import datetime
import json
import os
import random
import requests

from tinydb import TinyDB, Query


class PrivateMessageManager(object):

    def __init__(self, data_dir, identity_manager, encryption_manager, known_blades_manager, subscriptions_manager):
        self.data_dir = data_dir
        self.identity_manager = identity_manager
        self.encryption_manager = encryption_manager
        self.known_blades_manager = known_blades_manager
        self.subscriptions_manager = subscriptions_manager
        self.inbox_db = TinyDB(os.path.join(self.data_dir, 'inbox.json'))
        self.outbox_db = TinyDB(os.path.join(self.data_dir, 'outbox.json'))
        self.private_messages_db = TinyDB(
            os.path.join(self.data_dir, 'private_messages.json'))

    def all_inbox_messages(self):
        self.inbox_db.all()

    def inbox_message_with_id(self, msg_id):
        self.inbox_db.search(Query().origin_id == msg_id)

    def add_inbox_message(self, msg):
        self.inbox_db.insert(msg)

    def remove_inbox_message_with_id(self, msg_id):
        self.inbox_db.remove(Query().id == msg_id)

    def handle_new_inbox_message(self, inbox_msg):

        if inbox_msg['type'] == 'new_subscriber':
            print('RECEIVED NEW SUBSCRIBER')
            self.subscriptions_manager.add_subscriber(
                inbox_msg['public_signing_key'], inbox_msg['url'])

        elif inbox_msg['type'] == 'new_private_messages':
            print('RECEIVED NEW PMs')
            resp_data = self.encryption_manager.encrypted_client_request(
                inbox_msg['public_signing_key'],
                requests.get,
                'http://' + inbox_msg['url'] + '/api/outbox')

            if resp_data:
                received_messages = json.loads(resp_data)

                for outbox_msg in received_messages:
                    if not self.inbox_message_with_id(outbox_msg['id']):
                        self.add_inbox_message({
                            'id': ''.join([random.choice('0123456789abcdef')
                                           for i in range(30)]),
                            'origin_id': outbox_msg['id'],
                            'sender': inbox_msg['public_signing_key'],
                            'sent_datetime': outbox_msg['sent_datetime'],
                            'type': outbox_msg['type'],
                            'content': outbox_msg['content']
                        })

        return True

    def all_outbox_messages(self):
        return self.outbox_db.all()

    def add_outbox_message(self, msg):
        message_id = ''.join([random.choice('0123456789abcdef')
                              for i in range(30)])

        msg['id'] = message_id
        msg['sent_datetime'] = datetime.datetime.utcnow().isoformat()

        blade_id = self.known_blades_manager.cached_blade_identity(
            msg['public_signing_key'])
        if blade_id is None:
            return False

        self.outbox_db.insert(msg)

        requests.post('http://' + blade_id['url'] + '/api/inbox',
                      data=json.dumps({
                          'type': 'new_private_messages',
                          'url': self.identity_manager.blade_url(),
                          'public_signing_key': self.identity_manager.public_signing_key()
                      }))

        return True

    def remove_outbox_message_with_id(self, msg_id):
        self.outbox_db.remove(Query().id == msg_id)

    def add_private_message_own_turn(self, msg):
        ...

    def add_private_message_other_turn(self, msg):
        ...
