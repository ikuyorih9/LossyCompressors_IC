#!/bin/bash

SECONDS=0

CLUSTER_DIR="./clusters_wtime"
INCREMENTAL_DIR="./incremental_output"
NCD_DIR="./ncds_wtime"
COMPRESSOR_TIMES_DIR="./compressor_times"
DAMICORE_TIMES_DIR="./times_wtime"

# O primeiro e segundo argumentos são os compressores
comp1="$1"
comp2="$2"

# O resto continua sendo flags extras
shift 2
extra_flags="$@"

echo "Usando compressores: $comp1 e $comp2"
echo "Flags extras: $extra_flags"

# Limpeza das pastas
rm -rf "$CLUSTER_DIR"/*
rm -rf "$INCREMENTAL_DIR"/*
rm -rf "$NCD_DIR"/*
rm -rf "$COMPRESSOR_TIMES_DIR"/*
rm -rf "$DAMICORE_TIMES_DIR"/*

echo "✅ Diretórios reiniciados!"

cd damicore-python3

# Chamada ao Python
python3 clustering_until_detection.py "$comp1" "$comp2" $extra_flags

duration=$SECONDS
echo "⏱️ Tempo total de execução: $(($duration / 60)) minutos e $(($duration % 60)) segundos"
