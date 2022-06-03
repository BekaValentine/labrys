import os

from tinydb import TinyDB, Query


class PermissionsManager(object):

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.permissions_dir = os.path.join(self.data_dir, 'permissions')
        self.permissions_groups_db = TinyDB(
            os.path.join(self.permissions_dir, 'groups.json'))
        self.permissions_blades_db = TinyDB(
            os.path.join(self.permissions_dir, 'blades.json'))

    def all_blades(self):
        return self.permissions_blades_db.all()

    def permissions_for_blade(self, public_signing_key):
        return self.permissions_blades_db.search(
            Query().public_signing_key == public_signing_key)

    def set_permissions_for_blade(self, public_signing_key, perms):
        if self.permissions_for_blade(public_signing_key):
            if perms:
                self.permissions_blades_db.update(
                    {'permissions': perms}, Query().public_signing_key == public_signing_key)
            else:
                self.permissions_blades_db.remove(
                    Query().public_signing_key == public_signing_key)
        else:
            self.permissions_blades_db.insert({
                'public_signing_key': public_signing_key,
                'permissions': perms
            })

    def all_groups(self):
        return self.permissions_groups_db.all()

    def add_group(self, grp):
        self.permissions_groups_db.insert(grp)

    def permissions_for_group(self, group_id):
        self.permissions_groups_db.search(Query().id == group_id)

    def update_group(self, group_id, grp):
        self.permissions_groups_db.update(grp, Query().id == group_id)

    def remove_group(self, group_id):
        self.permissions_groups_db.remove(Query().id == group_id)

    def permitted_to_view_message(self, public_signing_key, permissions_categories):
        if len(permissions_categories) == 0:
            return True

        if public_signing_key is not None:

            # determine if the blade has direct permissions
            blades = self.permissions_blades_db.search(
                Query().public_signing_key == public_signing_key)
            if blades:
                perm = blades[0]['permissions']
                if perm['type'] == 'all':
                    return True
                elif perm['type'] == 'categories' and any([k in perm['categories'] for k in permissions_categories]):
                    return True

            # determine if the blade is in any permissions group with access
            for grp in self.permissions_groups_db.all():
                if public_signing_key in grp['members']:
                    perm = grp['permissions']
                    if perm['type'] == 'all':
                        return True
                    elif perm['type'] == 'categories' and any([k in perm['categories'] for k in permissions_categories]):
                        return True

        return False
