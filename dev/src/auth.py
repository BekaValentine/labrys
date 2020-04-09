from flask import session
import functools


def require_authentication(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' in session:
            return f(*args, **kwargs)
        else:
            return 'unauthorized', 401

    return decorated_function
