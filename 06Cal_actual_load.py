import os
import pandas as pd

# Extract digits from a string
def extract_num(string):
    return ''.join([s for s in string if s.isdigit()])

# Read distance and farmland phosphorus demand data from Excel
def read_excel(filepath):
    df = pd.read_excel(filepath)
    global matrix
    matrix = df.iloc[:, 1:-1]  # Read all rows, columns from 2nd to second-last
    return matrix

# Calculate transport distance for each vehicle route
def calDistance(vehicle_route, matrix):
    distance = []
    for i in vehicle_route:  
        # Assume each route transports more than one farmland; loop skips if only one farmland
        i = str(i)
        route = [int(float(x)) for x in i.split('-')]
        dis = 0
        for j in range(len(route) - 1):
            dis += matrix.iloc[route[j] - 1, route[j + 1] - 1]  # Sum distance between farmlands
        dis += matrix.iloc[0, route[0] - 1]  # Add distance from wastewater plant to first farmland
        distance.append(dis)
    return distance

# Remove all NaN elements from the end of a list
def del_nan(lst):
    while lst and pd.isna(lst[-1]):  # Check if last element is NaN
        lst.pop()  # Remove last NaN element
    return lst

# Calculate actual load weight for each vehicle
def cal_load(vehicle_route, vehicle_best, demand_list):
    load = []
    for i in range(len(vehicle_route)):
        # Remove trailing NaN values (commented out here)
        '''
        while vehicle_route[i] and isinstance(vehicle_route[i], list) and len(vehicle_route[i]) > 0:
            if isinstance(vehicle_route[i][-1], float) and math.isnan(vehicle_route[i][-1]):
                vehicle_route[i].pop()
            else:
                break
        '''

        route = [int(float(x)) for x in str(vehicle_route[i]).split('-')]
        load_add = 0
        for j in route:
            load_add += demand_list[j - 1]

        # If a farmland requires multiple vehicles to transport its phosphorus
        if load_add > vehicle_best[i]:
            if len(route) == 1:
                demand_list[route[0] - 1] = demand_list[route[0] - 1] - vehicle_best[i]
            else:
                # For all but last farmland, phosphorus demand is fully met
                last_demand = demand_list[route[-1] - 1]
                for i in route:
                    demand_list[i - 1] = 0
                demand_list[route[-1] - 1] = load_add - vehicle_best[i]
            load_add = vehicle_best[i]  # Update load_add after adjustment
            load.append(load_add)  # Add load weight to list

        else:
            for y in route:
                demand_list[y - 1] = 0
            load.append(load_add)  # Add load weight to list

    return load

# Main function to run calculations and save results
def run(path_num, sapath_num, outpath, index):
    # Read distance cost matrix
    matrix = read_excel(path_num)

    # Read four columns from SA results
    sa_colums = ["routes_first", "vehicle_initial", "routes_best", "vehicle_best"]
    df = pd.read_excel(sapath_num, usecols=sa_colums)

    # Calculate driving distance for each truck under optimal conditions
    r_f_b = del_nan(df["routes_best"].tolist())
    routes_best_distance = calDistance(r_f_b, matrix)

    # Calculate actual load for each truck under optimal conditions
    r_b = del_nan(df["routes_best"].tolist())
    v_b = del_nan(df["vehicle_best"].tolist())
    demand = pd.read_excel(path_num)["demand"].tolist()
    demand = [i / index for i in demand]  # Adjust demand with conversion coefficient
    actual_load = cal_load(r_b, v_b, demand)

    # Create a copy of original DataFrame to store results
    result_df = pd.read_excel(sapath_num)

    # Calculate phosphorus transport distance per truck per unit phosphorus
    per_P_vehicle_transport_distance = []
    for i in range(len(routes_best_distance)):
        per_P_vehicle_transport_distance.append(routes_best_distance[i] / (1000 * actual_load[i] * index))

    # Pad with NaN if result lengths are shorter than DataFrame rows
    while len(routes_best_distance) < len(df):
        routes_best_distance.append(float('nan'))
        per_P_vehicle_transport_distance.append(float('nan'))
    while len(actual_load) < len(df):
        actual_load.append(float('nan'))

    # Add new columns to DataFrame
    result_df["routes_best_distance"] = routes_best_distance
    result_df["actual_load"] = actual_load
    result_df["per_P_vehicle_transport_distance"] = per_P_vehicle_transport_distance

    # Create target folder if not exist
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    # Define save path with extracted number in filename
    num = extract_num(path_num[-10:])
    target_file = os.path.join(outpath, f"sapath_load{num}.xlsx")

    # Save results to Excel
    result_df.to_excel(target_file, index=False)

    print(f"Results saved to: {target_file}")

# Sort list by numeric value extracted from last part of string
def sort_by_num(lst):
    sorted_lst = sorted(lst, key=lambda x: int(''.join(filter(str.isdigit, x[-10:-1]))))
    return sorted_lst

if __name__ == "__main__":
    # Param 1: path_name - path to truck transport routes (distance matrices)
    # Param 2: sapath_name - folder with SA algorithm results
    # Param 3: outpath - folder to save detailed truck transport info
    # Param 4: index - conversion coefficient for guano or sludge

    # Paths for distance matrices
    path_name = 'example for SA/path' # r"E:\vhicle_combination\csv_25_processed"
    path_dir = os.listdir(path_name)
    path = [os.path.join(path_name, i) for i in path_dir]
    path = sort_by_num(path)
    print(path)

    # Paths for SA results
    sapath_name = 'example for SA/result' # r"E:\vehicle_gai\result_25%_0.1265"
    sapath_dir = os.listdir(sapath_name)
    sapath = [os.path.join(sapath_name, i, "sapath" + extract_num(i) + ".xlsx") for i in sapath_dir]
    sapath = sort_by_num(sapath)
    print(sapath)

    outpath = 'example for SA/result' # r"E:\vehicle_gai\Per_vehicle_actual_load_25%_0.1265"

    for i in range(len(sapath)):
        if os.path.exists(os.path.join(outpath, f"sapath_load{i+1}.xlsx")):
            print(f"{sapath[i]} already exists, skipping calculation")
        else:
            run(path[i], sapath[i], outpath, 0.1265)