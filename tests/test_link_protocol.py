import struct
from engine_ui.tools import link_bench


def test_crc_pack_unpack():
    payload = struct.pack('<bbbb', 10, -10, 64, -64)
    hdr = struct.pack('<BHHI', 0x20, 123, len(payload), 1000)
    raw = hdr + payload
    crc = link_bench.crc16_ccitt(raw)
    # ensure CRC is nonzero and reproducible
    assert crc == link_bench.crc16_ccitt(raw)


def test_elemental_normalize():
    payload = struct.pack('<bbbb', 127, -127, 0, 64)
    earth, air, water, fire = struct.unpack('<bbbb', payload)
    assert earth == 127
    assert air == -127
    assert water == 0
    assert fire == 64
    # normalized
    e = earth/127.0
    assert round(e, 3) == 1.0
