import math

def calculate_entropy_compression(s: str) -> int:

    freq: dict = {}
    for char in s:
        if not char in freq:
            freq[char] = 0
        freq[char] += 1

    entropy = 0
    for char in freq:
        p_x = freq[char] / len(s)
        entropy += -p_x * math.log2(p_x)

    byte_size = (entropy * len(s)) / 8
    return math.ceil(byte_size)

if __name__ == "__main__":

    with open("../../original_data/CANCER-PHON/CONTROL/CANCER_PHON_dtc_experiment_code_CONTROL_py_6_csv", "r") as f:
        data = f.read()

    import bitmap
    in_bytes = bitmap.get_bitmap_hex_bytes(data, "../../img_bitmap.bmp")
    print(f"Original data bytes: {len(in_bytes)}")
    print(f"Compression lower bound: {calculate_entropy_compression(in_bytes)} bytes")
    

    # string_to_be_compressed: str = input("input string: ")
    # fixed_overhead: int = int(input("number of bytes to consider as overhead: "))
    # print(f"Compression lower bound: {calculate_entropy_compression(string_to_be_compressed) + fixed_overhead} bytes")