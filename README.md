# ITESO BDNR - MongoDB Sample (Esqueleto)

Plantilla y arquitectura base cualquier modelo de datos en MongoDB, utilizando una arquitectura cliente-servidor con una API REST en Python (Falcon ASGI) y un cliente de consola interactivo.

---

## Arquitectura

```
┌────────────────────────┐       ┌────────────────────────┐       ┌────────────────────────┐
│     Cliente Python     │ HTTP  │        Servidor        │ PyMongo│        MongoDB         │
│    (client/menu.py)    │ ────► │      (API REST /       │ ────►  │     (Docker / Nodo)    │
│                        │       │      Falcon ASGI)      │       │                        │
└────────────────────────┘       └────────────────────────┘       └────────────────────────┘
         client/                          server/                         puerto 27017
```

---

## Estructura del Proyecto

```
iteso-bdnr-mongodb-sample/
├── client/
│   └── menu.py         # Menú interactivo de consola para realizar peticiones REST
├── server/
│   ├── app.py          # Configuración de la aplicación Falcon ASGI y rutas
│   ├── resources.py    # Controladores de endpoints REST (Health, Setup, Data, Item)
│   └── model.py        # Conexión a MongoDB, creación de índices y operaciones CRUD
├── requirements.txt    # Dependencias del proyecto (servidor y cliente)
└── README.md
```

---

## Cómo implementar cualquier modelo de datos

MongoDB es una base de datos orientada a documentos sin esquema rígido (*schema-less*), lo que permite almacenar documentos flexibles directamente. Esta plantilla permite adaptar el proyecto a cualquier caso de uso (por ejemplo: catálogo de productos, usuarios, dispositivos IoT, métricas, etc.) en tres pasos:

1. **Definir tus índices y colección en [server/model.py](server/model.py)**:
   - Modifica `DEFAULT_COLLECTION` con el nombre de tu colección principal.
   - Configura tus índices en `ALL_INDEXES = [(colección, campos, opciones)]` para optimizar las consultas que requiera tu aplicación.
   - Implementa o personaliza tus funciones de consulta e inserción según la lógica de tu negocio.
2. **Personalizar endpoints en [server/resources.py](server/resources.py) y [server/app.py](server/app.py)**:
   - Modifica `DataResource` o crea nuevos recursos Falcon según las entidades o filtros de tu modelo.
   - Registra o actualiza las rutas con `app.add_route('/ruta', recurso)`.
3. **Interactuar desde el cliente en [client/menu.py](client/menu.py)**:
   - Agrega o ajusta las opciones del menú para solicitar los campos requeridos y llamar a los nuevos endpoints de tu API.

---

## Puesta en Marcha

Se recomienda trabajar con **2 terminales**: una para mantener en ejecución el servidor ASGI y otra para utilizar el menú interactivo.

### 1. Iniciar MongoDB con Docker

```bash
docker run --name mongodb -p 27017:27017 -d mongo

# Verificar que el contenedor esté corriendo y responda al ping:
docker exec -it mongodb mongosh --eval "db.runCommand({ping:1})"
```

### 2. Entorno Virtual e Instalación de Dependencias

```bash
# Crear entorno virtual (si no existe)
python3 -m venv .venv

# Activar entorno virtual
source .venv/bin/activate       # En Linux / macOS
# .venv\Scripts\activate        # En Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Iniciar el Servidor de la API REST

En la primera terminal:

```bash
cd server
uvicorn app:app --reload --port 8001
```

El servidor quedará disponible en `http://localhost:8001`.

### 4. Ejecutar el Cliente Interactivo

En la segunda terminal (con el entorno virtual activado):

```bash
cd client
python menu.py
```

O directamente desde la raíz del repositorio:
```bash
python client/menu.py
```

---

## Opciones del Cliente Interactivo (`menu.py`)

El cliente por consola ofrece un menú en bucle que permite probar de inmediato las operaciones básicas:

| Opción | Acción | Petición REST |
|--------|--------|---------------|
| **1** | Verificar estado del servidor | `GET /health` |
| **2** | Inicializar base de datos / índices | `POST /setup` (crea índices configurados) |
| **3** | Consultar registros | `GET /data` |
| **4** | Insertar un nuevo registro | `POST /data` (solicita los campos e inserta el documento) |
| **5** | Consultar un registro por ID | `GET /data/{id}` |
| **6** | Eliminar un registro por ID | `DELETE /data/{id}` |
| **0** | Salir | Cierra el programa |

---

## Endpoints REST Disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET`  | `/health` | Verifica la salud del servicio y el estado de la conexión a MongoDB |
| `POST` | `/setup`  | Crea los índices configurados en `ALL_INDEXES` |
| `GET`  | `/data`   | Obtiene la lista de documentos almacenados (parámetro opcional: `?limit=N`) |
| `POST` | `/data`   | Inserta un nuevo documento directamente a partir de un cuerpo JSON |
| `GET`  | `/data/{id}` | Consulta un documento específico por su `_id` |
| `DELETE` | `/data/{id}` | Elimina un documento específico por su `_id` |

### Ejemplos con `curl`

```bash
# 1. Comprobar salud del servicio
curl http://localhost:8001/health

# 2. Inicializar índices
curl -X POST http://localhost:8001/setup

# 3. Consultar documentos existentes
curl http://localhost:8001/data

# 4. Insertar un documento
curl -X POST http://localhost:8001/data \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Elemento A", "categoria": "General", "valor": "99.9"}'

# 5. Consultar un documento por ID
curl http://localhost:8001/data/<id>

# 6. Eliminar un documento por ID
curl -X DELETE http://localhost:8001/data/<id>
```

---

## Variables de Entorno

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `API_URL` | `http://localhost:8001` | URL base de la API utilizada por el cliente |
| `MONGODB_HOST` | `localhost` | Host o dirección IP de la instancia de MongoDB |
| `MONGODB_PORT` | `27017` | Puerto de conexión a MongoDB |
| `MONGODB_DATABASE` | `app_db` | Nombre de la base de datos a utilizar |

---

## Solución de Problemas

- **"No se pudo conectar con el servidor"**: Asegúrate de haber iniciado el servidor con `uvicorn app:app --reload --port 8001` dentro de la carpeta `server/`.
- **"Fallo al conectar con MongoDB"**: Verifica que el contenedor de Docker esté iniciado ejecutando `docker ps`. Si no está activo, inícialo con `docker start mongodb`.
- **"ModuleNotFoundError: No module named 'falcon'"**: Verifica que tu terminal tenga activo el entorno virtual (`source .venv/bin/activate`).
