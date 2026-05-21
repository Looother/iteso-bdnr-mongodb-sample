#!/usr/bin/env python3
"""
Books CLI — bookstore management client.

Admin (run once):
  setup  — create indexes on the books collection
  seed   — load demo books from CSV

Bookstore actions:
  add     — add a single book
  list    — list/search books
  get     — get a book by ID
  update  — update a book by ID
  delete  — delete a book by ID
"""
import argparse
import os
import sys

import requests
from tabulate import tabulate

API_URL = os.getenv('API_URL', 'http://localhost:8001')


def _err(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _get(path, **params):
    try:
        return requests.get(f"{API_URL}{path}", params=params or None, timeout=30)
    except requests.exceptions.ConnectionError:
        _err(f"Cannot connect to API at {API_URL}")


def _post(path, body=None, timeout=60):
    try:
        return requests.post(f"{API_URL}{path}", json=body, timeout=timeout)
    except requests.exceptions.ConnectionError:
        _err(f"Cannot connect to API at {API_URL}")


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

def cmd_status():
    r = _get('/health')
    if r.ok:
        d = r.json()
        print(f"API:      {d.get('status')}")
        print(f"Database: {d.get('database')}")
    else:
        _err(f"HTTP {r.status_code}")


def cmd_setup():
    """
    Create indexes on the books collection.

    MongoDB is schema-less — any document can be stored without prior setup.
    Indexes are MongoDB's DDL equivalent: they don't define structure, but they
    determine which queries run efficiently vs. which require a full scan.
    """
    r = _post('/setup', timeout=30)
    if not r.ok:
        _err(f"Setup failed: {r.text}")

    d = r.json()
    print(f"OK: {d['message']}\n")
    print(f"Note: {d['note']}\n")
    print("Indexes created:")
    for idx in d.get('indexes', []):
        print(f"  {idx['index']:<20} ← {idx.get('supports', '')}")


def cmd_seed(limit):
    """Load books from CSV via the same logic used by POST /books."""
    print(f"Loading {limit} books from CSV …")
    r = _post('/seed', {'limit': limit}, timeout=120)
    if not r.ok:
        _err(f"Seed failed: {r.text}")

    d = r.json()
    print(f"OK: {d['inserted']} books inserted, {d['skipped']} skipped")


# ---------------------------------------------------------------------------
# Bookstore actions
# ---------------------------------------------------------------------------

def cmd_add(title, authors, rating, isbn, isbn13, language, pages, publisher, pub_date):
    """Add a single book."""
    book = {
        'title': title,
        'authors': [a.strip() for a in authors.split(',')],
        'average_rating': rating,
        'isbn': isbn,
        'isbn13': isbn13,
        'language_code': language,
        'num_pages': pages,
        'ratings_count': 0,
        'text_reviews_count': 0,
        'publication_date': pub_date,
        'publisher': publisher,
    }
    r = _post('/books', book)
    if not r.ok:
        _err(f"Failed: {r.text}")

    d = r.json()
    print(f"Book added!\n  ID:    {d['_id']}\n  Title: {d['title']}")


def cmd_list(rating=None, language=None, search=None):
    """
    List books with optional filters.
    Each filter uses a different index — run 'setup' first to create them.
    """
    params = {}
    if rating is not None:  params['rating'] = rating
    if language:            params['language'] = language
    if search:              params['search'] = search

    r = _get('/books', **params)
    if not r.ok:
        _err(f"Failed: {r.text}")

    d = r.json()
    books = d.get('books', [])
    if not books:
        print("No books found.")
        return

    table = [
        [
            b.get('_id', ''),
            b.get('title', '')[:40],
            ', '.join(b.get('authors', []))[:25],
            f"{b.get('average_rating', 0):.1f}",
            b.get('language_code', ''),
        ]
        for b in books
    ]
    print(tabulate(table, headers=['ID', 'Title', 'Authors', 'Rating', 'Lang'], tablefmt='github'))
    print(f"\n{len(books)} book(s)")


def cmd_get(book_id):
    r = _get(f'/books/{book_id}')
    if not r.ok:
        if r.status_code == 404:
            _err(f"Book not found: {book_id}")
        _err(f"Failed: {r.text}")

    book = r.json()
    for key, value in book.items():
        print(f"  {key}: {value}")


def cmd_update(book_id, title, authors, rating, isbn, isbn13, language, pages, publisher, pub_date):
    """Update a book by ID."""
    book = {
        'title': title,
        'authors': [a.strip() for a in authors.split(',')],
        'average_rating': rating,
        'isbn': isbn,
        'isbn13': isbn13,
        'language_code': language,
        'num_pages': pages,
        'ratings_count': 0,
        'text_reviews_count': 0,
        'publication_date': pub_date,
        'publisher': publisher,
    }
    try:
        r = requests.put(f"{API_URL}/books/{book_id}", json=book, timeout=10)
    except requests.exceptions.ConnectionError:
        _err(f"Cannot connect to API at {API_URL}")

    if not r.ok:
        if r.status_code == 404:
            _err(f"Book not found: {book_id}")
        _err(f"Failed: {r.text}")

    print(f"Book {book_id} updated successfully")


def cmd_delete(book_id):
    try:
        r = requests.delete(f"{API_URL}/books/{book_id}", timeout=10)
    except requests.exceptions.ConnectionError:
        _err(f"Cannot connect to API at {API_URL}")

    if not r.ok:
        if r.status_code == 404:
            _err(f"Book not found: {book_id}")
        _err(f"Failed: {r.text}")

    print(f"Book {book_id} deleted")


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Books CLI — bookstore management client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Admin (run once):
  python cli.py setup
  python cli.py seed --limit 100

List and search:
  python cli.py list
  python cli.py list --rating 4.5
  python cli.py list --language eng
  python cli.py list --search "Harry Potter"

Manage books:
  python cli.py get    --id <id>
  python cli.py delete --id <id>
        """
    )
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('status', help='Check API health')
    sub.add_parser('setup',  help='Create indexes on books collection (run once)')

    p = sub.add_parser('seed', help='Load demo books from CSV')
    p.add_argument('--limit', type=int, default=100, help='Max books to load (default 100)')

    p = sub.add_parser('add', help='Add a single book')
    p.add_argument('--title',     required=True)
    p.add_argument('--authors',   required=True, help='Comma-separated author names')
    p.add_argument('--rating',    required=True, type=float)
    p.add_argument('--isbn',      required=True)
    p.add_argument('--isbn13',    required=True)
    p.add_argument('--language',  required=True, help='e.g. eng')
    p.add_argument('--pages',     required=True, type=int)
    p.add_argument('--publisher', required=True)
    p.add_argument('--pub-date',  required=True, help='e.g. 1/1/2020')

    p = sub.add_parser('list', help='List/search books')
    p.add_argument('--rating',   type=float, help='Minimum rating')
    p.add_argument('--language', help='Language code e.g. eng')
    p.add_argument('--search',   help='Full-text search in title and authors')

    p = sub.add_parser('get', help='Get a book by ID')
    p.add_argument('--id', '-i', required=True)

    p = sub.add_parser('update', help='Update a book by ID')
    p.add_argument('--id',       required=True)
    p.add_argument('--title',    required=True)
    p.add_argument('--authors',  required=True)
    p.add_argument('--rating',   required=True, type=float)
    p.add_argument('--isbn',     required=True)
    p.add_argument('--isbn13',   required=True)
    p.add_argument('--language', required=True)
    p.add_argument('--pages',    required=True, type=int)
    p.add_argument('--publisher', required=True)
    p.add_argument('--pub-date', required=True)

    p = sub.add_parser('delete', help='Delete a book by ID')
    p.add_argument('--id', '-i', required=True)

    args = parser.parse_args()

    if   args.command == 'status': cmd_status()
    elif args.command == 'setup':  cmd_setup()
    elif args.command == 'seed':   cmd_seed(args.limit)
    elif args.command == 'add':    cmd_add(args.title, args.authors, args.rating, args.isbn,
                                           args.isbn13, args.language, args.pages,
                                           args.publisher, args.pub_date)
    elif args.command == 'list':   cmd_list(args.rating, args.language, args.search)
    elif args.command == 'get':    cmd_get(args.id)
    elif args.command == 'update': cmd_update(args.id, args.title, args.authors, args.rating,
                                              args.isbn, args.isbn13, args.language, args.pages,
                                              args.publisher, args.pub_date)
    elif args.command == 'delete': cmd_delete(args.id)


if __name__ == '__main__':
    main()
