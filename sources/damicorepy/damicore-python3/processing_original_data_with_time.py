from damicore import damicore
from time import process_time
from time import time
import shutil
import json
import os


def level_based_compressor_clustering(compressor:str, tipo:str, output_path:str, ncd_path:str, levelset=[9], export_time_dir:str="../compressor_times"):
    data = []
    for level in levelset:
        clusterdir = f"{output_path}/{compressor}_level_{level}"
        if not os.path.exists(clusterdir):
            os.makedirs(clusterdir)

        clusterpath = f"{clusterdir}/{compressor}_{tipo}_level_{level}.out"

        ncddir = f"{ncd_path}/{compressor}_level_{level}"
        if not os.path.exists(ncddir):
            os.makedirs(ncddir)

        ncdpath = f"{ncddir}/{compressor}_{tipo}_level_{level}.csv"

        print(f"[LOG] Gerando arquivo de clusterização no {compressor} de nível {level}")
        
        args = ["--compressor", compressor, 
                "--level", str(level),
                "--ncd-output", ncdpath, 
                "--no-verbose", 
                "--json-time", f"{export_time_dir}/{compressor}_{tipo}_level_{level}.json",
                "--output", clusterpath, "../sample_data"]
        
        e0 = time()
        p0 = process_time()
        damicore.main(args)
        p = process_time()
        e = time()
        data.append({"compressor": f"{compressor}_level_{level}", "type": tipo, "time": e-e0, "process_time": p-p0})

    return data

def entropy_clustering(tipo:str, output_path:str, ncd_path:str, export_time_dir:str="../compressor_times"):
    clusterdir = os.path.join(output_path, "entropy")
    if not os.path.exists(clusterdir):
        os.makedirs(clusterdir)
    clusterfile = f"entropy_{tipo}.out"
    clusterpath = os.path.join(clusterdir, clusterfile)

    ncddir = os.path.join(ncd_path, "entropy")
    if not os.path.exists(ncddir):
        os.makedirs(ncddir)
    ncdfile = f"entropy_{tipo}.csv"
    ncdpath = os.path.join(ncddir, ncdfile)
    print(f"[LOG] Gerando arquivo de clusterização no entropy.")

    args = ["--compressor", "entropy", 
            "--ncd-output", ncdpath, 
            "--no-verbose", 
            "--json-time", f"{export_time_dir}/entropy.json",
            "--output", clusterpath, "../sample_data"]
    
    e0 = time()
    p0 = process_time()
    damicore.main(args)
    p = process_time()
    e = time()
    

    return [{"compressor": "entropy", "type": tipo, "time": e-e0, "process_time": p-p0}]

def png_clustering(tipo:str, output_path:str, ncd_path:str, export_time_dir:str="../compressor_times"):
    clusterdir = os.path.join(output_path, "png")
    if not os.path.exists(clusterdir):
        os.makedirs(clusterdir)
    clusterfile = f"png_{tipo}.out"
    clusterpath = os.path.join(clusterdir, clusterfile)

    ncddir = os.path.join(ncd_path, "png")
    if not os.path.exists(ncddir):
        os.makedirs(ncddir)
    ncdfile = f"png_{tipo}.csv"
    ncdpath = os.path.join(ncddir, ncdfile)
    print(f"[LOG] Gerando arquivo de clusterização no PNG.")

    args = ["--compressor", "png", 
            "--ncd-output", ncdpath, 
            "--no-verbose", 
            "--json-time", f"{export_time_dir}/png.json",
            "--output", clusterpath, "../sample_data"]
    
    e0 = time()
    p0 = process_time()
    damicore.main(args)
    p = process_time()
    e = time()

    return [{"compressor": "png", "type": tipo, "time": e-e0, "process_time": p-p0}]

def webp_clustering(tipo:str, output_path:str, ncd_path:str, lossy = False, export_time_dir:str="../compressor_times"):
    if lossy == True:
        lossy_str = "_lossy"
    else:
        lossy_str = "_lossless"
    
    clusterdir = os.path.join(output_path, f"webp{lossy_str}")
    if not os.path.exists(clusterdir):
        os.makedirs(clusterdir)

    clusterfile = f"webp_{tipo}{lossy_str}.out" 
    clusterpath = os.path.join(clusterdir, clusterfile)

    ncddir = os.path.join(ncd_path, f"webp{lossy_str}")
    if not os.path.exists(ncddir):
        os.makedirs(ncddir)

    ncdfile = f"webp_{tipo}{lossy_str}.csv" 
    ncdpath = os.path.join(ncddir, ncdfile)

    print(f"[LOG] Gerando arquivo de clusterização no WEBP.")

    args = ["--compressor", "webp", 
            "--lossy", str(int(lossy)),
            "--ncd-output", ncdpath, 
            "--no-verbose", 
            "--json-time", f"{export_time_dir}/webp{lossy_str}.json",
            "--output", clusterpath, "../sample_data"]
    e0 = time()
    p0 = process_time()
    damicore.main(args)
    p = process_time()
    e = time()

    return [{"compressor": f"webp{lossy_str}", "type": tipo, "time": e-e0, "process_time" : p-p0}]

def jp2_clustering(tipo:str, output_path:str, ncd_path:str, lossy = False,  export_time_dir:str="../compressor_times"):
    if lossy == True:
        lossy_str = "_lossy"
    else:
        lossy_str = "_lossless"
    
    clusterdir = os.path.join(output_path, f"jp2{lossy_str}")
    if not os.path.exists(clusterdir):
        os.makedirs(clusterdir)

    clusterfile = f"jp2_{tipo}{lossy_str}.out" 
    clusterpath = os.path.join(clusterdir, clusterfile)

    ncddir = os.path.join(ncd_path, f"jp2{lossy_str}")
    if not os.path.exists(ncddir):
        os.makedirs(ncddir)

    ncdfile = f"jp2_{tipo}{lossy_str}.csv" 
    ncdpath = os.path.join(ncddir, ncdfile)

    print(f"[LOG] Gerando arquivo de clusterização no JP2.")

    args = ["--compressor", "jp2", 
            "--lossy", str(int(lossy)),
            "--ncd-output", ncdpath, 
            "--no-verbose", 
            "--json-time", f"{export_time_dir}/jp2{lossy_str}.json",
            "--output", clusterpath, "../sample_data"]
    e0 = time()
    p0 = process_time()
    damicore.main(args)
    p = process_time()
    e = time()

    return [{"compressor": f"jp2{lossy_str}", "type": tipo, "time": e-e0, "process_time" : p-p0}]

def heif_clustering(tipo:str, output_path:str, ncd_path:str,  export_time_dir:str="../compressor_times"):
    clusterdir = os.path.join(output_path, "heif")
    if not os.path.exists(clusterdir):
        os.makedirs(clusterdir)
    clusterfile = f"heif_{tipo}.out"
    clusterpath = os.path.join(clusterdir, clusterfile)

    ncddir = os.path.join(ncd_path, "heif")
    if not os.path.exists(ncddir):
        os.makedirs(ncddir)
    ncdfile = f"heif_{tipo}.csv"
    ncdpath = os.path.join(ncddir, ncdfile)
    print(f"[LOG] Gerando arquivo de clusterização no HEIF.")

    args = ["--compressor", "heif", 
            "--ncd-output", ncdpath, 
            "--no-verbose", 
            "--json-time", f"{export_time_dir}/heif.json",
            "--output", clusterpath, "../sample_data"]
    
    e0 = time()
    p0 = process_time()
    damicore.main(args)
    p = process_time()
    e = time()

    return [{"compressor": "heif", "type": tipo, "time": e-e0, "process_time" : p-p0}]

def ppmd_clustering(tipo:str, output_path:str, ncd_path:str, orderset=[16], memset = [16], by_order=True, export_time_dir:str="../compressor_times"):
    data = []
    if by_order:
        memset = [16]
    else:
        orderset = [16]

    for mem in memset:
        for order in orderset:
            if by_order:
                clusterdir = os.path.join(output_path, "ppmd_order_" + str(order))
                clusterfile = "ppmd_" + tipo + "_order_"+ str(order) + ".out"

                ncddir = os.path.join(ncd_path, "ppmd_order_" + str(order))
                ncdfile = "ppmd_" + tipo + "_order_"+ str(order) + ".csv"
            else:
                clusterdir = os.path.join(output_path, "ppmd_mem_" + str(mem))
                clusterfile = "ppmd_" + tipo + "_mem_"+ str(mem) + ".out"

                ncddir = os.path.join(ncd_path, "ppmd_mem_" + str(mem))
                ncdfile = "ppmd_" + tipo + "_mem_"+ str(mem) + ".csv"

            if not os.path.exists(clusterdir):
                os.makedirs(clusterdir)
            if not os.path.exists(ncddir):
                os.makedirs(ncddir)

            clusterpath = os.path.join(clusterdir, clusterfile)
            ncdpath = os.path.join(ncddir, ncdfile)

            print(f"[LOG] Gerando arquivo de clusterização no PPMD de ordem {order} e memória {mem}")
            args = ["--compressor", "ppmd",
                    "--model-order", str(order),
                    "--memory",str(mem),
                    "--ncd-output", ncdpath, 
                    "--no-verbose",  
                    "--json-time", f"{export_time_dir}/ppmd_{tipo}_order_{order}.json",
                    "--output", clusterpath, "../sample_data"]
            e0 = time()
            p0 = process_time()
            damicore.main(args)
            p = process_time()
            e = time()
            data.append({"compressor": f"ppmd_order_{order}", "type": tipo, "time":e-e0, "process_time":p-p0})
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

def execute_compressor(compressor:str, type:str, output_path:str, ncd_path:str, levels=[9], orderset=[16], export_time_dir:str="../compressor_times"):
    if compressor == "zlib":
        return level_based_compressor_clustering("zlib", type, output_path, ncd_path, levels, export_time_dir=export_time_dir)
    elif compressor == "gzip":
        return level_based_compressor_clustering("gzip", type, output_path, ncd_path, levels, export_time_dir=export_time_dir)
    elif compressor == "bz2":
        return level_based_compressor_clustering("bz2", type, output_path, ncd_path, levels, export_time_dir=export_time_dir)
    elif compressor == "bzip2":
        return level_based_compressor_clustering("bzip2", type, output_path, ncd_path, levels, export_time_dir=export_time_dir)
    elif compressor == "lzma":
        return level_based_compressor_clustering("lzma", type, output_path, ncd_path, levels, export_time_dir=export_time_dir)
    elif compressor == "ppmd":
        return ppmd_clustering(type, output_path, ncd_path, orderset = orderset, export_time_dir=export_time_dir)
    elif compressor == "webp_lossless":
        return webp_clustering(type, output_path, ncd_path, lossy=False, export_time_dir=export_time_dir)
    elif compressor == "png":
        return png_clustering(type, output_path, ncd_path, export_time_dir=export_time_dir)
    elif compressor == "jp2_lossless":
        return jp2_clustering(type, output_path, ncd_path, lossy=False, export_time_dir=export_time_dir)
    elif compressor == "entropy":
        return entropy_clustering(type, output_path, ncd_path, export_time_dir=export_time_dir)
    elif compressor == "webp_lossy":
        return webp_clustering(type, output_path, ncd_path, lossy=True, export_time_dir=export_time_dir)
    elif compressor == "jp2_lossy":
        return jp2_clustering(type, output_path, ncd_path, lossy=True, export_time_dir=export_time_dir)
    elif compressor == "heif":
        return heif_clustering(type, output_path, ncd_path, export_time_dir=export_time_dir)
    else: 
        raise Exception(f"Compressor {compressor} não está catalogado")
    

if __name__ == '__main__':
    limpa_dir("../clusters_wtime")
    limpa_dir("../ncds_wtime")
    limpa_dir("../times_wtime")
    limpa_dir("../compressor_times")

    default_dir = '../original_data/'
    default_export_time_dir = '../compressor_times'
    # selected_load = ['BANK-PIMA', 'CANCER-PHON', 'IONO-SOLAR', 'IRIS-HARBER', 'OIL-MAMMO', 'WINE-HEART']
    selected_load = ['CANCER-PHON']
    # selected_type = ['API', 'CONC', 'LOGIC', 'MEMORY', 'MODEL', 'PROCESS', 'TRAIN']
    selected_type = ['API', 'MEMORY', 'PROCESS']
    compressors = ["zlib", "gzip", "bzip2", "bz2", "ppmd", "webp_lossless", "png", "jp2_lossless", "entropy", "webp_lossy", "jp2_lossy", "heif"]
    repetition = 100
    max = len(selected_load) * len(selected_type) * len(compressors) * repetition
    current = 1

    # selected_load = ['CANCER-PHON']
    # selected_type = ['API']

    init_time = time()

    for load in os.listdir(default_dir):
        if not load in selected_load:
            continue

        load_dir = os.path.join(default_dir, load)
        if not os.path.isdir(load_dir):
            continue

        print(f"[PATH] abrindo caminho {load_dir}")

        control_dir = os.path.join(load_dir, 'CONTROL')

        type_init_time = time()

        for type in os.listdir(load_dir):
            if type in selected_type:
                export_time_dir=f"{default_export_time_dir}/{load}/{type}"
                if not os.path.exists(export_time_dir):
                    os.makedirs(export_time_dir)

                type_dir = os.path.join(load_dir, type)
                print(f"\t[PATH] abrindo caminho {type_dir}")

                copia_samples(control_dir, type_dir, '../sample_data')
                # input("Continuar...")

                output_path = os.path.join("../clusters_wtime/", load)
                ncd_path = os.path.join("../ncds_wtime/", load)
                
                for compressor in compressors:
                    compressor_init_time = time()
                    for i in range(repetition):
                       print(f"\n\033[33mLOAD: {load}")
                       print(f"TYPE: {type}")
                       print(f"COMPRESSOR: {compressor}\n")
                       print(f"\033[36m[REPETITION]: {i}\033[0m\n") 

                       time_path = f"../times_wtime/{load}.json"
                       data = execute_compressor(compressor, type, output_path, ncd_path, export_time_dir=export_time_dir)
                       processing_time_to_json(data, time_path)
                       print()
                       print_progress_bar(current=current,min=0, max=max)

                       current += 1
                    print(f"\n\033[36m[LOOP TIME] {time() - compressor_init_time} s\033[0m\n")
        print(f"\n\033[36m[TYPE TIME] {time() - type_init_time} s\033[0m\n")
    print(f"\n\033[36m[TOTAL TIME] {time() - init_time} s\033[0m\n")
                

        