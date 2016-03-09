# encoding: utf-8
import os
import rsa
import json

from Crypto.Cipher import AES
from Crypto import Random
from binascii import b2a_hex, a2b_hex

class AESC():
	""" aes加密 """

	def __init__(self, key):
		# key长度为16、24或32
		self.key = key
		self.mode = AES.MODE_CBC
		self.iv = '0' * AES.block_size
		self.cryptor = AES.new(self.key, self.mode, self.iv)

	def encrypt(self, text):
		""" 
		加密函数，如果text不足16位就用空格补足，
		如果超过则补足为16的倍数。
		"""

		length = AES.block_size
		count = len(text)
		padding = length - count % length
		text = text + '\0' * padding
		cipher_text = self.cryptor.encrypt(text)
		return cipher_text

	def decrypt(self, text):
		""" 解密后，去掉补足的空格 """
		plain_text = self.cryptor.decrypt(text)
		return plain_text.rstrip('\0')


class RSAC(object):
	"""rsa加密"""

	_PRIKEY = 'rsa_private_key.pem'
	_PUBKEY = 'rsa_public_key.pem'

	def __init__(self):
		""""""
		with open(self._PRIKEY, mode='rb') as private_file:
			key = private_file.read()
		self.prikey = rsa.PrivateKey.load_pkcs1(key)

		with open(self._PUBKEY, mode='rb') as public_file:
			key = public_file.read()
		self.pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(key)

	def encrypt(self, text):
		""" 加密 """
		cipher_text = rsa.encrypt(text, self.pubkey)
		return cipher_text

	def decrypt(self, cipher_text):
		""" 解密 """
		text = rsa.decrypt(cipher_text, self.prikey)
		return text


if __name__ == '__main__':
	aesc = AESC('k'*16)
	cipher_text = aesc.encrypt('i love beijing')
	print cipher_text
	print aesc.decrypt(cipher_text)

	rsac = RSAC()
	cipher_text = rsac.encrypt('i love beijing')
	print rsac.decrypt(cipher_text)


