# Translation API Endpoints

Base URL: `http://10.10.12.79:8000/api/translations/`

---

## 1. Search Translations

**Endpoint:** `POST /api/translations/search/`

**Description:** Search for translations in English or Marshallese with optional category filter

**Authentication:** Not required (AllowAny)

**Request Body:**
```json
{
    "query": "bone",
    "source_language": "english",
    "category": "body_parts"
}
```

**Parameters:**
- `query` (required): Search text
- `source_language` (optional): "english" or "marshallese" (default: "english")
- `category` (optional): Filter by category (body_parts, common_phrases, emergency, general, medical_equipment, medical_staff, medication, procedures, questions, symptoms)

**Response Example:**
```json
{
    "error": false,
    "message": "Found 5 translations",
    "data": [
        {
            "id": 1,
            "english_text": "Bone",
            "marshallese_text": "Boon",
            "category": "body_parts",
            "description": "Skeletal structure",
            "is_favorite": false,
            "usage_count": 15,
            "is_sample": true,
            "created_by_email": null,
            "created_date": "2024-01-15T10:30:00Z",
            "updated_date": "2024-01-20T14:20:00Z"
        }
    ]
}
```

**Test Examples:**

1. **Search English to Marshallese:**
```json
POST http://10.10.12.79:8000/api/translations/search/
{
    "query": "hello",
    "source_language": "english"
}
```

2. **Search Marshallese to English:**
```json
POST http://10.10.12.79:8000/api/translations/search/
{
    "query": "iakwe",
    "source_language": "marshallese"
}
```

3. **Search with Category Filter:**
```json
POST http://10.10.12.79:8000/api/translations/search/
{
    "query": "pain",
    "source_language": "english",
    "category": "symptoms"
}
```

---

## 2. Get Translation Detail (with AI Context)

**Endpoint:** `GET /api/translations/{id}/`

**Description:** Get detailed translation with AI-generated context information

**Authentication:** Not required (AllowAny)

**Response Example:**
```json
{
    "error": false,
    "message": "Translation details retrieved successfully",
    "data": {
        "id": 1,
        "english_text": "Bone",
        "marshallese_text": "Boon",
        "category": "body_parts",
        "description": "Skeletal structure",
        "is_favorite": false,
        "usage_count": 16,
        "is_sample": true,
        "created_by_email": null,
        "created_date": "2024-01-15T10:30:00Z",
        "updated_date": "2024-01-20T14:25:00Z",
        "ai_context": "This is a body part term used in medical contexts. 'Bone (Boon)' refers to Skeletal structure. When communicating with Marshallese speakers, you can use this term to discuss anatomy and medical conditions related to this body part."
    }
}
```

**Test Examples:**

```
GET http://10.10.12.79:8000/api/translations/1/
GET http://10.10.12.79:8000/api/translations/25/
GET http://10.10.12.79:8000/api/translations/100/
```

**Note:** This endpoint automatically increments the `usage_count` each time it's accessed.

---

## 3. Get Recent Translations

**Endpoint:** `GET /api/translations/recent/`

**Description:** Get the 10 most recently accessed translations

**Authentication:** Not required (AllowAny)

**Response Example:**
```json
{
    "error": false,
    "message": "Recent translations retrieved successfully",
    "data": [
        {
            "id": 1,
            "english_text": "Bone",
            "marshallese_text": "Boon",
            "category": "body_parts",
            "usage_count": 16
        },
        {
            "id": 5,
            "english_text": "Hello",
            "marshallese_text": "Iakwe",
            "category": "common_phrases",
            "usage_count": 42
        }
    ]
}
```

**Test Example:**
```
GET http://10.10.12.79:8000/api/translations/recent/
```

---

## 4. Get All Categories

**Endpoint:** `GET /api/translations/categories/`

**Description:** Get list of all available translation categories with counts

**Authentication:** Not required (AllowAny)

**Response Example:**
```json
{
    "error": false,
    "message": "Categories retrieved successfully",
    "data": [
        {
            "name": "body_parts",
            "display_name": "Body Parts",
            "count": 85
        },
        {
            "name": "common_phrases",
            "display_name": "Common Phrases",
            "count": 120
        },
        {
            "name": "emergency",
            "display_name": "Emergency",
            "count": 45
        }
    ]
}
```

**Test Example:**
```
GET http://10.10.12.79:8000/api/translations/categories/
```

---

## 5. Get Translations by Category

**Endpoint:** `GET /api/translations/category/{category}/`

**Description:** Get all translations in a specific category

**Authentication:** Not required (AllowAny)

**Response Example:**
```json
{
    "error": false,
    "message": "Found 85 translations in category: body_parts",
    "data": [
        {
            "id": 1,
            "english_text": "Bone",
            "marshallese_text": "Boon",
            "category": "body_parts",
            "description": "Skeletal structure",
            "is_favorite": false,
            "usage_count": 16,
            "is_sample": true,
            "created_by_email": null,
            "created_date": "2024-01-15T10:30:00Z",
            "updated_date": "2024-01-20T14:25:00Z"
        }
    ]
}
```

**Test Examples:**
```
GET http://10.10.12.79:8000/api/translations/category/body_parts/
GET http://10.10.12.79:8000/api/translations/category/medication/
GET http://10.10.12.79:8000/api/translations/category/emergency/
GET http://10.10.12.79:8000/api/translations/category/common_phrases/
```

---

## 6. Get Favorite Translations

**Endpoint:** `GET /api/translations/favorites/`

**Description:** Get all favorited translations for the authenticated user

**Authentication:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response Example:**
```json
{
    "error": false,
    "message": "Favorite translations retrieved successfully",
    "data": [
        {
            "id": 5,
            "english_text": "Hello",
            "marshallese_text": "Iakwe",
            "category": "common_phrases",
            "description": "Common greeting",
            "is_favorite": true,
            "usage_count": 42,
            "is_sample": true,
            "created_by_email": null,
            "created_date": "2024-01-15T10:30:00Z",
            "updated_date": "2024-01-20T14:25:00Z"
        }
    ]
}
```

**Test Example:**
```
GET http://10.10.12.79:8000/api/translations/favorites/
Headers: 
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 7. Toggle Favorite

**Endpoint:** `POST /api/translations/favorites/toggle/`

**Description:** Add or remove a translation from favorites

**Authentication:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request Body:**
```json
{
    "translation_id": 5
}
```

**Response Example:**
```json
{
    "error": false,
    "message": "Translation added to favorites",
    "data": {
        "id": 5,
        "is_favorite": true
    }
}
```

**Test Examples:**

1. **Add to Favorites:**
```json
POST http://10.10.12.79:8000/api/translations/favorites/toggle/
Headers: Authorization: Bearer YOUR_TOKEN
{
    "translation_id": 5
}
```

2. **Remove from Favorites (same call):**
```json
POST http://10.10.12.79:8000/api/translations/favorites/toggle/
Headers: Authorization: Bearer YOUR_TOKEN
{
    "translation_id": 5
}
```

---

## 8. Submit New Translation

**Endpoint:** `POST /api/translations/submit/`

**Description:** Users can contribute new translations for admin review

**Authentication:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request Body:**
```json
{
    "english_text": "Good morning",
    "marshallese_text": "Emman mour",
    "category": "common_phrases",
    "description": "Morning greeting"
}
```

**Response Example:**
```json
{
    "error": false,
    "message": "Translation submitted successfully. Pending admin review for accuracy.",
    "data": {
        "id": 768,
        "english_text": "Good morning",
        "marshallese_text": "Emman mour",
        "category": "common_phrases",
        "description": "Morning greeting",
        "is_favorite": false,
        "usage_count": 0,
        "is_sample": false,
        "created_by_email": "user@example.com",
        "created_date": "2024-01-20T15:00:00Z",
        "updated_date": "2024-01-20T15:00:00Z"
    }
}
```

**Test Example:**
```json
POST http://10.10.12.79:8000/api/translations/submit/
Headers: Authorization: Bearer YOUR_TOKEN
{
    "english_text": "Thank you very much",
    "marshallese_text": "Kommol tata",
    "category": "common_phrases",
    "description": "Expression of gratitude"
}
```

---

## 9. List All Translations (Paginated)

**Endpoint:** `GET /api/translations/?page=1&limit=50`

**Description:** Get paginated list of all translations

**Authentication:** Not required (AllowAny)

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 50)

**Response Example:**
```json
{
    "error": false,
    "message": "Translations retrieved successfully",
    "data": {
        "translations": [
            {
                "id": 1,
                "english_text": "Bone",
                "marshallese_text": "Boon",
                "category": "body_parts",
                "description": "Skeletal structure",
                "is_favorite": false,
                "usage_count": 16,
                "is_sample": true,
                "created_by_email": null,
                "created_date": "2024-01-15T10:30:00Z",
                "updated_date": "2024-01-20T14:25:00Z"
            }
        ],
        "page": 1,
        "limit": 50,
        "total": 767,
        "has_more": true
    }
}
```

**Test Examples:**
```
GET http://10.10.12.79:8000/api/translations/
GET http://10.10.12.79:8000/api/translations/?page=2
GET http://10.10.12.79:8000/api/translations/?page=1&limit=100
```

---

## Available Categories

- `body_parts` - Body Parts
- `common_phrases` - Common Phrases
- `emergency` - Emergency
- `general` - General
- `medical_equipment` - Medical Equipment
- `medical_staff` - Medical Staff
- `medication` - Medication
- `procedures` - Procedures
- `questions` - Questions
- `symptoms` - Symptoms

---

## Error Response Format

All endpoints return errors in this format:

```json
{
    "error": true,
    "message": "Error description",
    "details": {
        "field_name": ["Error message"]
    }
}
```

**Common Error Codes:**
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing or invalid token)
- `404` - Not Found (translation doesn't exist)
- `500` - Server Error

---

## AI Context Feature

When you access a translation detail (`GET /api/translations/{id}/`), the API automatically generates contextual information based on the category:

**Category-Specific AI Context Examples:**

1. **Body Parts:**
   > "This is a body part term used in medical contexts. 'Bone (Boon)' refers to Skeletal structure. When communicating with Marshallese speakers, you can use this term to discuss anatomy and medical conditions related to this body part."

2. **Medication:**
   > "Medication/pharmaceutical term: 'Aspirin (Aspirin)' - Pain reliever. Important medical translation for discussing treatment and prescriptions with Marshallese-speaking patients."

3. **Emergency:**
   > "Emergency situation term: 'Help (Jiban)' - Call for assistance. Critical phrase for urgent medical situations when communicating with Marshallese speakers."

4. **Symptoms:**
   > "Medical symptom description: 'Fever (Kalbuuj)' - High body temperature. Use this when discussing patient conditions with Marshallese-speaking individuals."

---

## Quick Test Flow

1. **Get all categories:**
   ```
   GET http://10.10.12.79:8000/api/translations/categories/
   ```

2. **Search for a translation:**
   ```json
   POST http://10.10.12.79:8000/api/translations/search/
   {
       "query": "hello",
       "source_language": "english"
   }
   ```

3. **Get translation detail with AI context:**
   ```
   GET http://10.10.12.79:8000/api/translations/1/
   ```

4. **Check recent translations:**
   ```
   GET http://10.10.12.79:8000/api/translations/recent/
   ```

5. **Browse by category:**
   ```
   GET http://10.10.12.79:8000/api/translations/category/common_phrases/
   ```

---

## Notes for Frontend Developer

1. **Search is flexible:** You can search in either English or Marshallese by setting `source_language`
2. **AI Context is automatic:** Just click the AI button and call the detail endpoint
3. **Usage tracking:** Every time detail is viewed, `usage_count` increments automatically
4. **Recent list:** Shows last 10 accessed translations based on `updated_date`
5. **Favorites require auth:** User must be logged in to manage favorites
6. **No auth for search/view:** Public can search and view translations without login
7. **Pagination:** Use page/limit params to control data volume
