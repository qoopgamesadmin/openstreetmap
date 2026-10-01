# ayder — derived map data

This data is derived from OpenStreetMap.

**© OpenStreetMap contributors.** Available under the Open Database License (ODbL) 1.0:
https://opendatacommons.org/licenses/odbl/1-0/ — https://www.openstreetmap.org/copyright

## What it is
`ayder.bytes` is a derived database made from an OpenStreetMap extract. It is used by the game Qoop World
(qoop games) to draw the real streets, building footprints, coast, parks and sights of this area.

## How it was made (the method of the alterations)
- Downloaded: 29 September 2026, from the Overpass API (https://overpass-api.de), with the queries in `q-*.txt`.
- Area: south 40.940, west 41.082, north 40.966, east 41.118 (Ayder highland, Çamlıhemşin, Rize).
- Processed with `build_city.py` (in this folder):
  `python3 build_city.py <folder with buildings/roads/coast/parks/sights/relations .json> ayder.bytes 40.940 41.082 40.966 41.118`
  The script keeps geometry and a few tags (building type, levels, height; road type, bridge; names of mosques,
  historic buildings and sights), simplifies lines, converts to metres from the middle of the area, and draws the
  land and sea as a 4 m raster from the coastline.

## File format
See the header of `build_city.py`: magic `QRC1`, the area, the land raster as runs per row, then the features
(kind, sub-type, levels, points in decimetres, name).

## Ground heights (added 29 September 2026)
The file ends with the ground's heights (`HGT1` section), from the Terrain Tiles on the AWS Registry of Open Data
(Tilezen/Mapzen, terrarium PNG, zoom 14; in Turkey from NASA's SRTM), fetched with `fetch_heights.py` for the same
box and appended by `build_city.py` / `add_heights.py`. Attribution for the terrain data:
https://github.com/tilezen/joerd/blob/master/docs/attribution.md

## Streams (added 29 September 2026)
Rivers and streams (`waterway=river|stream`, query `q-water.txt`) are in the file as kind 6 (build_city.py).
