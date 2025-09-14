# Sources

Este diretório contém os scripts utilizados para gerar todos os resultados apresentados no relatório. Eles estão organizados em ordem de apresentação da seção 4.2 do relatório.

- `4.2.1_compressors_accuracy.py`: script para executar a DAMICORE com todos os perfis na iteração 30;
- `4.2.2_generate_process_time_heatmap`: script que gera os mapas de calor com os dados gerados em `4.2.1_compressors_accuracy.py`;
- `4.2.3_execute_incremental_damicore`: script para executar a DAMICORE com todos os perfis da iteração 0 à 30;
- `4.2.4_effectiveness_efficiency_heatmap`: script para gerar dois heatmaps - a matriz de iterações e a matriz de mediana de tempo de resposta;
- `4.2.5_generate_effectiveness_barplots`: script para gerar o gráfico de barras de acurácia, precisão, recall e f1-score;
- `4.2.6_generate_boxplots`: script para gerar os boxplots de distribuição dos tempos de execução;
- `4.2.7_shapiro_and_wilcoxon_test`: script para calcular os testes de Shapiro-Wilk e Wilcoxon;
- `4.2.8_generate_effectiveness_efficiency_map`: script para gerar o mapa de eficiência por eficácia.

Há ainda o `execute_damicore.sh`, que é um script genérico do bash para executar a DAMICORE. 

>❗**IMPORTANTE**: o script foi executado no Ubuntu 22 e foi preciso ativá-lo com `chmod +x execute_damicore.sh`.