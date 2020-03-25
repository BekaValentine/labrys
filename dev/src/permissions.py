import os

def split_path(path):
  parts = []

  while True:
    head, tail = os.path.split(path)
    if tail.strip() != '':
      parts = [tail] + parts
    if not head: break
    path = head

  return parts

def file_permissions(loc_perm_dir, file_name):
  groups_path = os.path.join(loc_perm_dir, 'files', file_name + '.groups')
  groups = None
  if os.path.isfile(groups_path):
    with open(groups_path, 'r') as f: groups = f.read().split()
  
  people_path = os.path.join(loc_perm_dir, 'files', file_name + '.people')
  people = None
  if os.path.isfile(people_path):
    with open(people_path, 'r') as f: people = f.read().split()

  if groups or people:
    return (groups or [], people or [])
  else:
    return None

def directory_permissions(loc_perm_dir):
  groups_path = os.path.join(loc_perm_dir, 'groups')
  groups = None
  if os.path.isfile(groups_path):
    with open(groups_path, 'r') as f: groups = f.read().split()

  people_path = os.path.join(loc_perm_dir, 'people')
  people = None
  if os.path.isfile(people_path):
    with open(people_path, 'r') as f: people = f.read().split()

  if groups or people:
    return (groups or [], people or [])
  else:
    return None

def permissions(permissions_dir, content_dir, path):
  restricted_user_content_dir = os.path.join(permissions_dir, 'restricted_user_content')
  content_path = os.path.join(content_dir, path)
  content_is_file = os.path.isfile(content_path)
  path_parts = split_path(path)

  def rec(loc_perm_dir, rem_parts):
    if not os.path.exists(loc_perm_dir) or 0 == len(rem_parts):
      return None
    elif 1 == len(rem_parts):
      if content_is_file:
        return file_permissions(loc_perm_dir, rem_parts[0]) or\
                 directory_permissions(loc_perm_dir)
      else:
        return directory_permissions(os.path.join(loc_perm_dir,
                                                  'directories',
                                                  rem_parts[0])) or\
               directory_permissions(loc_perm_dir)
    else:
      return rec(os.path.join(loc_perm_dir, 'directories', rem_parts[0]),
                 rem_parts[1:]) or\
             directory_permissions(loc_perm_dir)

  return rec(restricted_user_content_dir, path_parts)

def group_members(permissions_dir, group_name):
  group_file = os.path.join(permissions_dir, 'groups', group_name)
  group_members = None
  if os.path.isfile(group_file):
    with open(group_file, 'r') as f: group_members = f.read().split()
  return group_members or []

def person_can_access(permissions_dir, content_dir, person, path):
  perms = permissions(permissions_dir, content_dir, path)

  if not perms: return True

  (group_perms, people_perms) = perms

  if group_perms and\
     (any([ person in group_members(permissions_dir, group) for group in group_perms])\
      or\
      'ALL' in group_perms):
    return True

  if people_perms and person in people_perms:
    return True

  return False
