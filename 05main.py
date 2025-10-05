import subprocess
import os
from concurrent.futures import ProcessPoolExecutor

# List all files in the data folder and print them as a list
data_folder = "example for SA/path"
file_list = os.listdir(data_folder)

# Create the result folder if it doesn't exist
result_folder = "example for SA/result"
os.makedirs(result_folder, exist_ok=True)

names = []

# For each file, create a folder in the result directory using the filename without extension
for file_name in file_list:
    file_name_without_extension = os.path.splitext(file_name)[0]
    names.append(file_name_without_extension)
    folder_name = os.path.join(result_folder, file_name_without_extension)
    os.makedirs(folder_name, exist_ok=True)

# Sort filenames based on the number part after the 4th character
names = sorted(names, key=lambda x: int(x[4:]))

# Define a function to call SA.py script with a data name
def run_sa(data_name):
    try:
        subprocess.run(["python", "04SA_find_optimal_combination.py", data_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error calling 04SA_find_optimal_combination.py for {data_name}:", e)

# Set the maximum number of parallel processes
MAX_WORKERS = 4

# Set the maximum number of parallel processes
if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(run_sa, names)
