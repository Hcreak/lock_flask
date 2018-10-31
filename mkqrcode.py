# coding=utf-8

import qrcode
from PIL import Image
import os
import requests


from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

import shortuuid

key_M = '***REMOVED***'
key_F = '***REMOVED***'
server_host = 'http://127.0.0.1'


class prpcrypt():
    def __init__(self, key):
        self.key = key
        self.mode = AES.MODE_CBC

    # 加密函数，如果text不是16的倍数【加密文本text必须为16的倍数！】，那就补足为16的倍数
    def encrypt(self, text):
        cryptor = AES.new(self.key, self.mode, self.key)
        # 这里密钥key 长度必须为16（AES-128）、24（AES-192）、或32（AES-256）Bytes 长度.目前AES-128足够用
        length = 16
        count = len(text)
        add = length - (count % length)
        text = text + ('\0' * add)
        self.ciphertext = cryptor.encrypt(text)
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        return b2a_hex(self.ciphertext)

    # 解密后，去掉补足的空格用strip() 去掉
    def decrypt(self, text):
        cryptor = AES.new(self.key, self.mode, self.key)
        plain_text = cryptor.decrypt(a2b_hex(text))
        return plain_text.rstrip('\0')


pc_M = prpcrypt(key_M)  # 初始化密钥
pc_F = prpcrypt(key_F)


def p_qrcode(lockno):
    e_M = pc_M.encrypt(lockno)
    e_F = pc_F.encrypt(lockno)
    print e_F, e_M

    img_M = qrcode.make(e_M + 'm')
    img_F = qrcode.make(e_F + 'f')

    print d_qrcode(e_M + 'm')
    print d_qrcode(e_F + 'f')

    lpassword = ''
    url = server_host + '/locksignup?lockno={}&lpassword={}'.format(lockno, lpassword)
    req = requests.post(url)
    if req.text == 'success':

        # esp8266 spiffs

        if not os.path.exists(lockno):
            os.mkdir(lockno)

        img_M.save(lockno + '/' + lockno + '_M.jpg')
        img_F.save(lockno + '/' + lockno + '_F.jpg')


def d_qrcode(code):
    if len(code) == 33:
        if code[-1] == 'm':
            d = pc_M.decrypt(code[:-1])
            return d, 'm'
        if code[-1] == 'f':
            d = pc_F.decrypt(code[:-1])
            return d, 'f'

    return 'error'


if __name__ == '__main__':
    newno = shortuuid.ShortUUID().random(length=11)
    print newno

    p_qrcode(newno)

    # print '924810c98a233ddfbf3645ccd3ea9f14'[:-1]

    # d = pc.decrypt(e)
