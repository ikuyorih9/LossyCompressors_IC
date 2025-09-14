#!/bin/bash

SECONDS=0  # <- inicia contagem

# Lista de compressores
compressors=("zlib" "gzip" "bzip2" "bz2" "ppmd"
             "png" "webp_lossless" "jp2_lossless" "entropy"
             "webp_lossy" "jp2_lossy" "heif")

CLUSTER_DIR="./clusters_wtime"
INCREMENTAL_DIR="./incremental_output"
NCD_DIR="./ncds_wtime"
COMPRESSOR_TIMES_DIR="./compressor_times"
DAMICORE_TIMES_DIR="./times_wtime"

# Armazena todas as flags passadas ao .sh (exceto o nome do compressor)
extra_flags="$@"

echo "$extra_flags"

rm -rf "$CLUSTER_DIR"/*
rm -rf "$INCREMENTAL_DIR"/*
rm -rf "$NCD_DIR"/*
rm -rf "$COMPRESSOR_TIMES_DIR"/*
rm -rf "$DAMICORE_TIMES_DIR"/*

echo "✅ Diretórios reiniciados!"

cd damicore-python3
# Loop pelos compressores
for compressor in "${compressors[@]}"; do
    echo "🚀 Executando para compressor: $compressor"
    
    # Executando o script Python com o compressor e as flags adicionais
    python3 clustering_until_detection.py "$compressor" $extra_flags

    echo "-----------------------------------"
done

# 🔚 Ao fim, imprime tempo total
duration=$SECONDS
echo "⏱️ Tempo total de execução: $(($duration / 60)) minutos e $(($duration % 60)) segundos"