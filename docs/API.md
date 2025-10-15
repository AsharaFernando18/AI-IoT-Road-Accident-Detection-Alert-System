# RoadSafeNet API Documentation

## Authentication

All API endpoints (except `/api/auth/login` and `/api/auth/register`) require authentication using JWT tokens.

### Getting a Token

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the Authorization header:
```
Authorization: Bearer <your_token_here>
```

## Endpoints

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "role": "viewer"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### Accidents

#### List Accidents
```http
GET /api/accidents?skip=0&limit=100&severity=high&status_filter=pending
Authorization: Bearer <token>
```

**Query Parameters:**
- `skip` (int): Number of records to skip
- `limit` (int): Maximum records to return
- `severity` (string): Filter by severity (low, medium, high, critical)
- `status_filter` (string): Filter by status (pending, confirmed, false_alarm, resolved)

#### Create Accident
```http
POST /api/accidents
Authorization: Bearer <token>
Content-Type: application/json

{
  "location_lat": 40.7128,
  "location_lon": -74.0060,
  "location_name": "Times Square",
  "address": "Manhattan, New York, NY",
  "city": "New York",
  "country": "USA",
  "severity": "high",
  "confidence": 0.92,
  "detected_objects": "[{\"class\": \"car\", \"confidence\": 0.95}]",
  "image_path": "/uploads/accident_123.jpg",
  "video_frame": 1542,
  "notes": "Multiple vehicles involved"
}
```

#### Get Accident Details
```http
GET /api/accidents/{accident_id}
Authorization: Bearer <token>
```

#### Update Accident
```http
PATCH /api/accidents/{accident_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "confirmed",
  "severity": "critical",
  "notes": "Ambulance dispatched"
}
```

#### Delete Accident (Admin Only)
```http
DELETE /api/accidents/{accident_id}
Authorization: Bearer <token>
```

### Analytics

#### Get Statistics
```http
GET /api/analytics/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_accidents": 150,
  "total_alerts": 450,
  "pending_accidents": 5,
  "confirmed_accidents": 120,
  "severity_breakdown": {
    "low": 30,
    "medium": 60,
    "high": 45,
    "critical": 15
  },
  "recent_24h": 8
}
```

#### Get Timeline
```http
GET /api/analytics/timeline?days=7
Authorization: Bearer <token>
```

#### Get Heatmap Data
```http
GET /api/analytics/heatmap
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "lat": 40.7128,
    "lon": -74.0060,
    "severity": "high",
    "timestamp": "2025-10-15T14:30:00"
  }
]
```

### Alerts

#### List Alerts
```http
GET /api/alerts?skip=0&limit=100&accident_id=5
Authorization: Bearer <token>
```

#### Create Alert
```http
POST /api/alerts
Authorization: Bearer <token>
Content-Type: application/json

{
  "accident_id": 5,
  "language": "en",
  "message": "Accident detected at Times Square",
  "translated_message": "Accidente detectado en Times Square",
  "recipient": "123456789"
}
```

### Users (Admin Only)

#### List Users
```http
GET /api/users?skip=0&limit=100
Authorization: Bearer <admin_token>
```

#### Update User
```http
PATCH /api/users/{user_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "is_active": false,
  "role": "operator"
}
```

### System Logs

#### List Logs
```http
GET /api/logs?skip=0&limit=100&level=ERROR&source=detection
Authorization: Bearer <token>
```

**Query Parameters:**
- `skip` (int): Number of records to skip
- `limit` (int): Maximum records to return
- `level` (string): Filter by log level (INFO, WARNING, ERROR, CRITICAL)
- `source` (string): Filter by source (detection, translation, telegram, api, system)

### System Settings (Admin Only)

#### Get All Settings
```http
GET /api/settings
Authorization: Bearer <admin_token>
```

#### Update Setting
```http
PATCH /api/settings/{key}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "value": "0.6"
}
```

### Health Check

#### Check API Health
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-15T14:30:00",
  "version": "1.0.0"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin access required"
}
```

### 404 Not Found
```json
{
  "detail": "Accident not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

API endpoints are subject to rate limiting to prevent abuse. Current limits:
- Authenticated users: 1000 requests/hour
- Unauthenticated: 100 requests/hour

## Pagination

List endpoints support pagination using `skip` and `limit` parameters:
- Default `limit`: 100
- Maximum `limit`: 1000
- Response includes total count

Example paginated response:
```json
{
  "data": [...],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

## Interactive Documentation

For interactive API documentation, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
