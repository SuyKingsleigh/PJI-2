import pika
import json
from threading import Thread, Event
from shared import *

class Transmissor(Thread):
	"""docstring for TransmissoSR"""

	def __init__(self, host):
		super(Transmissor, self).__init__()
		credenciais = pika.PlainCredentials('robot', 'maker')
		self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=str(host), credentials=credenciais))
		self.channel = self.connection.channel()
		self.channel.queue_declare(queue='SR_to_SS')


	def run(self):
		global shared_obj

		while True:
			# Espera ate ter uma mensagem a transmitir
			shared_obj.wait_event(SharedObj.TransmitirEvent)

			# Bloqueia enquanto a mensagem e enviada
			shared_obj.acquire(SharedObj.TransmitirLock)
			msg = shared_obj.get_directly(SharedObj.TransmitirLock)

			try:
				msg = json.dumps(msg)
				self.channel.basic_publish(exchange='', routing_key='SR_to_SS', body=msg)
			except Exception as e:
				print(str(e))
				pass

			shared_obj.clear_event(SharedObj.TransmitirEvent)
			shared_obj.release(SharedObj.TransmitirLock)

		self.connection.close()