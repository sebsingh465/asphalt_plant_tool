import streamlit as st
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
import folium
from streamlit_folium import st_folium

print("Starting Streamlit app")  # <--- Add here

# Load the saved road data
@st.cache_data
def load_roads():
    return gpd.read_file("enriched_roads.gpkg")

roads = load_roads()
print("Loaded roads data")  # <--- Add here

st.title("Asphalt Plant Location Tool (PA)")

# User input for radius
radius_miles = st.slider("Select radius (miles):", min_value=1, max_value=50, value=10)
radius = radius_miles * 1609.34  # Convert miles to meters

# Reproject to metric CRS for distance calculations
roads_proj = roads.to_crs(epsg=3857)
roads_proj = roads_proj.drop_duplicates(subset="geometry")
minx, miny, maxx, maxy = roads_proj.total_bounds

# User input for grid spacing in miles
grid_spacing_miles = st.slider("Grid spacing (miles):", min_value=5, max_value=50, value=25, step=5)
grid_spacing = grid_spacing_miles * 1609.34  # Convert miles to meters

# Create a grid of points
x_points = np.arange(minx, maxx, grid_spacing)
y_points = np.arange(miny, maxy, grid_spacing)
grid_points = [Point(x, y) for x in x_points for y in y_points]
grid_gdf = gpd.GeoDataFrame(geometry=grid_points, crs=roads_proj.crs)

print("Created grid")  # <--- Add here

# Calculate total road length within the radius for each grid point
asphalt_density = []
for point in grid_gdf.geometry:
    buffer = point.buffer(radius)
    roads_in_buffer = roads_proj[roads_proj.intersects(buffer)]
    total_length = roads_in_buffer.length.sum() / 1000  # in kilometers
    asphalt_density.append(total_length)
print("Calculated asphalt density")  # <--- Add here

grid_gdf["asphalt_km_within_radius"] = asphalt_density

# Prompt user for number of top locations to highlight
num_top_points = st.number_input("How many top locations to highlight?", min_value=1, max_value=len(grid_gdf), value=5, step=1)

# Find the top N locations
if len(grid_gdf) > 0:
    top_locations = grid_gdf.sort_values("asphalt_km_within_radius", ascending=False).head(num_top_points)
else:
    top_locations = grid_gdf.copy()

# Reproject to lat/lon for folium plotting
if not grid_gdf.empty:
    grid_gdf_latlon = grid_gdf.to_crs(epsg=4326)
else:
    grid_gdf_latlon = grid_gdf.copy()
if not top_locations.empty:
    top_locations_latlon = top_locations.to_crs(epsg=4326)
else:
    top_locations_latlon = top_locations.copy()

# Show results (convert geometry to WKT for display)
top_locations_display = top_locations.copy()
top_locations_display["geometry"] = top_locations_display["geometry"].apply(lambda geom: geom.wkt)
st.subheader("Top 5 Locations with Most Asphalt Nearby")
st.write(top_locations_display[["geometry", "asphalt_km_within_radius"]])

# Center the map on the grid centroid in lat/lon
if not grid_gdf_latlon.empty:
    center = [grid_gdf_latlon.unary_union.centroid.y, grid_gdf_latlon.unary_union.centroid.x]
else:
    center = [40.4406, -79.9959]  # Default to Pittsburgh if grid is empty
m = folium.Map(location=center, zoom_start=7)
print("Created folium map")  # <--- Add here

# Add all grid points as circles, color by density
for idx, row in grid_gdf_latlon.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=5,
        color='blue',
        fill=True,
        fill_opacity=0.3,
        popup=f"Asphalt within {radius_miles}mi: {row.asphalt_km_within_radius:.2f} km"
    ).add_to(m)

# Highlight top locations in red
for idx, row in top_locations_latlon.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=10,
        color='red',
        fill=True,
        fill_opacity=0.7,
        popup=f"TOP: {row.asphalt_km_within_radius:.2f} km"
    ).add_to(m)

st.subheader("Map of Asphalt Density")
st_folium(m, width=700, height=500)
print("Displayed map in Streamlit")  # <--- Add here

m.save("asphalt_density_map.html")
print("Saved HTML map")  # <--- Add here