import base64
from flask import request
import functools
import json
import nacl


class String:
    pass


class Integer:
    pass


class Float:
    pass


def check(term, type):
    if type == String:
        return isinstance(term, str)
    elif type == Integer:
        return isinstance(term, int)
    elif type == Float:
        return isinstance(term, float)
    elif isinstance(type, list):
        if not isinstance(term, list):
            return False
        else:
            el_type = type[0]
            for x in term:
                if not check(x, el_type):
                    return False
            return True
    elif isinstance(type, dict):
        if not isinstance(term, dict):
            return False
        elif set(type.keys()) != set(term.keys()):
            return False
        else:
            for key in type:
                val_type = type[key]
                if not check(term[key], val_type):
                    return False
            return True


def match_keys(d, *ks):
    return set(d.keys()) == set(ks)


def header_params(cls):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            parsed = cls.parse(request.headers)
            if parsed is not None:
                return f(parsed, *args, **kwargs)
            else:
                return 'bad request', 400

        return decorated_function

    return decorator


def many_header_params(cls):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            parsed = cls.parse(request.headers)
            if parsed is not None:
                return f(*parsed, *args, **kwargs)
            else:
                return 'bad request', 400

        return decorated_function

    return decorator


def query_params(cls):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            parsed = cls.parse(request.args)
            if parsed is not None:
                return f(parsed, *args, **kwargs)
            else:
                return 'bad request', 400

        return decorated_function

    return decorator


def many_query_params(cls):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            parsed = cls.parse(request.args)
            if parsed is not None:
                return f(*parsed, *args, **kwargs)
            else:
                return 'bad request', 400

        return decorated_function

    return decorator


def request_body(cls):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            parsed = cls.parse(str(request.data, encoding='ascii'))
            if parsed is not None:
                return f(parsed, *args, **kwargs)
            else:
                return 'bad request', 400

        return decorated_function

    return decorator


class SignMessage:
    @staticmethod
    def parse(args):
        if not match_keys(args, 'message'):
            return None

        return args.get('message')


class Password:
    @staticmethod
    def parse(pwd):
        return pwd


class InboxMessage:

    @staticmethod
    def parse(sender_info_json):
        try:
            sender_info = json.loads(sender_info_json)
        except:
            return None

        sender_info_type = {'url': String,
                            'public_signing_key': String}

        if not check(sender_info, sender_info_type):
            return None

        return sender_info


class OutboxMessage:

    @staticmethod
    def parse(message_json):
        try:
            message = json.loads(message_json)
        except:
            return None

        message_type = {'type': String, 'receiver_public_signing_key': String,
                        'receiver_url': String, 'content': String}

        if not check(message, message_type):
            return None

        return message


class FeedOptions:

    @staticmethod
    def parse(args):

        if not (len(args) <= 1 and all([k in ['last_seen'] for k in args])):
            return None

        last_seen = [None]

        if 'last_seen' in args:
            last_seen[0] = args['last_seen']

        return last_seen


class FeedMessage:

    @staticmethod
    def parse(message_json):
        try:
            message = json.loads(message_json)
        except:
            return None

        message_type = {'type': String, 'content': String,
                        'permissions_categories': [String]}

        if not check(message, message_type):
            return None

        return message


class Subscription:

    @staticmethod
    def parse(blade_url):
        return blade_url


class PermissionsGroup:

    @staticmethod
    def parse(group_json):
        try:
            grp = json.loads(group_json)
        except:
            return None

        permissions_group_type = {'name': String,
                                  'description': String,
                                  'permissions': [String],
                                  'members': [String]}

        if not check(grp, permissions_group_type):
            return None

        return grp


class PermissionsBlade:

    @staticmethod
    def parse(blade_json):
        try:
            perms = json.loads(blade_json)
        except:
            return None

        permissions_blade_type = [String]

        if not check(perms, permissions_blade_type):
            return None

        return perms


class BladeAuthorization:

    @staticmethod
    def parse(headers):
        if not 'Authorization' in headers:
            return [None]

        auth_string = headers['Authorization']
        prefix = 'LabrysBlade '
        if auth_string[:len(prefix)] != prefix:
            return [None]

        try:
            auth_info = json.loads(auth_string[len(prefix):])
        except:
            return [None]

        auth_type = {'public_signing_key': String,
                     'dh_public_key': String,
                     'signed_dh_public_key': String}

        if not check(auth_info, auth_type):
            return [None]

        verify_key = nacl.signing.VerifyKey(bytes(auth_info['public_signing_key'], encoding='ascii'),
                                            encoder=nacl.encoding.Base64Encoder)

        client_public_signing_key = auth_info['public_signing_key']
        client_dh_public_key = base64.urlsafe_b64decode(
            bytes(auth_info['dh_public_key'], encoding='ascii'))
        client_signed_dh_public_key = base64.urlsafe_b64decode(
            bytes(auth_info['signed_dh_public_key'], encoding='ascii'))

        try:
            verify_key.verify(client_dh_public_key,
                              client_signed_dh_public_key)

        except nacl.exceptions.BadSignatureError:
            return [None]

        return [{
            'public_signing_key': auth_info['public_signing_key'],
            'dh_public_key': client_dh_public_key,
            'signed_dh_public_key': client_signed_dh_public_key
        }]
