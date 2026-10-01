# The city file format (QRC1)

Every `cities/<key>/<key>.bytes` file is little-endian binary. `tools/qrc_to_geojson.py` reads it and writes
GeoJSON (and optionally the land raster and the heights), so you never have to parse it yourself.

Positions are metres from the middle of the area's box: **x east, z north**. To get back to degrees:

    KY = 111320
    KX = 111320 * cos(lat0)
    lon = lon0 + x / KX
    lat = lat0 + z / KY

## Header
| Type | Field |
|---|---|
| 4 bytes | `QRC1` |
| float32 ×2 | `lat0`, `lon0`: the middle of the box |
| float32 ×4 | `minx`, `minz`, `maxx`, `maxz`: the box in metres |
| int16 ×2 | `GW`, `GH`: the land raster's width and height in cells |
| float32 | `CELL`: the raster's cell size in metres (4) |

## Land raster
`GH` rows from the south. Each row: `uint16` run count, then for each run `uint16 start, uint16 length` — the
cells that are land. Everything else is water (sea, lakes, river beds). It was drawn from the coastline (land to
the left of the way, OpenStreetMap's rule) and from `natural=water` / `waterway=riverbank` areas.

## Features
`uint32` count, then each feature:

| Type | Field |
|---|---|
| uint8 | kind |
| uint8 | sub-type |
| uint8 | levels (buildings; 0 = unknown) |
| uint16 | point count `n` |
| int16 ×2 × n | points `x, z` in decimetres |
| uint8 + bytes | name, UTF-8, at most 255 bytes |

| kind | What | sub-type |
|---|---|---|
| 1 | building outline (closed, last point not repeated) | 0 other, 1 mosque, 2 residential, 3 commercial, 4 public, 5 historic |
| 2 | road (line) | 0 main, 1 local, 2 path, 3 steps; +10 a bridge |
| 4 | park outline | — |
| 5 | sight (one point) | — |
| 6 | waterway (line) | 0 river, 1 stream |

Names are kept only for places of worship, historic buildings, sights, bridges and waterways: the `name:tr` tag,
else `name:en`, else `name` when it is in Latin letters. Levels come from `building:levels`, or `height / 3.2`.
Lines are simplified (Ramer–Douglas–Peucker, 0.6 m for buildings, 1–1.5 m for the rest).

## Ground heights (optional)
When present, after the features: `HGT1`, then `uint16 nx, uint16 nz, float32 step, float32 x0, float32 z0,
float32 base`, then `nx * nz` × `uint16` — decimetres above `base` metres, row by row from the south-west
(x fastest). Older readers stop before this section. These heights are not from OpenStreetMap (see LICENSE).

## Street names (`<city>.names.bytes`)

Beside each city file, the named streets of the same box, in the same metres (from the city file's header):
`QRN1`, int32 count, then per street: uint8 road kind (as in the city file), uint8 byte length + the name in UTF-8
(Turkish name, else English, else the local one in Latin letters), uint16 point count, then float32 x, float32 z per
point. Made by `tools/build_names.py` from OpenStreetMap (Overpass, `way["highway"]["name"]`). © OpenStreetMap
contributors, ODbL 1.0.
