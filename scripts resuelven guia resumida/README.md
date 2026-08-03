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

## Cómo compilar y ejecutar

```bash
# Receptor (compilar una sola vez)
g++ -std=c++17 -O2 -o receptor receptor.cpp

# Ejecutar Emisor
python3 emisor.py

# Ejecutar Receptor
./receptor
```

## Flujo de uso

1. Corre `emisor.py`, elige algoritmo (1=Hamming, 2=CRC-32), ingresa el mensaje binario.
2. Copia la "Trama" que imprime el emisor.
3. Corre `./receptor`, elige el mismo algoritmo, pega la trama (intacta o con bits modificados).
4. El receptor indica: sin errores / error detectado / error corregido.

## Formato de trama (acordado entre Emisor–Receptor)

- Hamming: la trama = codeword completo. El receptor deduce `r` (bits de paridad)
  automáticamente a partir de la longitud total `n` (mínimo `r` tal que `2^r >= n+1`),
  así que no requiere metadata adicional.
- CRC-32: la trama = `[bits de datos] + [32 bits de CRC]`. El receptor siempre
  interpreta los últimos 32 bits como el CRC.

## Plan de pruebas sugerido para el reporte (3 mensajes × 2 algoritmos × 3 escenarios)

Usa mensajes de longitud distinta, por ejemplo:
- Corto: `1101` (4 bits)
- Medio: `110101011` (9 bits)
- Largo: `1101011010110110101101011` (25 bits)

Para cada mensaje y cada algoritmo:
1. Cero errores: pega la trama tal cual → debe validar OK.
2. Un error: invierte manualmente 1 bit de la trama → Hamming debe corregir;
   CRC-32 debe detectar y descartar.
3. Dos o más errores: invierte 2+ bits → observa el resultado. Este es el
   escenario clave para la pregunta de "¿se puede engañar al algoritmo?":
   - Con Hamming SEC, 2 errores casi siempre lo "engañan": el algoritmo
     detecta un síndrome válido y "corrige" en la posición equivocada,
     produciendo datos incorrectos sin avisar que algo salió mal. Esto es una
     debilidad estructural conocida de Hamming SEC (solo garantiza corrección
     de 1 error; con 2 errores el síndrome apunta a una posición distinta).
   - Con CRC-32, casi cualquier combinación de bits volteados cambia el
     residuo y se detecta. Solo se "engaña" si el patrón de error exacto es
     múltiplo del polinomio generador (matemáticamente posible, pero muy
     improbable con errores aleatorios) — es una forma directa de responder
     la pregunta de debilidad estructural: la detección de CRC no es 100%
     infalible en teoría, solo con probabilidad extremadamente alta.

Toma captura de pantalla de cada corrida (emisor + receptor) para el reporte.

## Nota sobre el generador CRC-32 usado

Se implementa por división polinomial directa(ag regar 32 ceros al mensaje,
dividir mod-2 por el generador de 33 bits, el residuo es el CRC), usando el
mismo polinomio estándar IEEE 802.3 (`0x04C11DB7`). Esto difiere ligeramente
del CRC-32 "de Ethernet/zlib" que además reflexiona los bits de entrada/salida
y aplica XOR inicial/final de `0xFFFFFFFF` — vale la pena mencionar esto como
nota de diseño en la sección de descripción del reporte.
