"""
generar_graficas.py 

Corre una simulacion estadistica usando los algoritmos de emisor.py 
(Hamming SEC y CRC-32) para generar los datos y las graficas solicitadas.
Varia el tamaño de mensaje, probabilidad de error, algoritmo, y overhead.

Para utilizarlo, se debe de tener instalada la libreria matplotlib
"""

import os
import sys
import json
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from emisor import hamming_encode, crc32_encode, codificar_mensaje, is_power_of_two
except ImportError:
    print("ERROR: no se encontro emisor.py en esta carpeta.")
    print("Coloca generar_graficas.py junto a emisor.py y vuelve a correr.")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("ERROR: falta matplotlib/numpy. Instala con:")
    print("  pip install matplotlib numpy --break-system-packages")
    sys.exit(1)

random.seed(42)  # reproducibilidad: siempre da los mismos numeros

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados_pruebas")
os.makedirs(OUT_DIR, exist_ok=True)


# Decodificadores (misma logica que receptor.cpp, reescrita en Python)
def hamming_decode(codeword):
    n = len(codeword)
    code = [0] * (n + 1)
    for i in range(1, n + 1):
        code[i] = int(codeword[i - 1])
    r = 0
    while (1 << r) < (n + 1):
        r += 1
    syndrome = 0
    for i in range(r):
        p = 1 << i
        parity = 0
        for pos in range(1, n + 1):
            if pos & p:
                parity ^= code[pos]
        if parity:
            syndrome += p
    corregido = code[:]
    if syndrome != 0 and syndrome <= n:
        corregido[syndrome] ^= 1
    datos = "".join(str(corregido[pos]) for pos in range(1, n + 1) if not is_power_of_two(pos))
    return datos, syndrome


CRC32_GENERATOR = "1" + format(0x04C11DB7, "032b")


def crc32_remainder(bits, generator=CRC32_GENERATOR):
    data = list(bits)
    n = len(generator)
    for i in range(len(data) - n + 1):
        if data[i] == "1":
            for j in range(n):
                data[i + j] = "0" if data[i + j] == generator[j] else "1"
    return "".join(data[-(n - 1):])


def aplicar_ruido(trama, prob):
    bits = list(trama)
    for i in range(len(bits)):
        if random.random() < prob:
            bits[i] = "1" if bits[i] == "0" else "0"
    return "".join(bits)


def decodificar_ascii(bits):
    chars = []
    for i in range(0, len(bits) - 7, 8):
        chars.append(chr(int(bits[i:i + 8], 2)))
    return "".join(chars)


# Configuracion de la simulacion
MENSAJES = {
    "Corto (2 car.)": "Hi",
    "Medio (11 car.)": "Hola Mundo!",
    "Largo (40 car.)": "Este es un mensaje de prueba mas largo.",
}
ALGORITMOS = ["1", "2"]  # 1 = Hamming, 2 = CRC-32
TASAS = [0.0, 0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2]
N_TRIALS = 300


def correr_simulacion():
    resultados_exito = {}
    resultados_silencioso = {}
    resultados_descartado = {}

    print(f"Corriendo simulacion ({N_TRIALS} corridas por punto)...")
    for algo in ALGORITMOS:
        nombre_algo = "Hamming" if algo == "1" else "CRC-32"
        for label, texto in MENSAJES.items():
            bits = codificar_mensaje(texto)
            trama = hamming_encode(bits) if algo == "1" else crc32_encode(bits)

            tasas_exito, tasas_silencioso, tasas_descartado = [], [], []
            for p in TASAS:
                exitos = silenciosos = descartados = 0
                for _ in range(N_TRIALS):
                    ruidosa = aplicar_ruido(trama, p)
                    if algo == "1":
                        datos, syndrome = hamming_decode(ruidosa)
                        recibido = decodificar_ascii(datos)
                        n = len(ruidosa)
                        if recibido == texto:
                            exitos += 1
                        elif syndrome != 0 and syndrome <= n:
                            silenciosos += 1  # "corrigio" mal, sin avisar
                        else:
                            descartados += 1
                    else:
                        residuo = crc32_remainder(ruidosa)
                        if all(c == "0" for c in residuo):
                            datos = ruidosa[:-32]
                            recibido = decodificar_ascii(datos)
                            if recibido == texto:
                                exitos += 1
                            else:
                                silenciosos += 1  # CRC no detecto el error
                        else:
                            descartados += 1
                tasas_exito.append(exitos / N_TRIALS)
                tasas_silencioso.append(silenciosos / N_TRIALS)
                tasas_descartado.append(descartados / N_TRIALS)

            resultados_exito[f"{algo}|{label}"] = tasas_exito
            resultados_silencioso[f"{algo}|{label}"] = tasas_silencioso
            resultados_descartado[f"{algo}|{label}"] = tasas_descartado
            print(f"  {nombre_algo:8s} | {label:18s} listo")

    # overhead
    overhead_data = []
    for label, texto in MENSAJES.items():
        bits = codificar_mensaje(texto)
        m = len(bits)
        trama_h = hamming_encode(bits)
        trama_c = crc32_encode(bits)
        overhead_data.append({
            "label": label,
            "m": m,
            "hamming_total": len(trama_h),
            "hamming_redundancia": len(trama_h) - m,
            "crc_total": len(trama_c),
            "crc_redundancia": len(trama_c) - m,
        })

    datos = {
        "tasas": TASAS,
        "mensajes": MENSAJES,
        "resultados_exito": resultados_exito,
        "resultados_silencioso": resultados_silencioso,
        "resultados_descartado": resultados_descartado,
        "overhead": overhead_data,
        "n_trials": N_TRIALS,
    }

    json_path = os.path.join(OUT_DIR, "datos_prueba.json")
    with open(json_path, "w") as f:
        json.dump(datos, f, indent=2)
    print(f"\nDatos guardados en {json_path}")
    return datos


# Graficas
def generar_graficas(d):
    tasas = d["tasas"]
    overhead = d["overhead"]

    # ---- Grafica 1: overhead vs tamano de mensaje ----
    labels = [o["label"] for o in overhead]
    m_bits = [o["m"] for o in overhead]
    hred = [o["hamming_redundancia"] for o in overhead]
    cred = [o["crc_redundancia"] for o in overhead]

    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x - width / 2, hred, width, label="Hamming SEC")
    ax.bar(x + width / 2, cred, width, label="CRC-32")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{l}\n({m} bits datos)" for l, m in zip(labels, m_bits)], fontsize=8)
    ax.set_ylabel("Bits de redundancia (overhead)")
    ax.set_title("Overhead por algoritmo segun tamano del mensaje")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "grafica_overhead.png"), dpi=150)
    plt.close(fig)

    # ---- Grafica 2: tasa de exito vs probabilidad de error (mensaje medio) ----
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(tasas, d["resultados_exito"]["1|Medio (11 car.)"], marker="o", label="Hamming SEC")
    ax.plot(tasas, d["resultados_exito"]["2|Medio (11 car.)"], marker="s", label="CRC-32")
    ax.set_xlabel("Probabilidad de error por bit")
    ax.set_ylabel("Tasa de entrega correcta")
    ax.set_title(f"Tasa de exito vs probabilidad de error\n(mensaje de 11 caracteres, {d['n_trials']} corridas por punto)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "grafica_exito.png"), dpi=150)
    plt.close(fig)

    # ---- Grafica 3: tasa de falla silenciosa ----
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(tasas, d["resultados_silencioso"]["1|Medio (11 car.)"], marker="o", color="crimson", label="Hamming SEC")
    ax.plot(tasas, d["resultados_silencioso"]["2|Medio (11 car.)"], marker="s", color="seagreen", label="CRC-32")
    ax.set_xlabel("Probabilidad de error por bit")
    ax.set_ylabel("Tasa de falla silenciosa")
    ax.set_title(f"Entregas INCORRECTAS sin aviso de error\n(mensaje de 11 caracteres, {d['n_trials']} corridas por punto)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "grafica_silenciosa.png"), dpi=150)
    plt.close(fig)

    print("Graficas guardadas:")
    print(f"  {OUT_DIR}/grafica_overhead.png")
    print(f"  {OUT_DIR}/grafica_exito.png")
    print(f"  {OUT_DIR}/grafica_silenciosa.png")


def generar_resumen_texto(d):
    """Genera tablas en texto plano listas para copiar al reporte."""
    lines = []
    lines.append("=== TASA DE ENTREGA CORRECTA (%) ===\n")
    for algo, nombre in [("1", "Hamming SEC"), ("2", "CRC-32")]:
        lines.append(f"\n{nombre}:")
        header = "Tasa error".ljust(14) + "".join(l.ljust(20) for l in MENSAJES.keys())
        lines.append(header)
        for i, t in enumerate(d["tasas"]):
            fila = (f"1/{round(1/t)}" if t else "0").ljust(14)
            for label in MENSAJES.keys():
                val = d["resultados_exito"][f"{algo}|{label}"][i]
                fila += f"{val*100:.0f}%".ljust(20)
            lines.append(fila)

    lines.append("\n\n=== TASA DE FALLA SILENCIOSA (entrega incorrecta sin avisar) (%) ===\n")
    for algo, nombre in [("1", "Hamming SEC"), ("2", "CRC-32")]:
        lines.append(f"\n{nombre}:")
        header = "Tasa error".ljust(14) + "".join(l.ljust(20) for l in MENSAJES.keys())
        lines.append(header)
        for i, t in enumerate(d["tasas"]):
            fila = (f"1/{round(1/t)}" if t else "0").ljust(14)
            for label in MENSAJES.keys():
                val = d["resultados_silencioso"][f"{algo}|{label}"][i]
                fila += f"{val*100:.0f}%".ljust(20)
            lines.append(fila)

    lines.append("\n\n=== OVERHEAD (bits de redundancia) ===\n")
    lines.append("Mensaje".ljust(20) + "Bits datos".ljust(14) + "Hamming (+bits)".ljust(20) + "CRC-32 (+bits)")
    for o in d["overhead"]:
        lines.append(
            o["label"].ljust(20)
            + str(o["m"]).ljust(14)
            + f"+{o['hamming_redundancia']}".ljust(20)
            + f"+{o['crc_redundancia']}"
        )

    txt_path = os.path.join(OUT_DIR, "resumen.txt")
    with open(txt_path, "w") as f:
        f.write("\n".join(lines))
    print(f"\nResumen en texto guardado en {txt_path}")


if __name__ == "__main__":
    datos = correr_simulacion()
    generar_graficas(datos)
    generar_resumen_texto(datos)
    print("\nListo. Revisa la carpeta 'resultados_pruebas/'.")
