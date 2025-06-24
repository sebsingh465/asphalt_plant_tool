import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point

# Pittsburgh coordinates
center_lat, center_lon = 40.4406, -79.9959

# 100 mile radius in meters
radius_meters = 100 * 1609.34

# Create a circular buffer around Pittsburgh
center_point = Point(center_lon, center_lat)
gdf = gpd.GeoDataFrame(geometry=[center_point], crs="EPSG:4326")
gdf_proj = gdf.to_crs(epsg=3857)
buffer = gdf_proj.buffer(radius_meters).to_crs(epsg=4326).iloc[0]

print("Downloading road network within 100 miles of Pittsburgh...")
G = ox.graph_from_polygon(buffer, network_type='drive')

# Convert the graph to a GeoDataFrame of edges (roads)
print("Converting to GeoDataFrame...")
gdf_edges = ox.graph_to_gdfs(G, nodes=False, edges=True)

# Filter for roads with surface=asphalt (if available)
if 'surface' in gdf_edges.columns:
    gdf_asphalt = gdf_edges[gdf_edges['surface'] == 'asphalt']
else:
    print("No surface data found; using all roads as a fallback.")
    gdf_asphalt = gdf_edges

# Save to a GeoPackage file for later use
output_file = "pa_asphalt_roads.gpkg"
print(f"Saving asphalt roads to {output_file}...")
gdf_asphalt.to_file(output_file, driver="GPKG")

print("Done! Asphalt road data saved.")