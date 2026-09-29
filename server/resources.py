#!/usr/bin/env python3
"""
Clases de recursos Falcon para la API REST con MongoDB (Esqueleto Genérico).
Expone endpoints estándar para comprobación de salud, inicialización de índices y CRUD base.
"""
import logging
import falcon
import model

log = logging.getLogger(__name__)


class HealthResource:
    """Endpoint para verificar el estado de salud de la API y de MongoDB."""

    def __init__(self, conn):
        self.conn = conn

    async def on_get(self, req, resp):
        """GET /health"""
        if self.conn.is_connected():
            resp.media = {'status': 'healthy', 'database': 'connected'}
        else:
            resp.media = {'status': 'unhealthy', 'database': 'disconnected'}
            resp.status = falcon.HTTP_503


class SetupResource:
    """Endpoint administrativo para crear colecciones e índices en MongoDB."""

    def __init__(self, conn):
        self.conn = conn

    async def on_post(self, req, resp):
        """POST /setup"""
        try:
            indexes = model.create_indexes(self.conn.db)
            resp.media = {
                'status': 'success',
                'message': f'Base de datos {self.conn.database_name} e índices creados exitosamente',
                'indexes': indexes,
                'note': 'MongoDB no requiere esquema rígido; los índices definen el rendimiento de consultas.',
            }
            resp.status = falcon.HTTP_201
        except Exception as e:
            log.exception("Fallo al ejecutar setup")
            resp.media = {'status': 'error', 'message': str(e)}
            resp.status = falcon.HTTP_500


class DataResource:
    """
    Recurso plantilla para operaciones del modelo de datos en MongoDB.
    Personalizable según los requerimientos de la aplicación.
    """

    def __init__(self, conn):
        self.conn = conn

    async def on_get(self, req, resp):
        """GET /data — Consulta registros con límite opcional"""
        try:
            limit = req.get_param_as_int('limit') or 100
            items = model.get_all_records(self.conn.db, limit=limit)
            resp.media = {'count': len(items), 'data': items}
        except Exception as e:
            log.exception("Error al consultar registros")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500

    async def on_post(self, req, resp):
        """POST /data — Inserta un documento directamente desde el JSON recibido"""
        try:
            body = await req.get_media() or {}
            if not body:
                resp.media = {'error': "Cuerpo JSON requerido"}
                resp.status = falcon.HTTP_400
                return

            resultado = model.insert_record(self.conn.db, body)
            resp.media = {'status': 'created', 'item': resultado}
            resp.status = falcon.HTTP_201
        except Exception as e:
            log.exception("Error al insertar registro")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500


class ItemResource:
    """
    Recurso para consultar o eliminar documentos específicos por ID.
    """

    def __init__(self, conn):
        self.conn = conn

    async def on_get(self, req, resp, item_id):
        """GET /data/{item_id} — Consulta un documento específico"""
        try:
            item = model.get_record_by_id(self.conn.db, item_id)
            if not item:
                resp.media = {'error': f'Registro con ID {item_id} no encontrado'}
                resp.status = falcon.HTTP_404
                return
            resp.media = {'status': 'success', 'item': item}
        except Exception as e:
            log.exception(f"Error al consultar registro {item_id}")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500

    async def on_delete(self, req, resp, item_id):
        """DELETE /data/{item_id} — Elimina un documento específico"""
        try:
            deleted = model.delete_record_by_id(self.conn.db, item_id)
            if not deleted:
                resp.media = {'error': f'Registro con ID {item_id} no encontrado'}
                resp.status = falcon.HTTP_404
                return
            resp.media = {'status': 'success', 'message': f'Registro {item_id} eliminado exitosamente'}
        except Exception as e:
            log.exception(f"Error al eliminar registro {item_id}")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500
