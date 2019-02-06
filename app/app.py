from pymongo import MongoClient
from reader import Reader
from blinker import signal
from broker import Broker
import time
import config


class Manager:
    def __init__(self):
        self.client = MongoClient(config.DBURI + config.DBNAME)
        self.db = self.client[config.DBNAME]
        self.active_readers = dict()
        self.broker = Broker()
        self.no_exception = True
        self.stopped = False

        signal('reader_updated').connect(self.update_readers)

    def update_readers(self, sender, **kwargs):
        antenna = self.db['antennas'].find_one({'name': kwargs['name']})
        if antenna['name'] in self.active_readers:
            self.active_readers[antenna['name']].set_conf(antenna)
        else:
            reader = Reader(antenna, self.broker)
            self.active_readers[antenna['name']] = reader

    def start(self):
        for antenna in self.db['antennas'].find():
            if antenna['enabled']:
                reader = Reader(antenna, self.broker)
                self.active_readers[antenna['name']] = reader
        while not self.stopped:
            time.sleep(0.1)
            for key, r in self.active_readers.items():
                if r.conf['enabled']:
                    r.inventory_tags()


manager = Manager()
try:
    manager.start()
except KeyboardInterrupt:
    manager.stopped = True
    manager.broker.conn_data.connection.close()
