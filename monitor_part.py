# coding=utf-8

from config import *

from flask_mqtt import Mqtt

randompwd = base64.b64encode(os.urandom(16))
r.hset('mqtt_user:monitor', 'password', randompwd)

app.config['MQTT_BROKER_URL'] = 'myemqx'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'monitor'
app.config['MQTT_PASSWORD'] = randompwd
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds
mqtt = Mqtt(app)

## MONITOR PART ##

def pushhistory(lockno, action):
    db.insert("INSERT INTO lockhistory(lockno,ldate,action) VALUE ('{}',now(),'{}')".format(lockno, action))


# def topic_sys(topic_part):
#     clientid = topic_part[-2]
#     connectstatu = topic_part[-1]
#
#     if (len(clientid) == 11) & (connectstatu == 'disconnected'):
#         pubtopic = '/' + clientid + '/statu'
#         mqtt.publish(pubtopic, '-2')


def topic_common(topic_part, payload):
    if len(topic_part[1]) == 11:
        lockno = topic_part[1]
        command = topic_part[2]
        # if command == 'ping':
        #     topic_ping(lockno)
        if command == 'm':
            topic_m(lockno)
        if command == 'f':
            topic_f(lockno)
        if command == 'statu':
            topic_statu(lockno, payload)
    else:
        if topic_part[1] == 'unauth':
            mqtt_user = 'mqtt_user:' + payload
            mqtt_acl = 'mqtt_acl:' + payload
            r.delete(mqtt_user)
            r.delete(mqtt_acl)


def topic_statu(lockno, nowstatu):
    laststatu = r1.hget('monitor', lockno)
    if nowstatu != laststatu:
        r1.hset('monitor', lockno, nowstatu)
        if laststatu == '-2':
            pushhistory(lockno, '设备上线')
            return None
        if nowstatu == '-2':
            pushhistory(lockno, '设备离线')
            return None
        if nowstatu == '1':
            pushhistory(lockno, '上锁')
            return None
        if nowstatu == '0':
            pushhistory(lockno, '开锁')
            return None


# def topic_ping(lockno):
#     req = requests.get('http://172.20.0.145:8080/api/v3/connections/' + lockno,
#                        auth=('42b31862dac81', 'Mjg0MjYxNDY5MDE1MDEwNDEwMDcxNTIzMzcxMDUzMjE5ODE'))
#     # print json.loads(req.text)
#     if len(json.loads(req.text)) == 0:
#         pubtopic = '/' + lockno + '/statu'
#         mqtt.publish(pubtopic, '-2')
#     else:
#         pubtopic = '/' + lockno + '/call'
#         mqtt.publish(pubtopic, 'export')


def topic_m(lockno):
    if r1.exists(lockno + '_f'):
        r1.delete(lockno + '_f')
        pubtopic = '/' + lockno + '/call'
        mqtt.publish(pubtopic, 'unlock')
    else:
        r1.set(lockno + '_m', 1, ex=35)


def topic_f(lockno):
    if r1.exists(lockno + '_m'):
        r1.delete(lockno + '_m')
        pubtopic = '/' + lockno + '/call'
        mqtt.publish(pubtopic, 'unlock')
    else:
        r1.set(lockno + '_f', 1, ex=35)


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    # mqtt.subscribe('$SYS/brokers/emqx@127.0.0.1/clients/#')
    mqtt.subscribe('/#')


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode()

    topic_part = topic.split('/')
    # if topic_part[0] == '$SYS':
    #     topic_sys(topic_part)
    # if topic_part[0] == '':
    #     topic_common(topic_part, payload)
    topic_common(topic_part, payload)


if __name__ == '__main__':
    app.run()
