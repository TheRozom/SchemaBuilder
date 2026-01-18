# Schema Builder API

A FastAPI backend for generating JSON schemas from sample JSON data.

## Features

- 🔧 Generate JSON schemas from sample data
- 📊 Schema quality scoring (Strictness, Completeness, Ambiguity)
- ✅ Automatic schema validation against input data
- 🔍 Structural analysis to detect when to split schemas
- 🐳 Docker support
- 🤖 Optional AI-powered regex generation (OpenAI)
- 📝 Automatic API documentation (Swagger/OpenAPI)

## Getting Started

### Running with Docker

```bash
docker build -t schema-builder .
docker run -p 8000:8000 schema-builder
```

Access the API:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Running Locally

```bash
poetry install
poetry run uvicorn src.api.main:app --reload
```

Or with Python directly:

```bash
pip install poetry
poetry install
python -m src.api.main
```

## API Endpoints

### POST /schemas/infer
Generate schema from JSON data (single object or array)

**Request Body:**
```json
{
  "name": "John",
  "age": 30,
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "schema_content": {
    "type": "object",
    "properties": {
      "name": {"type": "string", "maxLength": 4},
      "age": {"type": "integer", "minimum": 0, "maximum": 30},
      "email": {"type": "string", "pattern": "..."}
    }
  },
  "score": {
    "total_score": 85.5,
    "breakdown": {
      "strictness": 90.0,
      "completeness": 85.0,
      "ambiguity": 82.0
    },
    "ai_score": null
  },
  "validation": {
    "valid": true,
    "total_errors": 0,
    "errors": []
  }
}
```

**Validation Field:**
- `valid`: Whether all input data validates against the generated schema
- `total_errors`: Number of validation errors found
- `errors`: List of validation errors (if any) with object index, path, and message

### POST /schemas/build
Generate schema from list of JSON objects

### POST /schemas/analyze
Analyze structural differences between JSON objects to determine if they should use separate schemas.

**Use Case**: Detects when you're mixing different data types (users, products, configs) that shouldn't be in one giant schema.

**Request Body:**
```json
[
  {"user": {"name": "John", "email": "john@test.com"}},
  {"user": {"name": "Jane", "email": "jane@test.com"}},
  {"product": {"id": 123, "price": 99.99}},
  {"version": {"major": 1, "minor": 0}}
]
```

**Response:**
```json
{
  "total_objects": 4,
  "unique_structures": 3,
  "should_split_schemas": true,
  "recommendation": "Found 3 distinct structure groups with low similarity (37.5%). Create 3 separate schemas.",
  "confidence": "high"
}
```

### GET /health
Health check endpoint

## Environment Variables

Create a `.env` file:

```
ENABLE_AI=false
OPENAI_API_KEY=your-api-key-here
```

- `ENABLE_AI` - Enable AI-powered features (default: false)
- `OPENAI_API_KEY` - OpenAI API key (required if ENABLE_AI=true)

## Project Structure

```
.
├── src/
│   ├── api/              # FastAPI endpoints
│   ├── bl/               # Business logic & scoring
│   ├── core/             # Configuration
│   ├── domain/           # Domain models & interfaces
│   └── infrastructure/   # External services (AI)
├── tests/                # Unit & integration tests
├── Dockerfile            # Docker configuration
└── pyproject.toml        # Dependencies
```

## Testing

```bash
poetry run pytest
poetry run pytest --cov=src tests/
```

## Development

Built with:
- FastAPI - Modern, fast web framework
- Pydantic - Data validation
- Poetry - Dependency management
