"""Bounded PNG decoder for 8-bit, non-interlaced RGB/RGBA evidence frames."""
import hashlib
from pathlib import Path
import struct
import zlib

SIGNATURE = b'\x89PNG\r\n\x1a\n'
MAX_PIXELS = 16_777_216
MAX_FILE_BYTES = 80 * 1024 * 1024


def decode_frame(path: Path):
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError('PNG exceeds file size limit')
    data = path.read_bytes()
    if not data.startswith(SIGNATURE):
        raise ValueError('invalid PNG signature')
    offset, header, ended, idat_ended = 8, None, False, False
    compressed = bytearray()
    seen_idat = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('truncated PNG chunk')
        length = struct.unpack_from('>I', data, offset)[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError('truncated PNG payload')
        kind = data[offset+4:offset+8]
        payload = data[offset+8:end-4]
        crc = struct.unpack_from('>I', data, end-4)[0]
        if zlib.crc32(kind + payload) != crc:
            raise ValueError('corrupt PNG chunk CRC')
        if header is None and kind != b'IHDR':
            raise ValueError('PNG must begin with IHDR')
        if kind == b'IHDR':
            if header is not None or length != 13:
                raise ValueError('invalid or repeated IHDR')
            width, height, bits, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', payload)
            if not width or not height or width * height > MAX_PIXELS:
                raise ValueError('PNG exceeds decoded pixel limit')
            if bits != 8 or color not in (2, 6) or compression or filtering or interlace:
                raise ValueError('evidence requires non-interlaced 8-bit RGB/RGBA PNG')
            header = (width, height, 3 if color == 2 else 4)
        elif kind == b'IDAT':
            if idat_ended:
                raise ValueError('PNG IDAT chunks must be consecutive')
            seen_idat = True
            compressed.extend(payload)
        elif kind == b'IEND':
            if length or not seen_idat or end != len(data):
                raise ValueError('invalid PNG end or trailing data')
            ended = True
            break
        else:
            if seen_idat:
                idat_ended = True
            if kind in (b'tRNS', b'acTL', b'fcTL', b'fdAT'):
                raise ValueError('normalize transparency/animation to a single RGBA frame')
            if kind == b'PLTE':
                if seen_idat or not length or length % 3 or length > 768:
                    raise ValueError('invalid PNG palette')
            elif not (kind[0] & 32):
                raise ValueError('unknown critical PNG chunk')
        offset = end
    if header is None or not ended:
        raise ValueError('incomplete PNG: IHDR, IDAT and IEND required')
    width, height, bpp = header
    stride = width * bpp
    expected = height * (stride + 1)
    decoder = zlib.decompressobj()
    raw = decoder.decompress(compressed, expected + 1)
    if len(raw) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('invalid or oversized PNG compressed stream')
    digest = hashlib.sha256(struct.pack('>II', width, height))
    previous = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        filt = raw[start]
        if filt > 4:
            raise ValueError('invalid PNG row filter')
        row = bytearray(raw[start+1:start+1+stride])
        if filt:
            for i in range(stride):
                left = row[i-bpp] if i >= bpp else 0
                up = previous[i]
                corner = previous[i-bpp] if i >= bpp else 0
                if filt == 1:
                    predictor = left
                elif filt == 2:
                    predictor = up
                elif filt == 3:
                    predictor = (left+up)//2
                else:
                    p = left+up-corner
                    a, b, c = abs(p-left), abs(p-up), abs(p-corner)
                    predictor = left if a <= b and a <= c else up if b <= c else corner
                row[i] = (row[i]+predictor) & 255
        previous = row
        rgba = bytearray(width * 4)
        rgba[0::4], rgba[1::4], rgba[2::4] = row[0::bpp], row[1::bpp], row[2::bpp]
        rgba[3::4] = row[3::4] if bpp == 4 else b'\xff' * width
        # Invisible RGB does not make a distinct rendered frame.
        if bpp == 4:
            for x in range(width):
                if rgba[x*4+3] == 0:
                    rgba[x*4:x*4+3] = b'\0\0\0'
        digest.update(rgba)
    return width, height, digest.hexdigest()
