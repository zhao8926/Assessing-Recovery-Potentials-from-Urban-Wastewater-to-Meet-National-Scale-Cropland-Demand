# -*- coding: utf-8 -*-
import arcpy
import os
import multiprocessing
# import sys
# sys.stderr = open(os.devnull,'w')

# Extract numbers from a string
def extract_numbers_from_string(string):
    numbers = ""
    for char in string:
        if char.isdigit():
            numbers += char
    return numbers

def identify_list(workspace,path_dir):
    arcpy.env.workspace = workspace
    fc_lst = [f"c_W{i}" for i in path_dir]
    # fc_lst = arcpy.ListFeatureClasses("c_W*")
    sorted_list = sorted(fc_lst, key=lambda x: int(''.join(filter(str.isdigit, x))))

    # Get list of already computed OD matrix numbers
    OD_Dataset = os.listdir(path_dir)
    OD_num = [int(''.join(filter(str.isdigit, path))) for path in OD_Dataset]
    # print(OD_num)

    # Filter sorted_list to only keep items not in OD_num
    s = [item for item in sorted_list if int(extract_numbers_from_string(item)) not in OD_num]
    print(s)

    return s

def cal_OD(workspace,cw,path_dir,roadnet_YRD_3_):
    WWTP = os.path.join(workspace,cw)
    num = extract_numbers_from_string(cw)
    OD_Path_name = "OD" + num
    OD_path = os.path.join(path_dir,OD_Path_name) 
    if os.path.exists(OD_path):
        print(f"{OD_Path_name} already exists, skipping calculation")
    else:
        os.makedirs(OD_path)
        GDB = arcpy.management.CreateFileGDB(OD_path,"OD_MATRIX"+num)
        print(f"{OD_Path_name} created, starting OD cost matrix calculation...")
        OD_name="ODCostMatrix"+num
        arcpy.env.workspace = str(GDB)
        # os.path.join(OD_path,OD_name+".gdb")  # For example, "E:\\W_C\\path\\OD1\\OD_MATRIX1.gdb"

        # Process: Create OD Cost Matrix Analysis Layer
        OD_1 = arcpy.MakeODCostMatrixAnalysisLayer_na(network_data_source=roadnet_YRD_3_, layer_name="", 
                                                    travel_mode="", cutoff=None, number_of_destinations_to_find=None, 
                                                    time_of_day="", time_zone="LOCAL_TIME_AT_LOCATIONS", line_shape="STRAIGHT_LINES", 
                                                    accumulate_attributes=["Length", "Time"])[0]


        # Process: Add Locations (Origins)
        OD_2 = arcpy.AddLocations_na(in_network_analysis_layer=OD_1,
                                     sub_layer="起始点", # Origins
                                     in_table=WWTP, 
                                    field_mappings="Name Name #;TargetDestinationCount # #;CurbApproach # 0",  
                                    search_tolerance="50 Meters", sort_field="", 
                                    search_criteria=[["road_China_Merge", "SHAPE"], 
                                                    ["road_China_ND_Junctions", "NONE"]], 
                                    match_type="MATCH_TO_CLOSEST", append="APPEND", 
                                    snap_to_position_along_network="SNAP", snap_offset="1 Meters", exclude_restricted_elements="EXCLUDE", 
                                    search_query=[["road_China_Merge", ""], 
                                                  ["road_China_ND_Junctions", ""]])[0]

        # Process: Add Locations (Destinations)
        OD_3 = arcpy.AddLocations_na(in_network_analysis_layer=OD_2,
                                    sub_layer="目的地点", # Destinations
                                    in_table=WWTP,
                                    field_mappings="Name Name #;CurbApproach # 0", 
                                    search_tolerance="50 Meters", sort_field="", 
                                    search_criteria=[["road_China_Merge", "SHAPE"], 
                                                    ["road_China_ND_Junctions", "NONE"]], 
                                    match_type="MATCH_TO_CLOSEST", append="APPEND", snap_to_position_along_network="SNAP", 
                                    snap_offset="1 Meters", exclude_restricted_elements="EXCLUDE", 
                                    search_query=[["road_China_Merge", ""], 
                                                 ["road_China_ND_Junctions", ""]])[0]

        # Process: Solve the OD cost matrix
        roadnet_layer, solve_successfully = arcpy.Solve_na(in_network_analysis_layer=OD_3, ignore_invalids="SKIP", 
                                  terminate_on_solve_error="TERMINATE", simplification_tolerance="", overrides="")
        print(OD_name + " calculation completed!")

def main():
    workspace = "E:\\W_C\\cW_CC_25.gdb" # GDB containing WWTP and cropland combined features
    path_dir = "E:\W_C\path_25" # Directory to save OD matrices
    roadnet_YRD_3_ = "E:\\WWTP_China\\roadnet.gdb\\road_China\\road_China_ND" # Road network dataset
    sorted_list = identify_list(workspace,path_dir)

    # Create a process pool
    num_processes = 3
    with multiprocessing.Pool(processes=num_processes) as pool:
        ### Use multiprocessing to calculate OD matrices
        pool.starmap(cal_OD,[(workspace,cw,path_dir,roadnet_YRD_3_) for cw in sorted_list])

if __name__ == "__main__":
    main()
