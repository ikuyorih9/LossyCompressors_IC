import os
import pandas as pd
import numpy as np
from utils.format import *
from utils.barplots import *

data = "../results/4.2.3_incremental_damicore/RESULTS"
results = "../results/4.2.5_generate_effectiveness_barplots"
os.makedirs(results, exist_ok=True)
compressor_order = ['ZLIB', 'PPMD', 'GZIP','BZ2','JP2','WEBP', 'HEIF']
selected_load = 'CANCER-PHON'

all_stats = []
types = ['API', 'CONC', 'LOGIC', 'MEMORY', 'MODEL', 'PROCESS', 'TRAIN', 'ANOTHER-CONTROL']

# GENERATE PERFORMANCE DATA

for load in os.listdir(data):
    load_dir = f"{data}/{load}"
    for type in os.listdir(load_dir):
        if type not in types:
            continue
        file_path = f"{load_dir}/{type}"

        df = pd.read_json(file_path)
        mean_iteration_by_compressor = df.groupby(['load','type','compressor'])["iteration"].mean().reset_index()


        all_stats.append(mean_iteration_by_compressor)

df = pd.concat(all_stats, ignore_index=True)
df['type'] = df['type'].str.upper()
df['identified'] = df['iteration'] != -1
df['is_my_control'] = df['type'] == "ANOTHER-CONTROL"


result = []
grouped = df.groupby(['compressor', 'load'])
epsilon = 1e-10

for (compressor, load), group in grouped:

    VP = ((~group['is_my_control']) & (group['identified'])).sum()
    FP = ((group['is_my_control']) & (group['identified'])).sum()
    FN = ((~group['is_my_control']) & (~group['identified'])).sum()
    VN = ((group['is_my_control']) & (~group['identified'])).sum()

    accuracy = (VP + 7*VN) / (VP + 7*FP + FN + 7*VN + epsilon)
    precision = VP / (VP + 7*FP + epsilon)
    recall = VP / (VP + FN + epsilon)
    f1_score = 2 * (precision * recall) / (precision + recall + epsilon)

    result.append({
        'compressor': compressor,
        'load': load,
        'VP': VP,
        'FN': FN,
        'VN': VN,
        'FP': FP,
        'accuracy': round(accuracy, 4),
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1_score': round(f1_score, 4)
    })

# Converter resultado para DataFrame final
metrics_df = pd.DataFrame(result)
df = metrics_df
df = remove_compressor_from_df(['bzip2', 'lzma','entropy', 'png', 'webp_lossless', 'jp2_lossless'], df)
df["compressor"] = df["compressor"].replace("heif", "hevc")
df = remove_lossy_or_lossless_from_df(df)
df = order_df_by_compressor(df, ['ZLIB', 'PPMD', 'GZIP','BZ2','JP2','WEBP', 'HEVC'])
df.to_csv(f"{results}/incremental_performance_stats.csv")

# GENERATE BARPLOTS

df = df[df['load'] == selected_load]


df['accuracy'] = df['accuracy']*100
df['precision'] = df['precision']*100
df['recall'] = df['recall']*100
df['f1_score'] = df['f1_score']*100

df_melted = df.melt(
    id_vars=['compressor'],  # colunas que você quer manter fixas
    value_vars=['accuracy', 'precision', 'recall', 'f1_score'],  # colunas que viram “categorias”
    var_name='param',  # nova coluna para o nome da métrica
    value_name='value'     # nova coluna com os valores
)

bp = BarPlot(
    title=f"Métricas de eficácia na carga de trabalho {selected_load}",
    title_size=24,
    x='compressor',
    xlabel_size=16,
    xlabel="Compressor",
    y='value',
    ylabel="Valor (%)",
    ylabel_size=16,
    show_values=True,
    fmt='%.1f',
    ylim=[0,120],
    figsize=(8,4)
)  

plots = [
    lambda ax: bp.generate(ax=ax, dataset=df_melted[df_melted['param'] == 'accuracy'], title="Acurácia", show_plot=False, bar_colors=['#2ecc71']),
    lambda ax: bp.generate(ax=ax, dataset=df_melted[df_melted['param'] == 'precision'], title="Precisão", show_plot=False, show_ylabel=False,bar_colors=['#2ecc71']),
    lambda ax: bp.generate(ax=ax, dataset=df_melted[df_melted['param'] == 'recall'], title="Recall", show_plot=False, bar_colors=['#2ecc71']),
    lambda ax: bp.generate(ax=ax, dataset=df_melted[df_melted['param'] == 'f1_score'], title="F1-Score", show_plot=False, show_ylabel=False, bar_colors=['#2ecc71']),
]


bp.generate_multiplots(plot_functions=plots, output_image_path=f"{results}/{selected_load}_eficacia_stats.png", nrows=2, ncols=2)
