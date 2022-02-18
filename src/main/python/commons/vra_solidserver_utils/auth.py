"""
vra_solidserver_utils.auth
~~~~~~~~~~~~~~~~

EfficientIP SOLIDserver authentication handler

:copyright: (c) 2021 by Julia Leblond.
:license: CeCILL 2.1, see LICENSE for more details.
"""

from requests.auth import AuthBase
from base64 import b64encode

class SOLIDserverAuth(AuthBase):
    def __init__(self, username, password):
        self.b64username = b64encode(username.encode("utf-8"))
        self.b64password = b64encode(password.encode("utf-8"))

    def __eq__(self, other):
        return all([
            self.b64username == getattr(other, 'b64username', None),
            self.b64password == getattr(other, 'b64password', None)
        ])

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers['X-IPM-Username'] = self.b64username
        r.headers['X-IPM-Password'] = self.b64password
        return r
