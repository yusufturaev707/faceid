from contextlib import contextmanager

import requests
from requests.auth import HTTPDigestAuth


@contextmanager
def hikvision_session(ip_address: str, username: str, password: str):
    """Avtomatik session management"""
    session = requests.Session()
    session.auth = HTTPDigestAuth(username, password)
    try:
        yield session
    finally:
        session.close()