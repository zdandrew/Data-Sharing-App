from flask import Flask
from flask_pymongo import PyMongo
import os, binascii

app = Flask(__name__)
app.config.from_object(__name__)

# MongoDB stuff
app.config['MONGO_URI'] = 'mongodb+srv://andrew:ace123@cluster0.aqb1j.mongodb.net/pda?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE'
mongo = PyMongo(app)

# key-related stuff
key = b'90cd2b297105ea9922b283b02ed6d9be96cdb5ba544fc0af' # binascii.hexlify(os.urandom(24))
app.secret_key = key
app.config['SECRET_KEY'] = key

# import routes
from pdaota import routes