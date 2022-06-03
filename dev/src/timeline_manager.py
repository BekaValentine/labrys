import os


from tinydb import TinyDB, Query


class TimelineManager(object):

    def __init__(self, data_dir, identity_manager, subscriptions_manager, known_blades_manager):
        self.data_dir = data_dir
        self.identity_manager = identity_manager
        self.subscriptions_manager = subscriptions_manager
        self.known_blades_manager = known_blades_manager
        self.timeline_cache_db = TinyDB(
            os.path.join(self.data_dir, 'timeline_cache.json'))
        self.max_list_items_to_display = 3

    def update_subscriptions(self):

        local_messages = self.subscriptions_manager.update_subscriptions()

        for msg in local_messages:
            self.timeline_cache_db.insert(msg)

        return local_messages

    def timeline(self, last_seen=None):

        self.update_subscriptions()

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
            message['blade_identity'] = self.known_blades_manager.cached_blade_identity(
                message['public_signing_key'])

        return messages, next_last_seen
