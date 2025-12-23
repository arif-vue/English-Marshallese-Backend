# AI-Powered Translation API

## Overview
The AI-powered translation service combines database lookups with Google Gemini AI to provide high-quality English ↔ Marshallese translations with quality indicators.

## Endpoint

**POST** `/api/translations/ai-translate/`

**Authentication:** Not required (AllowAny)

---

## How It Works

### Workflow:

1. **API receives text** - Client sends text to translate
2. **Keyword extraction** - Text is cleaned and split into meaningful keywords (stop words removed)
3. **Database lookup** - For each keyword:
   - Try exact match in database (English ↔ Marshallese)
   - If not found, try fuzzy match (handles typos/similar words)
4. **Build search summary** - Results grouped into:
   - Exact matches
   - Fuzzy matches
   - Missing words
5. **LLM assistance (Gemini)** - Database findings + instructions sent to Gemini:
   - Detects input language
   - Uses exact matches first
   - Uses fuzzy matches next
   - Generates missing translations
   - Combines everything into natural sentence
6. **Parse LLM response** - JSON cleaned and parsed
7. **Determine quality & source** - Marks result as:
   - `exact_match` - All words found exactly
   - `fuzzy_match` - Found with typo corrections
   - `combined` - Mix of exact/fuzzy/generated
   - `llm_generated` - Fully AI generated
8. **Return response** - Includes translation, context, source, confidence, breakdown

---

## Request Format

```json
POST /api/translations/ai-translate/
Content-Type: application/json

{
    "text": "I have a headache"
}
```

**Parameters:**
- `text` (required): Text to translate (English or Marshallese)

---

## Response Format

```json
{
    "error": false,
    "message": "Translation completed successfully",
    "data": {
        "translation": "Im̗ōlaṃlōṃ metak in bar",
        "context": "Medical symptom - describing pain",
        "source": "combined",
        "confidence": "high",
        "details": {
            "total_keywords": 3,
            "exact_matches": 2,
            "fuzzy_matches": 0,
            "generated_words": 1,
            "breakdown": {
                "headache": {
                    "translation": "metak in bar",
                    "source": "exact",
                    "confidence": "high"
                },
                "have": {
                    "translation": "im̗ōlaṃlōṃ",
                    "source": "fuzzy",
                    "confidence": "medium"
                }
            },
            "exact_match_list": [
                {
                    "keyword": "headache",
                    "translation": "Headache ↔ Metak bar"
                }
            ],
            "fuzzy_match_list": []
        },
        "admin_review_needed": false,
        "notes": "Translation quality: high. Admin review: Not needed"
    }
}
```

---

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `translation` | string | Final translated text |
| `context` | string | Brief description of translation topic/category |
| `source` | string | Quality indicator: `exact_match`, `fuzzy_match`, `combined`, `llm_generated` |
| `confidence` | string | Confidence level: `high`, `medium`, `low` |
| `details` | object | Detailed breakdown of translation process |
| `admin_review_needed` | boolean | Whether translation needs admin verification |
| `notes` | string | Additional information about translation quality |

---

## Source Types

### 1. **exact_match** (Confidence: high)
- All keywords found exactly in database
- No AI generation needed
- Most reliable translation

**Example:**
```json
{
    "text": "headache"
}
```

### 2. **fuzzy_match** (Confidence: medium)
- Keywords found with typo correction
- Uses similarity matching (>65% threshold)
- Good reliability

**Example:**
```json
{
    "text": "hedache"  // typo of "headache"
}
```

### 3. **combined** (Confidence: medium)
- Mix of exact matches, fuzzy matches, and AI-generated words
- Most common for full sentences
- May require admin review if many generated words

**Example:**
```json
{
    "text": "I have a severe headache"
}
```

### 4. **llm_generated** (Confidence: medium/low)
- No database matches found
- Fully AI-generated translation
- Requires admin review

**Example:**
```json
{
    "text": "Can you help me with my prescription?"
}
```

---

## Examples

### Example 1: Simple Translation (Exact Match)

**Request:**
```json
POST http://10.10.12.35:8000/api/translations/ai-translate/
{
    "text": "pain"
}
```

**Response:**
```json
{
    "error": false,
    "message": "Translation completed successfully",
    "data": {
        "translation": "Metak",
        "context": "Medical symptom",
        "source": "exact_match",
        "confidence": "high",
        "details": {
            "total_keywords": 1,
            "exact_matches": 1,
            "fuzzy_matches": 0,
            "generated_words": 0,
            "breakdown": {
                "pain": {
                    "translation": "Metak",
                    "source": "exact",
                    "confidence": "high"
                }
            },
            "exact_match_list": [
                {
                    "keyword": "pain",
                    "translation": "Pain ↔ Metak"
                }
            ],
            "fuzzy_match_list": []
        },
        "admin_review_needed": false,
        "notes": "Translation quality: high. Admin review: Not needed"
    }
}
```

---

### Example 2: Sentence Translation (Combined)

**Request:**
```json
POST http://10.10.12.35:8000/api/translations/ai-translate/
{
    "text": "Where is the doctor?"
}
```

**Response:**
```json
{
    "error": false,
    "message": "Translation completed successfully",
    "data": {
        "translation": "Ej̗et taktō?",
        "context": "Medical question - asking about doctor location",
        "source": "combined",
        "confidence": "medium",
        "details": {
            "total_keywords": 2,
            "exact_matches": 1,
            "fuzzy_matches": 0,
            "generated_words": 1,
            "breakdown": {
                "doctor": {
                    "translation": "taktō",
                    "source": "exact",
                    "confidence": "high"
                },
                "where": {
                    "translation": "ej̗et",
                    "source": "generated",
                    "confidence": "medium"
                }
            },
            "exact_match_list": [
                {
                    "keyword": "doctor",
                    "translation": "doctor ↔ taktō"
                }
            ],
            "fuzzy_match_list": []
        },
        "admin_review_needed": true,
        "notes": "Translation quality: medium. Admin review: Required"
    }
}
```

---

### Example 3: Typo Correction (Fuzzy Match)

**Request:**
```json
POST http://10.10.12.35:8000/api/translations/ai-translate/
{
    "text": "hedache"  // typo
}
```

**Response:**
```json
{
    "error": false,
    "message": "Translation completed successfully",
    "data": {
        "translation": "Metak bar",
        "context": "Medical symptom (corrected from typo)",
        "source": "fuzzy_match",
        "confidence": "medium",
        "details": {
            "total_keywords": 1,
            "exact_matches": 0,
            "fuzzy_matches": 1,
            "generated_words": 0,
            "breakdown": {
                "hedache": {
                    "translation": "Metak bar",
                    "source": "fuzzy",
                    "confidence": "medium"
                }
            },
            "exact_match_list": [],
            "fuzzy_match_list": [
                {
                    "keyword": "hedache",
                    "translation": "Headache ↔ Metak bar",
                    "similarity": 0.87
                }
            ]
        },
        "admin_review_needed": false,
        "notes": "Translation quality: medium. Admin review: Not needed"
    }
}
```

---

### Example 4: Bidirectional (Marshallese to English)

**Request:**
```json
POST http://10.10.12.35:8000/api/translations/ai-translate/
{
    "text": "metak"
}
```

**Response:**
```json
{
    "error": false,
    "message": "Translation completed successfully",
    "data": {
        "translation": "Pain",
        "context": "Medical symptom",
        "source": "exact_match",
        "confidence": "high",
        "details": {
            "total_keywords": 1,
            "exact_matches": 1,
            "fuzzy_matches": 0,
            "generated_words": 0,
            "breakdown": {
                "metak": {
                    "translation": "Pain",
                    "source": "exact",
                    "confidence": "high"
                }
            },
            "exact_match_list": [
                {
                    "keyword": "metak",
                    "translation": "Pain ↔ Metak"
                }
            ],
            "fuzzy_match_list": []
        },
        "admin_review_needed": false,
        "notes": "Translation quality: high. Admin review: Not needed"
    }
}
```

---

## Error Responses

### Missing Text Field
```json
{
    "error": true,
    "message": "Text is required",
    "details": {
        "text": ["This field is required"]
    }
}
```

### API Key Not Configured
```json
{
    "error": false,
    "message": "Translation completed successfully",
    "data": {
        "translation": "input text",
        "context": "Error",
        "source": "error",
        "confidence": "low",
        "details": {},
        "admin_review_needed": true,
        "notes": "Gemini API key not configured"
    }
}
```

### Database Error
```json
{
    "error": false,
    "message": "Translation completed successfully",
    "data": {
        "translation": "input text",
        "context": "Error",
        "source": "error",
        "confidence": "low",
        "details": {},
        "admin_review_needed": true,
        "notes": "Database error: connection failed"
    }
}
```

---

## Configuration

### Environment Variables (.env)

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Django Settings (settings.py)

```python
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
```

---

## Features

✅ **Auto language detection** - Automatically detects English or Marshallese input
✅ **Database-first approach** - Prioritizes existing translations from database
✅ **Fuzzy matching** - Handles typos and similar words (65% similarity threshold)
✅ **AI fallback** - Uses Gemini AI for missing translations
✅ **Quality indicators** - Clear source and confidence levels
✅ **Admin review flags** - Marks translations needing verification
✅ **Detailed breakdown** - Shows which words are exact/fuzzy/generated
✅ **Bidirectional** - Works for both English → Marshallese and Marshallese → English

---

## Stop Words

The AI service automatically filters common words:

**English:** a, an, and, are, as, at, be, by, for, from, has, he, in, is, it, its, of, on, or, that, the, to, was, will, with, i, me, my, you, your, this, these, those, can, do, does, did, where, what, when, who, which, why, how

**Marshallese:** im, eo, ro, ji

---

## Integration with Flutter

```dart
// Example Flutter integration
Future<Map<String, dynamic>> translateWithAI(String text) async {
  final response = await http.post(
    Uri.parse('http://10.10.12.35:8000/api/translations/ai-translate/'),
    headers: {'Content-Type': 'application/json'},
    body: json.encode({'text': text}),
  );
  
  if (response.statusCode == 200) {
    return json.decode(response.body);
  } else {
    throw Exception('Translation failed');
  }
}

// Usage
void main() async {
  var result = await translateWithAI("I have a headache");
  print(result['data']['translation']);
  print("Confidence: ${result['data']['confidence']}");
  print("Admin review: ${result['data']['admin_review_needed']}");
}
```

---

## Testing with cURL

```bash
# Test English to Marshallese
curl -X POST http://10.10.12.35:8000/api/translations/ai-translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "headache"}'

# Test Marshallese to English
curl -X POST http://10.10.12.35:8000/api/translations/ai-translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "metak"}'

# Test full sentence
curl -X POST http://10.10.12.35:8000/api/translations/ai-translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "Where is the doctor?"}'

# Test typo correction
curl -X POST http://10.10.12.35:8000/api/translations/ai-translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "hedache"}'
```

---

## Performance Notes

- **Exact matches**: Fast (database lookup only)
- **Fuzzy matches**: Moderate (requires similarity calculation across all entries)
- **AI generation**: Slower (requires Gemini API call ~1-3 seconds)
- **Combined**: Variable (depends on mix of sources)

---

## Best Practices

1. **Use for natural language input** - Best for full sentences and questions
2. **Check admin_review_needed flag** - Review AI-generated translations before production use
3. **Cache results** - Store frequently used translations in your app
4. **Handle errors gracefully** - Implement fallback for API failures
5. **Monitor confidence levels** - Display confidence to users for transparency

---

## Comparison with Regular Search API

| Feature | Regular Search (`/search/`) | AI Translate (`/ai-translate/`) |
|---------|---------------------------|--------------------------------|
| Input | Single words/phrases | Full sentences |
| Output | List of matches | Single translation |
| AI Enhancement | Basic context only | Full Gemini integration |
| Typo Handling | ❌ No | ✅ Yes (fuzzy matching) |
| Quality Indicators | ❌ No | ✅ Yes (source, confidence) |
| Admin Review Flag | ❌ No | ✅ Yes |
| Word Breakdown | ❌ No | ✅ Yes |
| Speed | Fast | Moderate (with AI call) |
| Best For | Dictionary lookup | Natural conversation |
