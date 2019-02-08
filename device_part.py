# coding=utf-8

from config import *

from mkqrcode import d_qrcode


## DEVICE PART ##

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

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        return render_template()
    if request.method == 'POST':
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
            r1.hset('monitor', lockno, '-2')

            return 'success'


@app.route('/ota', methods=['GET', 'POST'])
def ota():
    if request.method == 'GET':
        return render_template('update.html')
    if request.method == 'POST':
        f = request.files['file']
        basepath = os.path.dirname(__file__)
        upload_path = os.path.join(basepath, 'static\uploads', f.filename)
        f.save(upload_path)
        return 'ok'


if __name__ == '__main__':
    app.run()
