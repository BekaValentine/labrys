from tinydb import TinyDB, Query
import sys
import requests
import re
import random
import os
import nacl.signing
import nacl.encoding
import html
from flask import *
import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import base64

# Labrys imports

from src.viewarguments import *
import src.identity_manager as identity_manager
import src.encryption_manager as encryption_manager
import src.feed_manager as feed_manager
import src.permissions_manager as permissions_manager
import src.subscriptions_manager as subscriptions_manager
import src.known_blades_manager as known_blades_manager
import src.timeline_manager as timeline_manager
import src.public_keys as public_keys
import src.private_message_manager as private_message_manager
from src.auth import *

################################################################################

app = Flask(__name__)

DATA_DIR = os.environ['DATA_DIR']
if not DATA_DIR:
    print('Data directory is needed.')
    exit()


IDENTITY_MANAGER = identity_manager.IdentityManager(DATA_DIR)
ENCRYPTION_MANAGER = encryption_manager.EncryptionManager(IDENTITY_MANAGER)
PERMISSIONS_MANAGER = permissions_manager.PermissionsManager(DATA_DIR)
FEED_MANAGER = feed_manager.FeedManager(
    DATA_DIR,
    IDENTITY_MANAGER,
    PERMISSIONS_MANAGER,
)
KNOWN_BLADES_MANAGER = known_blades_manager.KnownBladesManager(DATA_DIR)
SUBSCRIPTIONS_MANAGER = subscriptions_manager.SubscriptionsManager(
    DATA_DIR,
    IDENTITY_MANAGER,
    ENCRYPTION_MANAGER,
    KNOWN_BLADES_MANAGER,
)
TIMELINE_MANAGER = timeline_manager.TimelineManager(
    DATA_DIR,
    IDENTITY_MANAGER,
    SUBSCRIPTIONS_MANAGER,
    KNOWN_BLADES_MANAGER,
)
PRIVATE_MESSAGE_MANAGER = private_message_manager.PrivateMessageManager(
    DATA_DIR,
    IDENTITY_MANAGER,
    ENCRYPTION_MANAGER,
    KNOWN_BLADES_MANAGER,
    SUBSCRIPTIONS_MANAGER,
)

# The Session Secret Key is used to sign cookies.
app.secret_key = IDENTITY_MANAGER.unsafe_session_secret_key()


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
    if IDENTITY_MANAGER.avatar_file_name() is not None:
        avatar_url = '/api/identity/avatar'
    else:
        avatar_url = None
    display_name = IDENTITY_MANAGER.display_name()
    bio = IDENTITY_MANAGER.bio()
    public_signing_key = IDENTITY_MANAGER.public_signing_key()
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
    if not IDENTITY_MANAGER.check_password(submitted_password):
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

    if IDENTITY_MANAGER.avatar_file_name() is not None:
        avatar_url = '/api/identity/avatar'
    else:
        avatar_url = None

    if logged_in:
        messages, next_last_seen = FEED_MANAGER.feed_owner_authorization(
            last_seen)
    else:
        messages, next_last_seen = FEED_MANAGER.feed_public_authorization(
            last_seen)

    return render_template('feed.html', logged_in=logged_in, display_name=IDENTITY_MANAGER.display_name(), avatar_url=avatar_url, messages=messages, next_last_seen=next_last_seen)


@app.route('/feed/<message_id>', methods=['GET'])
def feed_id_get(message_id):
    logged_in = session.get('authenticated') == 'authenticated'

    if IDENTITY_MANAGER.avatar_file_name() is not None:
        avatar_url = '/api/identity/avatar'
    else:
        avatar_url = None

    if logged_in:
        message = FEED_MANAGER.message_with_id(message_id)
    else:
        message = FEED_MANAGER.message_with_id_public_authorization(message_id)

    if message is None:
        return redirect('/')

    return render_template('feed_message.html', logged_in=True, display_name=IDENTITY_MANAGER.display_name(), avatar_url=avatar_url, message=message)


@app.route('/feed', methods=['POST'])
@request_form(FormFeedMessage)
def feed_post(message):
    FEED_MANAGER.add_feed_message(message)

    return redirect('/feed')


# The timeline endpoint displays the user's timeline
@app.route('/timeline', methods=['GET'])
@many_query_params(TimelineOptions)
def timeline(last_seen):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    messages, next_last_seen = TIMELINE_MANAGER.timeline(last_seen)

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

    subs, next_last_seen = SUBSCRIPTIONS_MANAGER.subscriptions(last_seen)

    return render_template('subscriptions.html', logged_in=True, subscriptions=subs, next_last_seen=next_last_seen)


@app.route('/subscriptions', methods=['POST'])
@request_form(FormSubscription)
def subscriptions_post(blade_url):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    SUBSCRIPTIONS_MANAGER.add_subscription(blade_url)

    return redirect('/subscriptions')


@app.route('/subscriptions/<subscription_id>/delete', methods=['POST'])
def subscriptions_delete(subscription_id):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    SUBSCRIPTIONS_MANAGER.remove_subscription(subscription_id)

    return redirect('/subscriptions')


# The subscribers endpoint displays the user's subscribers
@app.route('/subscribers', methods=['GET'])
def subscribers():
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    subscribers_info = [KNOWN_BLADES_MANAGER.cached_blade_identity(sub['public_signing_key'])
                        for sub in SUBSCRIPTIONS_MANAGER.all_subscribers()]

    return render_template('subscribers.html', logged_in=True, subscribers=subscribers_info)


# The private_messages endpoint displays the user's private messages
@app.route('/private_messages', methods=['GET'])
def private_messages_get():
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    return render_template('private_messages.html', logged_in=True, known_blades=KNOWN_BLADES_MANAGER.all_known_blades())


@app.route('/private_messages', methods=['POST'])
@request_form(FormPrivateMessage)
def private_messages_post(private_message):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    print('NEW PRIVATE MESSAGE', private_message)

    message = {
        'type': 'private_message',
        'public_signing_key': private_message['receiver'],
        'content': {
            'text': private_message['text']
        }
    }

    if PRIVATE_MESSAGE_MANAGER.add_outbox_message(message):
        return redirect('/private_messages')

    return 'ok', 200


# The blade endpoint displays other blades information
@app.route('/blade/<blade_url>', methods=['GET'])
def blade_get(blade_url):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    blade_identity, messages, subscription_id = KNOWN_BLADES_MANAGER.blade(
        blade_url)

    return render_template('blade.html', logged_in=True, blade_identity=blade_identity, subscription_id=subscription_id, messages=messages)


@app.route('/known_blades/avatars/<avatar_file_name>', methods=['GET'])
def known_blades_avatars_get(avatar_file_name):
    if not session.get('authenticated') == 'authenticated':
        return redirect('/')

    return send_from_directory(KNOWN_BLADES_MANAGER.known_blades_avatars_dir, avatar_file_name)


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
    avatar_file_name = IDENTITY_MANAGER.avatar_file_name()

    if avatar_file_name is None:
        return 'not found', 404
    else:
        return send_from_directory(IDENTITY_MANAGER.identity_dir, avatar_file_name)


# Gets the display name
@app.route('/api/identity/display_name', methods=['GET'])
def api_identity_display_name():
    return IDENTITY_MANAGER.display_name()


# Gets the bio
@app.route('/api/identity/bio', methods=['GET'])
def api_identity_bio():
    return IDENTITY_MANAGER.bio()


# Gets the public signing key
@app.route('/api/identity/public_signing_key', methods=['GET'])
def api_identity_public_signing_key():
    return IDENTITY_MANAGER.public_signing_key()


# The identity/sign endpoint is used to get a signed value from the blade.
@app.route('/api/identity/sign', methods=['GET'])
@query_params(SignMessage)
def api_identity_sign(message):
    return IDENTITY_MANAGER.sign(message)


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
    if not IDENTITY_MANAGER.check_password(submitted_password):
        return 'unauthorized', 401

    session['authenticated'] = 'authenticated'

    return 'ok'


# The /api/inbox endpoint is where incoming private message notifications go.
@app.route('/api/inbox', methods=['GET'])
@require_authentication
def api_inbox_get():
    return json.dumps(PRIVATE_MESSAGE_MANAGER.all_inbox_messages()), 200


@app.route('/api/inbox', methods=['POST'])
@request_body(InboxMessage)
def api_inbox_post(message):

    PRIVATE_MESSAGE_MANAGER.handle_new_inbox_message(message)

    return 'ok', 200


@app.route('/api/inbox/<message_id>', methods=['DELETE'])
@require_authentication
def api_inbox_delete(message_id):

    PRIVATE_MESSAGE_MANAGER.remove_inbox_message_with_id(message_id)

    return 'ok', 200


# The /api/outbox endpoint is where incoming private message notifications go.
@app.route('/api/outbox', methods=['GET'])
@many_header_params(BladeAuthorization)
def api_outbox_get(authorization):

    if authorization is None:
        return 'unauthorized', 401

    messages = []
    for msg in PRIVATE_MESSAGE_MANAGER.all_outbox_messages():
        if msg['public_signing_key'] == authorization['public_signing_key']:

            messages += [msg]

    encrypted_messages = ENCRYPTION_MANAGER.encrypt_server_response(
        authorization,
        json.dumps(messages))

    return json.dumps(encrypted_messages), 200


@app.route('/api/outbox', methods=['POST'])
@require_authentication
@request_body(OutboxMessage)
def api_outbox_post(message):

    PRIVATE_MESSAGE_MANAGER.add_outbox_message(message)

    return 'ok', 200


@app.route('/api/outbox/<message_id>', methods=['DELETE'])
@require_authentication
def api_outbox_delete(message_id):

    PRIVATE_MESSAGE_MANAGER.remove_outbox_message_with_id(message_id)

    return 'ok', 200


# The /api/feed endpoint provides the public broadcast messages from this blade.
@app.route('/api/feed', methods=['GET'])
@many_query_params(FeedOptions)
@many_header_params(BladeAuthorization)
def api_feed_get(authorization, last_seen):

    if last_seen:
        found = FEED_MANAGER.message_with_id(last_seen)
        if found:
            messages = FEED_MANAGER.messages_after(found)
        else:
            messages = FEED_MANAGER.all_messages()
    else:
        messages = FEED_MANAGER.all_messages()

    if authorization:
        messages = [msg for msg in messages if PERMISSIONS_MANAGER.permitted_to_view_message(
            authorization['public_signing_key'], msg['permissions_categories'])]

        for msg in messages:
            msg.pop('permissions_categories', None)

        encrypted_message = ENCRYPTION_MANAGER.encrypt_server_response(
            authorization,
            json.dumps(messages))

        return json.dumps(encrypted_message), 200

    else:

        messages = [msg for msg in messages if PERMISSIONS_MANAGER.permitted_to_view_message(
            None, msg['permissions_categories'])]

        for msg in messages:
            msg.pop('permissions_categories', None)

        return json.dumps({'messages': messages}), 200


@app.route('/api/feed', methods=['POST'])
@require_authentication
@request_body(FeedMessage)
def api_feed_post(message):
    id = FEED_MANAGER.add_feed_message(message)

    return id, 200


@app.route('/api/feed/<message_id>', methods=['DELETE'])
@require_authentication
def api_feed_id_delete(message_id):

    FEED_MANAGER.remove_message(message_id)

    return 'ok', 200


@app.route('/api/feed_attachments/<attachment_name>', methods=['GET'])
def feed_attachments_id_get(attachment_name):

    return send_from_directory(FEED_MANAGER.feed_attachments_dir, attachment_name)


@app.route('/api/subscriptions', methods=['GET'])
@require_authentication
def api_subscriptions_get():

    subs = SUBSCRIPTIONS_MANAGER.subscriptions()

    return json.dumps(subs)


@app.route('/api/subscriptions', methods=['POST'])
@require_authentication
@request_body(Subscription)
def api_subscriptions_post(blade_url):

    SUBSCRIPTIONS_MANAGER.add_subscription(blade_url)

    return 'ok', 200


@app.route('/api/subscriptions/<sub_id>', methods=['DELETE'])
@require_authentication
def api_subscription_delete(sub_id):

    SUBSCRIPTIONS_MANAGER.remove_subscription(sub_id)

    return 'ok', 200


@app.route('/api/permissions/groups', methods=['GET'])
@require_authentication
def api_permissions_groups_get():

    summaries = []

    for grp in PERMISSIONS_MANAGER.all_groups():
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

    PERMISSIONS_MANAGER.add_group(grp)

    return 'ok', 200


@app.route('/api/permissions/groups/<group_id>', methods=['GET'])
@require_authentication
def api_permissions_groups_id_get(group_id):

    found = PERMISSIONS_MANAGER.permissions_for_group(group_id)

    if found:
        return json.dumps(found[0]), 200

    else:
        return 'not found', 404


@app.route('/api/permissions/groups/<group_id>', methods=['PUT'])
@require_authentication
@request_body(PermissionsGroup)
def api_permissions_groups_id_put(grp, group_id):

    if PERMISSIONS_MANAGER.permissions_for_group(group_id):
        PERMISSIONS_MANAGER.update_group(group_id, grp)

        return 'ok', 200

    else:

        return 'not found', 404


@app.route('/api/permissions/groups/<group_id>', methods=['DELETE'])
@require_authentication
def api_permissions_groups_id_delete(group_id):

    PERMISSIONS_MANAGER.remove_group(group_id)

    return 'ok', 200


@app.route('/api/permissions/blades', methods=['GET'])
@require_authentication
def api_permissions_blades_get():

    permissions_blades = PERMISSIONS_MANAGER.all_blades()

    for perm_blade in permissions_blades:
        perm_blade['id'] = public_keys.encode_public_key(
            perm_blade['public_signing_key'])

    return json.dumps(blades)


@app.route('/api/permissions/blades/<blade_id>', methods=['GET'])
@require_authentication
def api_permissions_blades_id_get(blade_id):

    public_signing_key = public_keys.decode_public_key(blade_id)

    found = PERMISSIONS_MANAGER.permissions_for_blade(public_signing_key)

    if found:
        return json.dumps(found[0]['permissions']), 200

    else:
        return 'not found', 404


@app.route('/api/permissions/blades/<blade_id>', methods=['PUT'])
@require_authentication
@request_body(PermissionsBlade)
def api_permissions_blades_id_put(perms, blade_id):

    public_signing_key = decode_public_key(blade_id)

    PERMISSIONS_MANAGER.set_permissions_for_blade(public_signing_key, perms)

    return 'ok', 200


@app.route('/api/permissions/blades/<blade_id>', methods=['DELETE'])
@require_authentication
def api_permissions_blades_id_delete(blade_id):

    public_signing_key = decode_public_key(blade_id)

    PERMISSIONS_MANAGER.set_permissions_for_blade(public_signing_key, [])

    return 'ok', 200


# The /api/timeline endpoint provides the current timeline for this blade.
@app.route('/api/timeline', methods=['GET'])
@require_authentication
def api_timeline_get():

    messages = TIMELINE_MANAGER.timeline()

    return json.dumps(messages), 200


if __name__ == '__main__':
    if '--port' in sys.argv:
        port = int(sys.argv[sys.argv.index('--port') + 1])
    else:
        port = 1337

    app.run(port=port, debug=True)
