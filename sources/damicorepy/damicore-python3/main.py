from damicore import damicore
from time import process_time
from time import time
import argparse
import shutil
import json
import sys
import os

all_types =  ['API', 'CONC', 'LOGIC', 'MEMORY', 'MODEL', 'PROCESS', 'TRAIN', 'ANOTHER-CONTROL']
all_loads =  ['BANK-PIMA', 'CANCER-PHON', 'IONO-SOLAR', 'IRIS-HABER', 'OIL-MAMMO', 'WINE-HEART']
compressors = ["zlib", "gzip", "bzip2", "bz2", "ppmd", "lzma", "webp_lossless", "png", "jp2_lossless", "entropy", "webp_lossy", "jp2_lossy", "heif"]
profiles_dir = "../../../data/profiles/original_data"
results_dir = "../../../results"

from damicore import damicore
from time import process_time
from time import time
import pandas as pd
import argparse
import shutil
import json
import sys
import os

def get_args_to_damicore(
        compressor:str, 
        output_cluster_path:str, 
        output_time_path:str = None, 
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
        pass

    args.append("--verbose" if verbose else "--no-verbose")

    args.append("--serial" if serial else "--parallel")

    if output_ncd_path:
        args.extend(["--ncd-output", output_ncd_path])

    # args.extend(["--json-time", output_time_path])

    args.extend(["--output", output_cluster_path, "../sample_data"])

    return args

def execute_damicore(
    compressor:str, 
    type:str,
    output_cluster_dir:str, 
    output_time_dir:str = None, 
    output_ncd_dir:str = None,
    level:int = None, 
    order:int = None,
    memory:int = None,
    serial:bool = False,
    verbose:bool = False,
    file_number:str = "0"
):
    data = []

    # Define o diretório para os clusters.
    cluster_dir = f"{output_cluster_dir}/{compressor}"
    cluster_path = f"{cluster_dir}/{compressor}_{type}_{file_number}.out"
    
    if not os.path.exists(cluster_dir):
        os.makedirs(cluster_dir)

    # Verifica se há output para os dados da NCD.
    if output_ncd_dir:
        ncd_dir = f"{output_ncd_dir}/{compressor}"
        ncd_path = f"{ncd_dir}/{compressor}_{type}_{file_number}.out"
        if not os.path.exists(ncd_dir):
            os.makedirs(ncd_dir)
    else:
        ncd_path = None

    # Obtem os argumentos para a DAMICORE
    args = get_args_to_damicore(
        compressor = compressor,
        output_cluster_path = cluster_path,
        output_ncd_path = ncd_path,
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

    data.append({
        "compressor": compressor, 
        "number": file_number,
        "type": type, 
        "time": e-e0, 
        "process_time": p-p0,
        "output": cluster_path
    })

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

def copia_arquivo(origem: str, destino: str):
    """
    Copia um único arquivo para um diretório de destino.

    Parâmetros:
    -----------
    origem : str
        Caminho absoluto ou relativo do arquivo de origem a ser copiado.

    destino : str
        Caminho do diretório de destino onde o arquivo será copiado.

    Comportamento:
    --------------
    - O arquivo será copiado com o mesmo nome no diretório de destino.
    - A função preserva metadados (data de modificação, permissões, etc).
    - Se o destino não existir ou não for um diretório, uma exceção será lançada.
    """
    # Verifica se o caminho de origem é um arquivo existente
    if not os.path.isfile(origem):
        raise FileNotFoundError(f"O arquivo de origem '{origem}' não existe.")

    # Verifica se o destino é um diretório válido
    if not os.path.isdir(destino):
        raise NotADirectoryError(f"O destino '{destino}' não é um diretório válido.")

    # Obtém o nome do arquivo
    nome_arquivo = os.path.basename(origem)

    # Define o caminho completo de destino
    destino_completo = os.path.join(destino, nome_arquivo)

    # Copia o arquivo
    shutil.copy2(origem, destino_completo)

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
        print(f"[COPY] Arquivos de {origem} foram copiados para {destino}")
    
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
 
def verify_singular_group(file: str):
    df = pd.read_csv(file, header=None)
    df.columns = ['file_name', 'group']
    # Extrai partes da string com regex direto da coluna 'file_name'
    df[['load', 'type', 'file']] = df["file_name"].str.extract(
    r'^(?P<load>[^_]+)_.*?_code_(?P<type>[A-Za-z\-]+)_py_(?P<file>\d+)_csv$'
)
    df['file'] = df['file'].astype(int)
    df['group'] = df['group'].astype(int)
    df = df[['load', 'type', 'file', 'group']]

    filtros = df.groupby("group")["type"].apply(lambda x: (x != "CONTROL").all())
    exclusive_groups = filtros[filtros].index.tolist()
    
    return len(exclusive_groups) > 0
if __name__ == '__main__':

    # Configura os argumentos para o script.
    parser = argparse.ArgumentParser(description="Executa o DAMICORE com diversos parâmetros configuráveis.")

    # Argumento posicional obrigatório
    parser.add_argument("compressor", help="Nome do compressor")

    # Flags opcionais
    parser.add_argument("--serial", action="store_true", help="Executar em modo serial")
    parser.add_argument("--all", action="store_true", help="Carregar todos os perfis de um tipo")
    parser.add_argument("--verbose", action="store_true", help="Exibir saídas detalhadas")

    # Argumentos opcionais com valores padrão
    parser.add_argument("--level", type=int, default=9, help="Nível de compressão (padrão: 9)")
    parser.add_argument("--order", type=int, default=16, help="Ordem do modelo (padrão: 16)")
    parser.add_argument("--memory", type=int, default=16, help="Tamanho da memória (padrão: 16)")
    parser.add_argument("--reps", type=int, default=100, help="Tamanho da memória (padrão: 16)")
    parser.add_argument(
        "--types",
        nargs="+",
        default=all_types,
        choices=all_types,
        help=f"Tipos selecionados (padrão: {all_types})"
    )
    parser.add_argument(
        "--loads",
        nargs="+",
        default=all_loads,
        choices=all_loads,
        help=f"Loads selecionados (padrão: {all_loads})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results",  # valor padrão
        help="Diretório ou arquivo de saída (padrão: 'resultados')"
    )

    args = parser.parse_args()

    compressor = args.compressor
    serial_flag = args.serial
    verbose_flag = args.verbose
    level_value = args.level
    order_value = args.order
    memory_value = args.memory
    repetition = args.reps
    selected_types = args.types
    selected_loads = args.loads
    all = args.all

    output_dir = f"{results_dir}/{args.output}"
    os.makedirs(output_dir, exist_ok=True)

    # Para cada load.
    for load in os.listdir(profiles_dir): # profiles
        load_dir = f"{profiles_dir}/{load}" # profiles/CANCHER-PHON
        
        if not os.path.isdir(load_dir): # Verifica se não é um diretório.
            continue
        if not load in selected_loads: # Se não está dentro dos loads selecionados.
            continue
        
        control_dir = f"{load_dir}/CONTROL" # Obtém o diretório de controle da carga. #profiles/CANCER-PHON/CONTROL
        times_dir = f"{output_dir}/TIMES"
        # Para cada tipo dentro de load.
        for type in os.listdir(load_dir): 
            if not type in selected_types: # Se não está dentro dos tipos selecionados.
                continue

            print(f"\n\033[33mLOAD: {load}")
            print(f"TYPE: {type}")
            print(f"COMPRESSOR: {compressor}\n\033[0m")

            type_dir = f"{load_dir}/{type}" # profiles/CANCHER-PHON/API
            cluster_dir = f"{output_dir}/CLUSTERS/{load}/{type}" # results/4_damicore/CLUSTERS/CANCER-PHON/API
            output_path = f"{output_dir}/RESULTS/{load}/{type}" # results/4_damicore/RESULTS/CANCER-PHON/API

            os.makedirs(cluster_dir, exist_ok=True)

            profile_paths = [f for f in os.listdir(type_dir) if os.path.isfile(os.path.join(type_dir, f))]

            for rep in range(repetition):
                limpa_dir("../sample_data")
                copia_arquivos(control_dir, "../sample_data") # Copia os arquivos CONTROL para sample_data

                total_time = 0

                if all:
                    i = len(profile_paths)
                    copia_arquivos(type_dir, "../sample_data")
                    if compressor in compressors:                    
                        data = execute_damicore(
                            compressor = compressor,
                            type = type,
                            output_cluster_dir = cluster_dir,
                            level = 9,
                            order = 16,
                            memory = 16,
                            verbose=False,
                            serial=serial_flag,
                            file_number = i if i != -1 else "default"
                        )
                        total_time += data[0]['time']
                        processing_time_to_json(data, f"../times_wtime/{load}.json")
                        is_singular = verify_singular_group(data[0]["output"])
                else:
                    for i in range(-1, len(profile_paths)):
                        if i != -1:
                            path = f"{type_dir}/{profile_paths[i]}"
                            copia_arquivo(path, "../sample_data")
                            print(f"\033[36mADICIONANDO {os.path.basename(path)} AOS GRUPOS\033[0m")
                        else:
                            print("\033[36mCONFIGURANDO AGRUPAMENTO DE CONTROLE...\033[0m")
                        if compressor in compressors:                    
                            data = execute_damicore(
                                compressor = compressor,
                                type = type,
                                output_cluster_dir = cluster_dir,
                                level = 9,
                                order = 16,
                                memory = 16,
                                verbose=False,
                                serial=serial_flag,
                                file_number = i if i != -1 else "default"
                            )
                            total_time += data[0]['time']
                            processing_time_to_json(data, f"../times_wtime/{load}.json")
                            is_singular = verify_singular_group(data[0]["output"])
                            if(is_singular):
                                break
                processing_time_to_json(
                    [{
                        "load": load,
                        "type": type,
                        "compressor": compressor,
                        "iteration": i if is_singular else -1,
                        "time": total_time,
                        "repetition": rep
                    }],
                    output_path)
                # TRANSFORMAR OS .OUT EM JSON

            
        