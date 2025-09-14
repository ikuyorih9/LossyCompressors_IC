import pandas as pd
import numpy as np
import os
from utils.XYPlot import XYPlot, Legend

selected_load = 'CANCER-PHON'

color_map = {
    "BZ2": "#1f77b4",
    "GZIP": "#1f77b4",
    "HEVC": "#d62728",
    "JP2": "#d62728",
    "PPMD": "#1f77b4",
    "WEBP": "#d62728",
    "ZLIB": "#1f77b4"
}

marker_map = {
    "MEMORY": "o",
    "API": "X",
    "PROCESS": "*"
}

output_dir="../results/4.2.8_generate_effectiveness_efficiency_map"
os.makedirs(output_dir, exist_ok=True)

times_data = "../results/4.2.3_incremental_damicore/incremental_stats.csv"
perf_data = "../results/4.2.5_generate_effectiveness_barplots/incremental_performance_stats.csv"


df_times = pd.read_csv(times_data)
df_times = df_times[df_times['load']==selected_load]

df_perf = pd.read_csv(perf_data).drop(columns=['Unnamed: 0'])
df_perf = df_perf[df_perf['load']==selected_load]


df_eficacia = df_perf[['compressor','accuracy']]
df_eficiencia = df_times[['compressor', 'type', 'median_time']]
df = pd.merge(df_eficiencia, df_eficacia, on='compressor')

df['inv_median_time'] = 1 / df['median_time']

types = df_times['type'].unique()
df["efficiency"] = np.nan
df["efficacy"] = np.nan

for t in types:
    mask = df["type"] == t
    subset = df[mask]
    min_inv = subset["inv_median_time"].min()
    max_inv = subset["inv_median_time"].max()

    # Normalização dentro do grupo e atribuição apenas nas linhas do grupo
    df.loc[mask, "efficiency"] = (
        (subset["inv_median_time"] - min_inv) / (max_inv - min_inv)
    )

    min_f1 = subset["accuracy"].min()
    max_f1 = subset["accuracy"].max()

    # Normalização dentro do grupo e atribuição apenas nas linhas do grupo
    df.loc[mask, "efficacy"] = (
        (subset["accuracy"] - min_f1) / (max_f1 - min_f1)
    )

df = df[['type','compressor', 'efficacy','efficiency']]
df["color"] = df["compressor"].map(color_map)
    
legend = Legend(
    "Tipo de compressor", 
    ["#d62728", "#1f77b4"], 
    ["Imagem", "Texto"],
    fontsize= 12,
)
plot = XYPlot(
    title_size=32,
    xlabel="Eficácia",
    xlabel_size=24,
    ylabel="Eficiência",
    ylim=(-0.05, 1.075),
    ylabel_size=24,
    rotation_x=0,
    rotation_y=0,
    legend = legend,
    figsize=(6,6)
)

plots = [
    lambda ax: plot.scatterplot(
        data=df[df['type']=='MEMORY'],
        x="efficacy",
        y="efficiency",
        label_col="compressor",
        # color_col="color",
        use_adjust_text=True,
        show_grid=True,
        point_style=dict(s=25),
        text_style=dict(fontsize=14, color="black", fontweight="bold"),
        show_legend=False,
        pound_x=3,
        pound_y=2,
        offset_x=0.25,
        offset_y=0.05,
        title="MEMORY",
        ax=ax,
        show_plot=False
    ),
    lambda ax: plot.scatterplot(
        data=df[df['type']=='API'],
        x="efficacy",
        y="efficiency",
        label_col="compressor",
        # color_col="color",
        pound_x=1,
        pound_y=1,
        offset_x=0.1,
        offset_y=0.05,
        use_adjust_text=True,
        show_grid=True,
        point_style=dict(s=25),
        text_style=dict(fontsize=14, color="black", fontweight="bold"),
        show_legend=False,
        title="API",
        ax=ax,
        show_ylabel=False,
        show_plot=False
    ),
    lambda ax: plot.scatterplot(
        data=df[df['type']=='PROCESS'],
        x="efficacy",
        y="efficiency",
        label_col="compressor",
        # color_col="color",
        pound_x=1,
        pound_y=3,
        offset_x=0.05,
        offset_y=0.08,
        use_adjust_text=True,
        show_grid=True,
        point_style=dict(s=25),
        text_style=dict(fontsize=14, color="black", fontweight="bold"),
        show_legend=False,
        title="PROCESS",
        ax=ax,
        show_plot=False,
        show_ylabel=False
    ),
]



plot.generate_multiplots(
    plot_functions=plots,
    title=f"Mapa de eficácia contra eficiência por tipos de defeito na carga {selected_load}",
    nrows=1,
    ncols=3,
    output_image_path=f"{output_dir}/{selected_load}_eficiencia_eficacia.png"
)
