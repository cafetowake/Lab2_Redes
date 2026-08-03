# Universidad del Valle de Guatemala
## CC3067 Redes
### Laboratorio 2

# Esquemas de Detección y Corrección de Errores (guía resumida)

- Corrección: Código de Hamming (SEC o Single Error Correction)
- Detección: CRC-32 (división polinomial bit a bit, generador 0x04C11DB7)
- Emisor: Python
- Receptor: C++
  
### Autores:
- Paula De León
- Angie Vela

## Diferencia con la versión raíz

Esta carpeta resuelve la guía resumida del laboratorio que es sin sockets ni capas de presentación ni de ruido. El usuario ingresa el mensaje ya en binario directamente, el emisor imprime la trama, y esa trama se copia manualmente a la consola del receptor. El plan de pruebas, el formato de trama y la nota sobre el generador CRC-32 son los mismos que en el README de la versión completa.

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
 
1. Corre `emisor.py`, elige algoritmo entre 1 para Hamming y 2 para CRC-32, ingresa el mensaje binario.
2. Copia la "Trama" que imprime el emisor.
3. Corre `./receptor`, elige el mismo algoritmo, pega la trama intacta o con bits modificados.
4. El receptor indica si no hubo errores o si hubo un error detectado o si hubo un error corregido.