#!/usr/bin/env python3
"""
Capa de modelo de base de datos para MongoDB.

Plantilla para implementar fácilmente cualquier modelo de datos basado en documentos.
Permite insertar y consultar diccionarios directamente sin esquemas rígidos.
"""
import logging
import time
from bson.objectid import ObjectId
from pymongo import MongoClient

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conexión a MongoDB
# ---------------------------------------------------------------------------

class MongoConnection:

    def __init__(self, host='localhost', port=27017, database='app_db'):
        self.host = host
        self.port = port
        self.database_name = database
        self.client = None
        self.db = None

    def connect(self, retries=5, delay=5):
        last_exc = None
        for attempt in range(1, retries + 1):
            try:
                log.info(f"Conectando a MongoDB en {self.host}:{self.port} (intento {attempt}/{retries})")
                self.client = MongoClient(
                    host=self.host,
                    port=self.port,
                    serverSelectionTimeoutMS=5000,
                )
                # Verificar conectividad inmediata con ping
                self.client.admin.command('ping')
                self.db = self.client[self.database_name]
                return True
            except Exception as e:
                last_exc = e
                log.warning(f"Fallo de conexión ({attempt}/{retries}): {e}")
                if attempt < retries:
                    time.sleep(delay)
        raise last_exc

    def close(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass

    def is_connected(self):
        if self.client is None:
            return False
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Definición de Colecciones e Índices (Personalizable para tu modelo)
# ---------------------------------------------------------------------------

DEFAULT_COLLECTION = 'sample_items'

# # Lista de configuraciones de índices de ejemplo: (colección, campos_o_clave, opciones)
# ALL_INDEXES = [
#     (DEFAULT_COLLECTION, [('nombre', 1)], {'name': 'idx_nombre'}),
# ]


# def create_indexes(db):
#     """
#     Crea los índices configurados en ALL_INDEXES.
#     En MongoDB, los índices definen el rendimiento de las consultas y
#     representan el equivalente al DDL en bases de datos relacionales/Cassandra.
#     """
#     created = []
#     for coll_name, keys, options in ALL_INDEXES:
#         log.info(f"Creando índice en colección '{coll_name}': {keys}")
#         coll = db[coll_name]
#         idx_name = coll.create_index(keys, **options)
#         created.append({'collection': coll_name, 'index': idx_name})
#     return created


# ---------------------------------------------------------------------------
# Inserción y Operaciones Simplificadas
# ---------------------------------------------------------------------------

def insert_record(db, data: dict, collection_name=None):
    """
    Inserta un registro individual (documento) en la colección especificada o por defecto.
    Retorna el documento con su campo '_id' convertido a string.
    """
    target = collection_name or DEFAULT_COLLECTION
    coll = db[target]
    doc = dict(data)
    result = coll.insert_one(doc)
    doc['_id'] = str(result.inserted_id)
    return doc


def get_all_records(db, collection_name=None, limit=100):
    """
    Consulta registros de la colección especificada o por defecto.
    Convierte el '_id' de cada documento a string para serialización JSON.
    """
    target = collection_name or DEFAULT_COLLECTION
    coll = db[target]
    cursor = coll.find().limit(limit)
    items = []
    for doc in cursor:
        doc['_id'] = str(doc['_id'])
        items.append(doc)
    return items


def get_record_by_id(db, item_id: str, collection_name=None):
    """Consulta un registro por su ID (ObjectId o identificador exacto)."""
    target = collection_name or DEFAULT_COLLECTION
    coll = db[target]

    query = None
    if ObjectId.is_valid(item_id):
        query = {'_id': ObjectId(item_id)}
    else:
        query = {'_id': item_id}

    doc = coll.find_one(query)
    if doc:
        doc['_id'] = str(doc['_id'])
    return doc


def get_record_by_name(db, name: str, collection_name=None):
    """Consulta un registro por su nombre (campo 'nombre' o 'name')."""
    target = collection_name or DEFAULT_COLLECTION
    coll = db[target]

    query = {'$or': [{'nombre': name}, {'name': name}]}
    doc = coll.find_one(query)
    if doc:
        doc['_id'] = str(doc['_id'])
    return doc


def get_records_by_name(db, name: str, collection_name=None, limit=100):
    """Consulta todos los registros que coincidan con el nombre (campo 'nombre' o 'name')."""
    target = collection_name or DEFAULT_COLLECTION
    coll = db[target]

    query = {'$or': [{'nombre': name}, {'name': name}]}
    cursor = coll.find(query).limit(limit)
    items = []
    for doc in cursor:
        doc['_id'] = str(doc['_id'])
        items.append(doc)
    return items


def delete_record_by_id(db, item_id: str, collection_name=None):
    """Elimina un registro por su ID (ObjectId o identificador exacto)."""
    target = collection_name or DEFAULT_COLLECTION
    coll = db[target]

    query = None
    if ObjectId.is_valid(item_id):
        query = {'_id': ObjectId(item_id)}
    else:
        query = {'_id': item_id}

    result = coll.delete_one(query)
    return result.deleted_count > 0
