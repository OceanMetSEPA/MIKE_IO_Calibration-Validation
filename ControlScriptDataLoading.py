#%% GENERAL REQUIREMENTS

#Install https://dhi.github.io/mikeio/ using the command: pip install mikeio

#TEST


#%% SET THE PATH TO THE CALIBRATION/VALIDATION LIBRARY SCRIPTS

import sys
from pathlib import Path

LIBPATH = Path(r"C:\CodeLibraryDev\MIKE_IO_Calibration-Validation")
if str(LIBPATH) not in sys.path:
    sys.path.append(str(LIBPATH))

#%% DEFINE THE LIST OF DFS0 FILES TO IMPORT
from pathlib import Path
# List of dfs0 files (absolute paths are safest)
dfs0_files = [
    Path(r"\\asb-hpc-vm01\Model Data\EastSkye\Run13_202507v8\test3d_Alt13_2025v8.m3fm - Result Files\MAOB1.dfs0"),
    Path(r"\\asb-hpc-vm01\Model Data\EastSkye\Run13_202507v8\test3d_Alt13_2025v8.m3fm - Result Files\SCQN1_17042020.dfs0"),
    
]



#%% LOAD THE DFS0 FILES
from load_dfs0_list import load_dfs0s

dfs0_output = load_dfs0s(dfs0_files)

#%% PRINT A SUMMARY OF THE LOADED DFS0 FILES
from print_dfs0_list import print_dfs0s

dfs0_output_summary = print_dfs0s(dfs0_output, dfs0_files)

#%%
from load_dfs0_list_todataframe import load_dfs0s_to_dataframe

# dfs0_files is already defined in your session
bundle = load_dfs0s_to_dataframe(dfs0_files)


#%%
# Example usage
print(bundle)
print(bundle.maob1.datetime)
print(bundle.maob1.dataframe.columns)


test=bundle.maob1.datetime

#%%
# dot access
time = bundle.flow_stationb.datetime
speed = bundle.flow_stationb.current_speed
level = bundle.stage_stationa.water_level
