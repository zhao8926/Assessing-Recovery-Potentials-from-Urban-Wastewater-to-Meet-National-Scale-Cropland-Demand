#-*-coding:utf-8-*-#
import arcpy
import warnings
warnings.filterwarnings("ignore")

WWTP_info = {}
cropland_info = {}

# Store the ID and value of cropland or WWTP into Info
def store_information(data, id_field, value_field, c_or_w):
    with arcpy.da.SearchCursor(data, [id_field, value_field]) as cursor:
        for row in cursor:
            obj_id = row[0]
            val = row[1]
            if c_or_w == "cropland":
                cropland_info[obj_id] = val
            else:
                WWTP_info[obj_id] = val

# First round of matching between WWTPs and croplands
def match(cropland, WWTP, cropland_id, cropland_value, workspace, lst):
    arcpy.Near_analysis(cropland, WWTP,"","","","GEODESIC")
    WWTP_count = int(arcpy.GetCount_management(WWTP).getOutput(0))
    
    for i in range(1, WWTP_count + 1):
        # Select croplands where the nearest WWTP is the current one
        cropland_select = arcpy.SelectLayerByAttribute_management(cropland, "NEW_SELECTION", f"NEAR_FID = {i}")
        cropland_demand_all = sum(row[0] for row in arcpy.da.SearchCursor(cropland_select, [cropland_value]))
        
        WWTP_supply = WWTP_info[i] # Use 0 if not found
        
        if WWTP_supply > cropland_demand_all:
            lst.append(i)
        else:
            # Sort and match croplands starting from the closest one
            sort_field = "NEAR_DIST"
            sql_clause = (None, "ORDER BY NEAR_DIST")  # Sort by distance (ascending)
            
            # Go through sorted croplands
            cropland_demand_a = 0
            distance = None
            fields = [cropland_id, cropland_value, sort_field]
            
            with arcpy.da.SearchCursor(cropland_select, fields, sql_clause=sql_clause) as cursor:
                for row in cursor:
                    cropland_demand_a += row[1]  # Accumulate cropland P demand
                    distance = row[2]  # Get distance to WWTP
                    
                    if cropland_demand_a >= WWTP_supply:
                        output_name = f"cropland{i}"
                        output_path = arcpy.ValidateTableName(output_name, workspace)
                        if arcpy.Exists(output_path):
                            arcpy.Delete_management(output_path)  # Delete if already exists
                        # # Save selected croplands that match the demand
                        arcpy.FeatureClassToFeatureClass_conversion(cropland_select, workspace, output_name, f"NEAR_FID = {i} And NEAR_DIST <= {distance}")
                        break
      
    return lst

# Re-matching between wastewater treatment plants and croplands
def rematch(cropland,WWTP,cropland_id,cropland_value,workspace,workspace_default,lst,num_count):
    # Try to select all matched cropland features in the workspace
    arcpy.env.workspace = workspace
    cropland_sure = arcpy.ListFeatureClasses("cropland*")
    num_count_name = "cropland_merge"+str(num_count)
    # num_count_path = arcpy.ValidateTableName(num_count_name,workspace_default)
    num_count_path = workspace_default + "\\" + num_count_name
    if arcpy.Exists(num_count_path):
        arcpy.Delete_management(num_count_path)
    cropland_merge = arcpy.Merge_management(cropland_sure,num_count_path)

    # Select WWTPs that haven't been matched yet

    objectid_str = ','.join(map(str, lst))   # Convert list to comma-separated string
    sql_expression = f"OBJECTID IN ({objectid_str})"
    WWTP_tobe_matched = arcpy.SelectLayerByAttribute_management(WWTP, "NEW_SELECTION", sql_expression)

    # Select croplands that are NOT intersecting with already matched croplands
    cropland_tobe_matched = arcpy.SelectLayerByLocation_management(cropland,"INTERSECT",cropland_merge,"","","INVERT")
    arcpy.Near_analysis(cropland_tobe_matched,WWTP_tobe_matched,"","","","GEODESIC")
    # arcpy.env.workspace = workspace
    for i in lst:
        cropland_select = arcpy.SelectLayerByAttribute_management(cropland_tobe_matched,"",f"NEAR_FID = {i}")
        cropland_demand_all = sum(row[0] for row in arcpy.da.SearchCursor(cropland_select, [cropland_value]))

        WWTP_supply = WWTP_info.get(i,0)
        if WWTP_supply > cropland_demand_all:
            pass
        else:
            lst.remove(i)
            # Sort and select the nearest croplands for matching
            sort_field = "NEAR_DIST"
            sql_clause = (None, "ORDER BY NEAR_DIST")
            
            cropland_demand_a = 0
            distance = None
            fields = [cropland_id, cropland_value, sort_field]
            
            with arcpy.da.SearchCursor(cropland_select, fields, sql_clause=sql_clause) as cursor:
                for row in cursor:
                    cropland_demand_a += row[1]  # Accumulate Cropland P demand
                    distance = row[2]  # Get NEAR_DIST value
                    
                    if cropland_demand_a >= WWTP_supply:
                        output_name = f"cropland{i}"
                        output_path = arcpy.ValidateTableName(output_name, workspace)
                        if arcpy.Exists(output_path):
                            arcpy.Delete_management(output_path)  # Delete if already exists
                        # Using attribute selection removes previous FID selections,
                        # So this filter should include all previous conditions!
                        arcpy.FeatureClassToFeatureClass_conversion(cropland_select, workspace, output_name, f"NEAR_FID = {i} And NEAR_DIST <= {distance}")
                        break
    return lst


if __name__ == "__main__":
    # Store cropland information
    cropland_in_road = "E:\\W_C\\special_process_25.gdb\\cropland_China_inverse_with_Shanghai_Guangdong" # "E:\\W_C\\crop.gdb\\crop_China_nearRoad" # "E:\\W_C\\crop.gdb\\crop_Hainan_nearRoad"
    cropland_id = "OBJECTID"  # Field name for cropland ID
    cropland_value = "P_demand_Mg_25" # Field name for P demand (25% cropland P demand rate scenario)
    store_information(cropland_in_road, cropland_id, cropland_value, "cropland")

    # Store WWTPs' information
    WWTP_in_road = "E:\\W_C\\special_process_25.gdb\\WWTPs_large_Shanghai_Guangdong" # "E:\\WWTP_China\\WWTP.gdb\\WWTP_China_5_nearRoad_D" # "E:\\W_C\\WWTP.gdb\\WWTP_Hainan_5_nearRoad" # 
    WWTP_id = "OBJECTID"  # Field name for WWTP ID
    WWTP_value = "GPS_X__Mg_P"  # Field name for P supply
    store_information(WWTP_in_road, WWTP_id, WWTP_value, "WWTP")

    # First matching between WWTP and cropland
    cropland = "E:\\W_C\\special_process_25.gdb\\cropland_China_inverse_with_Shanghai_Guangdong" # "E:\\W_C\\crop.gdb\\crop_China_nearRoad" # "E:\\W_C\\crop.gdb\\crop_Hainan_nearRoad"
    WWTP = "E:\\W_C\\special_process_25.gdb\\WWTPs_large_Shanghai_Guangdong" # "E:\\WWTP_China\\WWTP.gdb\\WWTP_China_5_nearRoad_D" # "E:\\W_C\\WWTP.gdb\\WWTP_Hainan_5_nearRoad"
    cropland_id = "OBJECTID"
    cropland_value = "P_demand_Mg_25"
    workspace = "E:\\W_C\\match_CC_25_special.gdb" # "D:\\W_C\\match_CC_25.gdb" # "E:\\W_C\\match_CC_hainan_25.gdb" # Output workspace for matched croplands
    lst = []
    lst = match(cropland, WWTP, cropland_id, cropland_value, workspace, lst)
    print("Matching completed successfully.(the first time)")
    print(lst)

    # Re-matching for unmatched WWTPs
    cropland = "E:\\W_C\\special_process_25.gdb\\cropland_China_inverse_with_Shanghai_Guangdong" # "E:\\W_C\\crop.gdb\\crop_China_nearRoad" # "E:\\W_C\\crop.gdb\\crop_Hainan_nearRoad"
    WWTP = "E:\\W_C\\special_process_25.gdb\\WWTPs_large_Shanghai_Guangdong" # "E:\\WWTP_China\\WWTP.gdb\\WWTP_China_5_nearRoad_D" # "E:\\W_C\\WWTP.gdb\\WWTP_Hainan_5_nearRoad" # 
    cropland_id = "OBJECTID"
    cropland_value = "P_demand_Mg_25"
    num_count = 1 # Record the number of rematching rounds
    workspace = "E:\\W_C\\match_CC_25_special.gdb" # "D:\\W_C\\match_CC_25.gdb" # "E:\\W_C\\match_CC_hainan_25.gdb"  # Workspace for matched cropland outputs
    workspace_default = "E:\\W_C\\workspace_default_CC_25_special.gdb" # "D:\\W_C\\workspace_default_CC_25.gdb" # "E:\\W_C\\workspace_default_CC_hainan_25.gdb" # Temporary workspace
    
    # Keep rematching until all WWTPs are matched
    while len(lst) != 0:
        rematch(cropland,WWTP,cropland_id,cropland_value,workspace,workspace_default,lst,num_count)
        print(f"number {num_count} rematch successfullt")
        num_count = num_count + 1
        
### At the beginning, lst holds the IDs of WWTPs that couldn't match cropland in the first round.
### Each round removes successfully matched WWTPs from lst.
### The loop continues until lst is empty, meaning all WWTPs are matched.