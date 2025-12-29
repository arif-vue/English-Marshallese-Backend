# Quick Reference: Category IDs

Use these IDs when making POST/PUT requests to translation endpoints:

## Category IDs
- **1** = Common Phrases
- **2** = Questions  
- **3** = General
- **4** = Symptoms
- **5** = Body Parts
- **6** = Medication

## POST /api/administration/translations/add/
```json
{
    "english_text": "Hello",
    "marshallese_text": "Iakwe",
    "category": 1,
    "context": "Greeting phrase"
}
```

**All Examples:**

### Common Phrases (ID: 1)
```json
{
    "english_text": "Thank you",
    "marshallese_text": "Kommol tata",
    "category": 1,
    "context": "Expression of gratitude"
}
```

### Questions (ID: 2)
```json
{
    "english_text": "How are you?",
    "marshallese_text": "Kwoj etal ippan?",
    "category": 2,
    "context": "Common greeting question"
}
```

### General (ID: 3)
```json
{
    "english_text": "Water",
    "marshallese_text": "Dren",
    "category": 3,
    "context": "Basic necessity"
}
```

### Symptoms (ID: 4)
```json
{
    "english_text": "Headache",
    "marshallese_text": "Nana in lojet",
    "category": 4,
    "context": "Pain in the head region"
}
```

### Body Parts (ID: 5)
```json
{
    "english_text": "Hand",
    "marshallese_text": "Lima",
    "category": 5,
    "context": "Part of the body at the end of the arm"
}
```

### Medication (ID: 6)
```json
{
    "english_text": "Aspirin",
    "marshallese_text": "Aapirin",
    "category": 6,
    "context": "Pain reliever and fever reducer"
}
```

## PUT /api/administration/translations/update/{id}/

Replace `{id}` with the translation ID you want to update.

**Example:** `PUT /api/administration/translations/update/1/`

```json
{
    "english_text": "Goodbye",
    "marshallese_text": "Yokwe",
    "category": 3,
    "context": "Farewell phrase - updated"
}
```

**Update Category Example:**
```json
{
    "english_text": "Hello",
    "marshallese_text": "Iakwe",
    "category": 1,
    "context": "Changed from general to common phrases"
}
```

## Changed APIs
- `POST /api/administration/translations/add/` - Use category ID
- `PUT /api/administration/translations/update/{id}/` - Use category ID

## Response Format
```json
{
    "id": 1,
    "category": 1,
    "category_details": {
        "id": 1,
        "name": "Common Phrases",
        "slug": "common-phrases"
    }
}
```

See **CATEGORY_FK_UPDATE.md** for complete documentation.
