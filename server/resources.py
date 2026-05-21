#!/usr/bin/env python3
"""
Falcon resource classes for the Books REST API.
"""
import csv
import logging
import os

import falcon
from bson.objectid import ObjectId
from pymongo import ASCENDING, TEXT

log = logging.getLogger(__name__)

DATA_DIR = os.getenv('DATA_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))


class HealthResource:

    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        """GET /health"""
        try:
            self.db.command('ping')
            resp.media = {'status': 'healthy', 'database': 'connected'}
        except Exception as e:
            log.exception("Health check failed")
            resp.media = {'status': 'unhealthy', 'error': str(e)}
            resp.status = falcon.HTTP_503


class SetupResource:
    """
    Admin — create indexes on the books collection.

    MongoDB is schema-less: any document can be inserted without prior setup.
    Indexes are the closest equivalent to DDL — they don't change what can be
    stored, but they define which queries run efficiently.

    Without indexes, every query scans the entire collection (full collection scan).
    With indexes, MongoDB can jump directly to matching documents.
    """

    def __init__(self, db):
        self.db = db

    async def on_post(self, req, resp):
        """POST /setup — create collection indexes"""
        try:
            collection = self.db.books

            indexes_created = []

            # Index on average_rating — supports: GET /books?rating=4.5
            collection.create_index([('average_rating', ASCENDING)], name='idx_rating')
            indexes_created.append({
                'index': 'idx_rating',
                'field': 'average_rating',
                'type': 'ascending',
                'supports': 'GET /books?rating=N  (filter by minimum rating)',
            })

            # Index on language_code — supports: GET /books?language=eng
            collection.create_index([('language_code', ASCENDING)], name='idx_language')
            indexes_created.append({
                'index': 'idx_language',
                'field': 'language_code',
                'type': 'ascending',
                'supports': 'GET /books?language=eng  (filter by language)',
            })

            # Text index on title + authors — supports full-text search
            collection.create_index(
                [('title', TEXT), ('authors', TEXT)],
                name='idx_text_search'
            )
            indexes_created.append({
                'index': 'idx_text_search',
                'fields': ['title', 'authors'],
                'type': 'text',
                'supports': 'GET /books?search=...  (full-text search)',
            })

            resp.media = {
                'status': 'success',
                'message': 'Indexes created on books collection',
                'indexes': indexes_created,
                'note': 'MongoDB is schema-less — indexes define query performance, not structure',
            }
            resp.status = falcon.HTTP_201
            log.info(f"Setup: {len(indexes_created)} indexes created")

        except Exception as e:
            log.exception("Setup failed")
            resp.media = {'status': 'error', 'message': str(e)}
            resp.status = falcon.HTTP_500


class SeedResource:
    """
    Admin — load books from CSV into the database via the real business endpoint.

    Reads books.csv and inserts each book through the same validation and insert
    logic used by POST /books — not a raw bulk insert bypassing the application.
    """

    def __init__(self, db):
        self.db = db

    async def on_post(self, req, resp):
        """POST /seed  body: { "limit": 100 }"""
        try:
            body = await req.get_media() or {}
            limit = int(body.get('limit', 100))

            csv_path = os.path.join(DATA_DIR, 'books.csv')
            inserted = 0
            skipped = 0

            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if inserted >= limit:
                        break
                    try:
                        book = _parse_book_row(row)
                        self.db.books.insert_one(book)
                        inserted += 1
                    except Exception as e:
                        log.warning(f"Skipping row: {e}")
                        skipped += 1

            resp.media = {
                'status': 'success',
                'inserted': inserted,
                'skipped': skipped,
            }
            resp.status = falcon.HTTP_201
            log.info(f"Seed: {inserted} books inserted, {skipped} skipped")

        except FileNotFoundError:
            resp.media = {'error': f'books.csv not found in {DATA_DIR}'}
            resp.status = falcon.HTTP_500
        except Exception as e:
            log.exception("Seed failed")
            resp.media = {'status': 'error', 'message': str(e)}
            resp.status = falcon.HTTP_500


class BooksResource:

    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        """
        GET /books — list books with optional filters.

        Query params: rating (min), language, search (full-text)

        Each filter uses a different index created by POST /setup.
        """
        rating = req.get_param_as_float('rating')
        language = req.get_param('language')
        search = req.get_param('search')

        query = {}
        if rating is not None:
            query['average_rating'] = {'$gte': rating}
        if language:
            query['language_code'] = language
        if search:
            query['$text'] = {'$search': search}

        try:
            books = list(self.db.books.find(query))
            for book in books:
                book['_id'] = str(book['_id'])
            resp.media = {'books': books, 'count': len(books)}
            resp.status = falcon.HTTP_200
            log.info(f"Listed {len(books)} books (filters: rating={rating}, language={language}, search={search})")
        except Exception as e:
            log.exception("Failed to list books")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_500

    async def on_post(self, req, resp):
        """POST /books — add a new book"""
        try:
            data = await req.get_media()
            book = _validate_book(data)
            result = self.db.books.insert_one(book)
            book['_id'] = str(result.inserted_id)
            resp.media = book
            resp.status = falcon.HTTP_201
            log.info(f"Book added: {book['title']}")
        except falcon.HTTPBadRequest:
            raise
        except Exception as e:
            log.exception("Failed to add book")
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_400


class BookResource:

    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp, book_id):
        """GET /books/{id}"""
        try:
            book = self.db.books.find_one({'_id': ObjectId(book_id)})
            if not book:
                resp.media = {'error': 'Book not found'}
                resp.status = falcon.HTTP_404
                return
            book['_id'] = str(book['_id'])
            resp.media = book
        except Exception as e:
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_400

    async def on_put(self, req, resp, book_id):
        """PUT /books/{id} — update a book"""
        try:
            data = await req.get_media()
            book = _validate_book(data)
            result = self.db.books.update_one({'_id': ObjectId(book_id)}, {'$set': book})
            if not result.matched_count:
                resp.media = {'error': 'Book not found'}
                resp.status = falcon.HTTP_404
                return
            resp.media = {'status': 'success', 'message': 'Book updated'}
        except falcon.HTTPBadRequest:
            raise
        except Exception as e:
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_400

    async def on_delete(self, req, resp, book_id):
        """DELETE /books/{id}"""
        try:
            result = self.db.books.delete_one({'_id': ObjectId(book_id)})
            if not result.deleted_count:
                resp.media = {'error': 'Book not found'}
                resp.status = falcon.HTTP_404
                return
            resp.media = {'status': 'success', 'message': 'Book deleted'}
        except Exception as e:
            resp.media = {'error': str(e)}
            resp.status = falcon.HTTP_400


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BOOK_FIELDS = {
    'title': str,
    'authors': list,
    'average_rating': float,
    'isbn': str,
    'isbn13': str,
    'language_code': str,
    'num_pages': int,
    'ratings_count': int,
    'text_reviews_count': int,
    'publication_date': str,
    'publisher': str,
}


def _validate_book(data):
    """Validate and coerce book fields."""
    book = {}
    for field, field_type in BOOK_FIELDS.items():
        if field not in data:
            raise falcon.HTTPBadRequest(title='Invalid data', description=f'{field} is required')
        try:
            book[field] = field_type(data[field]) if field_type != list else list(data[field])
        except (ValueError, TypeError):
            raise falcon.HTTPBadRequest(
                title='Invalid data',
                description=f'{field} must be {field_type.__name__}'
            )
    return book


def _parse_book_row(row):
    """Parse a CSV row into a book document."""
    return {
        'title': row['title'],
        'authors': [a.strip() for a in row['authors'].split('/')],
        'average_rating': float(row['average_rating']),
        'isbn': row['isbn'],
        'isbn13': row['isbn13'],
        'language_code': row['language_code'],
        'num_pages': int(row['num_pages']) if row['num_pages'] else 0,
        'ratings_count': int(row['ratings_count']) if row['ratings_count'] else 0,
        'text_reviews_count': int(row['text_reviews_count']) if row['text_reviews_count'] else 0,
        'publication_date': row['publication_date'],
        'publisher': row['publisher'],
    }
