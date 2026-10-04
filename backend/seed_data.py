"""Seed the SQLite prototype knowledge base.

Clearly labelled demonstration dataset — NOT an official BIS database.
Metadata-style records only; no copyrighted standard text reproduced.
"""
import json
import sqlite3
from pathlib import Path

from database import DB_PATH, SCHEMA

# condition helper: {"attr": ..., "allowed": [...]}


def C(attr, *allowed):
    return {"attr": attr, "allowed": list(allowed)}


def X(attr, *forbidden):
    return {"attr": attr, "forbidden": list(forbidden)}


def std(standard_id, title, product_category, scope_summary, keywords,
        conditions=None, exclusions=None, covers=None, status="CURRENT",
        revision_year=2021, superseded_by=None, related=None,
        normative_references=None, test_methods=None,
        certification_flag=False, role="SUPPORTING"):
    return {
        "standard_id": standard_id,
        "title": title,
        "product_category": product_category,
        "scope_summary": scope_summary,
        "keywords": keywords,
        "applicability_conditions": conditions or [],
        "exclusions": exclusions or [],
        "covers": covers or [],
        "status": status,
        "revision_year": revision_year,
        "superseded_by": superseded_by,
        "related": related or [],
        "normative_references": normative_references or [],
        "test_methods": test_methods or [],
        "certification_flag": certification_flag,
        "role": role,
        "is_synthetic_demo": True,
    }


def R(target, rel):
    return {"target": target, "rel": rel}


CURATED = [
    # ---------------- PRIMARY ----------------
    std("IS-DEM-VALVE-01",
        "Steel gate, globe and ball valves for high-pressure process service (Demo record)",
        "industrial valve",
        "Covers steel flanged valves for high-pressure process applications in stainless or carbon steel, pressure classes PN16 to PN40.",
        ["valve", "gate", "globe", "ball", "process", "high-pressure", "pressure", "stainless", "steel", "flanged", "flange", "industrial", "pn16", "pn40"],
        [C("product", "industrial valve"), C("application", "high-pressure process", "process plant"),
         C("material", "stainless steel", "carbon steel"), C("pressure_class", "pn16", "pn40", "class150", "class300"),
         C("connection", "flanged")],
        [X("application", "potable water"), X("medium", "drinking water")],
        ["product", "application", "material", "pressure_class", "medium"],
        revision_year=2022, related=[R("IS-DEM-FLANGE-11", "REFERENCES"), R("IS-DEM-MAT-10", "REFERENCES"),
                                     R("IS-DEM-TEST-20", "TESTED_BY"), R("IS-DEM-SAFE-30", "REQUIRES"),
                                     R("IS-DEM-DIM-12", "RELATED_TO")],
        normative_references=["IS-DEM-MAT-10", "IS-DEM-FLANGE-11"],
        test_methods=["IS-DEM-TEST-20"], role="PRIMARY"),
    std("IS-DEM-VALVE-02",
        "High-pressure range industrial valves PN40 and above (Demo record)",
        "industrial valve",
        "Specialist range covering valves rated PN40 / Class 300 and above for severe process service.",
        ["valve", "high-pressure", "pressure", "pn40", "class300", "process", "severe", "industrial", "steel"],
        [C("product", "industrial valve"), C("pressure_class", "pn40", "class300", "pn63"),
         C("application", "high-pressure process", "process plant")],
        [],
        ["product", "pressure_class"],
        revision_year=2021, related=[R("IS-DEM-VALVE-01", "RELATED_TO")],
        test_methods=["IS-DEM-TEST-20"], role="PRIMARY"),
    # ---------------- DECOY (must REJECT) ----------------
    std("IS-DEM-VALVE-WTR-09",
        "Valves for potable water supply and distribution (Demo record)",
        "water valve",
        "Covers sluice and butterfly valves intended ONLY for potable/drinking water supply. Explicitly excludes process and chemical service.",
        ["valve", "sluice", "butterfly", "water", "potable", "pressure", "flanged", "distribution", "supply", "industrial"],
        [C("product", "industrial valve"), C("application", "potable water")],
        [X("application", "high-pressure process", "process plant"),
         X("medium", "chemical", "steam", "hydrocarbon", "process fluid")],
        ["product", "connection"],
        revision_year=2019, role="ALLIED"),
    # ---------------- OUTDATED ----------------
    std("IS-DEM-VALVE-OLD-03",
        "Steel valves for general process service, 2008 edition (Demo record, superseded)",
        "industrial valve",
        "Older edition of the process valve specification. Superseded by IS-DEM-VALVE-01.",
        ["valve", "process", "steel", "pressure", "flanged", "industrial", "general"],
        [C("product", "industrial valve")],
        [],
        ["product", "pressure_class"],
        status="SUPERSEDED", revision_year=2008, superseded_by="IS-DEM-VALVE-01",
        related=[R("IS-DEM-VALVE-01", "SUPERSEDES")], role="PRIMARY"),
    # ---------------- SUPPORTING ----------------
    std("IS-DEM-MAT-10",
        "Stainless steel grades for valve and pressure-equipment bodies (Demo record)",
        "material",
        "Material specification for stainless steel castings and bars used in valve bodies.",
        ["stainless", "steel", "material", "casting", "valve", "body", "grade", "316", "304", "corrosion"],
        [C("material", "stainless steel")],
        [],
        ["material"],
        revision_year=2020, related=[R("IS-DEM-VALVE-01", "RELATED_TO")], role="SUPPORTING"),
    std("IS-DEM-MAT-HT-13",
        "Supplementary high-temperature material requirements for process valves (Demo record)",
        "material",
        "Supplementary elevated-temperature material properties. Applicability can only be judged once operating temperature is known.",
        ["material", "high-temperature", "temperature", "alloy", "valve", "steel", "elevated", "creep"],
        [C("product", "industrial valve"), C("temperature", "150-250c process", "high-temp above 300c", "ambient below 100c")],
        [],
        ["material", "temperature"],
        revision_year=2021, related=[R("IS-DEM-MAT-10", "RELATED_TO")], role="SUPPORTING"),
    std("IS-DEM-FLANGE-11",
        "Flanged pipe joints and flange dimensions up to PN16 (Demo record)",
        "flange",
        "Dimensions and facing requirements for flanged joints rated up to PN16 / Class 150.",
        ["flange", "flanged", "joint", "dimension", "pn16", "class150", "connection", "bolt", "facing", "pipe"],
        [C("connection", "flanged"), C("pressure_class", "pn10", "pn16", "class150")],
        [],
        ["connection"],
        revision_year=2019, related=[R("IS-DEM-DIM-12", "RELATED_TO")], role="SUPPORTING"),
    std("IS-DEM-FLANGE-HP-14",
        "High-pressure flanged joints PN40 / Class 300 (Demo record)",
        "flange",
        "Flange dimensions for high-pressure joints rated PN40 / Class 300.",
        ["flange", "flanged", "high-pressure", "pn40", "class300", "joint", "connection", "dimension"],
        [C("connection", "flanged"), C("pressure_class", "pn40", "class300", "pn63")],
        [],
        ["connection", "pressure_class"],
        revision_year=2022, related=[R("IS-DEM-VALVE-02", "RELATED_TO")], role="SUPPORTING"),
    std("IS-DEM-DIM-12",
        "Face-to-face dimensions of flanged industrial valves (Demo record)",
        "dimension",
        "Face-to-face and end-to-end dimensions for flanged valves.",
        ["dimension", "face-to-face", "valve", "flanged", "length", "connection", "industrial"],
        [C("product", "industrial valve"), C("connection", "flanged"),
         C("pressure_class", "pn10", "pn16", "class150")],
        [],
        ["product", "connection"],
        revision_year=2018, related=[R("IS-DEM-FLANGE-11", "RELATED_TO")], role="SUPPORTING"),
    # ---------------- TEST ----------------
    std("IS-DEM-TEST-20",
        "Hydrostatic pressure testing of industrial valves (Demo record)",
        "test method",
        "Hydrostatic shell and seat pressure testing procedure for industrial valves.",
        ["test", "testing", "hydrostatic", "pressure", "valve", "shell", "seat", "inspection", "hydraulic"],
        [C("testing", "required")],
        [],
        ["testing"],
        revision_year=2021, related=[R("IS-DEM-VALVE-01", "RELATED_TO")], role="TEST"),
    std("IS-DEM-TEST-21",
        "Non-destructive examination of valve castings (Demo record)",
        "test method",
        "Radiographic and ultrasonic examination of valve body castings.",
        ["test", "non-destructive", "radiographic", "ultrasonic", "casting", "valve", "examination", "inspection", "ndt"],
        [C("testing", "required")],
        [],
        ["testing"],
        revision_year=2020, role="TEST"),
    # ---------------- SAFETY (temperature-gated) ----------------
    std("IS-DEM-SAFE-30",
        "Fire-safe performance testing of process valves (Demo record)",
        "safety",
        "Fire-safe qualification of process valves. Temperature rating of the service must be known to confirm applicability.",
        ["safety", "fire", "fire-safe", "valve", "process", "qualification", "temperature", "testing"],
        [C("safety", "required"), C("temperature", "150-250c process", "high-temp above 300c", "ambient below 100c")],
        [],
        ["safety"],
        revision_year=2022, related=[R("IS-DEM-TEST-20", "REFERENCES")],
        test_methods=["IS-DEM-TEST-20"], role="SAFETY"),
    std("IS-DEM-SAFE-31",
        "Fugitive-emission control for process valve stem seals (Demo record)",
        "safety",
        "Emission-control requirements for valve stem seals in process service. Needs known operating temperature.",
        ["safety", "fugitive", "emission", "seal", "valve", "stem", "process", "temperature", "environment"],
        [C("safety", "required"), C("temperature", "150-250c process", "high-temp above 300c", "ambient below 100c")],
        [],
        ["safety"],
        revision_year=2021, role="SAFETY"),
    # ---------------- CERTIFICATION ----------------
    std("IS-DEM-CERT-40",
        "BIS certification scheme for industrial valves (Demo record)",
        "certification",
        "Factory inspection and marking scheme for certified industrial valves.",
        ["certification", "bis", "mark", "valve", "inspection", "factory", "licence", "quality", "industrial"],
        [C("product", "industrial valve")],
        [],
        ["product"],
        revision_year=2023, certification_flag=True,
        related=[R("IS-DEM-VALVE-01", "RELATED_TO")], role="CERTIFICATION"),
]

# Filler standards: broad catalogue so retrieval funnel is realistic.
_FILLERS = [
    ("IS-DEM-PIPE-50", "Steel pipes for process service", "pipe", "steel pipe process pressure welded seamless", ["material"]),
    ("IS-DEM-PIPE-51", "Cast iron pressure pipes for water lines", "pipe", "cast iron pipe water pressure distribution", ["product"]),
    ("IS-DEM-FIT-52", "Butt-welding pipe fittings", "fitting", "fitting elbow tee welding pipe dimension", ["connection"]),
    ("IS-DEM-GSK-53", "Gaskets for flanged joints", "gasket", "gasket sealing flange joint compressed fibre", ["connection"]),
    ("IS-DEM-BOLT-54", "Bolting for flanged joints", "fastener", "bolt nut stud flange joint high tensile", ["connection"]),
    ("IS-DEM-PUMP-55", "Centrifugal pumps for process service", "pump", "pump centrifugal process pressure flow industrial", ["product"]),
    ("IS-DEM-PUMP-56", "Submersible pumps for borewell water", "pump", "pump submersible borewell water motor", []),
    ("IS-DEM-BOIL-57", "Boiler feed and shell requirements", "boiler", "boiler steam pressure vessel safety feed", ["safety"]),
    ("IS-DEM-VESS-58", "Unfired pressure vessels", "pressure vessel", "pressure vessel unfired shell safety inspection", ["safety"]),
    ("IS-DEM-STEEL-59", "Structural steel grades and sections", "steel", "structural steel beam section grade construction", ["material"]),
    ("IS-DEM-BAR-60", "Thermo-mechanically treated bars for concrete", "steel", "tmt bar reinforcement concrete construction steel", ["material"]),
    ("IS-DEM-CEM-61", "Ordinary Portland cement 43 grade", "cement", "cement portland construction concrete grade", []),
    ("IS-DEM-CONC-62", "Ready-mixed concrete production", "concrete", "concrete ready mixed construction batching", []),
    ("IS-DEM-CABLE-63", "PVC insulated power cables", "electrical", "cable pvc insulated power conductor electrical", []),
    ("IS-DEM-MOTOR-64", "Three-phase induction motors", "electrical", "motor induction three phase efficiency electrical", []),
    ("IS-DEM-TRF-65", "Distribution transformers", "electrical", "transformer distribution oil cooled electrical", ["safety"]),
    ("IS-DEM-LED-66", "LED luminaires for street lighting", "electrical", "led luminaire street lighting photometric", []),
    ("IS-DEM-SOL-67", "Solar photovoltaic modules", "renewable", "solar photovoltaic module panel renewable", []),
    ("IS-DEM-TANK-68", "Polyethylene water storage tanks", "tank", "tank polyethylene water storage rotational", ["product"]),
    ("IS-DEM-TANK-69", "Steel tanks for petroleum storage", "tank", "tank steel petroleum storage welded", ["safety"]),
    ("IS-DEM-CHEM-70", "Caustic soda process specification", "chemical", "caustic soda chemical process alkali", ["medium"]),
    ("IS-DEM-ACID-71", "Sulphuric acid handling code", "chemical", "sulphuric acid chemical handling safety corrosion", ["safety", "medium"]),
    ("IS-DEM-PAINT-72", "Protective painting of steel structures", "coating", "paint coating protective steel primer", ["material"]),
    ("IS-DEM-WELD-73", "Fusion welding procedure qualification", "welding", "welding procedure fusion welder qualification test", ["testing"]),
    ("IS-DEM-NDT-74", "Ultrasonic testing general practice", "test method", "ultrasonic testing weld examination ndt inspection", ["testing"]),
    ("IS-DEM-QMS-75", "Quality management for valve manufacturers", "quality", "quality management iso manufacturing audit valve", ["product"]),
    ("IS-DEM-SAF-76", "Industrial safety helmets", "safety", "helmet safety head protection industrial ppe", ["safety"]),
    ("IS-DEM-FIRE-77", "Portable fire extinguishers", "safety", "fire extinguisher portable safety powder", ["safety"]),
    ("IS-DEM-LPG-78", "LPG cylinders and regulators", "gas", "lpg cylinder regulator gas safety domestic", ["safety"]),
    ("IS-DEM-GAS-79", "Piped natural gas distribution", "gas", "natural gas pipeline distribution city gas", ["safety"]),
    ("IS-DEM-FOOD-80", "Food-grade plastics contact materials", "food", "food grade plastic contact hygiene packaging", ["medium"]),
    ("IS-DEM-HYG-81", "Dairy plant hygienic design code", "food", "dairy hygienic food plant stainless design", ["medium"]),
    ("IS-DEM-WTR-82", "Drinking water quality tolerances", "water", "drinking water quality potable testing limits", ["testing"]),
    ("IS-DEM-SEW-83", "Sewage treatment plant guidelines", "water", "sewage treatment effluent plant wastewater", []),
    ("IS-DEM-METER-84", "Water meters for domestic service", "meter", "water meter domestic flow measurement", ["product"]),
    ("IS-DEM-PR-85", "Pressure gauges for process lines", "instrument", "pressure gauge bourdon process measurement", ["pressure_class"]),
    ("IS-DEM-INST-86", "Temperature sensors and thermowells", "instrument", "temperature sensor thermocouple rtd thermowell", ["temperature"]),
    ("IS-DEM-ACT-87", "Pneumatic actuators for valves", "actuator", "actuator pneumatic valve automation torque", ["product"]),
    ("IS-DEM-SEAL-88", "Elastomer O-rings and seals", "seal", "seal o-ring elastomer rubber gland", ["material"]),
    ("IS-DEM-LUBE-89", "Lubricating oils for machinery", "lubricant", "lubricant oil machinery grease viscosity", ["medium"]),
    ("IS-DEM-COMP-90", "Air compressors safety code", "compressor", "compressor air receiver safety pressure", ["safety"]),
    ("IS-DEM-CRANE-91", "Overhead crane structural code", "crane", "crane overhead hoist structural safety", ["safety"]),
    ("IS-DEM-LIFT-92", "Passenger lift installation code", "lift", "lift elevator passenger installation safety", ["safety"]),
    ("IS-DEM-DOOR-93", "Steel doors and shutters", "building", "door steel shutter building hardware", []),
    ("IS-DEM-BRICK-94", "Burnt clay bricks classification", "building", "brick clay building masonry construction", []),
    ("IS-DEM-AGG-95", "Coarse aggregates for concrete", "building", "aggregate coarse concrete sieve construction", ["material"]),
    ("IS-DEM-TIMB-96", "Structural timber grading", "building", "timber wood structural grading", ["material"]),
    ("IS-DEM-PLAS-97", "UPVC pipes for potable water", "pipe", "upvc pipe potable water pressure plumbing", ["product"]),
    ("IS-DEM-DUCT-98", "Ventilation ductwork fabrication", "hvac", "duct ventilation hvac sheet fabrication", ["connection"]),
    ("IS-DEM-AC-99", "Room air conditioners performance", "hvac", "air conditioner room cooling energy rating", ["temperature"]),
]


def build_filler(sid, title, category, kw, covers):
    # Every filler is scoped to its own product category, so a valve
    # procurement spec deterministically REJECTS them on applicability
    # even when lexical overlap (steel/pressure/test/...) is high.
    # This is what makes "semantic similarity is not enough" demonstrable.
    return std(sid, title + " (Demo record)", category,
               f"Demonstration catalogue entry for {title.lower()}.",
               (kw + " specification requirements").split(),
               [C("product", category)], [], covers,
               revision_year=2016 + (hash(sid) % 8),
               role="ALLIED")


def all_standards() -> list[dict]:
    fillers = [build_filler(sid, title, cat, kw, covers)
               for sid, title, cat, kw, covers in _FILLERS]
    return CURATED + fillers


def seed() -> int:
    Path(DB_PATH).unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    rows = all_standards()
    for s in rows:
        conn.execute(
            """INSERT INTO standards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (s["standard_id"], s["title"], s["product_category"], s["scope_summary"],
             ",".join(s["keywords"]), json.dumps(s["applicability_conditions"]),
             json.dumps(s["exclusions"]), json.dumps(s["covers"]), s["status"],
             s["revision_year"], s["superseded_by"], json.dumps(s["related"]),
             json.dumps(s["normative_references"]), json.dumps(s["test_methods"]),
             int(s["certification_flag"]), s["role"], int(s["is_synthetic_demo"])),
        )
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM standards").fetchone()[0]
    conn.close()
    print(f"Seeded {n} demonstration standards -> {DB_PATH}")
    return n


if __name__ == "__main__":
    seed()
