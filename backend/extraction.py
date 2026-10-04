"""Deterministic specification -> requirement profile extraction.

Rule/regex based so it runs on an i5 CPU with no GPU and no network.
Optional LLM hints (ai_layer) may only adjust terminology, never decide.
"""
import re

ATTRS = ["product", "application", "material", "pressure_class",
         "temperature", "connection", "testing", "safety", "medium", "size"]

LABELS = {
    "product": "Product", "application": "Application", "material": "Material",
    "pressure_class": "Pressure Class", "temperature": "Operating Temperature",
    "connection": "Connection", "testing": "Testing",
    "safety": "Safety", "medium": "Process Medium", "size": "Valve Size",
}

CLARIFY_OPTIONS = {
    "temperature": ["Ambient (below 100C)", "150-250C process", "High-temp (above 300C)"],
    "pressure_class": ["PN10", "PN16", "PN40", "Class150", "Class300"],
    "material": ["Stainless Steel", "Carbon Steel", "Cast Iron"],
    "connection": ["Flanged", "Threaded", "Welded"],
}

TEMP_CANON = {
    "ambient": "ambient below 100c", "below 100": "ambient below 100c",
    "<100": "ambient below 100c",
    "150": "150-250c process", "200": "150-250c process", "250": "150-250c process",
    "300": "high-temp above 300c", ">300": "high-temp above 300c", "high-temp": "high-temp above 300c",
}


def _canon(attr: str, value: str) -> str:
    v = value.strip().lower()
    if attr == "pressure_class":
        v = v.replace(" ", "")
        mapping = {"pn10": "pn10", "pn16": "pn16", "pn40": "pn40", "pn63": "pn63",
                   "class150": "class150", "150#": "class150", "class300": "class300",
                   "300#": "class300", "150lb": "class150", "300lb": "class300"}
        return mapping.get(v, v)
    if attr == "temperature":
        for k, canon in TEMP_CANON.items():
            if k in v:
                return canon
        return v
    return v


def extract_requirements(spec_text: str, llm_hints: dict | None = None) -> list[dict]:
    t = spec_text.lower()
    reqs: dict[str, dict] = {}

    def put(attr, value, display, status, evidence):
        reqs[attr] = {"key": attr, "label": LABELS[attr], "value": _canon(attr, value) if value else None,
                      "display_value": display, "status": status, "evidence": evidence,
                      "options": CLARIFY_OPTIONS.get(attr, [])}

    # product
    if re.search(r"\bvalves?\b", t):
        kind = "Industrial Valve"
        m = re.search(r"\b(gate|globe|ball|butterfly|check|sluice)\b[^.]{0,20}\bvalves?\b|\bvalves?\b[^.]{0,20}\b(gate|globe|ball|butterfly|check)\b", t)
        if m:
            kind = f"Industrial Valve ({(m.group(1) or m.group(2)).title()})"
        put("product", "industrial valve", kind, "CONFIRMED", "valve mentioned in specification")
    else:
        put("product", None, "Missing", "MISSING", "no valve/product identified")

    # application
    if re.search(r"high[\s-]*pressure\s+process|process\s+(plant|service|application)|chemical\s+process|hydrocarbon", t):
        put("application", "high-pressure process", "High-pressure process service", "CONFIRMED", "process-service context detected")
    elif re.search(r"potable|drinking\s+water|water\s+supply|distribution", t):
        put("application", "potable water", "Potable water service", "CONFIRMED", "water-service context detected")
    else:
        put("application", None, "Missing", "MISSING", "no application context identified")

    # material
    if re.search(r"stainless\s+steel|ss\s*316|ss\s*304|cf8|cf8m", t):
        put("material", "stainless steel", "Stainless Steel", "CONFIRMED", "stainless steel stated")
    elif re.search(r"carbon\s+steel|wcb|a216", t):
        put("material", "carbon steel", "Carbon Steel", "CONFIRMED", "carbon steel stated")
    elif re.search(r"cast\s+iron", t):
        put("material", "cast iron", "Cast Iron", "CONFIRMED", "cast iron stated")
    elif re.search(r"\b(brass|bronze)\b", t):
        put("material", "brass/bronze", "Brass/Bronze", "CONFIRMED", "copper alloy stated")
    else:
        put("material", None, "Missing", "MISSING", "no body material stated")

    # pressure class
    pm = re.search(r"\bpn\s*(10|16|40|63)\b|class\s*(150|300)\b|(150|300)\s*(#|lb|class)\b", t)
    if pm:
        raw = pm.group(0)
        put("pressure_class", raw, _canon("pressure_class", raw).upper().replace("CLASS", "Class "), "CONFIRMED", f"pressure rating '{raw.strip()}' stated")
    else:
        put("pressure_class", None, "Missing", "MISSING", "no pressure class stated")

    # temperature
    tm = re.search(r"(-?\d+\s*(to|-|–)\s*-?\d+\s*°?\s*c)|(above|over|up\s*to)\s*\d+\s*°?\s*c|\d+\s*°\s*c\b", t)
    if tm:
        put("temperature", tm.group(0), tm.group(0).strip(), "CONFIRMED", "temperature range stated")
    else:
        put("temperature", None, "Missing", "MISSING", "operating temperature not stated — several standards depend on it")

    # connection
    if re.search(r"flang", t):
        put("connection", "flanged", "Flanged", "CONFIRMED", "flanged ends stated")
    elif re.search(r"thread|screw", t):
        put("connection", "threaded", "Threaded", "CONFIRMED", "threaded ends stated")
    elif re.search(r"weld|butt[\s-]*end|socket", t):
        put("connection", "welded", "Welded", "CONFIRMED", "welded ends stated")
    elif re.search(r"wafer", t):
        put("connection", "wafer", "Wafer", "CONFIRMED", "wafer type stated")
    else:
        put("connection", None, "Missing", "MISSING", "no end-connection stated")

    # testing
    if re.search(r"test|hydrostatic|hydraulic|ndt|inspect|radiograph|ultrasonic", t):
        put("testing", "required", "Required", "CONFIRMED", "testing/inspection required")
    else:
        put("testing", None, "Missing", "MISSING", "no testing requirement stated")

    # safety
    if re.search(r"safe|fire|fugitive|emission|safety|sil|hazard", t):
        put("safety", "required", "Required", "CONFIRMED", "safety requirement stated")
    else:
        put("safety", "not stated", "Not stated", "MISSING", "no safety requirement stated")

    # medium — food-grade phrase is deliberately AMBIGUOUS in hero spec
    if re.search(r"food[\s-]*grade|hygienic|potable|drinking", t) and re.search(r"chemical|process|steam|hydrocarbon|oil|gas", t):
        put("medium", "process fluid", "Process fluid (food-grade phrase ambiguous — needs review)", "AMBIGUOUS",
            "'food-grade' appears alongside process service; treated as process fluid pending review")
    elif re.search(r"chemical|process fluid|hydrocarbon|steam|oil|gas|slurry", t):
        put("medium", "process fluid", "Process fluid", "CONFIRMED", "process medium stated")
    elif re.search(r"potable|drinking|water", t):
        put("medium", "water", "Water", "CONFIRMED", "water medium stated")
    else:
        put("medium", None, "Missing", "MISSING", "no process medium stated")

    # size
    sm = re.search(r"\bdn\s*\d+|nps\s*\d+|\b\d+\s*(inch|mm)\b.*(valve|bore|size)", t)
    if sm:
        put("size", sm.group(0), sm.group(0).strip().upper(), "CONFIRMED", "size stated")
    else:
        put("size", "not stated", "Not stated", "MISSING", "size not stated (non-blocking)")

    if llm_hints:
        for k, v in llm_hints.items():
            if k in reqs and reqs[k]["status"] == "MISSING" and v:
                reqs[k] = {"key": k, "label": LABELS[k], "value": _canon(k, str(v)),
                           "display_value": str(v), "status": "CONFIRMED",
                           "evidence": "terminology normalized via AI layer",
                           "options": CLARIFY_OPTIONS.get(k, [])}

    return [reqs[a] for a in ATTRS]


def requirement_map(requirements: list[dict]) -> dict[str, dict]:
    return {r["key"]: r for r in requirements}


def resolvable_keys(requirements: list[dict]) -> list[str]:
    """Requirements that can be covered: CONFIRMED or AMBIGUOUS, minus non-blocking size/safety-not-stated."""
    out = []
    for r in requirements:
        if r["status"] in ("CONFIRMED", "AMBIGUOUS") and r["key"] != "size":
            if r["key"] == "safety" and r["value"] == "not stated":
                continue
            out.append(r["key"])
    return out
