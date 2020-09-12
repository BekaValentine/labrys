import datetime
import os
import random
import requests
import re
from tinydb import Query

import src.permissions as permissions
import src.blade_identity as identity
import src.timeline as timeline


class DataStore(object):
    def __init__(self,
                 identity_dir,
                 display_name_file,
                 bio_file,
                 private_signing_key_file,
                 public_signing_key_file,
                 feed_db,
                 feed_attachments_dir,
                 timeline_cache_db,
                 permissions_groups_db,
                 permissions_blades_db,
                 subscriptions_db,
                 known_blades_db,
                 known_blades_avatars_dir):
        self.identity_dir = identity_dir
        self.display_name_file = display_name_file
        self.bio_file = bio_file
        self.private_signing_key_file = private_signing_key_file
        self.public_signing_key_file = public_signing_key_file
        self.feed_db = feed_db
        self.feed_attachments_dir = feed_attachments_dir
        self.timeline_cache_db = timeline_cache_db
        self.permissions_groups_db = permissions_groups_db
        self.permissions_blades_db = permissions_blades_db
        self.known_blades_db = known_blades_db
        self.known_blades_avatars_dir = known_blades_avatars_dir
        self.subscriptions_db = subscriptions_db
        self.max_list_items_to_display = 3

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

    def public_signing_key(self):
        with open(self.public_signing_key_file, 'r') as f:
            return f.read()

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
        messages = [msg for msg in messages if permissions.permitted_to_view_message(
            self.permissions_groups_db, self.permissions_blades_db, None, msg['permissions_categories'])]

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

    def timeline(self, last_seen=None):

        timeline.update_subscriptions(
            self.private_signing_key_file, self.public_signing_key_file, self.subscriptions_db, self.timeline_cache_db)

        if last_seen is None:
            messages = self.timeline_cache_db.search(Query().type == 'post')
        else:
            found = self.timeline_cache_db.search(Query().id == last_seen)
            found.sort(reverse=True, key=lambda m: m['publish_datetime'])
            print('FOUND: ', found)
            if found:
                messages = self.timeline_cache_db.search((Query().type == 'post') &
                                                         (Query().publish_datetime <= found[0]['publish_datetime']) &
                                                         (Query().id != last_seen))
            else:
                messages = self.timeline_cache_db.search(
                    Query().type == 'post')

        messages.sort(reverse=True, key=lambda m: m['publish_datetime'])

        if len(messages) <= self.max_list_items_to_display:
            next_last_seen = None
        else:
            next_last_seen = messages[self.max_list_items_to_display - 1]['id']

        messages = messages[:self.max_list_items_to_display]

        for message in messages:
            message['blade_identity'] = identity.cached_blade_identity(
                self.known_blades_db, message['public_signing_key'])

        return messages, next_last_seen

    def subscriptions(self, last_seen=None):
        if last_seen is not None:
            found = self.subscriptions_db.search(Query().id == last_seen)
            found.sort(reverse=True, key=lambda s: s['subscribe_datetime'])
            print('FOUND: ', found)
            if found:
                subs = self.subscriptions_db.search((Query().subscribe_datetime <= found[0]['subscribe_datetime']) &
                                                    (Query().id != last_seen))
            else:
                subs = self.subscriptions_db.all()
        else:
            subs = self.subscriptions_db.all()

        for sub in subs:
            blade_identity = identity.cached_blade_identity(
                self.known_blades_db, sub['public_signing_key'])

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

        blade_identity = identity.load_and_cache_blade_identity(
            self.known_blades_avatars_dir, self.known_blades_db, blade_url)

        if not self.subscriptions_db.search(Query().public_signing_key == blade_identity['public_signing_key']):

            self.subscriptions_db.insert({
                'id': identity.encode_public_key(blade_identity['public_signing_key']),
                'subscribe_datetime': datetime.datetime.utcnow().isoformat(),
                'url': blade_url,
                'public_signing_key': blade_identity['public_signing_key'],
                'last_seen': None
            })

    def remove_subscription(self, sub_id):
        public_signing_key = identity.decode_public_key(sub_id)

        self.subscriptions_db.remove(
            Query().public_signing_key == public_signing_key)

    def blade(self, blade_url):
        blade_identity = identity.load_and_cache_blade_identity(
            self.known_blades_avatars_dir, self.known_blades_db, blade_url)

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

        return blade_identity, messages, subscription_id
