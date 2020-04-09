import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet
import json
import nacl


def encrypted_client_request(private_signing_key_file, public_signing_key_file, server_public_signing_key, req_func, *args, **kwargs):

    # ##### DH Session Setup ###################################################

    dh_private_key = ec.generate_private_key(
        ec.SECP384R1(), default_backend())

    dh_public_key = dh_private_key.public_key()

    serialized_dh_public_key = dh_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)

    with open(private_signing_key_file, 'r') as f:
        signing_key = nacl.signing.SigningKey(f.read().encode(
            encoding='ascii'), encoder=nacl.encoding.Base64Encoder)
        signed_serialized_dh_public_key = signing_key.sign(
            serialized_dh_public_key).signature

    # ##### DH Auth Header Info ################################################

    with open(public_signing_key_file, 'r') as f:
        public_signing_key = f.read().strip()

    authorization_header = {'Authorization': 'LabrysBlade ' + json.dumps({
        'public_signing_key': public_signing_key,
        'dh_public_key': str(base64.urlsafe_b64encode(serialized_dh_public_key), encoding='ascii'),
        'signed_dh_public_key': str(base64.urlsafe_b64encode(signed_serialized_dh_public_key), encoding='ascii')})}

    # ##### Request ############################################################

    if 'headers' in kwargs:
        kwargs['headers'] = {**kwargs['headers'], **authorization_header}
    else:
        kwargs['headers'] = authorization_header

    resp = req_func(*args, **kwargs)

    if resp.status_code != 200:
        return None

    resp_data = resp.json()

    if 'encryption_info' not in resp_data:
        return None

    # ##### DH Decryption ######################################################

    if 'encryption_info' not in resp_data or 'encrypted_content' not in resp_data:
        return None

    server_public_signing_key = bytes(
        server_public_signing_key, encoding='ascii')
    server_dh_public_key = base64.urlsafe_b64decode(
        bytes(resp_data['encryption_info']['dh_public_key'], encoding='ascii'))
    server_signed_dh_public_key = base64.urlsafe_b64decode(
        bytes(resp_data['encryption_info']['signed_dh_public_key'], encoding='ascii'))

    verify_key = nacl.signing.VerifyKey(server_public_signing_key,
                                        encoder=nacl.encoding.Base64Encoder)

    try:
        verify_key.verify(server_dh_public_key,
                          server_signed_dh_public_key)
    except nacl.exceptions.BadSignatureError:
        return None

    loaded_server_public_key = serialization.load_pem_public_key(
        server_dh_public_key,
        backend=default_backend())

    shared_key = dh_private_key.exchange(
        ec.ECDH(), loaded_server_public_key)

    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'handshake data',
        backend=default_backend()).derive(shared_key)

    fernet_key = base64.urlsafe_b64encode(derived_key)

    decrypted_content = str(Fernet(fernet_key).decrypt(
        base64.urlsafe_b64decode(bytes(resp_data['encrypted_content'], encoding='ascii'))), encoding='ascii')

    return decrypted_content


def encrypt_server_response(private_signing_key_file, public_signing_key_file, client_authorization, message):

    with open(private_signing_key_file, 'r') as f:
        private_signing_key = nacl.signing.SigningKey(f.read().encode(
            encoding='ascii'), encoder=nacl.encoding.Base64Encoder)

    with open(public_signing_key_file, 'r') as f:
        public_signing_key = f.read().strip()

    server_private_key = ec.generate_private_key(
        ec.SECP384R1(), default_backend())

    loaded_client_public_key = serialization.load_pem_public_key(
        client_authorization['dh_public_key'],
        backend=default_backend())

    shared_key = server_private_key.exchange(
        ec.ECDH(), loaded_client_public_key)

    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'handshake data',
        backend=default_backend()).derive(shared_key)

    server_public_key = server_private_key.public_key()
    serialized_server_public_key = server_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)

    signed_serialized_server_public_key = private_signing_key.sign(
        serialized_server_public_key).signature

    fernet_key = base64.urlsafe_b64encode(derived_key)

    encrypted_message = str(base64.urlsafe_b64encode(
        Fernet(fernet_key).encrypt(
            bytes(message, encoding='ascii'))), encoding='ascii')

    return {
        'encryption_info': {
            'public_signing_key': public_signing_key,
            'dh_public_key': str(base64.urlsafe_b64encode(
                serialized_server_public_key), encoding='ascii'),
            'signed_dh_public_key': str(base64.urlsafe_b64encode(
                signed_serialized_server_public_key), encoding='ascii')
        },
        'encrypted_content': encrypted_message
    }
