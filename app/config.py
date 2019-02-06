import os
AMQP_HOST = os.getenv('AMQP_HOST', '127.0.0.1')
AMQP_PORT = os.getenv('AMQP_PORT', 5672)
AMQP_VIRTUAL_HOST = os.getenv('AMQP_VIRTUAL_HOST', '/')
AMQP_USER = os.getenv('AMQP_USER', 'normal')
AMQP_PASSWORD = os.getenv('AMQP_PASSWORD', 'normal')
DBURI = os.getenv('DBURI', 'mongodb://zippyttech:123456@127.0.0.1:27017/')
DBNAME = os.getenv('DBNAME', 'rfid')
