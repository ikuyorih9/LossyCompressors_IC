import pandas as pd
import re

def remove_param(name: str):
    new = name.lower()
    new = re.sub(r"_level_\d+", "", new)
    new = re.sub(r"_order_\d+", "", new)
    return new.upper()

def remove_lossy_or_lossless(name: str):
    new = name.lower()
    new = new.replace("_lossless", "")
    new = new.replace("_lossy", "")
    return new.upper()

def remove_param_from_df(df: pd.DataFrame):
    df = df.copy()
    df["compressor"] = df["compressor"].apply(remove_param)
    return df

def remove_lossy_or_lossless_from_df(df: pd.DataFrame):
    df = df.copy()
    df["compressor"] = df["compressor"].apply(remove_lossy_or_lossless)
    return df

def remove_compressor_from_df(compressors: list, df: pd.DataFrame):
    return  df[~df['compressor'].isin(compressors)].reset_index(drop=True)

def order_df_by_compressor(df: pd.DataFrame, order:list = ['ZLIB', 'PPMD', 'GZIP','BZ2', 'PNG', 'JP2','WEBP', 'HEIF']):
    df = df.copy()
    df['compressor'] = pd.Categorical(df['compressor'], categories=order, ordered=True)
    df = df.sort_values("compressor")
    return df
def order_df_by_type(df: pd.DataFrame, order:list = ['ZLIB', 'PPMD', 'GZIP','BZ2', 'PNG', 'JP2','WEBP', 'HEIF']):
    df = df.copy()
    df['type'] = pd.Categorical(df['type'], categories=order, ordered=True)
    df = df.sort_values("type")
    return df