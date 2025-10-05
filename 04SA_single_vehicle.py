# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xlsxwriter
import random
import time
import copy
import math
import sys
import os
np.set_printoptions(threshold = np.inf)

class Logger(object):
    def __init__(self, filename = "Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass
    
class Sol():
    def __init__(self):
        self.nodes_seq = None
        self.obj = None
        self.dis = None
        self.routes = None
        self.vehicle = None
        self.load = None

class Node():
    def __init__(self):
        self.name = 0
        self.seq_no = 0
        self.demand = 0
        self.vehicle = 0

class Model():
    def __init__(self):
        self.load_capacity = 35
        self.best_sol = None
        self.node_list = []
        self.node_seq_no_list = []
        self.depot = None
        self.number_of_nodes = 0
        self.temp_sol = None
        
# Read data from Excel
def read_excel(filepath, model, sheet_name=''):
    seq = -1
    # if sheet_name:
    #     # print(sheet_name)
    #     # df = pd.DataFrame
    #     df = pd.read_excel(filepath, sheet_name=sheet_name)
    df = pd.read_excel(filepath)
    global matrix
    matrix = df.iloc[:, 1:-1]
    for i in range(df.shape[0]):
        node = Node()
        node.seq_no = seq
        node.name = df['no'][i]
        demand = df['demand'][i]/0.1265 # Convert P weight to struvite weight
        node.vehicle = demand//35  # Max vehicle load capacity
        node.demand = demand - node.vehicle * 35
        if df['demand'][i] == 0:
            model.depot = node
        else:
            model.node_list.append(node)
            model.node_seq_no_list.append(node.seq_no)
        seq = seq + 1
    model.number_of_nodes = len(model.node_list)
    print('Data reading completed')

# Randomly generate an initial solution; node_seq is a list of all cropland node IDs
def initial_sol(node_seq):
    node_seq = copy.deepcopy(node_seq)
    random.seed(12)
    random.shuffle(node_seq)
    print("Initial solution generated: ", node_seq)
    return node_seq

# Swap operation: swap two elements in the list
def swap(nodes_seq):
    sol_length = len(nodes_seq) - 1
    i = random.randint(0, sol_length)
    j = random.randint(0, sol_length)
    while i == j:
        j = random.randint(0, sol_length)
    #print("Swap position 1: ", i, "-----", nodes_seq[i])
    #print("Swap position 2: ", j, "-----", nodes_seq[j])
    nodes_seq[i], nodes_seq[j] = nodes_seq[j], nodes_seq[i]
    #print("Solution after swap:", nodes_seq)
    return nodes_seq

# Reverse operation: randomly reverse the order of a segment between two elements in the list
def reverse(nodes_seq):
    sol_length = len(nodes_seq) - 1
    i = random.randint(0, sol_length)
    j = random.randint(0, sol_length)
    while i == j:
        j = random.randint(0, sol_length)
    if i < j:
        reverse_part = nodes_seq[i:j + 1]
        # print("Segment to reverse:", reverse_part)
        last_part = nodes_seq[j + 1:]
        del nodes_seq[i:]
        reverse_part.reverse()
        nodes_seq.extend(reverse_part)
        nodes_seq.extend(last_part)
    else:
        reverse_part = nodes_seq[j:i + 1]
        # print("Segment to reverse:", reverse_part)
        last_part = nodes_seq[i + 1:]
        del nodes_seq[j:]
        reverse_part.reverse()
        nodes_seq.extend(reverse_part)
        nodes_seq.extend(last_part)
    # print("Solution after reverse:", nodes_seq)
    return nodes_seq

# Insert operation: insert the selected element after another randomly chosen position
def insert(nodes_seq):
    sol_length = len(nodes_seq) - 1
    i = random.randint(0, sol_length)
    selected_one = nodes_seq[i]
    # print("Element selected for insertion:", i, nodes_seq[i])
    del nodes_seq[i]
    j = random.randint(0, sol_length - 1)
    while j == i - 1:  # Ensure the element is not inserted back to its original position
        j = random.randint(0, sol_length - 1)
    # print("Insert position:", j, nodes_seq[j])
    nodes_seq.insert(j + 1, selected_one)
    # print("Solution after insertion:", nodes_seq)
    return nodes_seq

# Roulette wheel selection for neighborhood operation
# Probability ranges: swap [0, 0.2), reverse [0.2, 0.7), insert [0.7, 1)
def roulette(p_swap = 0.2, p_reverse = 0.5, p_insert = 0.3):
    random_number = random.uniform(0, 1)  # 不包含1
    if 0 <= random_number < p_swap:
        way = 0  # swap
        # print("Roulette selected operation: swap")
    elif p_swap <= random_number < p_swap + p_reverse:
        way = 1  # reverse
        # print("Roulette selected operation: reverse")
    else:
        way = 2  # insert
        # print("Roulette selected operation: insert")
    return way

# Calculate a list of actions using roulette selection
def cal_action(n):
    action_list = []
    for i in range(n):
        way = roulette(0.2, 0.5, 0.3)
        action_list.append(way)
    print("Action list:", action_list)
    return action_list


def action(nodes_seq, way):
    nodes_seq = copy.deepcopy(nodes_seq)
    if way == 0:
        nodes_seq = swap(nodes_seq)
        return nodes_seq
    elif way == 1:
        nodes_seq = reverse(nodes_seq)
        return nodes_seq
    else:
        nodes_seq = insert(nodes_seq)
        return nodes_seq
    
# Split TSP route into vehicle paths and calculate the number of vehicles
# nodes_seq is a random initial solution containing all cropland node IDs
# model holds initial info for all croplands
# In data reading step, phosphorus weight was converted using struvite's phosphorus content percentage
def splitRoutes(nodes_seq, model):
    num_vehicle = None
    vehicle_routes = []
    route = []
    vehicle=[]
    vehicle_cap = model.load_capacity
    # vehicle_cap = random.choice(model.load_capacity)
    remained_cap = vehicle_cap
    vehicle.append(remained_cap)
    for node_no in nodes_seq:
        if remained_cap - model.node_list[node_no].demand >= 0:# model.node_list contains all cropland Nodes with demand
            route.append(node_no)
            remained_cap = remained_cap - model.node_list[node_no].demand
        else:
            continue_lop = True
            cropland = model.node_list[node_no].demand
            while continue_lop:
                vehicle_cap = model.load_capacity
                # vehicle_cap = random.choice(model.load_capacity)
                remained_cap = vehicle_cap
                vehicle.append(remained_cap)
                if cropland > remained_cap:
                    if len(route) != 0:
                        vehicle_routes.append(route) # Assign previous route to a vehicle
                        route = [node_no] # Start a new route
                        cropland = cropland - remained_cap # Reduce remaining cropland demand
                    else:
                        route = [node_no] # Start a new route
                        cropland = cropland - remained_cap
                else:
                    continue_lop = False
                    vehicle_routes.append(route)
                    route=[node_no]
                    remained_cap = remained_cap - cropland
    vehicle_routes.append(route) # Final route segmentation
    num_vehicle = len(vehicle_routes)
    return num_vehicle, vehicle_routes, vehicle



# Calculate route distance for a single vehicle's trip
def calDistance(route, model):
    distance = 0
    depot = model.depot
    for i in range(len(route) - 1): # Assumes route has more than one node; loop skips if only one cropland
        from_node = model.node_list[route[i]]
        to_node = model.node_list[route[i + 1]]
        distance += matrix.iloc[from_node.seq_no+1, to_node.seq_no+1]
    first_node = model.node_list[route[0]]
    # last_node = model.node_list[route[-1]]
    distance += matrix.iloc[0, first_node.seq_no+1]
    return distance

# Calculate objective function; nodes_seq is a random initial solution containing all cropland node IDs
def calObj(nodes_seq, model):
    num_vehicle, vehicle_routes, vehicle = splitRoutes(nodes_seq, model) # Calculate number of vehicles and routes
    distances = 0
    filtered_positions = [idx for idx, val in enumerate(vehicle_routes) if not val]
    vehicle_routes = [val for idx, val in enumerate(vehicle_routes) if idx not in filtered_positions]
    vehicle = [val for idx, val in enumerate(vehicle) if idx not in filtered_positions]

    # Check if the first vehicle can fully transport the first cropland's demand
    if len(vehicle_routes) == len(vehicle):
        pass
    else:
        del(vehicle[0])
    
    vehicle_load = sum(vehicle)
    num_vehicle = len(vehicle_routes)
    for route in vehicle_routes:
        distances += calDistance(route, model)
    return num_vehicle, vehicle_routes, distances, vehicle, vehicle_load

# Plot objective function values
def plotObj(obj_list, pic_path):
    plt.rcParams['font.sans-serif'] = ['SimHei']  # show chinese
    plt.rcParams['axes.unicode_minus'] = False  # Show minus sign
    plt.plot(np.arange(1, len(obj_list) + 1), obj_list)
    plt.xlabel('Iterations')
    plt.ylabel('Distance')
    plt.grid()
    plt.xlim(1, len(obj_list) + 1)
    plt.savefig(pic_path)
    # plt.show()
    
# Main SA function
# T0: initial temperature, Tf: final temperature, detaT: cooling factor
def run(filepath, T0, Tf, detaT, xlsx_path, pic_path, sheet_name=''):
    model = Model()
    read_excel(filepath, model, sheet_name=sheet_name)
    history_best_dis = []
    sol = Sol() # SA solution
    sol.nodes_seq = initial_sol(model.node_seq_no_list) # Generate random initial solution from cropland node IDs
    sol.obj, sol.routes, sol.dis, sol.vehicle, sol.load = calObj(sol.nodes_seq, model) # Calculate vehicles, routes, distance
    
    ### Before SA search, add distance and load for parts transported by 35-ton trucks (exceeding load filtered out)
    sol_first = copy.deepcopy(sol)
    for node in model.node_list:
        if node.vehicle == 0:
            pass
        else:
            for num in range(int(node.vehicle)):
                # vehicle_routes.append([int(node.name)-2])
                # vehicle.append(35)
                sol_first.routes.insert(0,[int(node.name)-2])
                sol_first.vehicle.insert(0,35)
                sol_first.dis += matrix.iloc[0, node.seq_no+1]
                sol_first.load += 35
    sol_first.obj = len(sol_first.routes)
    print("Initial solution including 35Mg truck loads: ", sol_first.obj, sol_first.routes, sol_first.dis, sol_first.vehicle, sol_first.load)
    ##################################################################################

    print("Starting SA algorithm to find optimal solution (excluding parts transported by 35-ton trucks)")
    print("Initial objective:", sol.obj, sol.routes, sol.dis, sol.vehicle, sol.load)
    firsts = copy.deepcopy(sol_first.routes) # Copy cropland transportation routes list
    for first in firsts:
        for i in range(len(first)):
            first[i] = model.node_list[first[i]].name # Convert node indices to GIS cropland IDs
    work = xlsxwriter.Workbook(xlsx_path)
    worksheet = work.add_worksheet(sheet_name)
    worksheet.write(0, 0, 'filename')
    worksheet.write(0, 1, 'drive distance_first')
    worksheet.write(0, 2, 'num_vehicle_first')
    worksheet.write(0, 3, 'routes_first')
    worksheet.write(0, 4, 'vehicle_initial')
    worksheet.write(0, 5, 'drive distance_best')
    worksheet.write(0, 6, 'num_vehicle_best')
    worksheet.write(0, 7, 'routes_best')
    worksheet.write(0, 8, 'vehicle_best')
    worksheet.write(1, 0, sheet_name)
    worksheet.write(1, 1, sol_first.dis)
    worksheet.write(1, 2, sol_first.obj)
    # worksheet.write(1, 7, str(sol.vehicle))
    for row, route in enumerate(firsts):
        r = [str(i) for i in route]
        worksheet.write(row + 1, 3, '-'.join(r)) # Write initial routes starting from second row
    for row, vehicle in enumerate(sol_first.vehicle):
        worksheet.write(row + 1, 4, vehicle)
    model.best_sol = copy.deepcopy(sol) # Keep a copy of initial solution (immutable)
    model.temp_sol = copy.deepcopy(sol)
    history_best_dis.append(sol.dis) # Store initial total distance
    Tk = T0  # Current temperature
    while Tk >= Tf:
        print("Current temperature: ", Tk)
        action_list = cal_action(500) # Generate list of 500 operations
        for i in range(500):
            new_sol = Sol() # New solution instance
            new_sol.nodes_seq = action(sol.nodes_seq, action_list[i]) # Apply one of three operations
            new_sol.obj, new_sol.routes, new_sol.dis, new_sol.vehicle, new_sol.load = calObj(new_sol.nodes_seq, model) # Calculate new solution metrics
            deta_f = new_sol.dis - sol.dis
            # New interpretation of acceptance criteria
            if deta_f <= 0 or math.exp(-deta_f / Tk) > random.random():
                sol = copy.deepcopy(new_sol)
            
            # Update temp_sol if new solution distance is shorter
            if sol.dis <= model.temp_sol.dis:
                model.temp_sol = copy.deepcopy(sol)
            
            ### Update best solution based on distance and load
            if sol.dis < model.best_sol.dis:
                model.best_sol = copy.deepcopy(sol)
            if model.temp_sol.load < model.best_sol.load:
                model.best_sol = copy.deepcopy(model.temp_sol)

        Tk = Tk * detaT # Cool down
        history_best_dis.append(model.best_sol.dis)
        print("Best solution at current temperature: ", model.best_sol.dis)
    print("Cooling finished--------------------------------------------------------------------------------")
    print("Optimization process: ", history_best_dis)
    print(f"Temperature: {Tk}, Current distance: {sol.dis}, Best distance: {model.best_sol.dis}")
    print("Best route: ", model.best_sol.routes)
    print("Improvement rate: ", history_best_dis[-1]/history_best_dis[0]*100, '%')
    print("Best vehicle combination: ", model.best_sol.vehicle)
    print("Best vehicle load:", model.best_sol.load)

    ### After SA search, add back the parts transported by 35-ton vehicles
    print("Adding back the initial 35Mg truck transport parts")
    for node in model.node_list:
        if node.vehicle == 0:
            pass
        else:
            for num in range(int(node.vehicle)):
                # vehicle_routes.append([int(node.name)-2])
                # vehicle.append(35)
                model.best_sol.routes.insert(0,[int(node.name)-2])
                model.best_sol.vehicle.insert(0,35)
                model.best_sol.dis += matrix.iloc[0, node.seq_no+1]
                model.best_sol.load += 35
    model.best_sol.obj = len(model.best_sol.routes)
    ##################################################################################
    
    for route in model.best_sol.routes:
        for i in range(len(route)):
            route[i] = model.node_list[route[i]].name
    print("Final best routes: ", model.best_sol.routes)
    worksheet.write(1, 5, model.best_sol.dis)
    worksheet.write(1, 6, model.best_sol.obj)
    # worksheet.write(1, 8, str(model.best_sol.vehicle))
    for row, route in enumerate(model.best_sol.routes):
        r = [str(i) for i in route]
        worksheet.write(row + 1, 7, '-'.join(r))
    for row, vehicle in enumerate(model.best_sol.vehicle):
        worksheet.write(row + 1, 8, vehicle)
    print("Final solution including 35Mg truck parts: ", model.best_sol.obj, model.best_sol.routes, model.best_sol.dis, model.best_sol.vehicle, model.best_sol.load)
    work.close()
    plotObj(history_best_dis, pic_path)

if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print("Usage: python SA.py <name>")
    #     sys.exit(1)

    name = sys.argv[1]
    # print("Received variable:", name)
    print('Starting calculation for ' + name)
    # If you don't want to skip already completed calculations, comment out this section
    # Check if there are exactly 3 files in the result folder
    if len(os.listdir('result/'+name)) == 3:
        print(name + ' calculation is already finished')
    else:    
        start = time.perf_counter()
        print('Calculating: ' + name)
        p = 'example for SA/path/'
        r = 'example for SA/result/'+name+'/'
        # sys.stdout = Logger(r + name +'.txt')
        sys.stdout = open(r + name +'.txt', mode='w', encoding='utf-8')

        file = p+name + '.xlsx'
        xlsx_path = r+'sa'+name+'.xlsx'
        pic_path = r+name+'.png'
        sheet_name = 'Sheet1'
        run(filepath = file, T0 = 1000, Tf = 0.001, detaT = 0.99, xlsx_path = xlsx_path, pic_path=pic_path, sheet_name=sheet_name)
        print("Output during running is successful")
        end = time.perf_counter()
        print('Time used: {:.4f} min'.format((end - start) / 60))