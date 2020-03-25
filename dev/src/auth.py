import binascii
import os
import random
import string
import time


# gets `num_bytes_` of random bytes from /dev/urandom
def get_random_bytes(num_bytes):

  with open('/dev/urandom', 'rb') as f:
    bytes = f.read(num_bytes)

  if len(bytes) != num_bytes:
    raise Exception('failed to get random bytes')

  return bytes



# checks that a string is all hex
def is_hex_string(s):
  for c in s:
    if c not in '0123456789abcdefABCDEF':
      return False
  return True



# removes old auth tokens
MAX_AUTH_TOKEN_AGE = 2 * 60 # 5 minutes
MAX_NUM_AUTH_TOKENS = 5
def cleanup_old_auth_tokens(auth_token_dir):

  # Remove auth tokens older than `MAX_AUTH_TOKEN_AGE`

  now = time.time()
  for file_name in os.listdir(auth_token_dir):
    tok_path = os.path.join(auth_token_dir, file_name)
    tok_time = os.path.getctime(tok_path)
    if now - tok_time > MAX_AUTH_TOKEN_AGE:
      print('Removing auth token ' + file_name + ' because it is ' + str(now - tok_time - MAX_AUTH_TOKEN_AGE) + ' seconds too old.')
      os.remove(tok_path)


  # Remove all but the `MAX_NUM_AUTH_TOKENS` most recent auth tokens

  toks = []
  for file_name in os.listdir(auth_token_dir):
    tok_path = os.path.join(auth_token_dir, file_name)
    tok_time = os.path.getctime(tok_path)
    toks += [(tok_path, tok_time)]

  toks.sort(key = lambda p: p[1], reverse = True)
  old_toks = toks[MAX_NUM_AUTH_TOKENS-1:]

  for (tok_path, tok_time) in old_toks:
    print('Removing auth token ' + os.path.split(tok_path)[1] + ' because there are too many auth tokens.')
    os.remove(tok_path)



# makes a new auth token for `requester` and `state` and stores it in
# `auth_token_dir`
def make_auth_token(auth_token_dir, requester, state):

  cleanup_old_auth_tokens(auth_token_dir)

  auth_token = str(binascii.hexlify(get_random_bytes(64)), 'ascii')

  with open(os.path.join(auth_token_dir, auth_token), 'w') as f:
    f.write(requester.strip() + '\n' + state.strip())

  return auth_token



# checks if `auth_token` was assigned for `requester` and `state`
def check_auth_token(auth_token_dir, auth_token, requester, state):

  if not is_hex_string(auth_token): return False

  auth_token_file = os.path.join(auth_token_dir, auth_token)

  if os.path.isfile(auth_token_file):
    with open(auth_token_file, 'r') as f:
      return f.read().strip() == requester.strip() + '\n' + state.strip()
  else:
    return False



# deletes `auth_token`
def delete_auth_token(auth_token_dir, auth_token):

  if is_hex_string(auth_token):

    auth_token_file = os.path.join(auth_token_dir, auth_token)

    if os.path.isfile(auth_token_file):
      os.remove(auth_token_file)



# makes a new auth state for `id_server` and stores it in
# `auth_state_dir`
def make_auth_state(auth_state_dir, id_server):

  auth_state = str(binascii.hexlify(get_random_bytes(64)), 'ascii')

  with open(os.path.join(auth_state_dir, auth_state), 'w') as f:
    f.write(id_server.strip())

  return auth_state




# gets the identity server associated with `auth_state`
def get_auth_state_identity_server(auth_state_dir, auth_state):

  if not is_hex_string(auth_state): return None

  auth_state_path = os.path.join(auth_state_dir, auth_state)

  if not os.path.isfile(auth_state_path): return None

  with open(auth_state_path, 'r') as f:
    return f.read().strip()



# deletes `auth_state`
def delete_auth_state(auth_state_dir, auth_state):

  if is_hex_string(auth_state):

    auth_state_file = os.path.join(auth_state_dir, auth_state)

    if os.path.isfile(auth_state_file):
      os.remove(auth_state_file)
