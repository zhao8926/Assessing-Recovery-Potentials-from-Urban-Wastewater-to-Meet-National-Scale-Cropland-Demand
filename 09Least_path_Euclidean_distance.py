#-*-coding:utf-8-*-
import pandas as pd
import re
import arcpy
import os
import sys
import time

def restart_program(next_y):
    """Force restart the program using system command, passing the next y value"""
    python_executable = sys.executable
    script = sys.argv[0]
    os.system(f'start "" "{python_executable}" "{script}" {next_y}')
    time.sleep(1)  # Wait 1 second to ensure the new process starts successfully
    sys.exit(0)  # Force exit the current process

def extract_numbers(string):
    return "".join(filter(str.isdigit, string))

# Define a function to process each row of data
def process_route(route_str):
    # Split the string connected by '-' into numbers and convert into a list
    route_list = []
    for part in str(route_str).split('-'):
        route_list.append(int(float(part)))  # Convert to int and add to the list
    return route_list

# Merge two feature classes into one output
def merge(i, j, outname):
    return arcpy.Merge_management([i, j], outname)

### The logic is as follows:
### Based on the SA algorithm paths, read each row of ODLines.
### If the row corresponds to a path in the optimal route, add its ID to the storage list (iteratively).
### Finally, merge the features with the stored IDs to calculate the route.
def cal_OD(WWTP_ID, ODLine_path, out_path, lst, y):
    i = 1
    storage = []
    for x in lst:
        ### (1) Calculate the path from WWTP to the first cropland
        first_ID = 1  ### Because the OD cost matrix sets WWTP's ID as 1
        with arcpy.da.SearchCursor(ODLine_path, ["OBJECTID", "OriginID", "DestinationID"]) as Cursor:
            for row in Cursor:
                if row[1] == first_ID and row[2] == x[0]:
                    storage.append(row[0])
        
        ### (2) Calculate paths from the first cropland to the last cropland
        for j in range(len(x) - 1):
            with arcpy.da.SearchCursor(ODLine_path, ["OBJECTID", "OriginID", "DestinationID"]) as Cursor:
                for row in Cursor:
                    if row[1] == x[j] and row[2] == x[j + 1]:
                        storage.append(row[0])
        
        print(f"Path {i} added to the storage list")
        i += 1

    if len(storage) == 1:
        arcpy.FeatureClassToFeatureClass_conversion(ODLine_path, out_path, f"ODLine_{WWTP_ID[y]}", f"OBJECTID = {storage[0]}")
    else:
        arcpy.FeatureClassToFeatureClass_conversion(ODLine_path, out_path, f"ODLine_{WWTP_ID[y]}", f"OBJECTID IN ({', '.join(map(str, storage))})")
    print(f"Path calculation completed for WWTP {WWTP_ID[y]}")


# ===== Main program starts =====

# Get command line arguments
if len(sys.argv) > 1:
    start_y = int(sys.argv[1])
else:
    start_y = 0

WWTP_ID = [num for num in range(1, 993)]
for y in range(start_y, 992):  # range(0, 989)
    OD_path = f"E:\\WWTP_China\\OD_Routes\\Routes.gdb\\ODLine_{WWTP_ID[y]}"
    
    if arcpy.Exists(OD_path):
        print(f"Route for {WWTP_ID[y]} has already been calculated")
        continue

    ### Step 1: Set the order

    # Read the Excel file
    file_path = f'E:\\vehicle_gai\\result_100%_0.1265\\path{WWTP_ID[y]}\\sapath{WWTP_ID[y]}.xlsx'
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    # Get data from 'routes_best' column
    routes_first = df['routes_best'].dropna()  # Drop rows with NaN
    # Process each row
    processed_routes = routes_first.apply(process_route).tolist()
    # Output result
    print(processed_routes)

    ### Step 2: Calculate routes
    ODLine_path = f"E:\\W_C\\path_hainan\\OD{WWTP_ID[y]-989}\\OD_MATRIX{WWTP_ID[y]-989}.gdb\\ODMatrix1\\ODLines1"
    
    out_path = "E:\\WWTP_China\\OD_Routes\\Routes.gdb"
    
    cal_OD(WWTP_ID, ODLine_path, out_path, processed_routes, y)
    
    # Restart the program to process the next y
    restart_program(WWTP_ID[y])
