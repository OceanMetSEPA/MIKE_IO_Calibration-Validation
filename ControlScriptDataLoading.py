from load_dfs0_list_todataframe import load_dfs0s_to_dataframe

# dfs0_files is already defined in your session
bundle = load_dfs0s_to_dataframe(dfs0_files)

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
