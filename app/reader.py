import socket
import cfru_crc16
import json
import sys


class Reader:
    # CONFIGURATION CONSTANTS
    DEFAULT_ADDRESS = 0
    GET_WORK_MODE = 54
    SET_WORK_MODE = 53
    SET_SCAN_TIME = 37
    SET_POWER = 47
    INVENTORY_TAGS = 1
    TAG_SIZE_IN_BYTES = 12

    def __init__(self, conf, broker):
        self.conf = conf
        self.started = False
        self.socket = None
        self.thread = None
        self.broker = broker
        self.connected = False

    def set_conf(self, conf):
        self.conf = conf

    def start(self):
        self.socket = socket.socket()
        self.try_connect()

    def try_connect(self):
        try:
            self.socket.settimeout(self.conf['timeout'])
            self.socket.connect((self.conf['ip'], self.conf['port']))
            self.connected = True
            self.started = True
        except socket.error:
            print('exception in connect, reader.py')
            sys.exit(1)

    def inventory_tags(self):
        self.start()
        self.try_connect()
        tags = []
        command = self._make_command(byte_length=4,
                                     address=self.DEFAULT_ADDRESS,
                                     command_code=self.INVENTORY_TAGS,
                                     extra_params=None)

        tries = self.conf['tries'] if self.conf['tries'] >= 1 else 1
        for x in range(1, tries):
            try:
                self.socket.send(command)
            except ConnectionResetError:
                print('connection reset error')
                self.socket = socket.socket()
                self.try_connect()
                self.socket.send(command)
            some_tags = self.build_inventory()
            if some_tags:
                tags += some_tags

        tags = set(tags)
        tags = list(tags)
        if 'e20000162614008519504c17' in tags:
            tags.remove('e20000162614008519504c17')
        if tags:
            batch = {
                'group': self.conf['group'],
                'isActivator': self.conf['isActivator'],
                'name': self.conf['name'],
                'tags': tags
            }

            json_tags = json.dumps(batch)

            self.broker.send(json_tags)
            self.socket.close()
        return tags

    @staticmethod
    def _make_command(byte_length, address, command_code, extra_params=None):
        temp_command = bytearray([byte_length, address, command_code])
        if extra_params:
            for param in extra_params:
                temp_command.append(param)
        return cfru_crc16.addCRC(temp_command)

    def build_inventory(self):
        try:
            first_byte = bytearray(self.socket.recv(1))
            if not len(first_byte):
                print('Failed to read length byte')
                return None
            bytes_to_read_total = int(first_byte[0])
            tries = 3
            remaining_bytes = bytearray([])

            while tries > 0:
                bytes_to_read = bytes_to_read_total - len(remaining_bytes)
                tries = tries - 1
                received_bytes = bytearray(self.socket.recv(bytes_to_read))
                if len(received_bytes):
                    remaining_bytes += received_bytes
                if len(remaining_bytes) >= bytes_to_read_total:
                    break

            data = first_byte + remaining_bytes

            if len(data) != (bytes_to_read_total + 1):
                print('Expected %d bytes but got %d bytes' %
                                (bytes_to_read_total + 1, len(data)))
                return None
            if cfru_crc16.crcOK(data):
                data = data[:-2]
                return self._parse_tag_list(data)
            else:
                print('CRC Check failed')

        except socket.error as message:
            print('Socket exception: %s', message)
            self.socket = socket.socket()
            self.try_connect()
        except IOError as message:
            print('IO Exception')
            sys.exit(1)

        return None

    def _parse_tag_list(self, data):
        tags = []
        tag_data = bytearray([])
        if data[3] == 1:
            tag_count = data[4]
            if not tag_count:
                return tags
            tag_byte_found = False
            tag_byte_count = 0
            for x in data[5:]:
                if not tag_byte_found and x == 12:
                    tag_byte_found = True
                    tag_data = bytearray([])
                    tag_byte_count = 0
                    continue
                if tag_byte_found:
                    tag_data.append(x)
                    tag_byte_count += 1
                    if tag_byte_count == self.TAG_SIZE_IN_BYTES:
                        tags.append(''.join(('{:02x}'.format(y) for y in tag_data)))
                        tag_byte_found = False
        return tags
