import os
import io
from PIL import Image
from math import sqrt

def get_bitmap_hex_bytes(data, output = None) -> bytes:
    pixels = []
    v_size = 0
    for line in data.splitlines():
        v_size += 1
        line = line.strip().split(';')
        h_size = len(line)
        # print(line)
        for value in line:
            value = int(float(value))
            a = int((value & 0xff000000) >> 24)
            r = int((value & 0xff0000) >> 16)
            g = int((value & 0x00ff00) >> 8)
            b = int((value & 0x0000ff) >> 0)
            # print(f"HEXCODE: {value.to_bytes(4, 'big').hex()} -> RGBA: {(r,g,b,a)}")
            pixels.insert(0, (r,g,b,a))

    # Criar uma nova imagem RGBA (com canal alpha)
    imagem = Image.new("RGBA", (h_size, v_size))


    for i in range(h_size):
        for j in range(v_size):
            pixel = pixels.pop()
            imagem.putpixel((i,j), pixel)

    img_bytes = io.BytesIO()

    # Salvar a imagem no formato BMP (32 bits para incluir o canal alpha)
    imagem.save(img_bytes, "BMP")

    if output is not None:
        imagem.save(output, "BMP")

    return img_bytes.getvalue()

def get_bitmap_bytes(data:str) -> bytes:
    pixels = []
    for line in data.splitlines():
        line = line.strip().split(';')
        r = int(float(line[0]))
        g = int(float(line[1]))
        b = int(float(line[2]))
        a = 255 - int(float(line[3]))
        pixels.insert(0,(r,g,b,a))

    nPixels = len(pixels)
    l = int(sqrt(nPixels))

    # Criar uma nova imagem RGBA (com canal alpha)
    imagem = Image.new("RGBA", (l, l))  # Vermelho semi-transparente

    for i in range(l):
        for j in range(l):
            pixel = pixels.pop()
            imagem.putpixel((i,j), pixel)

    img_bytes = io.BytesIO()

    # Salvar a imagem no formato BMP (32 bits para incluir o canal alpha)
    imagem.save(img_bytes, "BMP")

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

if __name__ == "__main__":
    with open("../../original_data/CANCER-PHON/CONTROL/CANCER_PHON_dtc_experiment_code_CONTROL_py_5_csv", "r") as f:
        data = f.read()
    
    bytes = get_bitmap_hex_bytes(data, "../../image.bmp")
