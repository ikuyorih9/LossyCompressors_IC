from damicore import damicore
from time import process_time
from time import time
import argparse
import shutil
import json
import sys
import os

def get_args_to_damicore(
        compressor:str, 
        output_cluster_path:str, 
        output_time_path:str, 
        output_ncd_path:str = None,
        level:int = None, 
        order:int = None,
        memory:int = None,
        serial:bool = False,
        verbose:bool = False
    ):

    args = []

    args.extend(["--compressor", compressor.split('_')[0]])

    if level:
        args.extend(["--level", str(level)])

    if order:
        args.extend(["--model-order", str(order)])

    if memory:
        args.extend(["--memory", str(memory)])
    
    try:
        if compressor.split('_')[1] == 'lossy':
            args.extend(['--lossy', str(1)])
        else:
            args.extend(['--lossy', str(0)])
    except:
        print("Its not lossy or lossless")

    args.append("--verbose" if verbose else "--no-verbose")

    args.append("--serial" if serial else "--parallel")

    if output_ncd_path:
        args.extend(["--ncd-output", output_ncd_path])

    args.extend(["--json-time", output_time_path])

    args.extend(["--output", output_cluster_path, "../sample_data"])

    return args

def execute_damicore(
    compressor:str, 
    type:str,
    output_cluster_dir:str, 
    output_time_dir:str, 
    output_ncd_dir:str = None,
    level:int = None, 
    order:int = None,
    memory:int = None,
    serial:bool = False,
    verbose:bool = False
):
    data = []

    # Define o diretório para os clusters.
    cluster_dir = f"{output_cluster_dir}/{compressor}"
    cluster_path = f"{cluster_dir}/{compressor}_{type}.out"
    
    if not os.path.exists(cluster_dir):
        os.makedirs(cluster_dir)

    # Verifica se há output para os dados da NCD.
    if output_ncd_dir:
        ncd_dir = f"{output_ncd_dir}/{compressor}"
        ncd_path = f"{ncd_dir}/{compressor}_{type}.out"
        if not os.path.exists(ncd_dir):
            os.makedirs(ncd_dir)
    else:
        ncd_path = None

    # Obtem os argumentos para a DAMICORE
    args = get_args_to_damicore(
        compressor = compressor,
        output_cluster_path = cluster_path,
        output_ncd_path = ncd_path,
        output_time_path = f"{output_time_dir}/{compressor}_{type}",
        level = level,
        order = order,
        memory = memory,
        serial = serial,
        verbose = verbose
    )

    # print(args)

    e0 = time()
    p0 = process_time()
    damicore.main(args)
    p = process_time()
    e = time()

    data.append({"compressor": compressor, "type": type, "time": e-e0, "process_time": p-p0})

    return data

def limpa_dir(output_dir:str):
    # Limpa o diretório de saída
    if os.path.exists(output_dir):
        # Remove todos os arquivos e subdiretórios dentro de output_dir
        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)  # Remove arquivos ou links simbólicos
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Remove diretórios recursivamente
    else:
        # Cria o diretório de saída se ele não existir
        os.makedirs(output_dir)

    # Aqui você pode adicionar o restante da lógica da função
    print(f"[CLEANING] O diretório {output_dir} foi limpo.")

def copia_arquivos(origem: str, destino: str, selection:str = None):
    if os.path.exists(origem):
        for item in os.listdir(origem):
            
            origem_item = os.path.join(origem, item)
            destino_item = os.path.join(destino, item)

            if not selection:
                if os.path.isfile(origem_item):
                    shutil.copy2(origem_item, destino_item)  # Copia o arquivo preservando metadados
                elif os.path.isdir(origem_item):
                    shutil.copytree(origem_item, destino_item)  # Copia diretórios recursivamente
            else:
                if selection in item:
                    print(f"Copiando {item}...")
                    if os.path.isfile(origem_item):
                        shutil.copy2(origem_item, destino_item)  # Copia o arquivo preservando metadados
                    elif os.path.isdir(origem_item):
                        shutil.copytree(origem_item, destino_item)  # Copia diretórios recursivamente

def copia_samples(main_dir:str, var_dir:str, output_dir:str, selection:str = None):
    limpa_dir(output_dir)

    # Copia os arquivos de main_dir para output_dir
    copia_arquivos(main_dir, output_dir, selection=selection)

    # Copia os arquivos de var_dir para output_dir
    copia_arquivos(var_dir, output_dir, selection=selection)

def processing_time_to_json(json_data, output:str="../data.json"):
    if not os.path.exists(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))

    try:
        with open(output, "r", encoding="utf-8") as json_file:
            read_data = json.load(json_file)
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        read_data = []

    read_data.extend(json_data)

    with open(output, "w", encoding="utf-8") as json_file:
        json.dump(read_data, json_file, indent=4, ensure_ascii=False)

def print_progress_bar(current:int, min:int = 0, max:int = 100, max_relative=40):
    if current < min or current > max:
        return
    
    progress = (current/(max - min))
    progress_relative = int(progress * max_relative)

    print("\033[32m", end='')
    for i in range (0, progress_relative):
        print('🟩', end='')
    for i in range (progress_relative + 1, max_relative):
        print('🟥', end='')
    print(f" {progress * 100:.1f}%\033[0m")
 

if __name__ == '__main__':

    # Configura os argumentos para o script.
    parser = argparse.ArgumentParser(description="Executa o DAMICORE com diversos parâmetros configuráveis.")

    # Argumento posicional obrigatório
    parser.add_argument("compressor", help="Nome do compressor")

    # Flags opcionais
    parser.add_argument("--serial", action="store_true", help="Executar em modo serial")
    parser.add_argument("--verbose", action="store_true", help="Exibir saídas detalhadas")

    # Argumentos opcionais com valores padrão
    parser.add_argument("--level", type=int, default=9, help="Nível de compressão (padrão: 9)")
    parser.add_argument("--order", type=int, default=16, help="Ordem do modelo (padrão: 16)")
    parser.add_argument("--memory", type=int, default=16, help="Tamanho da memória (padrão: 16)")
    parser.add_argument("--reps", type=int, default=100, help="Tamanho da memória (padrão: 16)")

    args = parser.parse_args()

    # Configuração de caminhos e tipo fictício (ajuste para o seu contexto)
    compressor = args.compressor
    serial_flag = args.serial
    verbose_flag = args.verbose
    level_value = args.level
    order_value = args.order
    memory_value = args.memory
    repetition = args.reps


    default_dir = '../modified_data/'
    default_export_time_dir = '../compressor_times'

    selected_load = ['CANCER-PHON']
    selected_type = ['API', 'MEMORY', 'PROCESS']
    compressors = ["zlib", "gzip", "bzip2", "bz2", "ppmd", "lzma", "webp_lossless", "png", "jp2_lossless", "entropy", "webp_lossy", "jp2_lossy", "heif"]
    max = len(selected_load) * len(selected_type) * repetition
    current = 1

    init_time = time()

    for load in os.listdir(default_dir):
        if not load in selected_load:
            continue

        load_dir = f"{default_dir}/{load}"
        if not os.path.isdir(load_dir):
            continue

        control_dir = f"{load_dir}/CONTROL"

        type_init_time = time()

        for type in os.listdir(load_dir):
            if not type in selected_type:
                continue

            export_time_dir=f"{default_export_time_dir}/{load}/{type}"
            if not os.path.exists(export_time_dir):
                os.makedirs(export_time_dir)

            type_dir = os.path.join(load_dir, type)
            print(f"\t[PATH] abrindo caminho {type_dir}")

            copia_samples(control_dir, type_dir, '../sample_data')
            # input("Continuar...")

            output_path = os.path.join("../clusters_wtime/", load)
            ncd_path = os.path.join("../ncds_wtime/", load)
            
            if compressor in compressors:
                compressor_init_time = time()
                for i in range(repetition):
                    print(f"\n\033[33mLOAD: {load}")
                    print(f"TYPE: {type}")
                    print(f"COMPRESSOR: {compressor}\n")
                    print(f"\033[36m[REPETITION]: {i}\033[0m\n") 

                    time_path = f"../times_wtime/{load}.json"

                    data = execute_damicore(
                        compressor = compressor,
                        type = type,
                        output_cluster_dir = output_path,
                        output_time_dir = export_time_dir,
                        level = 9,
                        order = 16,
                        memory = 16,
                        verbose=False,
                        serial=serial_flag
                    )

                    processing_time_to_json(data, time_path)
                    print()
                    print_progress_bar(current=current,min=0, max=max)

                    current += 1
                print(f"\n\033[36m[LOOP TIME] {time() - compressor_init_time} s\033[0m\n")
        print(f"\n\033[36m[TYPE TIME] {time() - type_init_time} s\033[0m\n")
    print(f"\n\033[36m[TOTAL TIME] {time() - init_time} s\033[0m\n")
                

        