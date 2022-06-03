import datetime
import os
import random
import re
from tinydb import TinyDB, Query


class FeedManager(object):

    def __init__(self, data_dir, identity_manager, permissions_manager):
        self.data_dir = data_dir
        self.feed_db = TinyDB(os.path.join(self.data_dir, 'feed.json'))
        self.feed_attachments_dir = os.path.join(
            self.data_dir, 'feed_attachments')

        self.identity_manager = identity_manager
        self.permissions_manager = permissions_manager

        self.max_list_items_to_display = 3

    def message_with_id(self, id):
        messages = self.feed_db.search(Query().id == id)
        if len(messages) == 0:
            return None
        return messages[0]

    def message_with_id_public_authorization(self, id):
        msg = self.message_with_id(id)
        if msg is None:
            return None

        if self.permissions_manager.permitted_to_view_message(None, msg['permissions_categories']):
            return msg
        else:
            return None

    def all_messages(self):
        return self.feed_db.all()

    def messages_after(self, message):
        messages = self.feed_db.search((Query().publish_datetime >= message['publish_datetime']) &
                                       (Query().id != message['id']))
        return messages

    def remove_message(self, id):
        self.feed_db.remove(Query().id == id)

    def feed(self, last_seen=None):
        if last_seen is None:
            messages = self.feed_db.search(Query().type == 'post')
        else:
            found = self.feed_db.search(Query().id == last_seen)
            found.sort(reverse=True, key=lambda m: m['publish_datetime'])
            print('FOUND: ', found)
            if found:
                messages = self.feed_db.search((Query().type == 'post') &
                                               (Query().publish_datetime <= found[0]['publish_datetime']) &
                                               (Query().id != last_seen))
            else:
                messages = self.feed_db.search(Query().type == 'post')

        messages.sort(reverse=True, key=lambda m: m['publish_datetime'])

        return messages

    def feed_owner_authorization(self, last_seen=None):
        messages = self.feed(last_seen)

        if len(messages) <= self.max_list_items_to_display:
            next_last_seen = None
        else:
            next_last_seen = messages[self.max_list_items_to_display - 1]['id']

        messages = messages[:self.max_list_items_to_display]

        return messages, next_last_seen

    def feed_public_authorization(self, last_seen=None):
        messages = self.feed(last_seen)
        messages = [msg for msg in messages if self.permissions_manager.permitted_to_view_message(
            None, msg['permissions_categories'])]

        if len(messages) <= self.max_list_items_to_display:
            next_last_seen = None
        else:
            next_last_seen = messages[self.max_list_items_to_display - 1]['id']

        messages = messages[:self.max_list_items_to_display]

        return messages, next_last_seen

    def add_feed_message(self, message):
        message['id'] = ''.join([random.choice('0123456789abcdef')
                                 for i in range(30)])
        message['publish_datetime'] = datetime.datetime.utcnow().isoformat()

        attached_files = message['content']['attachments']
        message['content']['attachments'] = []

        for file in attached_files:
            print(file.content_type)

            if re.match('^image/', file.content_type):
                content_type = 'image'
            elif re.match('^video/', file.content_type):
                content_type = 'video'
            elif re.match('^audio/', file.content_type):
                content_type = 'audio'
            else:
                content_type = 'other'

            print(content_type)

            parts = file.filename.split('.')
            if len(parts) >= 2:
                ext = parts[-1]
                file_id = ''.join([random.choice('0123456789abcdef')
                                   for i in range(30)])
                file_name = message['id'] + \
                    '_attachment_' + file_id + '.' + ext
                file.save(os.path.join(self.feed_attachments_dir, file_name))
                message['content']['attachments'].append({
                    'file_name': file_name,
                    'content_type': content_type
                })

        self.feed_db.insert(message)

        return message['id']
