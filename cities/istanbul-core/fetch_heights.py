#!/usr/bin/env python3
"""
Downloads the ground's height for a city's box and writes it as a grid, for build_city.py to put in the city file.

    fetch_heights.py <city folder> <south> <west> <north> <east> [zoom]

The heights come from the "Terrain Tiles" on the AWS Registry of Open Data (Tilezen / Mapzen, terrarium PNG):
https://registry.opendata.aws/terrain-tiles/ — each tile is a 256 x 256 map picture whose colours are heights,
metres = (red * 256 + green + blue / 256) - 32768. In Turkey the data under them is NASA's SRTM (30 m).
Attribution: see https://github.com/tilezen/joerd/blob/master/docs/attribution.md

Writes <city folder>/heights.json: the grid in the same metres as build_city.py (x east, z north, from the middle
of the box), one height every STEP metres, and keeps the downloaded tiles in <city folder>/tiles/.
"""
import json, math, os, struct, sys, time, urllib.request, zlib

STEP = 8.0                      # metres between the grid's points (the data itself is 30 m)
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"

folder = sys.argv[1]
S, W, N, E = map(float, sys.argv[2:6])
Z = int(sys.argv[6]) if len(sys.argv) > 6 else 14
lat0, lon0 = (S + N) / 2, (W + E) / 2
KY = 111320.0
KX = 111320.0 * math.cos(math.radians(lat0))


def tile_xy(lat, lon, z):
    """The tile a point is in, with the fraction across it (web mercator)."""
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def png_rgb(data):
    """The pixels of an 8-bit RGB or RGBA PNG, as rows of (r, g, b). Only what the terrarium tiles use."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, idat, width, height, kind = 8, b"", 0, 0, 0
    while pos < len(data):
        length, = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            width, height, depth, kind = struct.unpack(">IIBB", body[:10])
            assert depth == 8 and kind in (2, 6), f"unexpected PNG kind {kind}/{depth}"
        elif tag == b"IDAT":
            idat += body
        pos += 12 + length
    bpp = 3 if kind == 2 else 4
    raw = zlib.decompress(idat)
    stride = width * bpp
    rows, prev = [], bytearray(stride)
    for r in range(height):
        f = raw[r * (stride + 1)]
        line = bytearray(raw[r * (stride + 1) + 1:(r + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1: line[i] = (line[i] + a) & 255
            elif f == 2: line[i] = (line[i] + b) & 255
            elif f == 3: line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append([(line[i], line[i + 1], line[i + 2]) for i in range(0, stride, bpp)])
        prev = line
    return rows


tiles = {}


def tile(x, y):
    if (x, y) in tiles:
        return tiles[(x, y)]
    os.makedirs(f"{folder}/tiles", exist_ok=True)
    path = f"{folder}/tiles/{Z}-{x}-{y}.png"
    if not os.path.exists(path):
        request = urllib.request.Request(URL.format(z=Z, x=x, y=y), headers={"User-Agent": "QoopWorld-map-builder/1.0"})
        with urllib.request.urlopen(request, timeout=60) as reply, open(path, "wb") as f:
            f.write(reply.read())
        print(f"  tile {Z}/{x}/{y}: {os.path.getsize(path)} bytes")
        time.sleep(0.3)
    rows = png_rgb(open(path, "rb").read())
    tiles[(x, y)] = [[r * 256 + g + b / 256.0 - 32768.0 for (r, g, b) in row] for row in rows]
    return tiles[(x, y)]


def height_at(lat, lon):
    """Bilinear between the four nearest pixels, across tile edges."""
    fx, fy = tile_xy(lat, lon, Z)
    px, py = fx * 256 - 0.5, fy * 256 - 0.5
    x0, y0 = math.floor(px), math.floor(py)
    tx, ty = px - x0, py - y0

    def pixel(X, Y):
        return tile(X // 256, Y // 256)[Y % 256][X % 256]

    top = pixel(x0, y0) * (1 - tx) + pixel(x0 + 1, y0) * tx
    bottom = pixel(x0, y0 + 1) * (1 - tx) + pixel(x0 + 1, y0 + 1) * tx
    return top * (1 - ty) + bottom * ty


minx, maxx = (W - lon0) * KX, (E - lon0) * KX
minz, maxz = (S - lat0) * KY, (N - lat0) * KY
nx = int(math.ceil((maxx - minx) / STEP)) + 1
nz = int(math.ceil((maxz - minz) / STEP)) + 1
heights = []
for j in range(nz):
    z = minz + j * STEP
    for i in range(nx):
        x = minx + i * STEP
        heights.append(round(height_at(lat0 + z / KY, lon0 + x / KX), 1))
json.dump({"step": STEP, "nx": nx, "nz": nz, "x0": minx, "z0": minz, "h": heights}, open(f"{folder}/heights.json", "w"))
print(f"heights: {nx} x {nz}, {min(heights):.0f} to {max(heights):.0f} m, {len(tiles)} tiles")
