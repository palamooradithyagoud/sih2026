# API Standards & Specifications

## REST API Conventions

- **Base URL**: `/api/v1`
- **Formats**: JSON request and response payloads.
- **Documentation**: Automatically generated via OpenAPI at `/docs` (Swagger UI) and `/redoc`.

## Health Check Endpoint

### GET `/health`
- **Description**: Returns basic operational status of the backend service.
- **Request**: `GET /health` or `GET /api/v1/health`
- **Response**:
```json
{
  "status": "ok"
}
```

## Standard Error Response Format
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource could not be found."
  }
}
```
