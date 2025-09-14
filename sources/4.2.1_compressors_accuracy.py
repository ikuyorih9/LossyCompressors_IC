# THIS SCRIPT MUST BE RUN ON UBUNTU
import subprocess
import os
import pandas as pd

data_dir = '../results/4.2.1_compressors_accuracy'
data_results_dir = f'{data_dir}/RESULTS'
# EXECUTE DAMICORE
script = "execute_damicore.sh"
output = ""
params = [
    '--all',
    '--reps', '1',
    '--output', '4.2.1_compressors_accuracy'
]
result = subprocess.run(['bash', script] + params, capture_output=False, text=True)

vp_df = []

for load in os.listdir(data_results_dir):
    load_dir = f"{data_results_dir}/{load}"    
    for type in os.listdir(load_dir):
        file_path = f"{load_dir}/{type}"
        df = pd.read_json(file_path)
        vp_df.append(df)

df = pd.concat(vp_df, ignore_index=True)

# TRUE POSITIVE ASSIGNS
vp = (
    df[df["type"] != "ANOTHER-CONTROL"]
      .assign(vp=lambda d: (d["iteration"] != -1).astype(int))
      .groupby(["load", "compressor"], as_index=False)["vp"].sum()
)

# FALSE POSITIVE ASSIGNS
fp = (
    df[df["type"] == "ANOTHER-CONTROL"]              # só os controles
      .assign(fp=lambda d: d["iteration"].ne(-1).astype(int))
      .groupby(["load", "compressor"], as_index=False)["fp"].sum()
)

# OUTPUT TO compressor_simple_accuracy_by_load.csv
result = pd.merge(vp, fp, on=["load", "compressor"], how="outer").fillna(0)
result.to_csv(f"{data_dir}/compressor_simple_accuracy_by_load.csv")

result["vp"] = result["vp"].astype(int)
result["fp"] = result["fp"].astype(int)

total_vp = (
    df[df["type"] != "ANOTHER-CONTROL"]
      .groupby("compressor")
      .size()
      .rename("total_vp")
      .reset_index()
)


total_fp = (
    df[df["type"] == "ANOTHER-CONTROL"]
      .groupby("compressor")
      .size()
      .rename("total_fp")
      .reset_index()
)

resumo = (
    result.groupby("compressor", as_index=False)[["vp","fp"]].sum()
    .merge(total_vp, on="compressor", how="left")
    .merge(total_fp, on="compressor", how="left")
    .fillna(0)
)

# CALCULATE ACCURACY
resumo["vp_accuracy"] = resumo["vp"] / resumo["total_vp"].replace(0, 1)
resumo["fp_accuracy"] = resumo["fp"] / resumo["total_fp"].replace(0, 1)

print(resumo)
# OUTPUT TO compressor_simple_accuracy_total.csv
resumo.to_csv(f"{data_dir}/compressor_simple_accuracy_total.csv")