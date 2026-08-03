# Emisor - Lab 2
# Hamming (correccion) y CRC-32 (deteccion)

def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0


def hamming_encode(data_bits):
    m = len(data_bits)
    r = 0
    while (2 ** r) < (m + r + 1):
        r += 1
    n = m + r

    code = [0] * (n + 1)
    j = 0
    for pos in range(1, n + 1):
        if not is_power_of_two(pos):
            code[pos] = int(data_bits[j])
            j += 1

    for i in range(r):
        p = 2 ** i
        parity = 0
        for pos in range(1, n + 1):
            if pos != p and (pos & p):
                parity ^= code[pos]
        code[p] = parity

    return "".join(str(code[pos]) for pos in range(1, n + 1))


# generador CRC-32 estandar (0x04C11DB7), 33 bits con el 1 implicito
CRC32_GENERATOR = "1" + format(0x04C11DB7, "032b")


def crc32_remainder(bits, generator=CRC32_GENERATOR):
    data = list(bits)
    n = len(generator)
    for i in range(len(data) - n + 1):
        if data[i] == "1":
            for j in range(n):
                data[i + j] = "0" if data[i + j] == generator[j] else "1"
    return "".join(data[-(n - 1):])


def crc32_encode(data_bits):
    padded = data_bits + "0" * 32
    remainder = crc32_remainder(padded)
    return data_bits + remainder


def leer_binario(prompt):
    while True:
        s = input(prompt).strip()
        if s and all(c in "01" for c in s):
            return s
        print("Entrada invalida, solo 0s y 1s.")


def main():
    print("EMISOR")
    print("1) Hamming (correccion)")
    print("2) CRC-32 (deteccion)")

    opcion = input("Algoritmo (1/2): ").strip()
    mensaje = leer_binario("Mensaje en binario: ")

    if opcion == "1":
        trama = hamming_encode(mensaje)
        print(f"Mensaje: {mensaje}")
        print(f"Trama:   {trama}")
    elif opcion == "2":
        trama = crc32_encode(mensaje)
        print(f"Mensaje: {mensaje}")
        print(f"CRC:     {trama[len(mensaje):]}")
        print(f"Trama:   {trama}")
    else:
        print("Opcion invalida.")
        return

    print("Copie la trama y peguela en el receptor.")


if __name__ == "__main__":
    main()
