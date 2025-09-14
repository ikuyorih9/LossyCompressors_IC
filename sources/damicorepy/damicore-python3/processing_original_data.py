from damicore import damicore
from time import process_time
import shutil
import json
import os

def level_based_compressor_clustering(compressor:str, tipo:str, output_path:str, ncd_path:str, levelset=[9]):
    data = []
    for level in levelset:
        clusterdir = os.path.join(output_path, f"{compressor}_level_{level}")
        if not os.path.exists(clusterdir):
            os.makedirs(clusterdir)

        clusterfile = f"{compressor}_{tipo}_level_{level}_.out"
        clusterpath = os.path.join(clusterdir, clusterfile)

        ncddir = os.path.join(ncd_path, f"{compressor}_level_{level}")
        if not os.path.exists(ncddir):
            os.makedirs(ncddir)

        ncdfile = f"{compressor}_{tipo}_level_{level}_.csv"
        ncdpath = os.path.join(ncddir, ncdfile)

        print("\n[CLUSTER PATH]: " + clusterpath)
        print(f"[LOG] Gerando arquivo de clusterização no BZ2 de nível {level}")
        
        args = ["--compressor", compressor, 
                "--level", str(level),
                "--ncd-output", ncdpath, 
                "--tree-output", "tree.newick", 
                "--graph-image", "../graph.png", 
                "--output", clusterpath, "../sample_data"]
        
        t0 = process_time()
        damicore.main(args)
        t = process_time()
        data.append({"compressor": f"{compressor}_level_{level}", "type": tipo, "time": t-t0})

    return data

def entropy_clustering(tipo:str, output_path:str, ncd_path:str):
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
    print("\n[CLUSTER PATH]: " + clusterpath)
    print(f"[LOG] Gerando arquivo de clusterização no entropy.")

    args = ["--compressor", "entropy", 
            "--ncd-output", ncdpath, 
            "--output", clusterpath, "../sample_data"]
    
    t0 = process_time()
    damicore.main(args)
    t = process_time()

    return [{"compressor": "entropy", "type": tipo, "time": t-t0}]

def png_clustering(tipo:str, output_path:str, ncd_path:str):
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
    print("\n[CLUSTER PATH]: " + clusterpath)
    print(f"[LOG] Gerando arquivo de clusterização no PNG.")

    args = ["--compressor", "png", 
            "--ncd-output", ncdpath, 
            "--output", clusterpath, "../sample_data"]
    
    t0 = process_time()
    damicore.main(args)
    t = process_time()

    return [{"compressor": "png", "type": tipo, "time": t-t0}]

def webp_clustering(tipo:str, output_path:str, ncd_path:str, lossy = False):
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

    print("\n[CLUSTER PATH]: " + clusterpath)
    print(f"[LOG] Gerando arquivo de clusterização no WEBP.")
    print(f"[LOSSLESS]: {str(lossy)}")

    args = ["--compressor", "webp", 
            "--lossy", str(int(lossy)),
            "--ncd-output", ncdpath, 
            "--output", clusterpath, "../sample_data"]
    t0 = process_time()
    damicore.main(args)
    t = process_time()

    return [{"compressor": f"webp{lossy_str}", "type": tipo, "time": t-t0}]

def jp2_clustering(tipo:str, output_path:str, ncd_path:str, lossy = False):
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

    print("\n[CLUSTER PATH]: " + clusterpath)
    print(f"[LOG] Gerando arquivo de clusterização no JP2.")
    print(f"[LOSSY]: {str(lossy)}")

    args = ["--compressor", "jp2", 
            "--lossy", str(int(lossy)),
            "--ncd-output", ncdpath, 
            "--output", clusterpath, "../sample_data"]
    t0 = process_time()
    damicore.main(args)
    t = process_time()

    return [{"compressor": f"jp2{lossy_str}", "type": tipo, "time": t-t0}]

def heif_clustering(tipo:str, output_path:str, ncd_path:str):
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
    print("\n[CLUSTER PATH]: " + clusterpath)
    print(f"[LOG] Gerando arquivo de clusterização no HEIF.")

    args = ["--compressor", "heif", 
            "--ncd-output", ncdpath, 
            "--output", clusterpath, "../sample_data"]
    
    t0 = process_time()
    damicore.main(args)
    t = process_time()

    return [{"compressor": "heif", "type": tipo, "time": t-t0}]

def zlib_clustering(tipo:str, output_path:str, ncd_path:str, levelset=[9]):
    for level in levelset:
        clusterdir = os.path.join(output_path, "zlib_level_" + str(level))
        if not os.path.exists(clusterdir):
            os.makedirs(clusterdir)

        clusterfile = "zlib_" + tipo + "_level_"+ str(level) + ".out"
        clusterpath = os.path.join(clusterdir, clusterfile)

        ncddir = os.path.join(ncd_path, "zlib_level_" + str(level))
        if not os.path.exists(ncddir):
            os.makedirs(ncddir)

        ncdfile = "zlib_" + tipo + "_level_"+ str(level) + ".csv"
        ncdpath = os.path.join(ncddir, ncdfile)

        print("\n[CLUSTER PATH]: " + clusterpath)
        print(f"[LOG] Gerando arquivo de clusterização no ZLIB de nível {level}")
        args = ["--compressor", "zlib", 
                "--level", str(level),
                "--ncd-output", ncdpath, 
                "--tree-output", "tree.newick", 
                "--graph-image", "../graph.png", 
                "--output", clusterpath, "../sample_data"]
        damicore.main(args)

def ppmd_clustering(tipo:str, output_path:str, ncd_path:str, orderset=[16], memset = [16], by_order=True):
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

            print("\n[CLUSTER FILE]: "+ clusterfile)
            print(f"[LOG] Gerando arquivo de clusterização no PPMD de ordem {order} e memória {mem}")
            args = ["--compressor", "ppmd",
                    "--model-order", str(order),
                    "--memory",str(mem),
                    "--ncd-output", ncdpath, 
                    "--tree-output", "tree.newick", 
                    "--graph-image", "../graph.png", 
                    "--output", clusterpath, "../sample_data"]
            t0 = process_time()
            damicore.main(args)
            t = process_time()
            data.append({"compressor": f"ppmd_order_{order}", "type": tipo, "time": t-t0})
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

if __name__ == '__main__':
    limpa_dir("../clusters")
    limpa_dir("../ncds")
    limpa_dir("../times")

    default_dir = '../original_data/'
    selected_dir = ['API', 'CONC', 'LOGIC', 'MEMORY', 'MODEL', 'PROCESS', 'TRAIN', 'ANOTHER-CONTROL']
    # selected_dir = ['ANOTHER-CONTROL']

    for load in os.listdir(default_dir):
        load_dir = os.path.join(default_dir, load)
        if not os.path.isdir(load_dir):
            continue

        print(f"[PATH] abrindo caminho {load_dir}")

        control_dir = os.path.join(load_dir, 'CONTROL')

        for type in os.listdir(load_dir):
            if type in selected_dir:
                type_dir = os.path.join(load_dir, type)
                print(f"\t[PATH] abrindo caminho {type_dir}")

                copia_samples(control_dir, type_dir, '../sample_data')
                # input("Continuar...")

                # for filename in os.listdir('../sample_data'):
                #     if filename.split("_")[5] != 'CONTROL':
                #         tipo = filename.split("_")[5].lower()
                #         break

                output_path = os.path.join("../clusters/",load)
                ncd_path = os.path.join("../ncds/", load)
                time_path = f"../times/{load}.json"

                data = level_based_compressor_clustering("zlib", type, output_path, ncd_path,[9])
                # processing_time_to_json(data, f"../times/{load}.json")

                data = level_based_compressor_clustering("gzip", type, output_path, ncd_path,[9])
                # processing_time_to_json(data, f"../times/{load}.json")

                data =level_based_compressor_clustering("bz2", type, output_path, ncd_path,[9])
                # processing_time_to_json(data, f"../times/{load}.json")

                data = level_based_compressor_clustering("bzip2", type, output_path, ncd_path,[9])
                # processing_time_to_json(data, f"../times/{load}.json")

                data = ppmd_clustering(type, output_path, ncd_path, orderset = [16])
                # processing_time_to_json(data, f"../times/{load}.json")

                data = webp_clustering(type, output_path, ncd_path, lossy=False)
                # processing_time_to_json(data, f"../times/{load}.json")

                data =  png_clustering(type, output_path, ncd_path)
                # processing_time_to_json(data, f"../times/{load}.json")

                data = jp2_clustering(type, output_path, ncd_path, lossy=False)
                # processing_time_to_json(data, f"../times/{load}.json")

                # LOSSY

                data = webp_clustering(type, output_path, ncd_path, lossy=True)
                # processing_time_to_json(data, f"../times/{load}.json")

                data = jp2_clustering(type, output_path, ncd_path, lossy=True)
                # processing_time_to_json(data, f"../times/{load}.json")

                data =  heif_clustering(type, output_path, ncd_path)
                # processing_time_to_json(data, f"../times/{load}.json")

                # data = entropy_clustering(type, output_path, ncd_path)
                # processing_time_to_json(data, f"../times/{load}.json")
