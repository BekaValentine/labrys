import os
from tinydb import Query


def split_path(path):
    parts = []

    while True:
        head, tail = os.path.split(path)
        if tail.strip() != '':
            parts = [tail] + parts
        if not head:
            break
        path = head

    return parts


def permitted_to_view_message(permissions_groups_db, permissions_blades_db, public_signing_key, permissions_categories):
    if len(permissions_categories) == 0:
        return True

    if public_signing_key is not None:

        # determine if the blade has direct permissions
        blades = permissions_blades_db.search(
            Query().public_signing_key == public_signing_key)
        if blades:
            perm = blades[0]['permissions']
            if perm['type'] == 'all':
                return True
            elif perm['type'] == 'categories' and any([k in perm['categories'] for k in permissions_categories]):
                return True

        # determine if the blade is in any permissions group with access
        for grp in permissions_groups_db.all():
            if public_signing_key in grp['members']:
                perm = grp['permissions']
                if perm['type'] == 'all':
                    return True
                elif perm['type'] == 'categories' and any([k in perm['categories'] for k in permissions_categories]):
                    return True

    return False
