import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from utils.boxplot import BoxplotPlot
from utils.format import *

selected_load = 'CANCER-PHON'

dir = "../results/4.2.3_incremental_damicore/RESULTS"
images=f"../results/4.2.6_generate_boxplots"
os.makedirs(images, exist_ok=True)

plotter = BoxplotPlot(
    xlabel="Tempo (s)",
    ylabel="Compressor",
    title_size=48,
    xlabel_size=42,
    ylabel_size=42,
    ticklabel_size=24,
    figsize=(8, 8),
    rotation_x=45,
    showfliers=False 
)

dfs = []

for load in os.listdir(dir):
    load_dir = f"{dir}/{load}"
    for type in os.listdir(load_dir):
        file_path = f"{load_dir}/{type}"

        df = pd.read_json(file_path)
        df = df[(df['compressor'] != 'bzip2') & (df['compressor'] != 'lzma') & (df['compressor'] != 'entropy')]
        df["compressor"] = df["compressor"].astype(str).replace("heif", "hevc")

        df= remove_compressor_from_df(['bzip2','lzma','entropy','webp_lossless', 'jp2_lossless', 'png'], df)
        df = remove_lossy_or_lossless_from_df(df)
        df = order_df_by_compressor(df, ['ZLIB', 'PPMD', 'GZIP','BZ2','JP2','WEBP', 'HEVC'])

        dfs.append(df)

        grouped = df.groupby(['load','type','compressor','iteration'])

df = pd.concat(dfs, ignore_index=True)
# df = df[df['load']==selected_load]
plots = [
    lambda ax: plotter.generate(
        ax=ax,
        data=df[df['type']=='MEMORY'],
        x_col="time",
        y_col="compressor",
        title=f"MEMORY",
        show_plot=False,
        
    ),
    lambda ax: plotter.generate(
        ax=ax,
        data=df[df['type']=='API'],
        x_col="time",
        y_col="compressor",
        title=f"API",
        show_plot=False,
        show_ylabel=False
    ),
    lambda ax: plotter.generate(
        ax=ax,
        data=df[df['type']=='PROCESS'],
        x_col="time",
        y_col="compressor",
        title=f"PROCESS",
        show_plot=False,
        show_ylabel=False
    ),
]

plotter.generate_multiplots(
    plot_functions=plots,
    nrows=1,
    ncols=3,
    title=f"Distribuição dos tempos de resposta",
    output_image_path=f"{images}/time_boxplots.png"
)

df_filtered = df[df["type"].isin(["MEMORY", "PROCESS", "API"])]

# plotter.generate_multiboxplots(
#     data=df_filtered,
#     x_col="time",
#     y_col="compressor",
#     group_col="type",  # Pode ser 'parameter' ou outro, dependendo do dataset
#     title="Boxplots agrupados por Tipo e Compressor",
#     palette="Set2",
#     output_image_path=f"{images}/grouped_boxplots.png"
# )