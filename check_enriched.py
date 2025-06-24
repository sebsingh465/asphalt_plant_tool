import geopandas as gpd

gdf = gpd.read_file("enriched_roads.gpkg")
print(f"Number of features: {len(gdf)}")
print(gdf.head())