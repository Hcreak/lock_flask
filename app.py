# coding=utf-8

from flask import *
import redis
import os
import time
import base64

from olimysql import olimysql
from config import *
from mkqrcode import d_qrcode

import requests
from flask_mqtt import Mqtt

app = Flask(__name__)
app.debug = True

app.config['MQTT_BROKER_URL'] = '172.20.0.145'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'user'
app.config['MQTT_PASSWORD'] = 'pwd'
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds
mqtt = Mqtt(app)

# keys config
###############
# app.secret_key = os.urandom(16)
# randomkey = os.urandom(48)

# mysql config
###############
db = olimysql("172.20.0.145", "***REMOVED***", "***REMOVED***", "lockdata")

# redis config
###############
pool = redis.ConnectionPool(host='172.20.0.145', port=6379, decode_responses=True)
r = redis.Redis(connection_pool=pool)


## LOCK PART ##

# @app.route('/lockport', methods=['POST'])
# def lockport():
#     rdata = json.loads(request.data)
#     lockno = rdata['lockno']
#     ls = rdata['statu']
#     lc = rdata['charge']
#
#     if not r.exists(lockno):
#         r.hmset(lockno, {'statu': ls, 'charge': lc})
#     else:
#         rs, rc = r.hmget(lockno, 'statu', 'charge')
#         if ls != rs:
#             r.hset(lockno, 'statu', ls)
#         if lc != rc:
#             r.hset(lockno, 'charge', lc)
#
#     for i in range(5):
#         if r.exists(lockno + '_m') and r.exists(lockno + '_f'):
#             r.delete(lockno + '_m')
#             r.delete(lockno + '_f')
#             return 'unlock'
#         if i == 4:
#             return 'ok'
#         time.sleep(0.5)

@app.route('/locksignup', methods=['POST'])
def locksignup():
    rdata = json.loads(request.data)
    lockno = rdata['lockno']
    lpassword = rdata['lpassword']

    if r.exists(lockno):
        return 'exists'

    else:
        mqtt_user = 'mqtt_user:' + lockno
        mqtt_acl = 'mqtt_acl:' + lockno
        Topic_all = '/' + lockno + '/#'
        Topic_statu = '/' + lockno + '/statu'
        Topic_charge = '/' + lockno + '/charge'

        r.hset(mqtt_user, 'password', lpassword)
        r.hmset(mqtt_acl, {Topic_all: 1, Topic_statu: 2, Topic_charge: 2})

        return 'success'


## WX PART ##

@app.route('/login', methods=['POST'])
def login():
    rdata = json.loads(request.data)
    openid = getopenid(rdata['code'])
    print openid

    data = db.select("SELECT lockno,morf,adate FROM user2lock WHERE userno='{}'".format(openid))
    if len(data) == 0:
        return jsonify({'exists': 0})
    else:
        print data[0]
        lockno = data[0][0]
        morf = data[0][1]
        adate = data[0][2].strftime("%Y/%m/%d")
        randomkey = base64.b64encode(os.urandom(16))
        randompwd = base64.b64encode(os.urandom(8))
        mqtt_user = 'mqtt_user:' + randomkey
        mqtt_acl = 'mqtt_acl:' + randomkey
        Topic_all = '/' + lockno + '/#'
        Topic_morf = '/' + lockno + '/' + morf
        Topic_ping = '/' + lockno + '/ping'

        r.hset(mqtt_user, 'password', randompwd)
        r.hmset(mqtt_acl, {Topic_all: 1, Topic_morf: 2, Topic_ping: 2})
        r.expire(mqtt_user, 70)
        r.expire(mqtt_acl, 70)  # what the fuck!

        return jsonify(
            {'exists': 1, 'lockno': lockno, 'morf': morf, 'adate': adate, 'key': randomkey, 'pwd': randompwd})


@app.route('/updatekey', methods=['POST'])
def updatekey():
    rdata = json.loads(request.data)
    oldkey = rdata['oldkey']

    mqtt_user = 'mqtt_user:' + oldkey
    mqtt_acl = 'mqtt_acl:' + oldkey
    if r.exists(mqtt_user):
        r.expire(mqtt_user, 70)
        r.expire(mqtt_acl, 70)
        return '1'
    else:
        return '0'


@app.route('/logup', methods=['POST'])
def logup():
    rdata = json.loads(request.data)
    openid = getopenid(rdata['code'])
    qrcode = rdata['qrcode']
    # print len(qrcode)

    relust = d_qrcode(qrcode)
    print relust
    if len(relust) == 2:
        lockno = relust[0]
        morf = relust[1]
        db.insert(
            "INSERT INTO user2lock(userno,lockno,morf,adate) VALUE ('{}','{}','{}',now())".format(openid, lockno, morf))
        return '1'
    else:
        return '0'


@app.route('/dellog', methods=['DELETE'])
def dellog():
    pass


@app.route('/gethistory', methods=['GET'])
def gethistory():
    lockno = request.args['lockno']
    data = db.select("SELECT ldate,action FROM lockhistory WHERE lockno = '{}' ORDER BY ldate DESC".format(lockno))
    return jsonify(data)


## MQTT PART ##

def pushhistory(lockno, action):
    db.insert("INSERT INTO lockhistory(lockno,ldate,action) VALUE ('{}',now(),'{}')".format(lockno, action))


def topic_sys(topic_part):
    clientid = topic_part[-2]
    connectstatu = topic_part[-1]

    if (len(clientid) == 11) & (connectstatu == 'disconnected'):
        pubtopic = '/' + clientid + '/statu'
        mqtt.publish(pubtopic, '-2')


def topic_common(topic_part, payload):
    if len(topic_part[1]) == 11:
        lockno = topic_part[1]
        command = topic_part[2]
        if command == 'ping':
            topic_ping(lockno)
        if command == 'm':
            topic_m(lockno)
        if command == 'f':
            topic_f(lockno)


def topic_ping(lockno):
    req = requests.get('http://172.20.0.145:8080/api/v3/connections/' + lockno,
                       auth=('42b31862dac81', 'Mjg0MjYxNDY5MDE1MDEwNDEwMDcxNTIzMzcxMDUzMjE5ODE'))
    # print json.loads(req.text)
    if len(json.loads(req.text)) == 0:
        pubtopic = '/' + lockno + '/statu'
        mqtt.publish(pubtopic, '-2')
    else:
        pubtopic = '/' + lockno + '/call'
        mqtt.publish(pubtopic, 'export')


def topic_m(lockno):
    if r.exists(lockno + '_f'):
        r.delete(lockno + '_f')
        pubtopic = '/' + lockno + '/call'
        mqtt.publish(pubtopic, 'unlock')
    else:
        r.set(lockno + '_m', 1, ex=35)


def topic_f(lockno):
    if r.exists(lockno + '_m'):
        r.delete(lockno + '_m')
        pubtopic = '/' + lockno + '/call'
        mqtt.publish(pubtopic, 'unlock')
    else:
        r.set(lockno + '_f', 1, ex=35)


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('$SYS/brokers/emqx@127.0.0.1/clients/#')
    mqtt.subscribe('/#')


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode()

    topic_part = topic.split('/')
    if topic_part[0] == '$SYS':
        topic_sys(topic_part)
    if topic_part[0] == '':
        topic_common(topic_part, payload)


if __name__ == '__main__':
    app.run()
