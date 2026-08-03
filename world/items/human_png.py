"""Minimal PNG read/write in numpy + zlib. No PIL, no imageio, no dependency.

Neither PIL nor imageio exists in this box's python3 OR in Blender 5.2's bundled
interpreter, checked. Every pixel measurement on this project therefore either
runs inside a Blender image datablock or does this. Doing it here means
`human_fabric_probe` and the crop tool run under plain `python3` with nothing
installed, which is the difference between a measurement anyone can re-run and
one that needs an environment.

Supports what Cycles writes: 8- and 16-bit, greyscale / RGB / RGBA, non-
interlaced. Refuses anything else by name rather than returning something
plausible.
"""

import struct
import zlib

import numpy as np


def read(path):
    """PNG -> (H, W, C) uint8 or uint16 array.

    Inside Blender this hands the job to `bpy.data.images.load`, which is C and
    takes about a second on a 4K frame; the pure-python path below takes about a
    minute on the same file because PNG's Paeth filter is sequential per byte by
    definition. Both produce the same array -- `--selftest` compares them.
    """
    if _bpy is not None:
        return _read_bpy(path)
    return _read_py(path)


try:
    import bpy as _bpy
except ImportError:
    _bpy = None


def _read_bpy(path):
    img = _bpy.data.images.load(path, check_existing=False)
    try:
        w, h = img.size
        nch = img.channels
        a = np.empty(w * h * nch, np.float32)
        img.pixels.foreach_get(a)
        a = a.reshape(h, w, nch)[::-1]              # bpy is bottom-up
        if img.colorspace_settings.name in ("sRGB", "Filmic sRGB"):
            # foreach_get returns LINEAR for an sRGB-tagged file; put it back so
            # the two readers agree byte for byte.
            lin = a[..., :3]
            a = a.copy()
            a[..., :3] = np.where(lin <= 0.0031308, lin * 12.92,
                                  1.055 * np.maximum(lin, 0) ** (1 / 2.4) - 0.055)
        return np.clip(a * 255.0 + 0.5, 0, 255).astype(np.uint8)
    finally:
        _bpy.data.images.remove(img)


def _read_py(path):
    raw = open(path, "rb").read()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("%s is not a PNG (bad signature)" % path)
    pos = 8
    idat = []
    w = h = depth = ctype = None
    inter = 0
    while pos < len(raw):
        ln = struct.unpack(">I", raw[pos:pos + 4])[0]
        typ = raw[pos + 4:pos + 8]
        data = raw[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", data)
        elif typ == b"IDAT":
            idat.append(data)
        elif typ == b"IEND":
            break
    if inter:
        raise ValueError("interlaced PNG not supported: %s" % path)
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if nch is None or ctype == 3:
        raise ValueError("colour type %d (palette?) not supported: %s"
                         % (ctype, path))
    if depth not in (8, 16):
        raise ValueError("bit depth %d not supported: %s" % (depth, path))
    bpp = nch * depth // 8
    buf = np.frombuffer(zlib.decompress(b"".join(idat)), np.uint8)
    stride = w * bpp
    buf = buf.reshape(h, stride + 1)
    filt = buf[:, 0].copy()
    cur = buf[:, 1:].astype(np.int32).copy()
    # Unfilter. Sub/Paeth are sequential in x by definition, so the inner loop
    # is over BYTES PER PIXEL, not over pixels: bpp iterations, vectorised
    # across the row each time.
    prev = np.zeros(stride, np.int32)
    for y in range(h):
        f = filt[y]
        row = cur[y]
        if f == 0:
            pass
        elif f == 1:
            # Sub is a cumulative sum along each of the `bpp` interleaved byte
            # columns, so it vectorises. Paeth below genuinely does not.
            for k in range(bpp):
                col = row[k::bpp]
                np.cumsum(col, out=col)
                col &= 255
        elif f == 2:
            row += prev
            row &= 255
        elif f == 3:
            for x in range(stride):
                a = row[x - bpp] if x >= bpp else 0
                row[x] = (row[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = row[x - bpp] if x >= bpp else 0
                c = prev[x - bpp] if x >= bpp else 0
                b = prev[x]
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[x] = (row[x] + pr) & 255
        else:
            raise ValueError("unknown PNG filter %d on row %d" % (f, y))
        prev = row
    out = cur.astype(np.uint8)
    if depth == 16:
        out = out.reshape(h, w, nch, 2)
        return (out[..., 0].astype(np.uint16) << 8) | out[..., 1]
    return out.reshape(h, w, nch)


def write(path, a):
    """(H, W, C) uint8 -> PNG, filter 0. Small and correct beats small."""
    a = np.ascontiguousarray(a, np.uint8)
    if a.ndim == 2:
        a = a[:, :, None]
    h, w, nch = a.shape
    ctype = {1: 0, 3: 2, 4: 6}[nch]
    rows = np.concatenate([np.zeros((h, 1), np.uint8), a.reshape(h, w * nch)],
                          axis=1)
    comp = zlib.compress(rows.tobytes(), 6)

    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0)))
        f.write(chunk(b"IDAT", comp))
        f.write(chunk(b"IEND", b""))
    return path


def crop(src, dst, x0, y0, x1, y1, scale=1):
    """A pixel-exact crop, optionally nearest-neighbour magnified.

    Magnification is NEAREST on purpose. A bilinear zoom invents intermediate
    values, and the whole point of a pixel peep is to see the pixels that are
    actually there.
    """
    a = read(src)
    if a.dtype == np.uint16:
        a = (a >> 8).astype(np.uint8)
    c = a[int(y0):int(y1), int(x0):int(x1), :3]
    if scale > 1:
        c = np.repeat(np.repeat(c, scale, axis=0), scale, axis=1)
    write(dst, c)
    return c.shape


if __name__ == "__main__":
    import sys
    a = np.zeros((7, 11, 3), np.uint8)
    a[..., 0] = np.arange(11)[None, :] * 20
    a[..., 1] = np.arange(7)[:, None] * 30
    write("/tmp/_hp_test.png", a)
    b = read("/tmp/_hp_test.png")
    ok = b.shape == a.shape and (b == a).all()
    print("round trip %s: wrote %s, read %s, identical=%s"
          % ("PASS" if ok else "FAIL", a.shape, b.shape, ok))
    sys.exit(0 if ok else 1)
