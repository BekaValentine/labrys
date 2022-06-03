import os

from tinydb import TinyDB, Query


class OutboxManager(object):

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.outbox_db = TinyDB(os.path.join(self.data_dir, 'outbox.json'))

    def all_messages(self):
        self.outbox_db.all()

    def add_message(self, msg):
        self.outbox_db.insert(msg)

    def remove_message_with_id(self, msg_id):
        self.outbox_db.remove(Query().id == msg_id)
