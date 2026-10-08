"""
AI-powered Smart Issue Classifier for CampusFix
Analyzes campus issue descriptions & titles to automatically extract and suggest:
- Department / Category
- Priority Level (Low, Medium, High, Urgent)
- Location Entity (Room, Floor, Block, Lab, Campus zone)
- Confidence score & Human-readable reasoning

Works 100% offline with zero external API key requirements.
"""

import re

# Department keywords & semantic weights
DEPARTMENT_RULES = {
    "Facilities & Maintenance": {
        "keywords": [
            "leak", "leaking", "pipe", "plumbing", "dripping", "water drop", "tap", "faucet", "sink",
            "roof", "ceiling", "seepage", "chair", "table", "desk", "bench", "door", "window",
            "glass", "hinge", "tile", "wall", "paint", "crack", "ac", "air conditioner", "hvac",
            "cooling", "air condition", "ventilation", "elevator", "lift", "furniture", "drain",
            "drainage", "flush", "carpenter", "masonry", "handrail", "lock", "whiteboard", "blackboard"
        ],
        "weight": 1.2
    },
    "IT Support": {
        "keywords": [
            "wifi", "wi-fi", "internet", "network", "lan", "ethernet", "router", "signal",
            "projector", "hdmi", "vga", "display", "screen", "monitor", "audio", "speaker",
            "mic", "microphone", "sound", "computer", "pc", "laptop", "keyboard", "mouse",
            "printer", "scanner", "lab pc", "lab computer", "software", "portal", "login",
            "password", "server", "canvas", "moodle", "cable", "av", "dongle", "system crash"
        ],
        "weight": 1.3
    },
    "Electrical Services": {
        "keywords": [
            "light", "tube light", "bulb", "led", "streetlight", "floodlight", "flicker", "flickering",
            "dark", "power", "electricity", "spark", "sparks", "sparking", "short circuit", "wiring",
            "wire", "socket", "plug", "power outlet", "switch", "switchboard", "mcb", "tripping", "tripped",
            "voltage", "fluctuation", "blackout", "power cut", "shock", "fuse", "fan", "exhaust fan",
            "geyser element", "generator", "electrical panel"
        ],
        "weight": 1.25
    },
    "Sanitation & Hygiene": {
        "keywords": [
            "toilet", "restroom", "washroom", "urinal", "smell", "stink", "odor", "dirty",
            "dustbin", "garbage", "trash", "waste", "water dispenser", "drinking water", "purifier",
            "water purifier", "ro water", "dispenser", "cleanliness", "unhygienic", "pest",
            "cockroach", "insect", "mosquito", "rodent", "sewage", "soap", "sanitizer", "overflow"
        ],
        "weight": 1.3
    },
    "Campus Security": {
        "keywords": [
            "theft", "stolen", "lost", "missing", "bag stolen", "laptop stolen", "guard",
            "security", "cctv", "camera", "gate", "main gate", "trespass", "unauthorized",
            "fight", "harassment", "emergency exit", "fire exit", "exit door", "fire extinguisher",
            "smoke detector", "alarm", "siren", "locked out", "intruder", "safety hazard",
            "threat", "vandalism", "patrol"
        ],
        "weight": 1.35
    },
    "Hostel Administration": {
        "keywords": [
            "hostel", "dorm", "dormitory", "hostel room", "roommate", "warden", "girls hostel",
            "boys hostel", "hostel block", "mess", "dining", "canteen food", "food quality",
            "mess food", "geyser", "hot water", "bed", "mattress", "cupboard", "almirah",
            "laundry", "washing machine", "curfew", "in-time", "hostel gate", "hostel warden"
        ],
        "weight": 1.2
    }
}

# --- Dynamic Priority Rules ---
# High = safety hazards, exposed wires, water leakage, fire hazards, or major urgent failures.
HIGH_PRIORITY_RULES = [
    # Safety hazards
    (r'\b(?:safety\s+hazard|hazardous|danger(?:ous)?|severe\s+hazard|life\s+safety|injury|injured|hurt|collapse|falling\s+debris|fall\s+risk|slip\s+hazard|slippery\s+hazard|trip\s+hazard|chemical\s+leak|gas\s+leak|toxic|poisonous)\b',
     "safety hazard"),
    # Exposed wires & electrical hazards
    (r'\b(?:exposed\s+wires?|open\s+wires?|naked\s+wires?|hanging\s+wires?|live\s+wires?|electric\s+shock|shock|sparks?|sparking|short\s+circuit|wire\s+burning|outlet\s+smoking|socket\s+spark(?:ing|s)?)\b',
     "exposed wires / electrical hazard"),
    # Water leakage
    (r'\b(?:water\s+leak(?:age|ing|s)?|leaking\s+water|water\s+dripping|pipe\s+leak(?:age|ing)?|pipe\s+burst|burst\s+pipe|flooding?|water\s+overflowing?|ceiling\s+leak(?:ing|age)?|roof\s+leak(?:ing|age)?|seepage|water\s+seepage|leak(?:ing|age)?|dripping)\b',
     "water leakage"),
    # Fire hazards
    (r'\b(?:fire\s+hazard|fire|smoke|smoking|flames?|burning\s+smell|burnt|burning|fire\s+alarm|fire\s+extinguisher\s+discharged|explosion)\b',
     "fire hazard"),
    # Major urgent failures
    (r'\b(?:emergency(?:\s+exit)?|stuck\s+in\s+(?:lift|elevator)|elevator\s+stuck|lift\s+stuck|exit\s+(?:blocked|jammed)|door\s+jammed\s+shut|evacuation|total\s+blackout|complete\s+power\s+failure|water\s+supply\s+cut|no\s+drinking\s+water|critical\s+failure|urgent\s+failure|severe\s+outage)\b',
     "major urgent failure")
]

# Low = cleaning requests, cosmetic problems, and minor non-urgent issues.
LOW_PRIORITY_RULES = [
    # Cleaning requests
    (r'\b(?:clean(?:ing)?\s+request|needs?\s+clean(?:ing)?|please\s+clean|clean\s+up|sweep(?:ing)?|mop(?:ping)?|dust(?:ing)?|vacuum(?:ing)?|dustbin\s+full|trash\s+can\s+full|empty\s+(?:the\s+)?(?:trash|bin|dustbin)|garbage|trash|litter|waste\s+scattered|dirty\s+(?:floor|desk|bench|table|washroom|toilet|restroom)|refill\s+(?:soap|sanitizer|tissue|towel)|soap\s+dispenser\s+empty|whiteboard\s+dirty|clean\s+(?:whiteboard|blackboard)|bad\s+smell|odor|stink|stinky)\b',
     "cleaning request"),
    # Cosmetic problems
    (r'\b(?:cosmetic|aesthetic|paint\s+(?:peeled?|peeling|chipped?|faded?)|peeling\s+paint|scratch(?:ed)?|scuff(?:ed)?|small\s+dent|stain(?:ed)?|notice\s+board\s+torn|poster\s+torn|curtain\s+loose|blinds\s+stuck|loose\s+(?:knob|handle|screw)|drawer\s+handle|clock\s+battery|wall\s+clock\s+stopped)\b',
     "cosmetic problem"),
    # Minor non-urgent issues
    (r'\b(?:minor\s+(?:issue|problem|nuisance|concern)|slightly|small\s+issue|not\s+urgent|low\s+priority|suggestion|enhancement|feedback|dim\s+lighting|slightly\s+loose|squeaky\s+door)\b',
     "minor non-urgent issue")
]

# Medium = broken projector, fan, light, computer, Wi-Fi, or similar normal equipment problems.
MEDIUM_PRIORITY_RULES = [
    (r'\b(?:projector|hdmi|vga|screen|display|audio|speaker|mic(?:rophone)?|sound\s+system)\b',
     "broken projector / AV problem"),
    (r'\b(?:fan|ceiling\s+fan|exhaust\s+fan)\b',
     "fan problem"),
    (r'\b(?:light|tube\s*light|bulb|led|lamp|flicker(?:ing)?|blinking\s+light)\b',
     "light problem"),
    (r'\b(?:computer|pc|monitor|keyboard|mouse|printer|scanner|cpu|desktop)\b',
     "computer problem"),
    (r'\b(?:wi-?fi|internet|network|lan|ethernet|router|connection\s+drop)\b',
     "Wi-Fi / network problem"),
    (r'\b(?:ac|air\s+condition(?:er)?|cooler|cooling\s+not\s+working|ac\s+remote)\b',
     "AC problem"),
    (r'\b(?:broken\s+chair|broken\s+table|broken\s+desk|broken\s+bench|wobbly\s+chair)\b',
     "furniture problem"),
    (r'\b(?:door\s+lock|lock\s+broken|padlock|door\s+handle|window\s+latch)\b',
     "door / lock problem"),
    (r'\b(?:geyser|water\s+heater|dispenser\s+not\s+working|water\s+dispenser\s+not\s+dispensing)\b',
     "dispenser / appliance problem"),
    (r'\b(?:broken|damaged|not\s+working|faulty|defect(?:ive)?|malfunction(?:ing)?|stopped\s+working)\b',
     "equipment problem")
]

def determine_priority(text):
    """
    Dynamically analyzes text to determine priority:
    - High: safety hazards, exposed wires, water leakage, fire hazards, or major urgent failures.
    - Low: cleaning requests, cosmetic problems, and minor non-urgent issues.
    - Medium: broken projector, fan, light, computer, Wi-Fi, or similar normal equipment problems.
    - Fallback: Medium if unclear.
    """
    t = text.lower()

    # 1. HIGH: Safety hazards, exposed wires, water leakage, fire hazards, or major urgent failures
    # Wires & Electrical
    has_wire = bool(re.search(r'\b(?:wire|wires|cable|cables|cord|cords|switchboard|socket|plug|outlet)\b', t))
    has_wire_hazard = bool(re.search(r'\b(?:exposed|naked|bare|open|hanging|live|spark|sparks|sparking|shock|shocks|shocked|burnt|burning|smoke|smoking|melted|melting)\b', t))
    if has_wire and has_wire_hazard:
        return 'High', 'Exposed wires / electrical hazard'
    if re.search(r'\b(?:electric\s+shock|electrical\s+shock|shock|shocks|shocked|short\s+circuit|spark|sparks|sparking|electrocution|electrocuted)\b', t):
        return 'High', 'Electrical spark / shock hazard'

    # Water leakage & Flooding (covers leaks, bursts, overflows, flood, drips, seepage)
    if re.search(r'\b(?:leak|leaks|leaking|leakage|drip|drips|dripping|burst|bursts|bursting|flood|floods|flooding|flooded|overflow|overflows|overflowing|overflowed|seep|seeps|seepage|seeping)\b', t):
        return 'High', 'Water leakage / flooding hazard'

    # Fire hazards
    if re.search(r'\b(?:fire|fires|smoke|smoking|smoky|flame|flames|blaze|burning|burnt|burns|explosion|explode|exploding|fire\s+hazard|fire\s+alarm)\b', t):
        return 'High', 'Fire / smoke hazard'

    # Safety hazards
    if re.search(r'\b(?:safety\s+hazard|hazard|hazardous|hazards|danger|dangerous|injury|injuries|injured|hurt|hurting|collapse|collapsed|collapsing|fall\s+risk|slip\s+hazard|trip\s+hazard|slippery|chemical\s+spill|chemical|gas\s+leak|poison|poisonous|toxic|fumes|acid)\b', t):
        return 'High', 'Critical safety hazard'

    # Major urgent failures & Entrapment
    has_wide_scope = re.search(r'\b(?:entire|whole|all|building-wide|campus-wide)\s+(?:class(?:room|e)?s?|building|floor|campus)\b', t)
    has_service_disruption = re.search(r'\b(?:outage|failure|unavailable|down|disrupted|interruption|stopped|no\s+(?:power|electricity|water|internet|wi-?fi|network|service|access))\b', t)
    if has_wide_scope and has_service_disruption:
        return 'High', 'Major outage affecting an entire class / building'
    if re.search(r'\b(?:emergency|urgent|critical|evacuate|evacuation|disaster|blackout|power\s+outage|power\s+failure|water\s+cut|no\s+water|no\s+drinking\s+water)\b', t):
        return 'High', 'Major urgent failure'
    if re.search(r'\b(?:lift|elevator)\b', t) and re.search(r'\b(?:stuck|trapped|fallen|jammed|not\s+opening|broken\s+down)\b', t):
        return 'High', 'Elevator entrapment / failure'
    if re.search(r'\b(?:exit|door)\b', t) and re.search(r'\b(?:locked|blocked|jammed|shut|cannot\s+open)\b', t) and re.search(r'\b(?:emergency|urgent|fire|danger|trapped)\b', t):
        return 'High', 'Emergency exit blocked'

    # 2. LOW: Cleaning requests, cosmetic problems, and minor non-urgent issues
    # Cleaning requests
    if re.search(r'\b(?:clean|cleaning|cleaned|cleaner|cleanliness|sweep|sweeping|swept|mop|mopping|mopped|dust|dusting|vacuum|vacuuming|dustbin|trash|trashcan|garbage|litter|waste|dirty|mess|messy|stain|stains|stained|smell|smelly|stink|stinking|stinky|odor|odour|hygiene|unhygienic|soap|sanitizer|tissue|tissues|paper\s+towel)\b', t):
        return 'Low', 'Cleaning / custodial request'

    # Cosmetic problems
    if re.search(r'\b(?:cosmetic|aesthetic|paint|peel|peeling|peeled|chip|chipping|chipped|scratch|scratched|scratches|scuff|scuffed|dent|dented|faded|fading|discolor|discolored|poster|notice\s+board|bulletin|torn|ripped|curtain|blinds|clock|battery)\b', t):
        return 'Low', 'Cosmetic / aesthetic problem'

    # Minor non-urgent issues
    if re.search(r'\b(?:minor|slight|slightly|small\s+issue|not\s+urgent|non-urgent|low\s+priority|suggestion|feedback|preference|dim|squeak|squeaky)\b', t):
        return 'Low', 'Minor non-urgent issue'

    # 3. MEDIUM: Normal equipment (projector, fan, light, computer, wi-fi) or unclear fallback
    if re.search(r'\b(?:projector|hdmi|vga|screen|display|audio|sound|speaker|mic|microphone|fan|ceiling\s+fan|exhaust\s+fan|light|tube\s*light|tubelight|bulb|led|lamp|flicker|flickering|blinking|computer|pc|laptop|monitor|keyboard|mouse|printer|scanner|cpu|software|portal|login|wifi|wi-fi|internet|network|lan|ethernet|connection|router|hotspot|signal|ac|air\s+conditioner|cooler|chair|desk|bench|table|door\s+lock|lock|key|water\s+dispenser|purifier|geyser|broken|not\s+working|damaged|faulty|defect|malfunction|stopped\s+working|cannot\s+connect)\b', t):
        return 'Medium', 'Normal equipment problem'

    for pattern, reason in HIGH_PRIORITY_RULES:
        if re.search(pattern, t):
            return 'High', reason

    for pattern, reason in LOW_PRIORITY_RULES:
        if re.search(pattern, t):
            return 'Low', reason

    for pattern, reason in MEDIUM_PRIORITY_RULES:
        if re.search(pattern, t):
            return 'Medium', reason

    return 'Medium', 'Standard issue / unclear context'

# Targeted Campus location extractors (ordered from most specific to general)
LOCATION_REGEXES = [
    # E.g. "Central Library, 2nd Floor Study Room 204" or "Central Library, 2nd Floor"
    r'\b(?:Central\s+)?Library(?:,\s*\d+(?:st|nd|rd|th)?\s+Floor)?(?:[,\s]+(?:Study\s+Room|Study\s+Wing|Room)\s*\d+)?\b',
    # E.g. "Turing Block, Lab 302" or "Admin Block, Room 104"
    r'\b[A-Za-z0-9]+\s+Block[,\s]+(?:Lab|Room|Seminar\s+Hall|Hall)\s*\d+\b',
    # E.g. "Block B, 3rd Floor" or "Hostel Block A, Ground Floor"
    r'\bBlock\s+[A-Za-z0-9]+[,\s]+\d+(?:st|nd|rd|th)?\s+Floor\b',
    # E.g. "Hostel Block B, 1st Floor Common Area" or "Hostel Block B, 1st Floor"
    r'\bHostel\s+Block\s+[A-Za-z0-9]+(?:[,\s]+\d+(?:st|nd|rd|th)?\s+Floor)?(?:[,\s]+(?:Common\s+Area|Lounge|Room\s*\d+))?\b',
    # E.g. "Girls Hostel, Room 12" or "Block B Girls Hostel"
    r'\b(?:Block\s+[A-Za-z0-9]+\s+)?(?:Girls|Boys)\s+Hostel(?:[,\s]+(?:Room\s*\d+|\d+(?:st|nd|rd|th)?\s+Floor))?\b',
    # E.g. "Chemistry Annex Ground Floor" or "Science Complex, Chemistry Annex"
    r'\b(?:Science\s+Complex[,\s]+)?Chemistry\s+Annex(?:\s+(?:Ground|\d+(?:st|nd|rd|th)?)\s+Floor)?\b',
    # E.g. "CS Lab 3", "Chemistry Lab 2", "Seminar Hall 1", "Room 402"
    r'\b(?:CS|ECE|Mech|Chemistry|Physics|Civil|Bio|AI|AV)?\s*(?:Lab|Room|Seminar\s+Hall|Classroom)\s*\d+\b',
    # E.g. "Main Quadrangle, East Walkway" or "Main Quadrangle"
    r'\bMain\s+Quadrangle(?:[,\s]+(?:East|West|North|South)?\s*Walkway)?\b',
    # E.g. "Auditorium, Main Stage" or "Auditorium"
    r'\bAuditorium(?:[,\s]+(?:Main\s+Stage|Front\s+Entrance))?\b',
    # Generic campus landmarks
    r'\b(?:Main\s+Gate|Sports\s+Complex|Cafeteria|Canteen|University\s+Gym)\b'
]


def extract_location(text):
    """Extract campus location mention from text with clean boundaries."""
    for pattern in LOCATION_REGEXES:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted = match.group(0).strip()
            # Clean up excessive punctuation
            extracted = extracted.rstrip(',;.')
            if len(extracted) >= 3:
                return extracted

    # Fallback contextual extraction for "in <Location>" or "at <Location>"
    fallback_match = re.search(r'\b(?:in|at)\s+([A-Z][a-zA-Z0-9\s]{2,30}?(?:Lab|Room|Hall|Block|Library|Wing|Floor|Annex|Complex))\b', text)
    if fallback_match:
        return fallback_match.group(1).strip()

    return ""


def classify_issue(description, title=""):
    """
    Classifies campus issue description and title.
    Returns:
    {
        "suggested_department": str,
        "suggested_priority": str,
        "suggested_location": str,
        "confidence": int (0-100),
        "reasoning": str,
        "matched_keywords": list
    }
    """
    full_text = f"{title} {description}".lower()
    
    # 1. Department Matching
    dept_scores = {}
    dept_matches = {}

    for dept, info in DEPARTMENT_RULES.items():
        score = 0
        matches = []
        for kw in info["keywords"]:
            pattern = r'\b' + re.escape(kw) + r'\b'
            count = len(re.findall(pattern, full_text))
            if count > 0:
                score += count * info["weight"]
                matches.append(kw)
        
        dept_scores[dept] = score
        dept_matches[dept] = matches

    # Choose top department
    sorted_depts = sorted(dept_scores.items(), key=lambda x: x[1], reverse=True)
    best_dept, best_score = sorted_depts[0]
    matched_kws = dept_matches.get(best_dept, [])

    if best_score > 0:
        confidence = min(98, int(74 + (best_score * 6.5)))
    else:
        best_dept = "Facilities & Maintenance"
        confidence = 60
        matched_kws = []

    # 2. Dynamic Priority Matching
    priority, priority_reason = determine_priority(full_text)

    # 3. Location Extraction
    location = extract_location(f"{title} {description}")

    # 4. Generate Reasoning
    if matched_kws:
        kw_sample = ", ".join([f"'{k}'" for k in matched_kws[:3]])
        reasoning = f"Matched {best_dept} keywords: {kw_sample}. Priority set to {priority} ({priority_reason})."
    else:
        reasoning = f"Categorized as {best_dept} based on campus context. Priority set to {priority} ({priority_reason})."

    if location:
        reasoning += f" Detected location: '{location}'."

    return {
        "suggested_department": best_dept,
        "suggested_priority": priority,
        "suggested_location": location,
        "confidence": confidence,
        "reasoning": reasoning,
        "matched_keywords": matched_kws[:5]
    }


if __name__ == "__main__":
    test_cases = [
        # High priority tests (safety hazards, exposed wires, water leakage, fire hazards, major failures)
        ("Exposed wires hanging from the ceiling in CS Lab 3, sparking observed.", "Live wire risk"),
        ("Water pipe burst and major water leakage in Central Library, 2nd Floor Study Room 204.", "Water leak"),
        ("Fire hazard: smoke coming from electrical switchboard in Science Complex.", "Smoke detected"),
        ("Emergency exit push bar jammed in Chemistry Annex Ground Floor.", "Exit door stuck"),
        # Medium priority tests (normal equipment: projector, fan, light, computer, Wi-Fi)
        ("The projector in CS Lab 3 has a loose HDMI cable and flickering display.", "HDMI broken"),
        ("Ceiling fan in room 104 is not rotating.", "Fan broken"),
        ("Computer in library is not connecting to campus Wi-Fi network.", "Wi-Fi issue"),
        ("Tube light in seminar hall is flickering.", "Light blinking"),
        # Low priority tests (cleaning requests, cosmetic problems, minor non-urgent)
        ("Dustbin is overflowing in the hallway, cleaning request.", "Clean trash"),
        ("Wall paint is slightly peeled and scratched near the notice board.", "Peeling paint"),
        ("Minor cosmetic issue with clock battery running slow.", "Clock battery"),
        # Unclear fallback test
        ("Some papers are placed on the table.", "Table issue")
    ]

    print("Running AI Classifier self-tests:")
    for desc, title in test_cases:
        result = classify_issue(desc, title)
        print(f"\nText: {desc}")
        print(f" -> Dept: {result['suggested_department']} ({result['confidence']}%)")
        print(f" -> Priority: {result['suggested_priority']}")
        print(f" -> Location: '{result['suggested_location']}'")
        print(f" -> Reason: {result['reasoning']}")
    
    
        
        
