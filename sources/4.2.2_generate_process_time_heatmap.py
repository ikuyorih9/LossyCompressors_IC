import pandas as pd
import os
from utils.heatmap import HeatmapPlot
from utils.format import *

data_in = '../results/4.2.1_compressors_accuracy/RESULTS'
data_out = "../results/4.2.2_generate_process_time_heatmap"
os.makedirs(data_out,exist_ok=True)

show_ylabel = False
selected_loads = ['OIL-MAMMO', 'IONO-SOLAR', 'WINE-HEART']

for load in os.listdir(data_in):
    if not load in selected_loads:
        continue

    load_dir = f"{data_in}/{load}"    
    load_df = []

    for type in os.listdir(load_dir):
        file_path = f"{load_dir}/{type}"
        df = pd.read_json(file_path)
        load_df.append(df)
    df = pd.concat(load_df, ignore_index=True)
    df = remove_param_from_df(df)
    df = remove_compressor_from_df(['BZIP2', 'LZMA','PNG','WEBP_LOSSLESS', 'JP2_LOSSLESS', 'ENTROPY'], df)
    df = remove_lossy_or_lossless_from_df(df)
    df = order_df_by_compressor(df)

    show_ylabel = True if load == selected_loads[0] else False

    plot = HeatmapPlot(
        title = f"Tempos de processamento na carga de trabalho {load}",
        xlabel = "Compressores",
        ylabel = "Anomalia",
        cmap="RdYlGn_r",
        title_size=20,
        xlabel_size=16,
        ylabel_size=16,
        show_ylabel= show_ylabel,
        annot_kws={"size": 16}
    )

    plot.generate(
        data=df,
        index_col='type',
        columns_col='compressor',
        values_col='time',
        output_image_path=f"{data_out}/{load}_proc_times.png"
    )

    
