# Category ForeignKey Update - API Changes

## Summary
The `category` field in `Translation` and `UserSubmission` models has been changed from CharField (string) to ForeignKey (integer ID).

## Available Categories

| ID | Name | Slug |
|----|------|------|
| 1 | Common Phrases | common-phrases |
| 2 | Questions | questions |
| 3 | General | general |
| 4 | Symptoms | symptoms |
| 5 | Body Parts | body-parts |
| 6 | Medication | medication |

---

## API Changes

### 1. POST - Add Translation
**Endpoint:** `POST /api/administration/translations/add/`

#### OLD Format (Before):
```json
{
    "english_text": "Hello",
    "marshallese_text": "Iakwe",
    "category": "common_phrases",
    "description": "A greeting phrase",
    "is_sample": true
}
```

#### NEW Format (Now):
```json
{
    "english_text": "Hello",
    "marshallese_text": "Iakwe",
    "category": 1,
    "description": "A greeting phrase",
    "is_sample": true
}
```

**Note:** Use category ID instead of string. For "Common Phrases", use `1`.

---

### 2. PUT - Update Translation
**Endpoint:** `PUT /api/administration/translations/update/{id}/`

#### OLD Format (Before):
```json
{
    "english_text": "Goodbye",
    "marshallese_text": "Yokwe",
    "category": "common_phrases",
    "description": "A farewell phrase",
    "is_sample": false
}
```

#### NEW Format (Now):
```json
{
    "english_text": "Goodbye",
    "marshallese_text": "Yokwe",
    "category": 1,
    "description": "A farewell phrase",
    "is_sample": false
}
```

**Note:** Use category ID instead of string.

---

## Response Format Changes

### GET - All Translations
**Endpoint:** `GET /api/administration/translations/`

#### OLD Response:
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "english_text": "Hello",
            "marshallese_text": "Iakwe",
            "category": "common_phrases",
            "context": "A greeting phrase",
            "description": "A greeting phrase",
            "is_favorite": false,
            "usage_count": 0,
            "is_sample": true,
            "created_by": 1,
            "created_by_email": "admin@example.com",
            "created_date": "2025-12-28T10:00:00Z",
            "updated_date": "2025-12-28T10:00:00Z"
        }
    ]
}
```

#### NEW Response:
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "english_text": "Hello",
            "marshallese_text": "Iakwe",
            "category": 1,
            "category_details": {
                "id": 1,
                "name": "Common Phrases",
                "slug": "common-phrases"
            },
            "context": "A greeting phrase",
            "description": "A greeting phrase",
            "is_favorite": false,
            "usage_count": 0,
            "is_sample": true,
            "created_by": 1,
            "created_by_email": "admin@example.com",
            "created_date": "2025-12-28T10:00:00Z",
            "updated_date": "2025-12-28T10:00:00Z"
        }
    ]
}
```

**Changes:**
- `category` is now an integer ID (1 instead of "common_phrases")
- New field `category_details` provides nested category information (id, name, slug)

---

## Complete Postman Test Examples

### Example 1: Add Body Parts Translation
```json
{
    "english_text": "Hand",
    "marshallese_text": "Lima",
    "category": 5,
    "description": "The part of the body at the end of the arm",
    "is_sample": true
}
```

### Example 2: Add Symptom Translation
```json
{
    "english_text": "Headache",
    "marshallese_text": "Nana in lojet",
    "category": 4,
    "description": "Pain in the head region",
    "is_sample": true
}
```

### Example 3: Add Medication Translation
```json
{
    "english_text": "Aspirin",
    "marshallese_text": "Aapirin",
    "category": 6,
    "description": "Pain reliever and fever reducer",
    "is_sample": false
}
```

### Example 4: Add Question
```json
{
    "english_text": "How are you?",
    "marshallese_text": "Kwoj etal ippan?",
    "category": 2,
    "description": "Common greeting question",
    "is_sample": true
}
```

### Example 5: Update Translation (Change Category)
**Endpoint:** `PUT /api/administration/translations/update/1/`

```json
{
    "english_text": "Hello",
    "marshallese_text": "Iakwe",
    "category": 3,
    "description": "Updated to general category",
    "is_sample": false
}
```

---

## User Submission Changes

### POST - Submit Translation for Review
**Endpoint:** `POST /api/core/submissions/add/`

#### OLD Format:
```json
{
    "source_text": "Thank you",
    "known_translation": "Kommol tata",
    "category": "common_phrases",
    "notes": "Very common phrase"
}
```

#### NEW Format:
```json
{
    "source_text": "Thank you",
    "known_translation": "Kommol tata",
    "category": 1,
    "notes": "Very common phrase"
}
```

---

## Category Management

You can get all available categories using:

**Endpoint:** `GET /api/administration/categories/`

**Response:**
```json
{
    "count": 6,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Common Phrases",
            "slug": "common-phrases",
            "description": "Everyday phrases used in conversations",
            "created_date": "2025-12-28T10:00:00Z",
            "updated_date": "2025-12-28T10:00:00Z"
        },
        {
            "id": 2,
            "name": "Questions",
            "slug": "questions",
            "description": "Question phrases and interrogatives",
            "created_date": "2025-12-28T10:00:00Z",
            "updated_date": "2025-12-28T10:00:00Z"
        }
        // ... other categories
    ]
}
```

---

## Migration Notes

- All existing translations with `category: "common_phrases"` → `category: 1`
- All existing translations with `category: "questions"` → `category: 2`
- All existing translations with `category: "general"` → `category: 3`
- All existing translations with `category: "symptoms"` → `category: 4`
- All existing translations with `category: "body_parts"` → `category: 5`
- All existing translations with `category: "medication"` → `category: 6`

---

## Benefits of This Change

1. **Dynamic Categories:** Admin can now add/update/delete categories without code changes
2. **Referential Integrity:** Database enforces category relationships (PROTECT on delete)
3. **Better Performance:** Integer joins are faster than string comparisons
4. **Flexibility:** Category names can be changed without affecting translations
5. **Admin Control:** Categories managed via `/administration/categories/` endpoints

---

## Testing Checklist

- [ ] Test POST `/administration/translations/add/` with category ID
- [ ] Test PUT `/administration/translations/update/{id}/` with category ID  
- [ ] Verify GET `/administration/translations/` returns `category_details`
- [ ] Test POST `/core/submissions/add/` with category ID
- [ ] Verify category filtering still works
- [ ] Check admin panel displays category names correctly
- [ ] Test that invalid category ID returns error
