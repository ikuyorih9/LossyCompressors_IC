import pandas as pd
import itertools
from scipy.stats import shapiro, wilcoxon, ttest_rel
import os
from utils.format import *

def verifica_distribuicao_normal(df: pd.DataFrame):
    shapiro = shapiro(df)
    return shapiro.pvalue

data = "../results/4.2.3_incremental_damicore/RESULTS"
results_dir = "../results/4.2.7_shapiro_and_wilcoxon"
os.makedirs(results_dir, exist_ok=True)

shapiros = []
for load in os.listdir(data):
    load_dir = f"{data}/{load}"
    for type in os.listdir(load_dir):
        file_path = f"{load_dir}/{type}"
        df = pd.read_json(file_path)
        compressors = df["compressor"].unique()
        for c in compressors:
            c_times = df[df['compressor'] == c]['time'].reset_index(drop=True)
            pvalue = shapiro(c_times).pvalue
            shapiros.append({
                "load": load,
                "type": type,
                "compressor": c,
                "p_value": pvalue,
                "normal": pvalue > 0.05
            })

shapiro_df = pd.DataFrame(shapiros)
shapiro_df = remove_compressor_from_df(['webp_lossless', 'jp2_lossless', 'png', 'entropy','bzip2'], shapiro_df)
shapiro_df = remove_lossy_or_lossless_from_df(shapiro_df)
shapiro_df.to_csv(f"{results_dir}/time_pvalues_shapiro.csv")
print(shapiro_df[shapiro_df['normal']==True])

results = []
for load in os.listdir(data):
    load_dir = f"{data}/{load}"
    for type in os.listdir(load_dir):
        file_path = f"{load_dir}/{type}"
        df = pd.read_json(file_path)
        df = remove_compressor_from_df(['webp_lossless', 'jp2_lossless', 'png', 'entropy','bzip2'], df)
        df = remove_lossy_or_lossless_from_df(df)
        df['compressor'] = df['compressor'].replace('HEIF', 'HEVC')
        df = order_df_by_compressor(df, ['ZLIB', 'PPMD', 'GZIP', 'BZ2','WEBP','JP2', 'HEVC'])
        
        compressores = df["compressor"].unique()

        pairs = list(itertools.combinations(compressores,2))
        for a, b in pairs:
            # print("="*80)
            # print(f"🔹 Comparando pares: {a}  VS  {b} - {load}:{type}")

            a_times = df[df['compressor'] == a]['time'].reset_index(drop=True)
            b_times = df[df['compressor'] == b]['time'].reset_index(drop=True)

            # print(f" -> {a}: {len(a_times)} amostras")
            # print(f" -> {b}: {len(b_times)} amostras")

            # se não tiver dados, pula
            if a_times.empty or b_times.empty:
                # print(" ⚠️ Algum grupo vazio, pulando comparação.")
                continue

            # Teste de normalidade (Shapiro-Wilk)
            try:
                p1 = shapiro(a_times).pvalue
                p2 = shapiro(b_times).pvalue
                normal1 = p1 > 0.05
                normal2 = p2 > 0.05
                # print(f"   Shapiro {a}: p={p1:.10f} -> normal={normal1}")
                # print(f"   Shapiro {b}: p={p2:.10f} -> normal={normal2}")
            except Exception as e:
                # print(f" ⚠️ Erro no Shapiro para {a} vs {b}: {e}")
                continue

            # Escolha do teste estatístico
            try:
                if normal1 and normal2:
                    test = "t-pareado"
                    stat, p = ttest_rel(a_times, b_times)
                else:
                    test = "wilcoxon"
                    stat, p = wilcoxon(a_times, b_times)

                significancia = p < 0.05
                # print(f"   ✅ Teste: {test} | stat={stat:.4f} | p={p:.4e} | significativo={significancia}")

            except Exception as e:
                # print(f" ⚠️ Erro ao rodar o teste em {a} vs {b}: {e}")
                stat, p, significancia, test = None, None, None, "erro"

            # Adiciona no resultado final
            results.append({
                'load': load,
                'type': type,
                "compressor_1": a,
                "compressor_2": b,
                "test": test,
                "pvalue": p,
                "significant": significancia
            })

# Resultado final
df = pd.DataFrame(results)
df.to_csv(f"{results_dir}/time_significance_test.csv")
print(df[df['significant']==False])