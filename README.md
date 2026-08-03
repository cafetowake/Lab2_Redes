# Universidad del Valle de Guatemala
## CC3067 Redes
### Laboratorio2 

# Esquemas de Detección y Corrección de Errores
- Corrección: Código de Hamming (SEC — Single Error Correction)
- Detección: CRC-32 (división polinomial bit a bit, generador 0x04C11DB7)
- Emisor: Python 
- Receptor: C++

### Autores:
- Paula De León
- Angie Vela

# Aclaración
No queda claro si debiamos resolver la guía resumida o la extendida. Decidimos
hacer ambas cosas. En la carpeta "scripts resuelven guia resumida" está la primera
versión de los scripts que resuelven este laboratorio. Los scripts en la raiz
del proyecto tienen una arquitectura más compleja, como solicita la guia extendida.

## Arquitectura de capas implementada

| Capa | Servicios | Dónde |
|---|---|---|
| Aplicación | `solicitar_mensaje`, `mostrar_mensaje` | ambos |
| Presentación | `codificar_mensaje` (texto → ASCII binario) / `decodificar_mensaje` (binario → texto) | emisor / receptor |
| Enlace | `calcular_integridad` / `verificar_integridad` + `corregir_mensaje` | emisor / receptor |
| Ruido | `aplicar_ruido` (flip de bits por probabilidad, ej. 1/100) | emisor |
| Transmisión | `enviar_informacion` / `recibir_informacion` (sockets TCP) | emisor / receptor |

El receptor es el servidor: se queda escuchando en un puerto hasta que el
emisor (cliente) se conecta y envía la trama ya afectada por el ruido.

## Cómo compilar y ejecutar

```bash
# 1. Compilar el receptor (una sola vez)
g++ -std=c++17 -O2 -o receptor receptor.cpp

# 2. Correr el receptor PRIMERO (se queda escuchando)
./receptor
# Puerto para escuchar [5000]: <enter para usar 5000>

# 3. En otra terminal, correr el emisor
python3 emisor.py
```

## Flujo de uso del emisor

El emisor pide, en orden:
1. Mensaje en texto libre (no binario — la capa de presentación lo
   convierte a ASCII binario automáticamente).
2. Algoritmo: `1` = Hamming (corrección), `2` = CRC-32 (detección).
3. Tasa de error del canal, como fracción (`1/100`) o decimal (`0.01`).
   Usa `0` para simular un canal sin ruido.
4. Host y puerto del receptor (por defecto `127.0.0.1:5000`, útil si
   ambos programas corren en la misma máquina).

El emisor imprime en pantalla: el texto original, los bits ASCII, la trama
antes y después del ruido (y cuántos bits se voltearon), y finalmente la
envía por el socket.

## Formato en el cable (protocolo interno)

Se envía una sola línea de texto: `"<algoritmo>|<trama_bits>\n"`.
El dígito de algoritmo (`1` o `2`) se trata como metadata de protocolo y
no pasa por `aplicar_ruido`; solo la trama de datos (incluyendo sus
bits de paridad/CRC) está expuesta al ruido simulado.

- Hamming: la trama = codeword completo. El receptor deduce `r` (bits
  de paridad) automáticamente a partir de la longitud total.
- CRC-32: la trama = `[bits ASCII del mensaje] + [32 bits de CRC]`.

## Plan de pruebas sugerido para el reporte

Repite con 3 mensajes de distinta longitud (ej. `"Hi"`, `"Hola Mundo"`,
un párrafo más largo) y ambos algoritmos, variando la tasa de error:

1. Cero errores: tasa `0` → debe entregar el texto exacto.
2. Un error probable: tasa baja (ej. `1/200`) hasta que ocurra
   exactamente 1 bit volteado → Hamming corrige y muestra el texto
   correcto con aviso de "error corregido en posición X"; CRC-32
   detecta y descarta.
3. Dos o más errores: tasa más alta (ej. `1/20` o mayor) → observa
   si el algoritmo lo maneja o falla silenciosamente. Con Hamming
   SEC, 2+ errores casi siempre lo "engañan": corrige una posición
   equivocada y entrega texto corrupto sin avisar — debilidad
   estructural conocida (solo garantiza corrección de 1 error). Con
   CRC-32, casi cualquier combinación de bits volteados cambia el
   residuo y se detecta; solo se "engaña" si el patrón de error exacto
   es múltiplo del polinomio generador (posible en teoría, muy
   improbable con errores aleatorios).

Toma captura de pantalla de ambas terminales (emisor y receptor) para
cada corrida.

## Nota sobre el generador CRC-32 usado

Se implementa por división polinomial directa (agregar 32 ceros al
mensaje, dividir mod-2 por el generador de 33 bits, el residuo es el CRC),
usando el polinomio estándar IEEE 802.3 (`0x04C11DB7`). Esto difiere
ligeramente del CRC-32 "de Ethernet/zlib", que además reflexiona los bits
de entrada/salida y aplica XOR inicial/final de `0xFFFFFFFF` — vale la
pena mencionar esto como nota de diseño en la sección de descripción del
reporte.
