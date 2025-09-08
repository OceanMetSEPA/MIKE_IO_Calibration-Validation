#%% GENERAL REQUIREMENTS

#Install https://dhi.github.io/mikeio/ using the command: pip install mikeio


#%% SET THE PATH TO THE CALIBRATION/VALIDATION LIBRARY SCRIPTS

import sys
from pathlib import Path

LIBPATH = Path(r"E:\CodeLibraryOps\MIKE_IO_CalibrationValidation")
if str(LIBPATH) not in sys.path:
    sys.path.append(str(LIBPATH))

#%% DEFINE THE LIST OF DFS0 FILES TO IMPORT
from pathlib import Path

# List of dfs0 files (absolute paths are safest)
dfs0_files = [
    Path(r"E:\ASB-HPC-VM01\EastSkye\Run13_202507v8\test3d_Alt13_2025v8.m3fm - Result Files\MAOB1.dfs0"),
#    Path(r"E:\ASB-HPC-VM01\EastSkye\Run13_202507v8\test3d_Alt13_2025v8.m3fm - Result Files\MAOB1_WL.dfs0"),
]

#%% LOAD THE DFS0 FILES
from load_dfs0_list import load_dfs0s

dfs0_output = load_dfs0s(dfs0_files)

#%% PRINT A SUMMARY OF THE LOADED DFS0 FILES
from print_dfs0_list import print_dfs0s

dfs0_output_summary = print_dfs0s(dfs0_output, dfs0_files)

#%% DEFINE THE LIST OF OBSERVED DATA FILES TO IMPORT
from pathlib import Path

# List of observed files (absolute paths are safest)
observed_files = [
    Path(r"\\asb-fp-mod01\AMMU\data\Ocean_Processed_New\AAA_Pre-AppData_NotForRelease\MAOB1_MaolBan\20250410_157048_831054_MaolBan_PF_0_PV_EX\all\pro\MaolBanPhysicalStruct.mat"),
]
#%%

from plot_dfs0_simple import plot_dfs0_item_exact

# Pick dataset from your dict
ds = dfs0_output["MAOB1.dfs0"]

# Plot exact item name
plot_dfs0_item_exact(ds, "bed: Current speed")






#%%



from load_mat_list import load_mat_files

observed_data_matlab = load_mat_files(observed_files)

#%%
from plot_speed_compare import plot_speed_compare

# choose keys exactly as they appear in your dicts
dfs0_key = "MAOB1.dfs0"
mat_key  = "MaolBanPhysicalStruct.mat"

# Plot MIKE item "Current speed" against HG Speed for the bed bin (0)
plot_speed_compare(
    datasets=dfs0_output,
    mat_data=observed_data_matlab,
    dfs0_key=dfs0_key,
    dfs0_item="Current speed",   # exact or substring
    mat_key=mat_key,
    bin_index=2,                 # 0=bed, 1=mid, 2=surface
    label_dfs0="MIKE surface speed",
    label_mat="Observed surface speed",
    # output_html=r"E:\temp\bed_speed_compare.html",   # optional
)
#%%
from align_and_metrics import compare_speed_stats

# choose keys exactly as in your dicts
dfs0_key = "MAOB1.dfs0"
mat_key  = "MaolBanPhysicalStruct.mat"

# Example 1: nearest-time alignment within 10 minutes (no resampling)
df_aligned, stats = compare_speed_stats(
    datasets=dfs0_output,
    mat_data=observed_data_matlab,
    dfs0_key=dfs0_key,
    dfs0_item="Current speed",
    mat_key=mat_key,
    bin_index=0,           # 0=bed, 1=mid, 2=surface
    align_method="asof",
    tolerance="10min",
    resample=None
)

print(stats)
print(df_aligned.head())

# Example 2: match your MATLAB hourly comparison
df_aligned_H, stats_H = compare_speed_stats(
    datasets=dfs0_output,
    mat_data=observed_data_matlab,
    dfs0_key=dfs0_key,
    dfs0_item="Current speed",
    mat_key=mat_key,
    bin_index=0,
    resample="H",          # resample both to hourly means
    align_method="inner"   # exact hourly timestamps after resample
)
print(stats_H)



