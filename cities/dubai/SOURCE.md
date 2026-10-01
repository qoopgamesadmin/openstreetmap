# dubai — derived map data

This data is derived from OpenStreetMap.

**© OpenStreetMap contributors.** Available under the Open Database License (ODbL) 1.0:
https://opendatacommons.org/licenses/odbl/1-0/ — https://www.openstreetmap.org/copyright

## What it is
`dubai.bytes` is a derived database made from an OpenStreetMap extract. It is used by the game Qoop World
(qoop games) to draw the real streets, building footprints, coast, parks and sights of this area.

## How it was made (the method of the alterations)
- Downloaded: 29 September 2026, from the Overpass API (https://overpass-api.de), with the queries in `q-*.txt`.
- Area: south 25.1873, west 55.2635, north 25.2071, east 55.2853 (the heart of Dubai).
- Processed with `build_city.py` (in this folder):
  `python3 build_city.py <folder with the downloaded .json> dubai.bytes 25.1873 55.2635 25.2071 55.2853`
  The script keeps geometry and a few tags (building type, levels, height; road type, bridge; names of places of
  worship, historic buildings and sights — Turkish, else English, else the local name in Latin letters),
  simplifies lines, converts to metres from the middle of the area, and draws the land and sea as a 4 m raster
  from the coastline.

## File format
See the header of `build_city.py`: magic `QRC1`, the area, the land raster as runs per row, then the features
(kind, sub-type, levels, points in decimetres, name).

## Ground heights
The file ends with the ground's heights (`HGT1` section), from the Terrain Tiles on the AWS Registry of Open Data
(Tilezen/Mapzen, terrarium PNG, zoom 14), fetched with `fetch_heights.py` for the same box. Attribution for the
terrain data: https://github.com/tilezen/joerd/blob/master/docs/attribution.md
