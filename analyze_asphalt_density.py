import geopandas as gpd
from shapely.geometry import Point
import numpy as np
import folium

# Load the saved road data
roads = gpd.read_file("pa_asphalt_roads.gpkg")

# Set the analysis area bounds (use the bounds of the road data)
minx, miny, maxx, maxy = roads.total_bounds

# Create a grid of points (every ~0.2 degree, adjust for more/less detail)
x_points = np.arange(minx, maxx, 0.2)
y_points = np.arange(miny, maxy, 0.2)
grid_points = [Point(x, y) for x in x_points for y in y_points]

# Create a GeoDataFrame for the grid points
grid_gdf = gpd.GeoDataFrame(geometry=grid_points, crs=roads.crs)

# Set the search radius in meters (e.g., 16093 meters ≈ 10 miles)
radius = 16093

# Reproject to a metric CRS for accurate distance calculations
roads_proj = roads.to_crs(epsg=3857)
grid_gdf_proj = grid_gdf.to_crs(epsg=3857)

# Calculate total road length within the radius for each grid point
asphalt_density = []
for point in grid_gdf_proj.geometry:
    buffer = point.buffer(radius)
    roads_in_buffer = roads_proj[roads_proj.intersects(buffer)]
    total_length = roads_in_buffer.length.sum() / 1000  # in kilometers
    asphalt_density.append(total_length)

grid_gdf["asphalt_km_within_radius"] = asphalt_density

# Find the top 5 locations with the most asphalt nearby
top_locations = grid_gdf.sort_values("asphalt_km_within_radius", ascending=False).head(5)

# Print the results
print("Top 5 locations with most asphalt (in km) within 10 miles:")
print(top_locations[["geometry", "asphalt_km_within_radius"]])

# Visualize on a map
center = [roads.geometry.centroid.y.mean(), roads.geometry.centroid.x.mean()]
m = folium.Map(location=center, zoom_start=7)
for idx, row in top_locations.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=10,
        color='red',
        fill=True,
        fill_opacity=0.7,
        popup=f"Asphalt within 10mi: {row.asphalt_km_within_radius:.2f} km"
    ).add_to(m)
m.save("asphalt_density_map.html")
print("Map saved as asphalt_density_map.html")