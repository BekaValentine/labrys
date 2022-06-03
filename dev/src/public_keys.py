import base64


def encode_public_key(s):
    return str(base64.urlsafe_b64encode(bytes(s, encoding='ascii')), encoding='ascii')


def decode_public_key(s):
    return str(base64.urlsafe_b64decode(bytes(s, encoding='ascii')), encoding='ascii')
