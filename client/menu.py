#!/usr/bin/env python3
"""
Menú simple de consola en Python para realizar peticiones REST.
Permite interactuar de forma interactiva y llamar a funciones para probar la API con MongoDB.
"""
import os
import sys
import requests

API_URL = os.getenv('API_URL', 'http://localhost:8001')


def verificar_salud():
    """Realiza una petición GET para comprobar el estado de la API."""
    url = f"{API_URL}/health"
    print(f"\n[INFO] Consultando estado en: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] No se pudo conectar con el servidor: {err}")


def inicializar_bd():
    """Realiza una petición POST para inicializar la base de datos e índices."""
    url = f"{API_URL}/setup"
    print(f"\n[INFO] Solicitando setup en: {url}")
    try:
        response = requests.post(url, timeout=30)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error al realizar la petición: {err}")


def consultar_registros():
    """Realiza una petición GET para consultar registros existentes."""
    url = f"{API_URL}/data"
    print(f"\n[INFO] Consultando datos en: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error en petición REST: {err}")


def insertar_registro():
    """Realiza una petición POST para insertar un nuevo registro."""
    url = f"{API_URL}/data"
    print(f"\n[INFO] Insertar registro en: {url}")
    nombre = input("Nombre: ").strip()
    categoria = input("Categoría: ").strip()
    valor = input("Valor: ").strip()

    payload = {
        "nombre": nombre,
        "categoria": categoria,
        "valor": valor
    }
    # Enviar solo campos con valor
    payload = {k: v for k, v in payload.items() if v}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error en petición REST: {err}")


def consultar_por_id():
    """Realiza una petición GET para consultar un registro específico."""
    item_id = input("ID del registro: ").strip()
    if not item_id:
        print("[AVISO] El ID no puede estar vacío.")
        return
    url = f"{API_URL}/data/{item_id}"
    print(f"\n[INFO] Consultando registro en: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error en petición REST: {err}")


def eliminar_por_id():
    """Realiza una petición DELETE para eliminar un registro específico."""
    item_id = input("ID del registro a eliminar: ").strip()
    if not item_id:
        print("[AVISO] El ID no puede estar vacío.")
        return
    url = f"{API_URL}/data/{item_id}"
    print(f"\n[INFO] Eliminando registro en: {url}")
    try:
        response = requests.delete(url, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error en petición REST: {err}")


def consultar_por_nombre():
    """Realiza una petición GET para consultar un registro por su nombre."""
    nombre = input("Nombre del registro a buscar: ").strip()
    if not nombre:
        print("[AVISO] El nombre no puede estar vacío.")
        return
    url = f"{API_URL}/data/name/{nombre}"
    print(f"\n[INFO] Consultando registro en: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:", response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] Error en petición REST: {err}")


def mostrar_menu():
    """Despliega el menú de opciones en pantalla."""
    print("\n" + "=" * 45)
    print("        MENÚ PRINCIPAL - REST CLIENT")
    print("=" * 45)
    print(f" Servidor objetivo: {API_URL}")
    print("-" * 45)
    print(" 1. IGNORAR LAB 02 | Inicializar base de datos / índices (POST /setup)")
    print(" 2. Consultar registros (GET /data)")
    print(" 3. Insertar un nuevo registro (POST /data)")
    print(" 4. Consultar un registro por ID (GET /data/{id})")
    print(" 5. Eliminar un registro por ID (DELETE /data/{id})")
    print(" 6. Consultar un registro por nombre (GET /data/name/{name})")
    print(" 0. Salir")
    print("=" * 45)


def main():
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción [0-6]: ").strip()

        if opcion == '1':
            inicializar_bd()
        elif opcion == '2':
            consultar_registros()
        elif opcion == '3':
            insertar_registro()
        elif opcion == '4':
            consultar_por_id()
        elif opcion == '5':
            eliminar_por_id()
        elif opcion == '6':
            consultar_por_nombre()
        elif opcion == '0':
            print("\nSaliendo del programa. ¡Hasta luego!")
            sys.exit(0)
        else:
            print("\n[AVISO] Opción no válida. Por favor, ingresa un número del 0 al 6.")


if __name__ == '__main__':
    main()
