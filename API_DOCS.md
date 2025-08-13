# CarbonIQ API Documentation

A comprehensive REST API for waste management and carbon footprint tracking.

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://your-deployed-api-url`

## Interactive Documentation
- **Swagger UI**: `{base_url}/docs`
- **ReDoc**: `{base_url}/redoc`
- **OpenAPI Schema**: `{base_url}/openapi.json`

---

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### POST /auth/register

**Description**: Register a new user account

**Authentication**: None required

**Request Body** (JSON):
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "role": "student"
}
```

**Available Roles**:
- `student` - Can create reports
- `staff` - Can create reports and institutions  
- `admin` - Full access to all endpoints
- `collector` - Can view and update reports

**Response** (200 OK):
```json
{
  "id": "user_id_here",
  "email": "user@example.com", 
  "full_name": "John Doe",
  "role": "student"
}
```

**Error Responses**:
- `400` - Email already registered
- `422` - Validation error

---

### POST /auth/login

**Description**: Login user and receive JWT token

**Authentication**: None required

**Request Body** (form-urlencoded):
```
username=user@example.com
password=password123
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `400` - Incorrect email or password
- `422` - Validation error

---

## Institutions

### POST /institutions/

**Description**: Create a new institution (requires admin/staff role)

**Authentication**: Required (admin or staff only)

**Request Body** (JSON):
```json
{
  "name": "Green Valley School",
  "kind": "school",
  "location": {
    "type": "Point",
    "coordinates": [-74.006, 40.7128]
  }
}
```

**Institution Types**:
- `school`
- `hospital` 
- `facility`

**Response** (200 OK):
```json
{
  "id": "institution_id_here",
  "name": "Green Valley School",
  "kind": "school",
  "location": {
    "type": "Point",
    "coordinates": [-74.006, 40.7128]
  }
}
```

**Error Responses**:
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `422` - Validation error

---

### GET /institutions/

**Description**: List all institutions

**Authentication**: None required

**Query Parameters**: None

**Response** (200 OK):
```json
[
  {
    "id": "institution_id_1",
    "name": "Green Valley School",
    "kind": "school",
    "location": {
      "type": "Point", 
      "coordinates": [-74.006, 40.7128]
    }
  },
  {
    "id": "institution_id_2",
    "name": "City Hospital",
    "kind": "hospital",
    "location": {
      "type": "Point",
      "coordinates": [-74.007, 40.7129]
    }
  }
]
```

---

## Reports

### POST /reports/

**Description**: Create a new waste report

**Authentication**: Required

**Request Body** (JSON):
```json
{
  "student_id": "student123",
  "nearest_institution_id": "institution_id_here",
  "image_url": "/static/images/waste_photo.jpg",
  "measure_height_cm": 15.5,
  "measure_width_cm": 10.2,
  "waste_type": "recyclable_plastic",
  "feedback": "Large plastic bottle found near playground",
  "safe": true,
  "urban_area": true,
  "children_present": false,
  "flood_risk": false,
  "animals_present": false,
  "collection_method": "curbside",
  "location": {
    "type": "Point",
    "coordinates": [-74.006, 40.7128]
  }
}
```

**Required Fields**:
- `student_id`
- `waste_type` 
- `location`

**Waste Types**:
- `organic`
- `recyclable_plastic`
- `recyclable_paper`
- `recyclable_glass`
- `e_waste`
- `waste_collection`
- `mixed`

**Collection Methods**:
- `curbside`
- `door_to_door`
- `drop_off`
- `pickup_services`
- `return_system`

**Response** (200 OK):
```json
{
  "id": "report_id_here",
  "student_id": "student123",
  "nearest_institution_id": "institution_id_here", 
  "image_url": "/static/images/waste_photo.jpg",
  "timestamp": "2025-08-13T17:07:03.279000",
  "measure_height_cm": 15.5,
  "measure_width_cm": 10.2,
  "waste_type": "recyclable_plastic",
  "feedback": "Large plastic bottle found near playground",
  "safe": true,
  "urban_area": true,
  "children_present": false,
  "flood_risk": false,
  "animals_present": false,
  "collection_method": "curbside",
  "location": {
    "type": "Point",
    "coordinates": [-74.006, 40.7128]
  },
  "status": "new",
  "priority": 0
}
```

**Error Responses**:
- `401` - Unauthorized (missing/invalid token)
- `422` - Validation error

---

### GET /reports/near

**Description**: Find reports near a specific location using geospatial search

**Authentication**: None required

**Query Parameters**:
- `lng` (float, required) - Longitude
- `lat` (float, required) - Latitude  
- `radius_m` (int, optional) - Search radius in meters (default: 500)

**Example Request**:
```
GET /reports/near?lng=-74.006&lat=40.7128&radius_m=1000
```

**Response** (200 OK):
```json
[
  {
    "id": "report_id_1",
    "student_id": "student123",
    "waste_type": "recyclable_plastic",
    "location": {
      "type": "Point",
      "coordinates": [-74.006, 40.7128]
    },
    "status": "new",
    "priority": 0,
    "timestamp": "2025-08-13T17:07:03.279000"
  }
]
```

**Error Responses**:
- `422` - Invalid coordinates

---

### POST /reports/upload

**Description**: Upload an image file for a report

**Authentication**: Required

**Request Body** (multipart/form-data):
- `file` - Image file (JPG, PNG, etc.)

**Response** (200 OK):
```json
{
  "url": "/static/images/1723567623_photo.jpg"
}
```

**Error Responses**:
- `401` - Unauthorized (missing/invalid token)
- `422` - Missing file or invalid file type

---

## Data Models

### Location (GeoJSON Point)
All location fields use GeoJSON Point format:
```json
{
  "type": "Point",
  "coordinates": [longitude, latitude]
}
```

### Report Status Values
- `new` - Recently created report
- `assigned` - Report assigned to collector
- `cleared` - Waste has been collected

### Priority Levels
- `0` - Normal priority (default)
- `1` - High priority
- `2` - Urgent

---

## Error Handling

### Standard HTTP Status Codes
- `200` - Success
- `201` - Created successfully
- `400` - Bad request
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Resource not found
- `422` - Validation error
- `500` - Internal server error

### Error Response Format
```json
{
  "detail": "Error message description"
}
```

### Validation Error Format
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "field_name"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

---

## Usage Examples

### Complete Authentication Flow

```javascript
// 1. Register
const registerResponse = await fetch('/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123',
    full_name: 'John Doe',
    role: 'student'
  })
});

// 2. Login
const loginResponse = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: 'username=user@example.com&password=password123'
});
const { access_token } = await loginResponse.json();

// 3. Create Report (authenticated)
const reportResponse = await fetch('/reports/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    student_id: 'student123',
    waste_type: 'recyclable_plastic',
    location: {
      type: 'Point',
      coordinates: [-74.006, 40.7128]
    },
    safe: true,
    urban_area: true
  })
});
```

### File Upload Example

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('/reports/upload', {
  method: 'POST', 
  headers: {
    'Authorization': `Bearer ${access_token}`
  },
  body: formData
});
const { url } = await uploadResponse.json();
```

---

## Rate Limiting

Currently no rate limiting is implemented, but recommended limits for production:
- Authentication endpoints: 5 requests per minute
- Report creation: 10 requests per minute
- File uploads: 3 requests per minute
- Read endpoints: 100 requests per minute

---

## CORS Policy

Development: All origins allowed
Production: Restrict to your frontend domain

---

## Support

For API questions or issues:
1. Check interactive documentation at `/docs`
2. Verify authentication headers
3. Validate request body format
4. Contact development team

**Last Updated**: August 13, 2025
