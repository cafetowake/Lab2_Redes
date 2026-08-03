// ============================================================
// RECEPTOR 
//
// Arquitectura de capas:
//
//   TRANSMISION  -> recibir_informacion (sockets TCP, escucha en un puerto)
//   ENLACE       -> verificar_integridad, corregir_mensaje
//   PRESENTACION -> decodificar_mensaje
//   APLICACION   -> mostrar_mensaje
//
// El receptor actua como servidor de socket. Se queda escuchando en
// el puerto elegido hasta que el emisor se conecta y envia la trama.
// ============================================================

#include <bits/stdc++.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
using namespace std;


// ALGORITMOS DE INTEGRIDAD (usados por la capa de ENLACE)

// Las posiciones de bits de paridad en Hamming son siempre potencias
// de 2 (1, 2, 4, ...). Sirve para separar datos de paridad al
// reconstruir el mensaje.
bool esPotenciaDeDos(int n) {
    return n > 0 && (n & (n - 1)) == 0;
}

struct HammingResult {
    int syndrome;          // posicion del error (0 si no hay error)
    string tramaCorregida; // codeword completo, con el bit corregido
    string datos;          // solo los bits de datos (sin paridad)
};

// Decodifica un codeword de Hamming; si detecta un error de 1 bit lo corrige.
//
// Paso 1: deducir automaticamente r (bits de paridad) a partir de la
//         longitud total n del codeword recibido.
// Paso 2: recalcular cada bit de paridad y comparar contra el recibido;
//         el "sindrome" (suma de las paridades que no cuadran) apunta
//         directamente a la posicion del bit erroneo (si hubo 1 solo error).
// Paso 3: invertir el bit en esa posicion y separar los datos (posiciones
//         que no son potencia de 2) del resto.
HammingResult hammingDecode(const string& codeword) {
    int n = (int)codeword.size();
    vector<int> code(n + 1, 0);
    for (int i = 1; i <= n; ++i) code[i] = codeword[i - 1] - '0';

    int r = 0;
    while ((1 << r) < (n + 1)) r++;

    int syndrome = 0;
    for (int i = 0; i < r; ++i) {
        int p = 1 << i;
        int parity = 0;
        for (int pos = 1; pos <= n; ++pos) {
            if (pos & p) parity ^= code[pos];
        }
        if (parity) syndrome += p;
    }

    vector<int> corregido = code;
    if (syndrome != 0 && syndrome <= n) {
        corregido[syndrome] ^= 1;
    }

    string tramaCorregida, datos;
    for (int pos = 1; pos <= n; ++pos) {
        tramaCorregida += char('0' + corregido[pos]);
        if (!esPotenciaDeDos(pos)) datos += char('0' + corregido[pos]);
    }

    return {syndrome, tramaCorregida, datos};
}

// Generador estandar CRC-32 (IEEE 802.3, polinomio 0x04C11DB7) como
// string de 33 bits (el "1" implicito + los 32 bits del polinomio).
string crc32Generador() {
    unsigned long poly = 0x04C11DB7UL;
    string bin;
    for (int i = 31; i >= 0; --i) bin += ((poly >> i) & 1) ? '1' : '0';
    return "1" + bin;
}

// Division polinomial modulo-2 (XOR). Debe ser identica a la del
// emisor: si la trama llego intacta, el residuo da todo ceros.
string crc32Remainder(const string& bits) {
    string data = bits;
    string gen = crc32Generador();
    int n = (int)gen.size();
    for (int i = 0; i + n <= (int)data.size(); ++i) {
        if (data[i] == '1') {
            for (int j = 0; j < n; ++j) {
                data[i + j] = (data[i + j] == gen[j]) ? '0' : '1';
            }
        }
    }
    return data.substr(data.size() - (n - 1));
}

bool esTodoCeros(const string& s) {
    for (char c : s) if (c != '0') return false;
    return true;
}


// CAPA DE PRESENTACION


// Convierte un string de bits ASCII (multiplo de 8) de vuelta a texto.
// Si 'bitsDatos' esta corrupto/incompleto, simplemente se detiene en
// el ultimo bloque completo de 8 bits disponible.
string decodificarMensaje(const string& bitsDatos) {
    string texto;
    for (size_t i = 0; i + 8 <= bitsDatos.size(); i += 8) {
        int valor = stoi(bitsDatos.substr(i, 8), nullptr, 2);
        texto += char(valor);
    }
    return texto;
}


// CAPA DE ENLACE
struct ResultadoEnlace {
    bool huboError;     // true si no se pudo entregar el mensaje
    bool fueCorregido;  // true si hubo 1 error y se corrigio (solo Hamming)
    int posicionError;  // posicion corregida (solo Hamming)
    string bitsDatos;   // datos recuperados (validos solo si !huboError)
};

// verificar_integridad + corregir_mensaje: recalcula la integridad del
// lado del receptor (Hamming o CRC-32, segun 'algoritmo') y decide si
// la trama esta limpia, se pudo corregir, o debe descartarse.
ResultadoEnlace verificarYCorregir(const string& trama, const string& algoritmo) {
    ResultadoEnlace res{false, false, 0, ""};

    if (algoritmo == "1") {
        HammingResult r = hammingDecode(trama);
        res.posicionError = r.syndrome;
        if (r.syndrome == 0) {
            res.bitsDatos = r.datos;
        } else if (r.syndrome <= (int)trama.size()) {
            // 1 error detectado y corregido (SEC solo garantiza 1 bit;
            // con 2+ errores esto puede "corregir" la posicion equivocada
            // sin que el receptor lo note -- debilidad estructural de Hamming SEC).
            res.bitsDatos = r.datos;
            res.fueCorregido = true;
        } else {
            // Sindrome fuera de rango: se sabe que hay error pero no se
            // puede ubicar con certeza.
            res.huboError = true;
        }
    } else {
        string residuo = crc32Remainder(trama);
        if (esTodoCeros(residuo)) {
            res.bitsDatos = trama.substr(0, trama.size() - 32);
        } else {
            // CRC-32 solo detecta, no corrige: se descarta la trama.
            res.huboError = true;
        }
    }

    return res;
}


// CAPA DE TRANSMISION (sockets TCP)

// Abre un socket TCP, hace bind+listen en 'puerto' y se queda
// "escuchando" (accept) hasta que el emisor se conecte y mande datos.
// Devuelve la linea cruda recibida: "<algoritmo>|<trama>\n"
string recibirInformacion(int puerto) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        cerr << "Error creando el socket.\n";
        exit(1);
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(puerto);

    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        cerr << "Error haciendo bind en el puerto " << puerto << ".\n";
        exit(1);
    }

    listen(server_fd, 1);
    cout << "Escuchando en el puerto " << puerto << "... (esperando al emisor)\n";

    int client_fd = accept(server_fd, nullptr, nullptr);
    if (client_fd < 0) {
        cerr << "Error aceptando la conexion.\n";
        exit(1);
    }

    string datos;
    char buffer[4096];
    ssize_t n;
    // Se lee hasta encontrar el salto de linea que marca el fin del mensaje.
    while (datos.find('\n') == string::npos &&
           (n = read(client_fd, buffer, sizeof(buffer))) > 0) {
        datos.append(buffer, n);
    }

    close(client_fd);
    close(server_fd);
    return datos;
}


// CAPA DE APLICACION
int solicitarPuerto() {
    cout << "RECEPTOR\n";
    cout << "Puerto para escuchar [5000]: ";
    string linea;
    getline(cin, linea);
    if (linea.empty()) return 5000;
    return stoi(linea);
}

void mostrarMensaje(const ResultadoEnlace& r, const string& algoritmo) {
    string nombreAlgo = (algoritmo == "1") ? "Hamming SEC" : "CRC-32";
    cout << "\n--- Resultado en el receptor ---\n";
    cout << "Algoritmo: " << nombreAlgo << "\n";

    if (r.huboError) {
        cout << "Error detectado. No fue posible entregar el mensaje.\n";
        cout << "Trama descartada.\n";
        return;
    }

    if (r.fueCorregido) {
        cout << "Se detecto y corrigio un error en la posicion "
             << r.posicionError << " antes de decodificar.\n";
    } else {
        cout << "Sin errores.\n";
    }

    // PRESENTACION: bits -> texto
    string texto = decodificarMensaje(r.bitsDatos);
    cout << "Mensaje recibido: " << texto << "\n";
    cout << "---------------------------------\n";
}

int main() {
    int puerto = solicitarPuerto();

    // TRANSMISION: recibir la linea cruda del emisor
    string linea = recibirInformacion(puerto);

    // separar "<algoritmo>|<trama>"
    size_t barPos = linea.find('|');
    if (barPos == string::npos) {
        cerr << "Formato de mensaje invalido.\n";
        return 1;
    }
    string algoritmo = linea.substr(0, barPos);
    string trama = linea.substr(barPos + 1);
    while (!trama.empty() && (trama.back() == '\n' || trama.back() == '\r')) {
        trama.pop_back();
    }

    cout << "Trama recibida (" << trama.size() << " bits): " << trama << "\n";

    // ENLACE: verificar integridad y corregir si aplica
    ResultadoEnlace resultado = verificarYCorregir(trama, algoritmo);

    // APLICACION: mostrar el resultado final al usuario
    mostrarMensaje(resultado, algoritmo);

    return 0;
}
