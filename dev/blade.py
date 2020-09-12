import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet
import datetime
from flask import *
import html
import nacl.encoding
import nacl.signing
import os
import random
import re
import requests
import sys
from tinydb import TinyDB, Query

# Labrys imports
from src.auth import *
from src.blade_identity import *
import src.datastore as datastore
import src.passwords as passwords
import src.permissions as permissions
from src.timeline import *
from src.viewarguments import *

app = Flask(__name__)

DATA_DIR = os.environ['DATA_DIR']
if not DATA_DIR:
    print('Data directory is needed.')
    exit()

SECRETS_DIR = os.path.join(DATA_DIR, 'secrets')
SESSION_SECRET_KEY_FILE = os.path.join(SECRETS_DIR, 'session_secret_key.txt')
PRIVATE_SIGNING_KEY_FILE = os.path.join(SECRETS_DIR, 'private_signing_key.txt')
PASSWORD_HASH_FILE = os.path.join(SECRETS_DIR, 'password_hash.txt')

IDENTITY_DIR = os.path.join(DATA_DIR, 'identity')
DISPLAY_NAME_FILE = os.path.join(IDENTITY_DIR, 'display_name.txt')
BIO_FILE = os.path.join(IDENTITY_DIR, 'bio.txt')
PUBLIC_SIGNING_KEY_FILE = os.path.join(IDENTITY_DIR, 'public_signing_key.txt')

PERMISSIONS_DIR = os.path.join(DATA_DIR, 'permissions')
PERMISSIONS_GROUPS_DB = TinyDB(os.path.join(PERMISSIONS_DIR, 'groups.json'))
PERMISSIONS_BLADES_DB = TinyDB(os.path.join(PERMISSIONS_DIR, 'blades.json'))

INBOX_DB = TinyDB(os.path.join(DATA_DIR, 'inbox.json'))

OUTBOX_DB = TinyDB(os.path.join(DATA_DIR, 'outbox.json'))

FEED_DB = TinyDB(os.path.join(DATA_DIR, 'feed.json'))
FEED_ATTACHMENTS_DIR = os.path.join(DATA_DIR, 'feed_attachments')

SUBSCRIPTIONS_DB = TinyDB(os.path.join(DATA_DIR, 'subscriptions.json'))

TIMELINE_CACHE_DB = TinyDB(os.path.join(DATA_DIR, 'timeline_cache.json'))

KNOWN_BLADES_DB = TinyDB(os.path.join(DATA_DIR, 'known_blades.json'))
KNOWN_BLADES_AVATARS_DIR = os.path.join(DATA_DIR, 'known_blades_avatars')

DATA_STORE = datastore.DataStore(
    identity_dir=IDENTITY_DIR,
    display_name_file=DISPLAY_NAME_FILE,
    bio_file=BIO_FILE,
    private_signing_key_file=PRIVATE_SIGNING_KEY_FILE,
    public_signing_key_file=PUBLIC_SIGNING_KEY_FILE,
    feed_db=FEED_DB,
    feed_attachments_dir=FEED_ATTACHMENTS_DIR,
    timeline_cache_db=TIMELINE_CACHE_DB,
    permissions_groups_db=PERMISSIONS_GROUPS_DB,
    permissions_blades_db=PERMISSIONS_BLADES_DB,
    subscriptions_db=SUBSCRIPTIONS_DB,
    known_blades_db=KNOWN_BLADES_DB,
    known_blades_avatars_dir=KNOWN_BLADES_AVATARS_DIR,
)

# The Session Secret Key is used to sign cookies.
with open(SESSION_SECRET_KEY_FILE, 'r') as f:
    app.secret_key = f.read().strip()


# Blade URL
with open(os.path.join(DATA_DIR, 'blade_url.txt'), 'r') as f:
    BLADE_URL = f.read().strip()


@app.template_filter('formatdatetime')
def format_datetime(value, format="%-H:%M %p, %b %-d, %Y (UTC)"):
    if value is None:
        return ""
    return datetime.datetime.fromisoformat(value).strftime(format)


######################
##                  ##
##   The Frontend   ##
##                  ##
######################


# The Blade root. Doesn't do anything interesting right now.
# TODO:
# LINK TO: my feed, my timeline
# FORM: login
@app.route('/', methods=['GET'])
def labrys_home():
    if DATA_STORE.avatar_file_name() is not None:
        avatar_url = '/api/identity/avatar'
    else:
        avatar_url = None
    display_name = DATA_STORE.display_name()
    bio = DATA_STORE.bio()
    public_signing_key = DATA_STORE.public_signing_key()
    return render_template('main_page.html',
                           avatar_url=avatar_url,
                           display_name=display_name,
                           bio=bio,
                           public_signing_key=public_signing_key,
                           logged_in=session.get('authenticated') == 'authenticated')


# The login endpoint handles user logins.
@app.route('/login', methods=['POST'])
@request_form(LoginFormPassword)
def login(submitted_password):
    with open(PASSWORD_HASH_FILE, 'r') as f:
        password_hash = f.read()

    if not passwords.check_password(submitted_password, password_hash):
        return redirect('/failed_login')

    session['authenticated'] = 'authenticated'

    return redirect('/')


# The logout endpoint handles user logouts.
@app.route('/logout', methods=['POST'])
def logout():
    if 'authenticated' in session:
        session.pop('authenticated')

    return redirect('/')


# The feeds endpoint displays the users own feed messages
@app.route('/feed', methods=['GET'])
@many_query_params(FeedOptions)
def feed_get(last_seen):
    logged_in = session.get('authenticated') == 'authenticated'

    if DATA_STORE.avatar_file_name() is not None:
        avatar_url = '/api/identity/avatar'
    else:
        avatar_url = None

    if logged_in:
        messages, next_last_seen = DATA_STORE.feed_owner_authorization(
            last_seen)
    else:
        messages, next_last_seen = DATA_STORE.feed_public_authorization(
            last_seen)

    return render_template('feed.html', logged_in=logged_in, display_name=DATA_STORE.display_name(), avatar_url=avatar_url, messages=messages, next_last_seen=next_last_seen)


@app.route('/feed/<message_id>', methods=['GET'])
def feed_id_get(message_id):
    return 'ok'


@app.route('/feed', methods=['POST'])
@request_form(FormFeedMessage)
def feed_post(message):
    DATA_STORE.add_feed_message(message)

    return redirect('/feed')


# The timeline endpoint displays the user's timeline
@app.route('/timeline', methods=['GET'])
@many_query_params(TimelineOptions)
def timeline(last_seen):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    messages, next_last_seen = DATA_STORE.timeline(last_seen)

    return render_template('timeline.html', logged_in=True, messages=messages, next_last_seen=next_last_seen)


@app.route('/timeline/<message_id>', methods=['GET'])
def timeline_id_get(message_id):
    return 'ok'


# The subscriptions endpoint displays the user's subscriptions
@app.route('/subscriptions', methods=['GET'])
@many_query_params(SubscriptionsOptions)
def subscriptions_get(last_seen):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    subs, next_last_seen = DATA_STORE.subscriptions(last_seen)

    return render_template('subscriptions.html', logged_in=True, subscriptions=subs, next_last_seen=next_last_seen)


@app.route('/subscriptions', methods=['POST'])
@request_form(FormSubscription)
def subscriptions_post(blade_url):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    DATA_STORE.add_subscription(blade_url)

    return redirect('/subscriptions')


@app.route('/subscriptions/<subscription_id>/delete', methods=['POST'])
def subscriptions_delete(subscription_id):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    DATA_STORE.remove_subscription(subscription_id)

    return redirect('/subscriptions')


# The subscribers endpoint displays the user's subscribers
@app.route('/subscribers', methods=['GET'])
def subscribers():
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    return render_template('subscribers.html', logged_in=True)


# The private_messages endpoint displays the user's private messages
@app.route('/private_messages', methods=['GET'])
def private_messages():
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    return render_template('private_messages.html', logged_in=True)


# The blade endpoint displays other blades information
@app.route('/blade/<blade_url>', methods=['GET'])
def blade_get(blade_url):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    blade_identity, messages, subscription_id = DATA_STORE.blade(blade_url)

    return render_template('blade.html', logged_in=True, blade_identity=blade_identity, subscription_id=subscription_id, messages=messages)


@app.route('/known_blades/avatars/<avatar_file_name>', methods=['GET'])
def known_blades_avatars_get(avatar_file_name):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    return send_from_directory(KNOWN_BLADES_AVATARS_DIR, avatar_file_name)


# The unauthorized endpoint tells the user that they're accessing a page that
# are not authorized to access.
@app.route('/failed_login', methods=['GET'])
def failed_login():
    return render_template('unauthorized.html', reason='failed_login')


# The 404 handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('page_not_found.html', logged_in=session.get('authenticated') == 'authenticated'), 404


#################
##             ##
##   The API   ##
##             ##
#################


# The identity/<file> endpoint serves the content of the identity directory,
# which is usually the display name, bio, and avatar.
@app.route('/api/identity/avatar', methods=['GET'])
def api_identity_avatar():
    avatar_file_name = DATA_STORE.avatar_file_name()

    if avatar_file_name is None:
        return 'not found', 404
    else:
        return send_from_directory(IDENTITY_DIR, avatar_file_name)


# Gets the display name
@app.route('/api/identity/display_name', methods=['GET'])
def api_identity_display_name():
    return DATA_STORE.display_name()


# Gets the bio
@app.route('/api/identity/bio', methods=['GET'])
def api_identity_bio():
    return DATA_STORE.bio()


# Gets the public signing key
@app.route('/api/identity/public_signing_key', methods=['GET'])
def api_identity_public_signing_key():
    return DATA_STORE.public_signing_key()


# The identity/sign endpoint is used to get a signed value from the blade.
@app.route('/api/identity/sign', methods=['GET'])
@query_params(SignMessage)
def api_identity_sign(message):
    with open(PRIVATE_SIGNING_KEY_FILE, 'r') as f:
        signing_key = nacl.signing.SigningKey(f.read().encode(
            encoding='ascii'), encoder=nacl.encoding.Base64Encoder)
        signed = signing_key.sign(message.encode(encoding='ascii'))
        return base64.b64encode(signed.signature)


# The identity/deauthenticate endpoint provides a means for the blade owner to
# log out of the blade.
@app.route('/api/identity/deauthenticate', methods=['GET'])
def api_identity_deauthenticate():
    session.pop('authenticated', None)
    return 'ok'


# The identity/authenticate endpoint provides a means for the blade owner to
# identify themselves to the blade.
@app.route('/api/identity/authenticate', methods=['POST'])
@request_body(Password)
def api_identity_authenticate_post(submitted_password):
    with open(PASSWORD_HASH_FILE, 'r') as f:
        password_hash = f.read().strip()

    if not passwords.check_password(submitted_password, password_hash):
        return 'unauthorized', 401

    session['authenticated'] = 'authenticated'

    return 'ok'


# The /api/inbox endpoint is where incoming private message notifications go.
@app.route('/api/inbox', methods=['GET'])
@require_authentication
def api_inbox_get():
    return json.dumps(INBOX_DB.all()), 200


@app.route('/api/inbox', methods=['POST'])
@request_body(InboxMessage)
def api_inbox_post(sender_info):

    resp_data = dh_sessions.encrypted_client_request(
        PRIVATE_SIGNING_KEY_FILE,
        PUBLIC_SIGNING_KEY_FILE,
        sender_info['public_signing_key'],
        requests.get,
        sender_info['url'] + '/api/outbox')

    if resp_data:
        received_messages = json.loads(resp_data)

        for msg in received_messages:
            if not INBOX_DB.search(Query().origin_id == msg['id']):
                INBOX_DB.insert({
                    'id': ''.join([random.choice('0123456789abcdef')
                                   for i in range(30)]),
                    'origin_id': msg['id'],
                    'sender': sender_info['public_signing_key'],
                    'sent_datetime': msg['sent_datetime'],
                    'type': msg['type'],
                    'content': msg['content']
                })

    return 'ok', 200


@app.route('/api/inbox/<message_id>', methods=['DELETE'])
@require_authentication
def api_inbox_delete(message_id):

    INBOX_DB.remove(Query().id == message_id)

    return 'ok', 200


# The /api/outbox endpoint is where incoming private message notifications go.
@app.route('/api/outbox', methods=['GET'])
@many_header_params(BladeAuthorization)
def api_outbox_get(authorization):

    if authorization is None:
        return 'unauthorized', 401

    messages = []
    for msg in OUTBOX_DB.all():
        if msg['receiver_public_signing_key'] == authorization['public_signing_key']:

            messages += [msg]

    encrypted_messages = dh_sessions.encrypt_server_response(
        PRIVATE_SIGNING_KEY_FILE,
        PUBLIC_SIGNING_KEY_FILE,
        authorization,
        json.dumps(messages))

    return json.dumps(encrypted_messages), 200


@app.route('/api/outbox', methods=['POST'])
@require_authentication
@request_body(OutboxMessage)
def api_outbox_post(message):
    message_id = ''.join([random.choice('0123456789abcdef')
                          for i in range(30)])

    message['id'] = message_id
    message['sent_datetime'] = datetime.datetime.utcnow().isoformat()

    OUTBOX_DB.insert(message)

    with open(PUBLIC_SIGNING_KEY_FILE, 'r') as f:
        public_signing_key = f.read().strip()

    resp = requests.post(message['receiver_url'] + '/api/inbox',
                         data=json.dumps({
                             'url': BLADE_URL,
                             'public_signing_key': public_signing_key
                         }))

    return 'ok', 200


@app.route('/api/outbox/<message_id>', methods=['DELETE'])
@require_authentication
def api_outbox_delete(message_id):

    OUTBOX_DB.remove(Query().id == message_id)

    return 'ok', 200


# The /api/feed endpoint provides the public broadcast messages from this blade.
@app.route('/api/feed', methods=['GET'])
@many_query_params(FeedOptions)
@many_header_params(BladeAuthorization)
def api_feed_get(authorization, last_seen):

    if last_seen:
        found = FEED_DB.search(Query().id == last_seen)
        if found:
            messages = FEED_DB.search((Query().publish_datetime >= found[0]['publish_datetime']) &
                                      (Query().id != last_seen))
        else:
            messages = FEED_DB.all()
    else:
        messages = FEED_DB.all()

    if authorization:
        messages = [msg for msg in messages if permissions.permitted_to_view_message(
            PERMISSIONS_GROUPS_DB, PERMISSIONS_BLADES_DB, authorization['public_signing_key'], msg['permissions_categories'])]

        for msg in messages:
            msg.pop('permissions_categories', None)

        encrypted_message = dh_sessions.encrypt_server_response(
            PRIVATE_SIGNING_KEY_FILE,
            PUBLIC_SIGNING_KEY_FILE,
            authorization,
            json.dumps(messages))

        return json.dumps(encrypted_message), 200

    else:

        messages = [msg for msg in messages if permissions.permitted_to_view_message(
            PERMISSIONS_GROUPS_DB, PERMISSIONS_BLADES_DB, None, msg['permissions_categories'])]

        for msg in messages:
            msg.pop('permissions_categories', None)

        return json.dumps({'messages': messages}), 200


@app.route('/api/feed', methods=['POST'])
@require_authentication
@request_body(FeedMessage)
def api_feed_post(message):
    id = DATA_STORE.add_feed_message(message)

    return id, 200


@app.route('/api/feed/<message_id>', methods=['DELETE'])
@require_authentication
def api_feed_id_delete(message_id):
    FEED_DB.remove(Query().id == message_id)

    return 'ok', 200


@app.route('/api/feed_attachments/<attachment_name>', methods=['GET'])
def feed_attachments_id_get(attachment_name):
    return send_from_directory(DATA_STORE.feed_attachments_dir, attachment_name)


@app.route('/api/subscriptions', methods=['GET'])
@require_authentication
def api_subscriptions_get():

    subs = DATA_STORE.subscriptions()

    return json.dumps(subs)


@app.route('/api/subscriptions', methods=['POST'])
@require_authentication
@request_body(Subscription)
def api_subscriptions_post(blade_url):

    DATA_STORE.add_subscription(blade_url)

    return 'ok', 200


@app.route('/api/subscriptions/<sub_id>', methods=['DELETE'])
@require_authentication
def api_subscription_delete(sub_id):

    DATA_STORE.remove_subscription(sub_id)

    return 'ok', 200


@app.route('/api/permissions/groups', methods=['GET'])
@require_authentication
def api_permissions_groups_get():

    summaries = []

    for grp in PERMISSIONS_GROUPS_DB.all():
        summaries += [{
            'id': grp['id'],
            'name': grp['name'],
            'description': grp['description'],
            'member_count': len(grp['members'])
        }]

    return json.dumps(summaries)


@app.route('/api/permissions/groups', methods=['POST'])
@require_authentication
@request_body(PermissionsGroup)
def api_permissions_groups_post(grp):

    group_id = ''.join([random.choice('0123456789abcdef')
                        for i in range(30)])

    grp['id'] = group_id

    PERMISSIONS_GROUPS_DB.insert(grp)

    return 'ok', 200


@app.route('/api/permissions/groups/<group_id>', methods=['GET'])
@require_authentication
def api_permissions_groups_id_get(group_id):

    found = PERMISSIONS_GROUPS_DB.search(Query().id == group_id)

    if found:
        return json.dumps(found[0]), 200

    else:
        return 'not found', 404


@app.route('/api/permissions/groups/<group_id>', methods=['PUT'])
@require_authentication
@request_body(PermissionsGroup)
def api_permissions_groups_id_put(grp, group_id):

    if PERMISSIONS_GROUPS_DB.search(Query().id == group_id):
        PERMISSIONS_GROUPS_DB.update(grp, Query().id == group_id)

        return 'ok', 200

    else:

        return 'not found', 404


@app.route('/api/permissions/groups/<group_id>', methods=['DELETE'])
@require_authentication
def api_permissions_groups_id_delete(group_id):

    PERMISSIONS_GROUPS_DB.remove(Query().id == group_id)

    return 'ok', 200


@app.route('/api/permissions/blades', methods=['GET'])
@require_authentication
def api_permissions_blades_get():

    permissions_blades = PERMISSIONS_BLADES_DB.all()

    for perm_blade in permissions_blades:
        perm_blade['id'] = encode_public_key(perm_blade['public_signing_key'])

    return json.dumps(blades)


@app.route('/api/permissions/blades/<blade_id>', methods=['GET'])
@require_authentication
def api_permissions_blades_id_get(blade_id):

    public_signing_key = decode_public_key(blade_id)

    found = PERMISSIONS_BLADES_DB.search(
        Query().public_signing_key == public_signing_key)

    if found:
        return json.dumps(found[0]['permissions']), 200

    else:
        return 'not found', 404


@app.route('/api/permissions/blades/<blade_id>', methods=['PUT'])
@require_authentication
@request_body(PermissionsBlade)
def api_permissions_blades_id_put(perms, blade_id):

    public_signing_key = decode_public_key(blade_id)

    if PERMISSIONS_BLADES_DB.search(Query().public_signing_key == public_signing_key):
        PERMISSIONS_BLADES_DB.update(
            {'permissions': perms}, Query().public_signing_key == public_signing_key)

    else:
        PERMISSIONS_BLADES_DB.insert({
            'public_signing_key': public_signing_key,
            'permissions': perms
        })

    return 'ok', 200


@app.route('/api/permissions/blades/<blade_id>', methods=['DELETE'])
@require_authentication
def api_permissions_blades_id_delete(blade_id):

    public_signing_key = decode_public_key(blade_id)

    PERMISSIONS_BLADES_DB.remove(
        Query().public_signing_key == public_signing_key)

    return 'ok', 200


# The /api/timeline endpoint provides the current timeline for this blade.
@app.route('/api/timeline', methods=['GET'])
@require_authentication
def api_timeline_get():

    messages = DATA_STORE.timeline()

    return json.dumps(messages), 200


if __name__ == '__main__':
    if '--port' in sys.argv:
        port = int(sys.argv[sys.argv.index('--port') + 1])
    else:
        port = 1337

    if '--url' in sys.argv:
        BLADE_URL = sys.argv[sys.argv.index('--url') + 1]

    app.run(port=port, debug=True)
