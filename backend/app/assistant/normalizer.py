"""
Query Normalization and Spelling Correction Engine for TravelGuard AI.

Normalizes user queries and corrects obvious typos and spelling mistakes
while strictly preserving the user's travel intent.
"""

import re
from typing import Tuple, Dict

# Common travel-specific spelling corrections
SPELLING_CORRECTIONS: Dict[str, str] = {
    # Transport & choices
    "chhoose": "choose",
    "chhose": "choose",
    "choos": "choose",
    "traain": "train",
    "trian": "train",
    "buus": "bus",
    "buss": "bus",
    "flite": "flight",
    "fligt": "flight",
    "vehical": "vehicle",
    "vechile": "vehicle",
    "whitch": "which",
    "wich": "which",
    "prefere": "prefer",
    "recomended": "recommended",
    "reccomend": "recommend",
    "recomend": "recommend",
    
    # Food & dining
    "restrurant": "restaurant",
    "restuarant": "restaurant",
    "resturant": "restaurant",
    "restraunt": "restaurant",
    "restaraunt": "restaurant",
    "resturent": "restaurant",
    "restro": "restaurant",
    "restros": "restaurants",
    "resturants": "restaurants",
    "restaurnts": "restaurants",
    "cafee": "cafe",
    "hotle": "hotel",
    "hotell": "hotel",
    "hotles": "hotels",
    "hotls": "hotels",
    
    # Travel & transport
    "trafic": "traffic",
    "traffick": "traffic",
    "traffik": "traffic",
    "routs": "routes",
    "rout": "route",
    "itinirary": "itinerary",
    "itinary": "itinerary",
    "itnery": "itinerary",
    "itenerary": "itinerary",
    "itiniary": "itinerary",
    "distence": "distance",
    "distanse": "distance",
    "ditance": "distance",
    
    # Timing
    "tommorow": "tomorrow",
    "tommorrow": "tomorrow",
    "tomorow": "tomorrow",
    "tmrw": "tomorrow",
    "2moro": "tomorrow",
    "tomo": "tomorrow",
    "yesturday": "yesterday",
    
    # Sightseeing & safety
    "plases": "places",
    "placess": "places",
    "placs": "places",
    "atraction": "attraction",
    "attractions": "attractions",
    "attarction": "attraction",
    "attarctions": "attractions",
    "sigthseeing": "sightseeing",
    "sightseing": "sightseeing",
    "neraby": "nearby",
    "nerby": "nearby",
    "safty": "safety",
    "saftey": "safety",
    "landslid": "landslide",
    "land slides": "landslides",
    "disastor": "disaster",
    "flod": "flood",
    "flods": "floods",
    "wheather": "weather",
    "wether": "weather",
    "weater": "weather",
    
    # Specific known destination corrections
    "mathren": "matheran",
    "matharan": "matheran",
    "mathern": "matheran",
    "mathearan": "matheran",
    "nasik": "nashik",
    "lonawala": "lonavala",
    "lonavla": "lonavala",
    "khandala": "khandala",
    "mumbay": "mumbai",
    "bombay": "mumbai",
    "delhy": "delhi",
    "bengluru": "bengaluru",
    "banglore": "bangalore",
}

# Regex replacements for common phrasing slip-ups without altering intent
PHRASE_PATTERNS = [
    # "which thing i choose" -> "which should i choose"
    (r"\bwhich\s+thing\s+i\s+(?:choose|chhoose)\b", "which should i choose"),
    # "how i can go matheran form nashik" -> "how can i go to matheran from nashik"
    (r"\bhow\s+i\s+can\s+go\s+(?:to\s+)?([a-zA-Z\s]+?)\s+form\s+([a-zA-Z\s]+)", r"how can i go to \1 from \2"),
    # "how can i go [place] from [place]" missing "to"
    (r"\bhow\s+can\s+i\s+go\s+([a-zA-Z]+)\s+from\s+([a-zA-Z]+)", r"how can i go to \1 from \2"),
    # "how to go [place] from [place]" missing "to"
    (r"\bhow\s+to\s+go\s+([a-zA-Z]+)\s+from\s+([a-zA-Z]+)", r"how to go to \1 from \2"),
    # "form [place]" -> "from [place]"
    (r"\bform\s+([a-zA-Z]+)", r"from \1"),
    # "near by" -> "nearby"
    (r"\bnear\s+by\b", "nearby"),
]

def normalize_query(query: str) -> Tuple[str, Dict[str, str]]:
    """
    Normalizes a user query by fixing obvious spelling mistakes,
    common typos, and grammatical transposition while keeping intent intact.
    
    Returns:
        (normalized_query, dict_of_corrections_made)
    """
    if not query:
        return "", {}
        
    original = query.strip()
    corrected = original
    corrections = {}
    
    # 1. Apply multi-word phrase patterns
    for pattern, replacement in PHRASE_PATTERNS:
        new_text = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        if new_text.lower() != corrected.lower():
            corrected = new_text

    # 2. Token-level spelling correction
    tokens = re.findall(r"[\w]+|[^\w\s]", corrected)
    rebuilt_tokens = []
    
    for token in tokens:
        lower_token = token.lower()
        if lower_token in SPELLING_CORRECTIONS:
            replacement = SPELLING_CORRECTIONS[lower_token]
            if token.isupper():
                replacement = replacement.upper()
            elif token.istitle():
                replacement = replacement.title()
            corrections[token] = replacement
            rebuilt_tokens.append(replacement)
        else:
            rebuilt_tokens.append(token)
            
    # Reassemble tokens with sensible spacing
    normalized = ""
    for idx, t in enumerate(rebuilt_tokens):
        if idx == 0 or re.match(r"[^\w\s]", t):
            normalized += t
        else:
            normalized += " " + t
            
    return normalized.strip(), corrections
