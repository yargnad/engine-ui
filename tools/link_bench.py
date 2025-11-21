"""
link_bench.py — simple bench for the Link Protocol

This script opens a serial port (or stdin) and parses Link Protocol frames.
It validates CRC and calculates arrival jitter for `ELEMENTAL_BUS` frames.

Usage (host):
    python tools/link_bench.py --serial COM5 --rate 115200

For development you can pipe a `elemental_producer.py` script to this on a pseudo-tty.
"""

import argparse
import serial
import struct
import time
import zlib
from collections import deque

SYNC = b"\xaa\x55"

# CRC16-CCITT (0x1021) - we'll use a small tableless implementation for portability

def crc16_ccitt(data: bytes, crc: int = 0xFFFF) -> int:
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def parse_frame(ser):
    # find sync
    while True:
        b = ser.read(1)
        if not b:
            return None
        if b == b"\xaa":
            b2 = ser.read(1)
            if b2 == b"\x55":
                break
    hdr = ser.read(1+2+2+4)
    if len(hdr) < 9:
        return None
    typ = hdr[0]
    seq = struct.unpack('<H', hdr[1:3])[0]
    length = struct.unpack('<H', hdr[3:5])[0]
    ts = struct.unpack('<I', hdr[5:9])[0]
    payload = ser.read(length)
    crc_raw = ser.read(2)
    if len(crc_raw) < 2:
        return None
    crc = struct.unpack('<H', crc_raw)[0]
    crc_calc = crc16_ccitt(bytes([typ]) + hdr[1:9] + payload)
    if crc != crc_calc:
        print("CRC error: got %04x expected %04x" % (crc, crc_calc))
        return None
    return dict(typ=typ, seq=seq, length=length, ts=ts, payload=payload)


def main():
    parser = argparse.ArgumentParser(description='Link bench')
    parser.add_argument('--serial', required=True, help='Serial port (e.g., COM5, /dev/ttyACM0)')
    parser.add_argument('--baud', type=int, default=115200)
    args = parser.parse_args()

    ser = serial.Serial(args.serial, args.baud, timeout=1)

    latencies = deque(maxlen=1000)

    print('Listening on', args.serial)
    try:
        while True:
            f = parse_frame(ser)
            if f is None:
                continue
            now_ms = int(time.time() * 1000)
            if f['typ'] == 0x20 and f['length'] == 4:
                # elemental bus frame
                earth, air, water, fire = struct.unpack('<bbbb', f['payload'])
                # normalize
                e = earth / 127.0
                a = air / 127.0
                w = water / 127.0
                fi = fire / 127.0
                latency = now_ms - f['ts']
                latencies.append(latency)
                avg = sum(latencies) / len(latencies)
                print('%s seq=%d e=%.2f a=%.2f w=%.2f f=%.2f latency=%dms avg=%dms' % (
                    time.strftime('%H:%M:%S'), f['seq'], e, a, w, fi, latency, avg
                ))
    except KeyboardInterrupt:
        print('Quitting')


if __name__ == '__main__':
    main()
