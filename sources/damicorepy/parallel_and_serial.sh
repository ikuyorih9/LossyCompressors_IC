#!/bin/bash

# Diretório para salvar os resultados
OUTPUT_BASE_DIR="../../DamicoreLocalResults"
mkdir -p "$OUTPUT_BASE_DIR"

# Função para salvar pastas após cada execução
salvar_resultados() {
    modo_execucao=$1  # serial ou parallel
    timestamp=$(date +'%Y%m%d_%H%M%S')
    destino="${OUTPUT_BASE_DIR}/${modo_execucao}_${timestamp}"

    echo "Salvando resultados no diretório '${destino}'..."
    mkdir -p "$destino"

    # Liste aqui todas as pastas que você quer salvar
    for pasta in clusters_wtime compressor_times times_wtime; do
        if [ -d "$pasta" ]; then
            mv "$pasta" "${destino}/"
        else
            echo "Aviso: Pasta '$pasta' não encontrada após execução '$modo_execucao'."
        fi
    done
}

# 1. Executa em modo paralelo
echo "==== Iniciando execução paralela ===="
./run_damicore_tests.sh
salvar_resultados "parallel"

echo ""

# 2. Executa em modo serial
echo "==== Iniciando execução serial ===="
./run_damicore_tests.sh --serial
salvar_resultados "serial"

echo "Execuções concluídas."
