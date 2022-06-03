import os

from tinydb import TinyDB, Query


class InboxManager(object):

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.inbox_db = TinyDB(os.path.join(self.data_dir, 'inbox.json'))

    def all_messages(self):
        self.inbox_db.all()

    def message_with_id(self, msg_id):
        self.inbox_db.search(Query().origin_id == msg_id)

    def add_message(self, msg):
        self.inbox_db.insert(msg)

    def remove_message_with_id(self, msg_id):
        self.inbox_db.remove(Query().id == msg_id)
