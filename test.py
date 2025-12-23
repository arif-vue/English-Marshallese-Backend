from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import google.generativeai as genai
import sqlite3
from pathlib import Path
from difflib import SequenceMatcher

# -----------------------------
# Database Configuration
# -------------------------------------------------------
DB_PATH = "/home/iamsmsr/Desktop/JVAI/lily/translations.db"

# Configure Gemini API
# -------------------------------------------------------
GEMINI_API_KEY = "AIzaSyAshE9cGFdqBVNLi7dVv9bvZ7QgkBPdDH0"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="English-Marshallese Translation API")

# -----------------------------
# Request & Response Models
# -----------------------------
class TranslationRequest(BaseModel):
    text: str

class TranslationResponse(BaseModel):
    translation: str
    context: str  # What the translation is about
    source: str  # "exact_match", "fuzzy_match", "combined", "llm_generated"
    confidence: str = "medium"
    details: Dict = {}  # Breakdown of which parts are exact/fuzzy/generated
    admin_review_needed: bool = False  # Flag for admin review
    notes: str = ""

# -----------------------------
# Actual functions that will be called based on model's suggestion
# -------------------------------------------------------
def extract_keywords(text: str) -> list:
    """Extract meaningful keywords from text, removing common words.
    Supports both English and Marshallese.
    
    Args:
        text: Input text to extract keywords from
    
    Returns:
        List of keywords
    """
    # Common English words to ignore
    english_stop_words = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that',
        'the', 'to', 'was', 'will', 'with', 'i', 'me', 'my', 'you', 'your',
        'this', 'these', 'those', 'can', 'do', 'does', 'did', 'where', 'what',
        'when', 'who', 'which', 'why', 'how'
    }
    
    # Common Marshallese stop words (if any)
    marshallese_stop_words = {
        'im', 'eo', 'ro', 'ji'  # Common Marshallese words
    }
    
    all_stop_words = english_stop_words | marshallese_stop_words
    
    # Split into words and filter
    words = text.lower().split()
    keywords = [w.strip('.,!?;:—-') for w in words if w.lower().strip('.,!?;:—-') not in all_stop_words and len(w.strip('.,!?;:—-')) > 0]
    return keywords

def fuzzy_match(query: str, target: str, threshold: float = 0.8) -> tuple:
    """Calculate fuzzy match similarity between two strings.
    
    Args:
        query: User input string
        target: Database string to compare
        threshold: Minimum similarity score (0-1)
    
    Returns:
        Tuple of (is_match, similarity_score)
    """
    query_lower = query.lower().strip()
    target_lower = target.lower().strip()
    
    # Calculate similarity ratio
    similarity = SequenceMatcher(None, query_lower, target_lower).ratio()
    
    return (similarity >= threshold, similarity)

def search_by_fuzzy(keyword: str, cursor, limit: int = 3) -> list:
    """Search database using fuzzy matching for typos and partial matches (bidirectional).
    Works for both English and Marshallese keywords.
    
    Args:
        keyword: Keyword to search with fuzzy matching
        cursor: Database cursor
        limit: Number of results to return
    
    Returns:
        List of fuzzy matched results
    """
    # Get all entries (for client-side fuzzy matching)
    cursor.execute('''
        SELECT marshallese_text, category, usage_count, english_text
        FROM translations 
        ORDER BY usage_count DESC
    ''')
    
    all_entries = cursor.fetchall()
    fuzzy_results = []
    
    # Fuzzy match against both English and Marshallese
    for entry in all_entries:
        english_text = entry[3]
        marshallese_text = entry[0]
        
        # Check similarity with English text
        is_match_eng, similarity_eng = fuzzy_match(keyword, english_text, threshold=0.65)
        
        # Check similarity with Marshallese text
        is_match_mar, similarity_mar = fuzzy_match(keyword, marshallese_text, threshold=0.65)
        
        # Use highest similarity
        best_similarity = max(similarity_eng, similarity_mar)
        is_match = is_match_eng or is_match_mar
        
        if is_match:
            fuzzy_results.append({
                "match": english_text if similarity_eng >= similarity_mar else marshallese_text,
                "english": english_text,
                "marshallese": marshallese_text,
                "category": entry[1],
                "usage_count": entry[2],
                "similarity": round(best_similarity, 2),
                "match_type": "fuzzy"
            })
    
    # Sort by similarity and return top results
    fuzzy_results.sort(key=lambda x: x["similarity"], reverse=True)
    return fuzzy_results[:limit]

def search_translation_db(query_text: str) -> dict:
    """Search translation database with simple workflow.
    
    Workflow:
    1. Extract keywords from input
    2. Try exact match on each keyword
    3. Try fuzzy match on remaining keywords (for typos)
    4. Return complete findings to LLM
    
    Args:
        query_text: The text to search for in the translation database
    
    Returns:
        A dictionary with exact_matches, fuzzy_matches, and keywords info
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Step 1: Extract keywords from input
        keywords = extract_keywords(query_text)
        if not keywords:
            keywords = [query_text]
        
        print(f"[DEBUG] Keywords: {keywords}")
        
        # Step 2: Try exact match on each keyword
        exact_matches = []
        keywords_for_fuzzy = []
        
        for keyword in keywords:
            cursor.execute('''
                SELECT marshallese_text, category, usage_count, english_text
                FROM translations 
                WHERE LOWER(english_text) = LOWER(?) 
                   OR LOWER(marshallese_text) = LOWER(?)
                LIMIT 1
            ''', (keyword, keyword))
            
            result = cursor.fetchone()
            if result:
                print(f"[DEBUG] Exact match for '{keyword}': {result[3]} ↔ {result[0]}")
                exact_matches.append({
                    "keyword": keyword,
                    "english": result[3],
                    "marshallese": result[0],
                    "category": result[1],
                    "match_type": "exact"
                })
            else:
                print(f"[DEBUG] No exact match for '{keyword}', adding to fuzzy search")
                keywords_for_fuzzy.append(keyword)
        
        # Step 3: Try fuzzy match for keywords without exact match (typos/similar)
        fuzzy_matches = []
        for keyword in keywords_for_fuzzy:
            fuzzy_results = search_by_fuzzy(keyword, cursor, limit=1)  # Get best match only
            if fuzzy_results:
                best_match = fuzzy_results[0]
                print(f"[DEBUG] Fuzzy match for '{keyword}': {best_match['english']} ↔ {best_match['marshallese']} (similarity: {best_match['similarity']})")
                fuzzy_matches.append({
                    "keyword": keyword,
                    "english": best_match["english"],
                    "marshallese": best_match["marshallese"],
                    "category": best_match["category"],
                    "similarity": best_match["similarity"],
                    "match_type": "fuzzy"
                })
            else:
                print(f"[DEBUG] No fuzzy match for '{keyword}'")
        
        conn.close()
        
        # Return findings for LLM
        return {
            "original_query": query_text,
            "keywords": keywords,
            "exact_matches": exact_matches,
            "fuzzy_matches": fuzzy_matches,
            "total_keywords": len(keywords),
            "exact_count": len(exact_matches),
            "fuzzy_count": len(fuzzy_matches),
            "not_found_count": len(keywords) - len(exact_matches) - len(fuzzy_matches)
        }
        
    except Exception as e:
        print(f"Database error: {e}")
        return {"error": str(e)}

# -----------------------------
# Translation Endpoint
# -----------------------------
@app.post("/translate", response_model=TranslationResponse)
def translate(req: TranslationRequest):
    user_text = req.text
    
    # Step 1: Extract keywords
    keywords = extract_keywords(user_text)
    if not keywords:
        keywords = [user_text]
    
    # Step 2: Search database (exact + fuzzy)
    search_results = search_translation_db(user_text)
    
    if "error" in search_results:
        return TranslationResponse(
            translation=user_text,
            source="error",
            match_type="error",
            needs_review=True,
            confidence="low",
            notes=f"Database error: {search_results['error']}"
        )
    
    # Step 3: Send findings to LLM with clear instructions
    exact_matches = search_results.get("exact_matches", [])
    fuzzy_matches = search_results.get("fuzzy_matches", [])
    not_found_count = search_results.get("not_found_count", 0)
    
    # Build context for LLM
    context = f"""Input: "{user_text}"
Keywords extracted: {keywords}

DATABASE SEARCH RESULTS:

EXACT MATCHES ({len(exact_matches)}):
"""
    
    for match in exact_matches:
        context += f"- '{match['keyword']}' → English: '{match['english']}' | Marshallese: '{match['marshallese']}'\n"
    
    context += f"\nFUZZY MATCHES ({len(fuzzy_matches)}) [for typos/similar words]:\n"
    for match in fuzzy_matches:
        context += f"- '{match['keyword']}' → English: '{match['english']}' | Marshallese: '{match['marshallese']}' (similarity: {match['similarity']})\n"
    
    if not_found_count > 0:
        context += f"\nKEYWORDS NOT FOUND: {not_found_count} (generate these using your knowledge)\n"
    
    context += """
INSTRUCTIONS:
1. Auto-detect input language (English or Marshallese)
2. Use exact matches as-is (highest priority)
3. Use fuzzy matches for typos (medium priority) 
4. Generate missing translations (lowest priority)
5. Combine all into one natural sentence in target language

Return in this EXACT JSON format:
{
  "translation": "the final clean translation",
  "context": "brief description of what this translation is about (topic/category)",
  "word_breakdown": {
    "word1": {"translation": "...", "source": "exact|fuzzy|generated", "confidence": "high|medium|low"},
    "word2": {"translation": "...", "source": "exact|fuzzy|generated", "confidence": "high|medium|low"}
  }
}"""

    # Step 4: Send to LLM
    response = model.generate_content(context)
    
    # Step 5: Parse LLM response and extract clean translation
    llm_text = response.text if response.text else "{}"
    
    try:
        import json
        import re
        
        # Clean up the response - remove markdown code blocks if present
        cleaned_text = llm_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = re.sub(r'^```json\s*', '', cleaned_text)
            cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
        elif cleaned_text.startswith("```"):
            cleaned_text = re.sub(r'^```\s*', '', cleaned_text)
            cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
        
        # Try to parse JSON response from LLM
        llm_response = json.loads(cleaned_text)
        translation = llm_response.get("translation", user_text)
        context_desc = llm_response.get("context", "Translation")
        word_breakdown = llm_response.get("word_breakdown", {})
    except:
        # Fallback: try to extract just the translation part
        try:
            # Look for translation field in the text
            match = re.search(r'"translation":\s*"([^"]+)"', llm_text)
            if match:
                translation = match.group(1)
            else:
                translation = llm_text.strip()
            context_desc = "Translation"
            word_breakdown = {}
        except:
            translation = user_text
            context_desc = "Translation"
            word_breakdown = {}
    
    # Step 6: Determine source, confidence, and admin flag
    if len(exact_matches) == len(keywords):
        source = "exact_match"
        confidence = "high"
        admin_review = False
    elif len(fuzzy_matches) > 0 and not_found_count == 0:
        source = "fuzzy_match"
        confidence = "medium"
        admin_review = False
    elif len(exact_matches) > 0 or len(fuzzy_matches) > 0:
        source = "combined"
        confidence = "medium"
        admin_review = True if not_found_count > 0 else False
    else:
        source = "llm_generated"
        confidence = "medium"
        admin_review = True
    
    # Build detailed breakdown
    details = {
        "total_keywords": len(keywords),
        "exact_matches": len(exact_matches),
        "fuzzy_matches": len(fuzzy_matches),
        "generated_words": not_found_count,
        "breakdown": word_breakdown,
        "exact_match_list": [{"keyword": m["keyword"], "translation": f"{m['english']} ↔ {m['marshallese']}"} for m in exact_matches],
        "fuzzy_match_list": [{"keyword": m["keyword"], "translation": f"{m['english']} ↔ {m['marshallese']}", "similarity": m["similarity"]} for m in fuzzy_matches]
    }
    
    return TranslationResponse(
        translation=translation,
        context=context_desc,
        source=source,
        confidence=confidence,
        details=details,
        admin_review_needed=admin_review,
        notes=f"Translation quality: {confidence}. Admin review: {'Required' if admin_review else 'Not needed'}"
    )
