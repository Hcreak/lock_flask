# coding=utf-8
import requests
import json

appid = '***REMOVED***'  # 小程序ID
secret = '***REMOVED***'


def getopenid(code):
    url = 'https://api.weixin.qq.com/sns/jscode2session?appid={}&secret={}&js_code={}&grant_type=authorization_code'.format(
        appid, secret, code)
    req = requests.post(url)
    openid = json.loads(req.text)['openid']
    # print openid
    return openid
