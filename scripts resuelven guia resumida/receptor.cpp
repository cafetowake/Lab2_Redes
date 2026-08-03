// Receptor - Lab 2
// Hamming (correccion) y CRC-32 (deteccion)

#include <bits/stdc++.h>
using namespace std;

bool esPotenciaDeDos(int n) {
    return n > 0 && (n & (n - 1)) == 0;
}

struct HammingResult {
    int syndrome;
    string tramaCorregida;
    string datos;
};

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

string crc32Generador() {
    unsigned long poly = 0x04C11DB7UL;
    string bin;
    for (int i = 31; i >= 0; --i) bin += ((poly >> i) & 1) ? '1' : '0';
    return "1" + bin;
}

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

string leerBinario(const string& prompt) {
    string s;
    while (true) {
        cout << prompt;
        cin >> s;
        bool valido = !s.empty();
        for (char c : s) if (c != '0' && c != '1') { valido = false; break; }
        if (valido) return s;
        cout << "Entrada invalida, solo 0s y 1s.\n";
    }
}

bool esTodoCeros(const string& s) {
    for (char c : s) if (c != '0') return false;
    return true;
}

int main() {
    cout << "RECEPTOR\n";
    cout << "1) Hamming (correccion)\n";
    cout << "2) CRC-32 (deteccion)\n";

    cout << "Algoritmo (1/2): ";
    string opcion;
    cin >> opcion;

    string trama = leerBinario("Trama recibida: ");

    if (opcion == "1") {
        HammingResult r = hammingDecode(trama);
        if (r.syndrome == 0) {
            cout << "Sin errores.\n";
            cout << "Datos: " << r.datos << "\n";
        } else if (r.syndrome <= (int)trama.size()) {
            cout << "Error corregido en posicion " << r.syndrome << "\n";
            cout << "Trama corregida: " << r.tramaCorregida << "\n";
            cout << "Datos: " << r.datos << "\n";
        } else {
            cout << "Error detectado, fuera de rango. Trama descartada.\n";
        }
    } else if (opcion == "2") {
        string remainder = crc32Remainder(trama);
        cout << "Residuo CRC-32: " << remainder << "\n";
        if (esTodoCeros(remainder)) {
            cout << "Sin errores.\n";
            cout << "Datos: " << trama.substr(0, trama.size() - 32) << "\n";
        } else {
            cout << "Error detectado. Trama descartada.\n";
        }
    } else {
        cout << "Opcion invalida.\n";
        return 1;
    }

    return 0;
}
