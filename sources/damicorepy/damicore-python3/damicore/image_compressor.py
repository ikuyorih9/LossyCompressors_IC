import io
import pillow_heif
from PIL import Image
from damicore.entro import calculate_entropy_compression

# Registrar suporte ao formato HEIF no Pillow
pillow_heif.register_heif_opener()

def compress_to_heif_from_bytes(input_bytes: bytes, quality=90) -> bytes:
    """
    Converte uma imagem em bytes (BMP ou outro formato suportado pelo Pillow) para HEIF/HEIC.
    
    :param input_bytes: Bytes da imagem de entrada.
    :param quality: Qualidade da compressão HEIF (0-100).
    :return: Bytes da imagem convertida para HEIF.
    """
    # Abrir a imagem a partir dos bytes
    img = Image.open(io.BytesIO(input_bytes))

    # Se a imagem tiver 4 canais (RGBA), remover o canal Alpha
    if img.mode == "RGBA":
        img = img.convert("RGB")  # Remove a transparência
    
    # Criar um objeto BytesIO para armazenar a imagem em memória
    img_bytes = io.BytesIO()

    # Salvar a imagem no formato HEIF dentro do BytesIO
    img.save(img_bytes, format="HEIF", quality=quality)

    # Retornar os bytes da imagem HEIF
    return img_bytes.getvalue()

def compress_to_jp2_from_bytes(input:bytes, output:str=None, lossy = True, quality_layers=[50]):
    img = Image.open(io.BytesIO(input))
    img = img.convert("RGB")
    img_bytes = io.BytesIO()

    if lossy:
        quality_mode = 'rates'
    else:
        quality_mode = 'lossless'
        quality_layers = [0]
    img.save(img_bytes, "JPEG2000", quality_mode=quality_mode, quality_layers=quality_layers)
    # if not output:
    #     img.save(output, "JPEG2000", quality_mode=quality_mode, quality_layers=quality_layers)

    return img_bytes.getvalue()

def compress_to_webp_from_bytes(input:bytes, lossy = False):
    # Abrir a imagem BMP
    img = Image.open(io.BytesIO(input))
    
    # Se a imagem tiver 4 canais (RGBA), remover o canal Alpha
    if img.mode == "RGBA":
        img = img.convert("RGB")  # Remove a transparência
    
    img_bytes = io.BytesIO()

    # Salvar como JPEG com compressão ajustável
    img.save(img_bytes, "WEBP", lossless = not lossy)
    
    return img_bytes.getvalue()

def compress_to_png_from_bytes(input:bytes, output:str=None, optimize = True):
    img = Image.open(io.BytesIO(input))
    
    img_bytes = io.BytesIO()

    # Salvar como JPEG com compressão ajustável
    img.save(img_bytes, format="PNG", optimize=optimize)
    
    if output is not None:
        img.save(output, format="PNG", optimize=optimize)

    return img_bytes.getvalue()

if __name__ == "__main__":
    with open("../../original_data/CANCER-PHON/CONTROL/CANCER-PHON_dtc_experiment_code_CONTROL_py_6_csv", "r") as f:
        data = f.read()

    import bitmap
    # in_bytes = bitmap.get_bitmap_hex_bytes(data, "../../img_bitmap.bmp")
    in_bytes = bitmap.get_bitmap_byte_to_pixel(data, output="../../img_bitmap.bmp")
    print(f"BITMAP: {len(in_bytes)}")
    out_bytes = compress_to_heif_from_bytes(in_bytes, quality=90)
    print(f"HEIF: {len(out_bytes)}")
    out_bytes = compress_to_jp2_from_bytes(in_bytes, "../../img_jp2.jp2", lossy=True)
    print(f"JP2: {len(out_bytes)}")
    out_bytes = compress_to_png_from_bytes(in_bytes, "../../img_png.png")
    print(f"PNG: {len(out_bytes)}")
    out_bytes = compress_to_webp_from_bytes(in_bytes, lossy=False)
    print(f"WEBP: {len(out_bytes)}")

    
    out_bytes = calculate_entropy_compression(data)
    print(f"ENTROPY: {out_bytes}")