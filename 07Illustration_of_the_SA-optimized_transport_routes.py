#-*-coding:utf-8-*-
import pandas as pd
import re
import arcpy
import os

# Extract digits from a string
def extract_numbers(string):
    return "".join(filter(str.isdigit,string))

# Define a function to process each row of data
def process_route(route_str):
    # Split strings connected by '-' and convert them to a list of numbers
    route_list = []
    for part in str(route_str).split('-'):
        route_list.append(int(float(part)))  # Convert to integer and add to the list
    return route_list

# Merge two input feature classes into one
def merge(i, j, outname):
    return arcpy.Merge_management([i, j], outname)

# Calculate the transport routes
def cal_route(WWTP_ID, WWTP_point, cropland_point, lst, road_China_ND):
    i = 1
    for x in lst:
        ### Determine point order
        first_ID = WWTP_ID[y] + 10000
        order = [first_ID]  # If WWTP ID and cropland ID happen to be the same, this may cause an issue
        x = [i-1 for i in x]
        order += x

        ### Select and merge points
        if len(x) == 1:
            select = arcpy.SelectLayerByAttribute_management(cropland_point, "", f"OBJECTID = {x[0]}")
        else:
            select = arcpy.SelectLayerByAttribute_management(cropland_point, "", f"OBJECTID IN ({', '.join(map(str, x))})")
        
        # Define the path to save merged points
        merge_point_path = f"basic_scenario_routes\\road_routes{WWTP_ID[y]}\\road_routes{WWTP_ID[y]}.gdb\\cropland{WWTP_ID[y]}_merge{i}"

        if arcpy.Exists(merge_point_path):  # Delete if already exists
            arcpy.Delete_management(merge_point_path)
        
        merge_point = merge(WWTP_point, select, outname=merge_point_path)
        arcpy.AddField_management(merge_point, "order_route", "LONG")
        print(f"cropland{WWTP_ID[y]}_merge{i} merge completed")

        with arcpy.da.UpdateCursor(merge_point, ["Id", "order_route"]) as Cursor:  # After merge, 'Id' field exists
            for row in Cursor:
                row[1] = order.index(int(row[0])) + 1
                Cursor.updateRow(row)  # Update the row

        ### Calculate the route for each point group
        # Process: Create Route Analysis Layer
        anlysis_layer = arcpy.MakeRouteAnalysisLayer_na(
            network_data_source=road_China_ND,
            layer_name=f"route_{WWTP_ID[y]}_{i}",
            travel_mode="",
            sequence="USE_CURRENT_ORDER",
            time_of_day="",
            time_zone="LOCAL_TIME_AT_LOCATIONS",
            line_shape="ALONG_NETWORK",
            accumulate_attributes=[],
            generate_directions_on_solve="DIRECTIONS"
        )[0]

        # Process: Add Locations
        anlysis_layer = arcpy.AddLocations_na(
            in_network_analysis_layer=anlysis_layer,
            sub_layer="停靠点",  # Stops
            in_table=merge_point,
            field_mappings="",
            search_tolerance="5000 Meters",
            sort_field="order_route",
            search_criteria=[["road_China_Merge", "SHAPE"], ["road_China_ND_Junctions", "NONE"]],
            match_type="MATCH_TO_CLOSEST",
            append="APPEND",
            snap_to_position_along_network="NO_SNAP",
            snap_offset="5 Meters",
            exclude_restricted_elements="EXCLUDE",
            search_query=[["road_China_Merge", ""], ["road_China_ND_Junctions", ""]]
        )[0]

        # Process: Solve the route
        anlysis_layer, solve_over = arcpy.Solve_na(
            in_network_analysis_layer=anlysis_layer,
            ignore_invalids="SKIP",
            terminate_on_solve_error="TERMINATE",
            simplification_tolerance="",
            overrides=""
        )
        print(f"cropland{WWTP_ID[y]}_merge{i} route solved")
        i += 1

if __name__ == "__main__":
    WWTP_ID = [num for num in range(1, 990)]
    for y in WWTP_ID:  # range(0, 989)
        if os.path.exists(f"WWTP_China\\basic_scenario_routes\\road_routes{WWTP_ID[y]}"):
            print(f"Route for {WWTP_ID[y]} has already been calculated")
        else:
            ### Step 1: Set the route order

            # Read the Excel file
            file_path = f'vehicle_gai\\result_100%_0.1265\\path{WWTP_ID[y]}\\sapath{WWTP_ID[y]}.xlsx' # SA result
            df = pd.read_excel(file_path, sheet_name='Sheet1')
            # Get data from the 'routes_best' column
            routes_first = df['routes_best'].dropna()  # Drop empty rows
            # Process each row
            processed_routes = routes_first.apply(process_route).tolist()
            # Output result
            print(processed_routes)

            ### Step 2: Calculate route

            WWTP = "WWTP.gdb\\WWTP_China_5_nearRoad_D_Feat" # Path to WWTP feature
            WWTP_point = arcpy.SelectLayerByAttribute_management(WWTP, "NEW_SELECTION", f"OBJECTID = {WWTP_ID[y]}")  # Select the WWTP point

            cropland_point = f"match_CC.gdb\\cropland{WWTP_ID[y]}"  # Path to cropland feature

            ### Add ID field to cropland if not already present
            if any("Id" in i.name for i in arcpy.ListFields(cropland_point)):
                print("Field 'Id' already exists")
            else:
                arcpy.AddField_management(cropland_point, "Id", "LONG")
                arcpy.CalculateField_management(cropland_point, "Id", "!OBJECTID!", "PYTHON3")
                print("Field 'Id' added to cropland")

            process_path = "WWTP_China\\basic_scenario_routes"
            os.makedirs(os.path.join(process_path, f"road_routes{WWTP_ID[y]}"), exist_ok=True)
            arcpy.CreateFileGDB_management(os.path.join(process_path, f"road_routes{WWTP_ID[y]}"), f"road_routes{WWTP_ID[y]}.gdb")
            
            merge_point_outpath = os.path.join(process_path, f"road_routes{WWTP_ID[y]}", f"road_routes{WWTP_ID[y]}.gdb")
            arcpy.env.workspace = merge_point_outpath

            road_China_ND = "WWTP_China\\roadnet.gdb\\road_China\\road_China_ND" ### Road network data

            cal_route(WWTP_ID, WWTP_point, cropland_point, processed_routes, road_China_ND)
