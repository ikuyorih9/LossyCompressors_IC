import io
import math
from PIL import Image

def get_bitmap_byte_to_component(data, block_size = 4, output = None):
    pixels = []
    
    # for line in data:
    byte_list = [ord(byte) for byte in data]  # Converte todos os caracteres da linha em seus valores numéricos
    # print(f"[LEN] {len(byte_list)}")
    for i in range(0, len(byte_list), 3):  # Percorre a lista em passos de 3
        r = byte_list[i] if i < len(byte_list) else 0
        g = byte_list[i+1] if i+1 < len(byte_list) else 0
        b = byte_list[i+2] if i+2 < len(byte_list) else 0
        pixels.insert(0, (r, g, b))  # Insere o RGB na lista de pixels
        # print((r,g,b))

    pixels_len = len(pixels)
    altura = block_size
    largura = math.ceil(pixels_len/altura)

    # Criar uma nova imagem RGBA (com canal alpha)
    imagem = Image.new("RGBA", (largura, altura))

    for i in range(largura):
        for j in range(altura):
            try:
                pixel = pixels.pop()
                imagem.putpixel((i,j), pixel)
            except IndexError:
                imagem.putpixel((i,j), (0,0,0))

    img_bytes = io.BytesIO()

    # Salvar a imagem no formato BMP (32 bits para incluir o canal alpha)
    imagem.save(img_bytes, "BMP")

    if output is not None:
        imagem.save(output, "BMP")

    return img_bytes.getvalue()

def get_bitmap_byte_to_pixel(data, block_size = 4, output= None):
    pixels = []
    
    for line in data:
        for byte in line:
            # print(f"Transformando {byte} -> {ord(byte)}")
            byte = ord(byte)
            b = int((byte & 0x0000ff))
            pixels.insert(0,(0,0,b))

    pixels_len = len(pixels)
    altura = block_size
    largura = math.ceil(pixels_len/altura)
    # print(f"{largura} x {altura} = {largura * altura} ({pixels_len})")

    # Criar uma nova imagem RGBA (com canal alpha)
    imagem = Image.new("RGBA", (largura, altura))

    for i in range(largura):
        for j in range(altura):
            try:
                pixel = pixels.pop()
                imagem.putpixel((i,j), pixel)
            except IndexError:
                imagem.putpixel((i,j), (0,0,0))

    img_bytes = io.BytesIO()

    # Salvar a imagem no formato BMP (32 bits para incluir o canal alpha)
    imagem.save(img_bytes, "BMP")

    if output is not None:
        imagem.save(output, "BMP")

    return img_bytes.getvalue()

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

if __name__ == "__main__":
    with open("../../original_data/CANCER-PHON/CONTROL/CANCER-PHON_dtc_experiment_code_CONTROL_py_6_csv", "r") as f:
        data = f.read()
        # print(data)
    get_bitmap_byte_to_pixel(data, output="../../color_pixels.bmp")
    get_bitmap_byte_to_component(data, output="../../component_pixels.bmp")