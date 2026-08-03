# ============================================================
# EMISOR 
#
# Arquitectura de capas:
#
#   APLICACION   -> solicitar_mensaje, mostrar_mensaje
#   PRESENTACION -> codificar_mensaje
#   ENLACE       -> calcular_integridad
#   RUIDO        -> aplicar_ruido
#   TRANSMISION  -> enviar_informacion (sockets TCP)
#
# El emisor actua como cliente de socket. Se conecta al receptor,
# que debe estar corriendo primero y escuchando en el puerto elegido.
# ============================================================

import socket
import random



# ALGORITMOS DE INTEGRIDAD (usados por la capa de ENLACE)
def is_power_of_two(n):
    """
    Las posiciones de los bits de PARIDAD en Hamming siempre son
    potencias de 2 (1, 2, 4, 8, ...). Sirve para distinguir, al armar
    la trama, que posiciones son de paridad (se calculan) y cuales
    son de datos (se copian del mensaje original).
    """
    return n > 0 and (n & (n - 1)) == 0


def hamming_encode(data_bits):
    """
    Codifica 'data_bits' (string de '0'/'1') en un codeword de Hamming
    SEC (Single Error Correction).

    Paso 1: encontrar el minimo r que cumple 2^r >= m + r + 1
            (m = numero de bits de datos). r = cantidad de bits de paridad.
    Paso 2: construir un arreglo de n = m + r posiciones (1-indexado).
            Las posiciones que son potencia de 2 se reservan para
            paridad; el resto se llena en orden con el mensaje original.
    Paso 3: cada bit de paridad = XOR de todas las posiciones que cubre
            (aquellas cuyo indice, en binario, tiene ese bit encendido).
    """
    m = len(data_bits)

    r = 0
    while (2 ** r) < (m + r + 1):
        r += 1
    n = m + r

    code = [0] * (n + 1)  # 1-indexado
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


# Generador estandar CRC-32 (IEEE 802.3): polinomio 0x04C11DB7,
# representado como 33 bits (el "1" implicito + los 32 bits del poly).
CRC32_GENERATOR = "1" + format(0x04C11DB7, "032b")


def crc32_remainder(bits, generator=CRC32_GENERATOR):
    """
    Division polinomial modulo-2 (XOR) de 'bits' entre 'generator'.
    El residuo final (ultimos 32 bits) es el valor de CRC.
    """
    data = list(bits)
    n = len(generator)
    for i in range(len(data) - n + 1):
        if data[i] == "1":
            for j in range(n):
                data[i + j] = "0" if data[i + j] == generator[j] else "1"
    return "".join(data[-(n - 1):])


def crc32_encode(data_bits):
    """
    Trama CRC-32 = datos originales + residuo de 32 bits.
    Se agregan 32 ceros al final del mensaje antes de dividir, para
    "hacer espacio" al residuo (igual que agregar x^32 al polinomio).
    """
    padded = data_bits + "0" * 32
    remainder = crc32_remainder(padded)
    return data_bits + remainder



# CAPA DE PRESENTACION
def codificar_mensaje(texto):
    """
    Codifica cada caracter del texto en su representacion ASCII
    binaria de 8 bits (ej. 'A' -> 01000001) y concatena todo.
    """
    return "".join(format(ord(c), "08b") for c in texto)



# CAPA DE ENLACE
def calcular_integridad(bits_mensaje, algoritmo):
    """
    Aplica el algoritmo de integridad elegido sobre los bits del
    mensaje (ya codificados en ASCII binario) y devuelve la trama
    completa (datos + redundancia) lista para transmitir.
    """
    if algoritmo == "1":
        return hamming_encode(bits_mensaje)
    else:
        return crc32_encode(bits_mensaje)



# CAPA DE RUIDO (simulada del lado del emisor, antes de transmitir)
def aplicar_ruido(trama, prob_error):
    """
    Recorre cada bit de la trama (incluyendo los bits de redundancia,
    que tambien estan expuestos al canal) y lo invierte con
    probabilidad 'prob_error'. Simula un canal no confiable con una
    tasa de error expresada en errores por bit transmitido
    (ej. 1/100 -> prob_error = 0.01).

    Devuelve la trama ya "ruidosa" y la cantidad de bits que se
    voltearon, para poder reportarlo en pantalla.
    """
    bits = list(trama)
    flips = 0
    for i in range(len(bits)):
        if random.random() < prob_error:
            bits[i] = "1" if bits[i] == "0" else "0"
            flips += 1
    return "".join(bits), flips



# CAPA DE TRANSMISION (sockets TCP)
def enviar_informacion(host, puerto, algoritmo, trama_ruidosa):
    """
    Envia la trama al receptor por un socket TCP. El receptor debe
    estar escuchando (accept) en 'host':'puerto' antes de correr esto.

    Formato en el cable: "<algoritmo>|<trama_bits>\n"
    El indicador de algoritmo NO pasa por aplicar_ruido: se trata como
    metadata de protocolo (como un encabezado de capa de enlace real),
    mientras que la trama de datos si sufre el ruido simulado.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, puerto))
        mensaje_wire = f"{algoritmo}|{trama_ruidosa}\n"
        s.sendall(mensaje_wire.encode("ascii"))



# CAPA DE APLICACION
def solicitar_mensaje():
    """
    Pide al usuario: el texto a enviar, el algoritmo de integridad,
    la tasa de error del canal, y los datos de conexion del receptor.
    """
    print("EMISOR")
    texto = input("Mensaje a enviar (texto): ")

    print("Algoritmo de integridad:")
    print("  1) Hamming SEC (correccion)")
    print("  2) CRC-32 (deteccion)")
    algoritmo = input("Opcion (1/2): ").strip()
    if algoritmo not in ("1", "2"):
        print("Opcion invalida, se usara CRC-32 por defecto.")
        algoritmo = "2"

    tasa_str = input(
        "Tasa de error del canal (ej. 1/100, o 0 para sin ruido): "
    ).strip()
    if "/" in tasa_str:
        num, den = tasa_str.split("/")
        prob_error = float(num) / float(den)
    elif tasa_str:
        prob_error = float(tasa_str)
    else:
        prob_error = 0.0

    host = input("Host del receptor [127.0.0.1]: ").strip() or "127.0.0.1"
    puerto_str = input("Puerto del receptor [5000]: ").strip()
    puerto = int(puerto_str) if puerto_str else 5000

    return texto, algoritmo, prob_error, host, puerto


def mostrar_mensaje(texto, bits_mensaje, trama, trama_ruidosa, flips, algoritmo):
    """Muestra en pantalla lo que se va a enviar, para dejar evidencia en el reporte."""
    nombre_algo = "Hamming SEC" if algoritmo == "1" else "CRC-32"
    print("\n--- Resumen de envio ---")
    print(f"Texto original     : {texto}")
    print(f"Bits (ASCII)       : {bits_mensaje}")
    print(f"Algoritmo           : {nombre_algo}")
    print(f"Trama (sin ruido)  : {trama}  ({len(trama)} bits)")
    print(f"Trama (con ruido)  : {trama_ruidosa}  ({flips} bit(s) volteado(s))")
    print("------------------------\n")


def main():
    texto, algoritmo, prob_error, host, puerto = solicitar_mensaje()

    # PRESENTACION: de texto a ASCII binario
    bits_mensaje = codificar_mensaje(texto)

    # ENLACE: agregar redundancia (Hamming o CRC-32)
    trama = calcular_integridad(bits_mensaje, algoritmo)

    # RUIDO: simular canal no confiable
    trama_ruidosa, flips = aplicar_ruido(trama, prob_error)

    mostrar_mensaje(texto, bits_mensaje, trama, trama_ruidosa, flips, algoritmo)

    # TRANSMISION: enviar por socket al receptor
    try:
        enviar_informacion(host, puerto, algoritmo, trama_ruidosa)
        print(f"Trama enviada a {host}:{puerto}.")
    except ConnectionRefusedError:
        print(
            f"No se pudo conectar a {host}:{puerto}. "
            "Asegurate de correr el receptor primero (./receptor)."
        )


if __name__ == "__main__":
    main()
