# ITESO BDNR - MongoDB Sample

A sample bookstore application demonstrating MongoDB document patterns with a REST API architecture.

## Architecture

```
┌────────────┐       ┌────────────┐       ┌────────────┐
│   Client   │ HTTP  │   Server   │       │  MongoDB   │
│   (CLI)    │ ────► │ (REST API) │ ────► │  (Docker)  │
└────────────┘       └────────────┘       └────────────┘
     client/              server/           port 27017
```

## Project Structure

```
iteso-bdnr-mongodb-sample/
├── server/
│   ├── app.py          # Falcon application and routes
│   └── resources.py    # REST endpoint handlers
├── client/
│   └── cli.py          # Command-line client
├── data/
│   └── books.csv       # Book dataset (~11k books)
├── requirements.txt
└── README.md
```

## Key MongoDB Concept: Schema-less + Indexes

MongoDB does not require a schema — any document can be inserted without prior table definitions. **Indexes** are the closest equivalent to DDL:

- Without indexes → every query performs a full collection scan
- With indexes → MongoDB jumps directly to matching documents

The `setup` command creates meaningful indexes and explains which query each one supports.

## Setup

You will need **2 terminal windows**: one for the server, one for the CLI.

### Step 1: Start MongoDB

```bash
docker run --name mongodb -p 27017:27017 -d mongo

# Verify it started:
docker exec -it mongodb mongosh --eval "db.runCommand({ping:1})"
```

### Step 2: Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# .\venv\Scripts\Activate.ps1   # Windows

pip install -r requirements.txt
```

### Step 3: Start the API Server

```bash
cd server
uvicorn app:app --reload --port 8001
```

### Step 4: Create Indexes

```bash
cd client
source ../venv/bin/activate

python cli.py setup
```

### Step 5: Load Demo Books

```bash
python cli.py seed --limit 100
```

## CLI Commands

### Admin

| Command | Description |
|---------|-------------|
| `status` | Check if API is running |
| `setup` | Create indexes on books collection |
| `seed --limit N` | Load N books from CSV (default 100) |

### Bookstore Actions

| Command | Description |
|---------|-------------|
| `list` | List all books |
| `list --rating N` | Books with rating >= N  (uses idx_rating) |
| `list --language eng` | Books by language  (uses idx_language) |
| `list --search "text"` | Full-text search  (uses idx_text_search) |
| `get --id ID` | Get a specific book |
| `add --title ... ` | Add a single book |
| `update --id ID ...` | Update a book |
| `delete --id ID` | Delete a book |

### Typical Session

```bash
# Admin
python cli.py setup
python cli.py seed --limit 100

# Browse books
python cli.py list
python cli.py list --rating 4.5
python cli.py list --language eng
python cli.py list --search "Harry Potter"

# Manage a book
python cli.py get --id <id>
python cli.py delete --id <id>
```

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/setup` | Create indexes |
| POST | `/seed` | Load demo books |
| GET | `/books` | List books (rating, language, search filters) |
| POST | `/books` | Add a book |
| GET | `/books/{id}` | Get a book |
| PUT | `/books/{id}` | Update a book |
| DELETE | `/books/{id}` | Delete a book |

### Example API Calls

```bash
curl http://localhost:8001/health
curl -X POST http://localhost:8001/setup
curl -X POST http://localhost:8001/seed -H "Content-Type: application/json" -d '{"limit": 50}'
curl http://localhost:8001/books
curl "http://localhost:8001/books?rating=4.5"
curl "http://localhost:8001/books?language=eng"
curl "http://localhost:8001/books?search=Harry+Potter"
curl http://localhost:8001/books/<id>
```

## Data Model

Books are stored as documents:

```json
{
    "_id": "ObjectId (auto-generated)",
    "title": "Harry Potter and the Chamber of Secrets",
    "authors": ["J.K. Rowling"],
    "average_rating": 4.42,
    "isbn": "0439554896",
    "isbn13": "9780439554893",
    "language_code": "eng",
    "num_pages": 352,
    "ratings_count": 6333,
    "text_reviews_count": 244,
    "publication_date": "11/1/2003",
    "publisher": "Scholastic"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_URL` | `http://localhost:8001` | API URL (client) |
| `MONGODB_HOST` | `localhost` | MongoDB host (server) |
| `MONGODB_PORT` | `27017` | MongoDB port (server) |
| `MONGODB_DATABASE` | `bookstore` | Database name (server) |

## Troubleshooting

**"Cannot connect to API"** — make sure the server is running: `cd server && uvicorn app:app --reload --port 8001`

**"Cannot connect to MongoDB"** — check Docker: `docker ps` then `docker exec -it mongodb mongosh`

**"No books found"** — run `setup` then `seed` first
