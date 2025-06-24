import geopandas as gpd

# Load OSM data (GeoPackage)
osm_roads = gpd.read_file("pa_asphalt_roads.gpkg")
print(f"Loaded OSM data: {len(osm_roads)} features")

# Load government GIS data (Shapefile)
gov_roads = gpd.read_file("RMSSEG_(State_Roads).shp")
print(f"Loaded government data: {len(gov_roads)} features")

# Reproject both to the same CRS (Web Mercator for distance calculations)
osm_roads = osm_roads.to_crs(epsg=3857)
gov_roads = gov_roads.to_crs(epsg=3857)

# Print available columns for reference
print("OSM columns:", osm_roads.columns)
print("Gov columns:", gov_roads.columns)

# Select relevant columns from government data (edit as needed)
gov_columns = ['geometry']
if 'surface' in gov_roads.columns:
    gov_columns.append('surface')
if 'lanes' in gov_roads.columns:
    gov_columns.append('lanes')

gov_roads = gov_roads[gov_columns]

# Spatial join: enrich OSM with government attributes where geometries intersect
enriched_osm = gpd.sjoin(osm_roads, gov_roads, how='left', predicate='intersects', lsuffix='_osm', rsuffix='_gov')

# Prefer government surface/lanes if available, otherwise use OSM
if 'surface_gov' in enriched_osm.columns:
    enriched_osm['surface_final'] = enriched_osm['surface_gov'].combine_first(enriched_osm['surface_osm'] if 'surface_osm' in enriched_osm.columns else None)
elif 'surface' in enriched_osm.columns:
    enriched_osm['surface_final'] = enriched_osm['surface']
else:
    enriched_osm['surface_final'] = None

if 'lanes_gov' in enriched_osm.columns:
    enriched_osm['lanes_final'] = enriched_osm['lanes_gov'].combine_first(enriched_osm['lanes_osm'] if 'lanes_osm' in enriched_osm.columns else None)
elif 'lanes' in enriched_osm.columns:
    enriched_osm['lanes_final'] = enriched_osm['lanes']
else:
    enriched_osm['lanes_final'] = None

# Save the enriched dataset
enriched_osm.to_file("enriched_roads.gpkg", driver="GPKG")
print("Saved enriched dataset as enriched_roads.gpkg")

def load_roads():
    return gpd.read_file("enriched_roads.gpkg")