import base64
import bcrypt
import nacl.signing
import os
import src.auth as auth
import src.passwords as passwords
import time



SLEEP_TIME = 0.75

time.sleep(SLEEP_TIME)

print()
print('******************************')
print('*                            *')
print('*   Labrys Setup Assistant   *')
print('*                            *')
print('******************************')



os.makedirs('data')
os.makedirs(os.path.join('data', 'authentication'))
os.makedirs(os.path.join('data', 'authentication', 'auth_state'))
os.makedirs(os.path.join('data', 'authentication', 'auth_tokens'))
os.makedirs(os.path.join('data', 'identity'))
os.makedirs(os.path.join('data', 'permissions'))
os.makedirs(os.path.join('data', 'permissions', 'groups'))
os.makedirs(os.path.join('data', 'permissions', 'restricted_user_content'))

# blade_url 
time.sleep(SLEEP_TIME)
print()
print()
canonical_url = input('What is the canonical url to use for this blade?\n\n> ')

with open(os.path.join('data', 'blade_url.txt'), 'w') as f:
  f.write(canonical_url)


# password_hash
time.sleep(SLEEP_TIME)
print()
print()
password = input('What password would you like to use to log in to this blade?\n\n> ')

with open(os.path.join('data', 'authentication', 'password_hash.txt'), 'w') as f:
  f.write(passwords.get_hashed_password(password).decode('ascii'))


# signing keys -> admins
time.sleep(SLEEP_TIME)
print()
print()
print('Generating signing keys...')
private_signing_key = nacl.signing.SigningKey.generate()

with open(os.path.join('data', 'identity', 'private_signing_key.txt'), 'w') as f:
  f.write(private_signing_key.encode(encoder = nacl.encoding.Base64Encoder).decode('ascii'))

with open(os.path.join('data', 'admins.txt'), 'w') as f:
  f.write(private_signing_key.encode(encoder = nacl.encoding.Base64Encoder).decode('ascii'))

with open(os.path.join('data', 'identity', 'public_signing_key.txt'), 'w') as f:
  f.write(private_signing_key.verify_key.encode(encoder = nacl.encoding.Base64Encoder).decode('ascii'))


# session secret key
time.sleep(SLEEP_TIME)
print()
print()
print('Generating session keys...')
session_key = auth.get_random_bytes(32)

with open(os.path.join('data', 'session_secret_key.txt'), 'w') as f:
  f.write(base64.b64encode(session_key).decode('ascii'))


time.sleep(SLEEP_TIME)
print()
print()
print('Setup complete.')
print()
print()

time.sleep(SLEEP_TIME)
