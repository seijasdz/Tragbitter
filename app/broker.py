import pika
from pika.exceptions import ConnectionClosed
import threading
import config
from blinker import signal
import time
import sys


class ConnectionData:
    def __init__(self):
        while True:
            try:
                credentials = pika.PlainCredentials(config.AMQP_USER, config.AMQP_PASSWORD)
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(config.AMQP_HOST,
                                                                                    config.AMQP_PORT,
                                                                                    config.AMQP_VIRTUAL_HOST,
                                                                                    credentials))
                self.channel = self.connection.channel()
                self.channel.exchange_declare(exchange='antenna_event',
                                              exchange_type='topic')
                break
            except ConnectionClosed:
                time.sleep(1)
                print('connection retry')


class Broker:
    def __init__(self):
        self.conn_data = ConnectionData()

    def send(self, json):
        while True:
            try:
                self.conn_data.channel.basic_publish(exchange='antenna_event',
                                                     routing_key='antenna.tag.read',
                                                     body=json)
                break
            except ConnectionClosed:
                self.conn_data = ConnectionData()


def to_wait():
    while True:
        try:
            print('trying to connect, hilo 2')
            credentials = pika.PlainCredentials(config.AMQP_USER, config.AMQP_PASSWORD)
            conn2 = pika.BlockingConnection(pika.ConnectionParameters(config.AMQP_HOST,
                                                                      config.AMQP_PORT,
                                                                      config.AMQP_VIRTUAL_HOST,
                                                                      credentials))
            print('connected, in wait, hilo 2')
            break
        except ConnectionClosed:
            time.sleep(1)
            print('Exception in wait, connecting, hilo 2')

    channel = conn2.channel()
    queue_created_declaration = channel.queue_declare(exclusive=True)
    queue_created = queue_created_declaration.method.queue
    channel.exchange_declare(exchange='antenna_event',
                             exchange_type='topic')

    channel.queue_bind(exchange='antenna_event',
                       queue=queue_created,
                       routing_key='antenna.created')

    def on_created(ch, method, properties, body):
        print('%r:%r' % (method.routing_key, body.decode('utf-8')))

    channel.basic_consume(on_created,
                          queue=queue_created,
                          no_ack=True)

    q_updated_dec = channel.queue_declare(exclusive=True)
    q_updated = q_updated_dec.method.queue
    channel.queue_bind(exchange='antenna_event',
                       queue=q_updated,
                       routing_key='antenna.updated')

    def on_updated(ch, method, properties, body):
        updated = body.decode('utf-8')
        signal('reader_updated').send(None, name=updated)

    channel.basic_consume(on_updated,
                          queue=q_updated,
                          no_ack=True)

    channel.start_consuming()


thread = threading.Thread(target=to_wait, daemon=True)
thread.start()
