# Embedded file name: /home/pi/Portal/src/cfru_crc16.py


def addCRC(data):
    length = len(data)
    crc = getCRC(data, length)
    data = data + crc
    return data


def getCRC(data, length):
    crc = 65535
    poly = 33800
    for i in range(0, length):
        crc = crc ^ data[i]
        for j in range(0, 8):
            if crc & 1 == 1:
                crc = crc >> 1 ^ poly
            else:
                crc = crc >> 1

    lsb = crc & 255
    msb = crc >> 8 & 255
    crc = bytearray([lsb, msb])
    return crc


def crcOK(data):
    dlen = len(data) - 1
    try:
        crc = getCRC(data, int(data[0]) - 1)
        if crc[1] == data[dlen] and crc[0] == data[dlen - 1]:
            return True
    except IndexError:
        pass

    return False
