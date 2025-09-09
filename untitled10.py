from convert_dfs0_to_dataframe import dfs0_to_dataframes

frames = dfs0_to_dataframes(dfs0_output)

df = frames["MAOB1.dfs0"]
print(df.head())
