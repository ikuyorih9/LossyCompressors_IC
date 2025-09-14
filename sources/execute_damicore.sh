#!/bin/bash

SECONDS=0  # Inicia contagem de tempo total

# Lista de compressores
compressors=("zlib" "gzip" "bz2" "ppmd" "webp_lossy" "jp2_lossy" "heif")

# Armazena todas as flags passadas ao .sh (exceto o nome do compressor)
extra_flags=("$@")

# ==============================
# Detecta diretório de saída (--output)
# ==============================
output_dir="results"  # valor padrão do clustering_until_detection.py
for i in "${!extra_flags[@]}"; do
    if [[ "${extra_flags[$i]}" == "--output" ]]; then
        if [[ -n "${extra_flags[$i+1]}" ]]; then
            output_dir="${extra_flags[$i+1]}"
        fi
    fi
done

cd damicorepy/damicore-python3 || exit

results_path="../../../results/$output_dir"

# Limpeza do diretório de saída (se existir)
echo "🧹 Limpando resultados em: $results_path"
rm -rf "$results_path"
mkdir -p "$results_path"
echo "✅ Diretório reiniciado!"

# ==============================
# Loop pelos compressores
# ==============================

for compressor in "${compressors[@]}"; do
    echo "🚀 Executando para compressor: $compressor"
    
    # Executando o script Python com o compressor e as flags adicionais
    python3 main.py "$compressor" "${extra_flags[@]}"

    echo "-----------------------------------"
done

# ==============================
# Tempo total
# ==============================
duration=$SECONDS
echo "⏱️ Tempo total de execução: $(($duration / 60)) minutos e $(($duration % 60)) segundos"
