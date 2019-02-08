# coding=utf-8

import requests
import json
import redis
import os
# import time
import base64

from olimysql import olimysql

from flask import *

app = Flask(__name__)
app.debug = True

# keys config
###############
# app.secret_key = os.urandom(16)
# randomkey = os.urandom(48)

# mysql config
###############
db = olimysql("mydb", "***REMOVED***", "***REMOVED***", "lockdata")

# redis config
###############
pool0 = redis.ConnectionPool(host='myredis', port=6379, decode_responses=True, db=0)
r0 = redis.Redis(connection_pool=pool0)
pool1 = redis.ConnectionPool(host='myredis', port=6379, decode_responses=True, db=1)
r1 = redis.Redis(connection_pool=pool1)
r = r0

