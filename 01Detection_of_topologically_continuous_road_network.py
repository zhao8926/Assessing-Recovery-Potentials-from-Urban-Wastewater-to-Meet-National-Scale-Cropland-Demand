#-*-coding:utf-8-*-
import arcpy
import os

# The input line feature must be processed with "Feature to Line" beforehand!
zhengti="2024_10_26china-latest-free/OSM_road/road_China_2024_no_m_l.shp" # Full road network
suoying="2024_10_26china-latest-free/OSM_road/road_China_index.shp" # Initial selected segment

# Check if the file paths exist
if os.path.exists(zhengti) and os.path.exists(suoying):
    print("Paths exist")
else:
    print("Path does not exist")
    raise FileNotFoundError("Input file path does not exist")

rows = arcpy.management.GetCount(zhengti)
print("Total number of rows in the road network: " + str(rows))

arcpy.env.workspace = "China_road.gdb"  # Workspace (output geodatabase)

# Process: Select features by location (intersect)
feaclass, name, num = arcpy.SelectLayerByLocation_management(
    in_layer=[zhengti], 
    overlap_type="INTERSECT",
    select_features=suoying,
    search_distance="",
    selection_type="NEW_SELECTION",
    invert_spatial_relationship="NOT_INVERT"
)

print("Rows selected in first intersection: " + str(num))
i = 1
u = None
while u != num:
    u = num  # First time u equals num, but num changes in the next step
    feaclass, name, num = arcpy.SelectLayerByLocation_management(
        in_layer=[zhengti],
        overlap_type="INTERSECT",
        select_features=feaclass,
        search_distance="",
        selection_type="NEW_SELECTION",
        invert_spatial_relationship="NOT_INVERT"
    )
    i = i + 1
    print("Intersection count: " + str(i) + ", number of rows: " + str(num))

outname = "China_overall_road"  # Output feature name
outlines = arcpy.env.workspace + "/" + outname  # Full output path

# Export the final selected features
arcpy.management.CopyFeatures(feaclass, outlines)
