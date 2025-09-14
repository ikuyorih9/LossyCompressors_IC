# THIS SCRIPT MUST BE RUN ON UBUNTU
import subprocess
import os
import pandas as pd
import numpy as np
import statistics
from utils.format import *

data_dir = '../results/4.2.3_incremental_damicore'
data_results_dir = f'{data_dir}/RESULTS'
types = ['API', 'CONC', 'LOGIC', 'MEMORY', 'MODEL', 'PROCESS', 'TRAIN', 'ANOTHER-CONTROL']

def compute_boxplot_stats(group):
    times = group['time'].tolist()

    avg_time = sum(times) / len(times)
    median_time = statistics.median(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0
    min_time = min(times)
    max_time = max(times)
    q1 = np.percentile(times, 25)
    q3 = np.percentile(times, 75)
    iqr = q3 - q1

    # Whiskers
    lower_whisker = min([v for v in times if v >= q1 - 1.5 * iqr], default=min_time)
    upper_whisker = max([v for v in times if v <= q3 + 1.5 * iqr], default=max_time)

    # Outliers
    outliers = [v for v in times if v < lower_whisker or v > upper_whisker]
    num_outliers = len(outliers)

    return pd.Series({
        'avg_time': avg_time,
        'std_dev': std_dev,
        'min_time': min_time,
        'max_time': max_time,
        'q1': q1,
        'median_time': median_time,
        'q3': q3,
        'iqr': iqr,
        'lower_whisker': lower_whisker,
        'upper_whisker': upper_whisker,
        'num_outliers': num_outliers
    })


# EXECUTE DAMICORE
script = "execute_damicore.sh"
output = ""
params = [
    '--reps', '1',
    '--output', '4.2.3_incremental_damicore'
]
result = subprocess.run(['bash', script] + params, capture_output=False, text=True)


# GENERATE INCREMENTAL DF
all_stats = []
for load in os.listdir(data_results_dir):
    load_dir = f"{data_results_dir}/{load}"
    for type in os.listdir(load_dir):
        if type not in types:
            continue
        file_path = f"{load_dir}/{type}"

        df = pd.read_json(file_path)
        grouped = df.groupby(['load','type','compressor','iteration'])
        stats_df = grouped.apply(compute_boxplot_stats).reset_index()
        all_stats.append(stats_df)

# Juntar tudo em um único DataFrame final
final_df = pd.concat(all_stats, ignore_index=True)
final_df =  remove_compressor_from_df(['lzma','png','webp_lossless','jp2_lossless', 'bzip2', 'entropy'], final_df)
final_df["compressor"] = final_df["compressor"].replace("heif", "hevc")
final_df = remove_lossy_or_lossless_from_df(final_df)
final_df.to_csv(f"{data_dir}/incremental_stats.csv")