# coding=utf-8

from config import *

from mkqrcode import d_qrcode


## WX PART ##

appid = '***REMOVED***'  # 小程序ID
secret = '***REMOVED***'

def getopenid(code):
    url = 'https://api.weixin.qq.com/sns/jscode2session?appid={}&secret={}&js_code={}&grant_type=authorization_code'.format(
        appid, secret, code)
    req = requests.post(url)
    openid = json.loads(req.text)['openid']
    # print openid
    return openid


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
        adate = data[0][2]
        randomkey = base64.b64encode(os.urandom(16))
        randompwd = base64.b64encode(os.urandom(8))
        mqtt_user = 'mqtt_user:' + randomkey
        mqtt_acl = 'mqtt_acl:' + randomkey
        Topic_all = '/' + lockno + '/#'
        Topic_morf = '/' + lockno + '/' + morf
        # Topic_ping = '/' + lockno + '/ping'
        Topic_unauth = '/unauth'

        r.hset(mqtt_user, 'password', randompwd)
        r.hmset(mqtt_acl, {Topic_all: 1, Topic_morf: 2, Topic_unauth: 2})
        # r.expire(mqtt_user, 70)
        # r.expire(mqtt_acl, 70)  # what the fuck!

        return jsonify(
            {'exists': 1, 'lockno': lockno, 'morf': morf, 'adate': adate, 'key': randomkey, 'pwd': randompwd})


# @app.route('/updatekey', methods=['POST'])
# def updatekey():
#     rdata = json.loads(request.data)
#     oldkey = rdata['oldkey']
#
#     mqtt_user = 'mqtt_user:' + oldkey
#     mqtt_acl = 'mqtt_acl:' + oldkey
#     if r.exists(mqtt_user):
#         r.expire(mqtt_user, 70)
#         r.expire(mqtt_acl, 70)
#         return '1'
#     else:
#         return '0'


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
        if (len(db.select("SELECT * FROM user2lock WHERE lockno='{}' AND morf='{}'".format(lockno, morf))) == 0):
            db.insert(
                "INSERT INTO user2lock(userno,lockno,morf,adate) VALUE ('{}','{}','{}',now())".format(openid, lockno,
                                                                                                      morf))
            return '1'
        else:
            return '2'
    else:
        return '0'


@app.route('/dellog', methods=['DELETE'])
def dellog():
    rdata = json.loads(request.data)
    openid = getopenid(rdata['code'])

    db.delete("DELETE FROM user2lock WHERE userno = '{}'".format(openid))
    return '1'


@app.route('/gethistory', methods=['GET'])
def gethistory():
    lockno = request.args['lockno']
    data = db.select("SELECT ldate,action FROM lockhistory WHERE lockno = '{}' ORDER BY ldate DESC".format(lockno))
    return jsonify(data)


if __name__ == '__main__':
    app.run()
