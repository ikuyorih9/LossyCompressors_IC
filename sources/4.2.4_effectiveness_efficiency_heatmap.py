import os
import pandas as pd
import numpy as np
import statistics
from utils.format import *
from utils.heatmap import HeatmapPlot

compressor_order = ['ZLIB', 'PPMD', 'GZIP','BZ2', 'PNG','WEBP','JP2', 'HEVC']
type_order = ['ANOTHER-CONTROL', 'MEMORY', 'MODEL', 'LOGIC', 'TRAIN', 'API', 'CONC', 'PROCESS']

input_csv = '../results/4.2.3_incremental_damicore/incremental_stats.csv'
output_dir = "../results/4.2.4_effectiveness_efficiency_heatmap"
os.makedirs(output_dir, exist_ok=True)

df = pd.read_csv(input_csv, sep=',', decimal='.')

# Instancia e configura o heatmap
heatmap = HeatmapPlot(
    xlabel="Tipo de defeito",
    ylabel="Compressor",
    cmap="RdYlGn_r",
    fmt=".0f",    
    title_size=20, 
    xlabel_size=16, 
    ylabel_size=16,
    exceptions=[-1.0],
    exception_color="#9e9e9e",
    figsize=(8, 8)
)

heatmap2 = HeatmapPlot(
    xlabel="Tipo de defeito",
    ylabel="Compressor",
    cmap="RdYlGn_r",
    fmt=".3f",    
    title_size=20, 
    xlabel_size=16, 
    ylabel_size=16,
    exceptions=[-1.0],
    exception_color="#9e9e9e",
    figsize=(8, 8)
)

plots = [
    lambda ax: heatmap.generate(
        ax=ax,
        data=df,
        title="Matriz de iteração",
        index_col="compressor",
        columns_col="type",
        values_col="iteration",
        show_plot=False
    ),
    lambda ax: heatmap2.generate(
        ax = ax,
        data=df,
        title="Matriz de mediana de tempo de resposta (s)",
        index_col="compressor",
        columns_col="type",
        values_col="median_time",
        show_plot=False
    )
]

heatmap.generate_multiplots(
    plot_functions=plots, 
    title="Matrizes de identificação de defeitos",
    output_image_path=f"{output_dir}/heatmap_iterative.png"
)

