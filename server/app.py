#!/usr/bin/env python3
"""
Falcon ASGI application for the Books REST API.
Connects to MongoDB and exposes REST endpoints.
"""
import logging
import os

import falcon.asgi as falcon
from pymongo import MongoClient

from resources import HealthResource, SetupResource, SeedResource, BooksResource, BookResource

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger(__name__)

MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
MONGODB_PORT = int(os.getenv('MONGODB_PORT', '27017'))
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'bookstore')


class LoggingMiddleware:
    async def process_request(self, req, resp):
        log.info(f"Request: {req.method} {req.uri}")

    async def process_response(self, req, resp, resource, req_succeeded):
        log.info(f"Response: {resp.status} for {req.method} {req.uri}")


client = MongoClient(f'mongodb://{MONGODB_HOST}:{MONGODB_PORT}/')
db = client[MONGODB_DATABASE]

app = falcon.App(middleware=[LoggingMiddleware()])

app.add_route('/health',        HealthResource(db))
app.add_route('/setup',         SetupResource(db))
app.add_route('/seed',          SeedResource(db))
app.add_route('/books',         BooksResource(db))
app.add_route('/books/{book_id}', BookResource(db))

log.info("Routes:")
log.info("  GET    /health")
log.info("  POST   /setup              — create indexes (run once)")
log.info("  POST   /seed               — load demo books from CSV")
log.info("  GET    /books              — list books (rating, language, search filters)")
log.info("  POST   /books              — add a book")
log.info("  GET    /books/{id}         — get a book")
log.info("  PUT    /books/{id}         — update a book")
log.info("  DELETE /books/{id}         — delete a book")
