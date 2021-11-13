from pdaota import app, mongo
from pdaota.lib import *
# more imports here

# Geshi, please import any encryption stuff to this file

# Get authentication token
def get_auth_token(site_email, expires_sec=3600):
    s = Serializer(app.config['SECRET_KEY'], expires_sec)
    return s.dumps({'site_id': site_email}).decode('UTF-8')