import arcpy
import os
import pandas as pd

# Extract digits from a string
def extract_num(string):
    return ''.join([s for s in string if s.isdigit()])

def cal_initial_destination(sa_path):
    # Read the Excel file
    df = pd.read_excel(sa_path, sheet_name='Sheet1')

    # Drop rows with NaN in the 'routes_best' column
    df_cleaned = df.dropna(subset=['routes_best'])

    # Extract the first part before '-' in the 'routes_best' column
    routes_best = df_cleaned['routes_best'].astype(str).str.split('-', expand=True)[0]

    # Convert to a list of integers
    route_list = routes_best.tolist()
    route_list = [int(float(i)) for i in route_list]
    print(route_list)

    # Count occurrences of each element in the list
    count_dict = {}
    for route in route_list:
        if route in count_dict:
            count_dict[route] += 1
        else:
            count_dict[route] = 1

    ID_list = [int(i) for i in count_dict.keys()]
    return ID_list

# Calculate transport routes
def calRoute(sa_path, vehicle_route, cost, WWTP, Cropland1, Cropland2, outspace, outname):
    arcpy.env.workspace = outspace
    q = 1
    ID_list = cal_initial_destination(sa_path)

    # Select cropland features based on initial destination IDs
    c = arcpy.SelectLayerByAttribute_management(Cropland1, "NEW_SELECTION", f"OBJECTID in {tuple(ID_list)}")
    # (use this for the case where WWTP transports to only one cropland)

    route0 = os.path.join(outspace, f"outRoute0")
    arcpy.LeastCostPath_intelligence(cost, WWTP, c, route0, "")
    print(f"{route0} initial segment calculated.")

    ### Get attribute values from route0
    route0_DestID = []
    with arcpy.da.SearchCursor(route0, ["DestID"]) as Cursor:
        for row in Cursor:
            route0_DestID.append(int(row[0]))

    last_value = None
    for i in vehicle_route:
        # This assumes each vehicle route serves more than one cropland.
        # If it only serves one, this loop would not run.
        i = str(i)
        route = [int(float(x)) for x in i.split('-')]

        if int(float(route[0])) not in route0_DestID and int(float(route[0])) != last_value:
            c1 = arcpy.SelectLayerByAttribute_management(Cropland1, "NEW_SELECTION", f"OBJECTID = {route[0]}")
            route00 = os.path.join(outspace, f"outRoute{q}_0")
            arcpy.LeastCostPath_intelligence(cost, WWTP, c1, route00)
            print(f"{route00} was not originally included, now added")

        s = 1
        for j in range(len(route) - 1):
            c2 = arcpy.SelectLayerByAttribute_management(Cropland1, "NEW_SELECTION", f"OBJECTID = {route[j]}")
            c3 = arcpy.SelectLayerByAttribute_management(Cropland2, "NEW_SELECTION", f"OBJECTID = {route[j+1]}")
            route1 = os.path.join(outspace, f"outRoute{q}_{s}")
            arcpy.LeastCostPath_intelligence(cost, c2, c3, route1)
            print(f"{route1} calculated")
            s += 1

        last_value = int(float(route[0]))  # Store previous first point to avoid redundant calculations
        q += 1

    arcpy.env.workspace = outspace
    Route_list = arcpy.ListFeatureClasses("", "Line")
    print("Route listing complete")
    arcpy.Merge_management(Route_list, outname)
    arcpy.management.DeleteIdentical(outname, "DestID")
    print("All routes merged")

# Remove all NaN elements from the end of the list
def del_nan(lst):
    while lst and pd.isna(lst[-1]):  # Check if the last element is NaN
        lst.pop()  # Remove the NaN element from the end
    return lst

# Sort list based on the number extracted from the last 10 to 1 characters of each item
def sort_by_num(lst):
    sorted_lst = sorted(lst, key=lambda x: int(''.join(filter(str.isdigit, x[-10:-1]))))
    return sorted_lst

# Run the main process
def run():
    cost = "E:\\W_C\\road_raster.gdb\\density_road_China_Raster_2_fu2" ### Road network data (2 km × 2 km resolution, raster)
    # arcpy.management.CalculateStatistics(cost)
    print("Raster data statistics completed")

    cW_space = "E:\\W_C\\r_CW_kl.gdb" ### Each WWTP and its connected cropland feature
    Route_space = "E:\\W_C\\Route_x.gdb" # save path

    ### Get the numeric sequence order
    arcpy.env.workspace = cW_space
    cW_list = arcpy.ListFeatureClasses()
    print("Feature listing successful")
    cW_num = [int(extract_num(i)) for i in cW_list]
    cW_num = sorted(cW_num)

    for i in cW_num:
        if arcpy.Exists(os.path.join(Route_space, f"Route{i}")):
            print(f"Route{i} already exists, skipping calculation")
        else:
            ### Read four columns from SA result
            sapath_num = f"E:\\vehicle_gai\\result_100%_0.1265\\path{i}\\sapath{i}.xlsx" # SA result
            sa_colums = ["routes_first", "vehicle_initial", "routes_best", "vehicle_best"]
            df = pd.read_excel(sapath_num, usecols=sa_colums)

            ### Calculate travel distance for each truck under optimal conditions
            r_f_b = del_nan(df["routes_best"].tolist())
    
            WWTP = f"E:\\W_C\\r_CW_kl.gdb\\c_W_kl_{i}"
            WWTP = arcpy.SelectLayerByAttribute_management(WWTP, "NEW_SELECTION", "OBJECTID = 1")
            Cropland1 = f"E:\\W_C\\r_CW_kl.gdb\\c_W_kl_{i}"
            Cropland2 = f"E:\\W_C\\r_CW_kl.gdb\\c_W_kl_{i}"

            outspace = "E:\\W_C\\Route_t.gdb"
            if arcpy.Exists(outspace):
                arcpy.Delete_management(outspace)
            arcpy.CreateFileGDB_management(os.path.dirname(outspace), os.path.basename(outspace))
            print(f"{outspace} created")

            outname = f"E:\\W_C\\Route_x.gdb\\Route{i}"

            calRoute(sapath_num, r_f_b, cost, WWTP, Cropland1, Cropland2, outspace, outname)

            arcpy.Delete_management(outspace)

            arcpy.env.workspace = "D:\\gis_test\\gis_test\\Default.gdb"
            raster_list = arcpy.ListRasters()
            for i in raster_list:
                arcpy.Delete_management(i)
            print("Intermediate data deleted")
            print(f"{outspace} deleted")
            print(f"{outname} calculation completed")
   
if __name__ == "__main__":
    run()



