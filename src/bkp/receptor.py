import pika
import json
from threading import Thread
from mensagens_robo import MsgSStoSR, MsgSRtoSS, ErroMsgSStoSR
from interface import *
import sys

class Receptor(Thread):
	"""Recebe e trata mensagens do SS"""

	def __init__(self, host):
		super(Receptor, self).__init__()
		credenciais = pika.PlainCredentials('robot', 'maker')
		self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=str(host), credentials=credenciais))
		self.channel = self.connection.channel()
		self.channel.queue_declare(queue='SS_to_SR')
		self.channel.basic_consume(self.trata_msg_recebida, queue='SS_to_SR', no_ack=True)

	def trata_msg_recebida(self, ch, method, properties, body):
		global shared_obj

		try:
			msg = json.loads(body.decode())
		except Exception as e:
			print(str(e))
			return

		if 'cmd' not in msg:
			return

		shared_obj.set(SharedObj.InterfaceEventMsg, msg)
		shared_obj.set_event(SharedObj.InterfaceEvent)

	def run(self):
		self.channel.start_consuming()