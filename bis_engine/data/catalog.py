"""Seed catalogue of Indian Standards (BIS) for the recommendation engine MVP.

DATA STATUS: This is a curated, hand-built DEMO SEED of 84 standards across 11
sectors, originally 40 entries hand-written in September 2026 and expanded the same
month with a CLOSED allied-reference graph (every IS code in `allied` resolves to a
catalogue entry — guarded by an integrity test). It is NOT a live mirror of the BIS catalogue.
Every entry carries `last_reviewed`, and the app surfaces a visible "seed data"
disclaimer. See README (Upgrade Path) for swapping in a live/licensed BIS feed.

Field guide:
  code            human-written standard reference (with year baked into `version`)
  version         edition/revision label as used in tender citations
  amendments      list of known amendment labels (empty list = verify manually)
  status          "active" | "superseded-edition" (older editions handled via `version`)
  sector          sector key (SECTORS)
  aliases         multilingual query vocabulary {en, hi, ta}
  allied          [{code, relation}] normative refs, test methods, related products
  certifications  mandatory schemes [{scheme, authority, note}]
  examples        [{bad, good, note}] real specification pitfalls for the UI
"""

import json
import re
from pathlib import Path

CATALOG_VERSION = "2026.09-seed-2"
LAST_SYNCED = "2026-09-29"

# SYNC_HEALTH is finalised after the snapshot merge at the bottom of the seed list.

SECTORS = {
    "construction": "Construction & Civil Works",
    "cement": "Cement",
    "electronics": "Electrical & Electronics",
    "appliances": "Consumer Appliances & Energy",
    "water": "Water Supply & Sanitation",
    "food": "Food & Agriculture",
    "safety": "Industrial & Safety Supplies",
    "steel": "Steel & Metals",
    "pumps": "Pumps & Fluid Machinery",
    "furniture": "Furniture & Office Equipment",
    "medical": "Medical & Hospital Supplies",
}
_SEED_STANDARDS = [
    # ------------------------------------------------------------------ CONSTRUCTION
    {
        "code": "IS 456",
        "title": "Plain and Reinforced Concrete — Code of Practice",
        "version": "2000 (4th revision, up to Amendment 2:2007)",
        "amendments": ["A1: 2005", "A2: 2007"],
        "status": "active",
        "sector": "construction",
        "category": "Structural concrete works",
        "summary": (
            "The general code of practice for structural concrete design and execution. "
            "Cited in nearly every civil tender involving RCC works, from foundations "
            "to superstructure."
        ),
        "aliases": {
            "en": ["concrete", "rcc", "reinforced concrete", "cement concrete works",
                   "structural concrete", "concrete construction", "rcc works"],
            "te": ["కాంక్రీట్", "ఆర్సీసీ పనులు"],
            "hi": ["कंक्रीट", "सीमेंट कंक्रीट", "ढांचागत कंक्रीट", "आरसीसी"],
            "ta": ["காங்கிரீட்", "சிமென்ட் காங்கிரீட் வேலைகள்"],
        },
        "allied": [
            {"code": "IS 383", "relation": "material — coarse & fine aggregates"},
            {"code": "IS 10262", "relation": "method — concrete mix proportioning"},
            {"code": "IS 13920", "relation": "code — ductile detailing for seismic zones"},
            {"code": "IS 875", "relation": "loading — design loads (other than earthquake)"},
            {"code": "IS 516", "relation": "method — strength tests of concrete"},
        ],
        "certifications": [],
        "examples": [
            {
                "bad": "IS 456:1978",
                "good": "IS 456:2000 (with amendments up to A2:2007)",
                "note": "The 1978 edition still circulates in legacy tender schedules and is superseded.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 383",
        "title": "Coarse and Fine Aggregate for Concrete — Specification",
        "version": "2016 (3rd revision)",
        "amendments": ["A1: 2018"],
        "status": "active",
        "sector": "construction",
        "category": "Construction materials",
        "summary": (
            "Specification for natural and manufactured aggregates used in concrete, "
            "including manufactured sand (M-sand) provisions introduced in the 2016 revision."
        ),
        "aliases": {
            "en": ["aggregate", "sand", "crushed stone", "gravel", "coarse aggregate",
                   "fine aggregate", "m-sand", "manufactured sand", "ballast"],
            "hi": ["रेत", "बजरी", "गिट्टी", "मोटा रेत"],
            "ta": ["மணல்", "கூழாங்கற்கள்"],
        },
        "allied": [
            {"code": "IS 2386", "relation": "method — tests for aggregates"},
            {"code": "IS 2430", "relation": "terminology — sampling of aggregates"},
            {"code": "IS 456", "relation": "usage — concrete works"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 875",
        "title": "Code of Practice for Design Loads (Other Than Earthquake) for Buildings and Structures",
        "version": "Parts 1–2, 4–5: 1987 · Part 3 (Wind Loads): 2015",
        "amendments": ["Part 3 revised as 2015 edition"],
        "status": "active",
        "sector": "construction",
        "category": "Structural design",
        "summary": (
            "Multi-part code covering dead, imposed, wind, snow and combination loads. "
            "Note the part-level versioning: Part 3 (wind loads) is the 2015 revision "
            "while other parts remain 1987 — citing a single blanket year is a common error."
        ),
        "aliases": {
            "en": ["design loads", "wind load", "dead load", "imposed load",
                   "load combinations", "structural loading"],
            "hi": ["भार संहिता", "पवन भार", "डिज़ाइन भार"],
            "ta": ["சுமை விவரக்குறிப்புகள்"],
        },
        "allied": [
            {"code": "IS 456", "relation": "usage — concrete design"},
            {"code": "IS 1893", "relation": "loading — earthquake loads (companion code)"},
        ],
        "certifications": [],
        "examples": [
            {
                "bad": "Wind loads as per IS 875:1987 (all parts)",
                "good": "Wind loads as per IS 875 (Part 3):2015; other loads per respective parts",
                "note": "Part 3 was revised in 2015 — blanket year citations pull in an outdated wind-load code.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1893 (Part 1)",
        "title": "Criteria for Earthquake Resistant Design of Structures — General Provisions and Buildings",
        "version": "2016",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Structural design",
        "summary": (
            "Seismic zoning, zone factors and response spectra for earthquake-resistant "
            "design of buildings. Mandatory companion for structural tenders in "
            "seismic zones II–V."
        ),
        "aliases": {
            "en": ["earthquake", "seismic design", "earthquake resistant",
                   "seismic zones", "response spectrum"],
            "hi": ["भूकंप प्रतिरोधी डिज़ाइन", "भूकंपीय", "भूकंप"],
            "ta": ["நிலநடுக்கம்", "நிலநடுக்க எதிர்ப்பு வடிவமைப்பு"],
        },
        "allied": [
            {"code": "IS 13920", "relation": "code — ductile detailing"},
            {"code": "IS 875", "relation": "loading — other design loads"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 13920",
        "title": "Ductile Design and Detailing of Reinforced Concrete Structures Subjected to Seismic Forces",
        "version": "2016",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Structural design",
        "summary": (
            "Special provisions for reinforcement detailing (confinement, laps, "
            "joint detailing) in seismic zones. Frequently omitted from tenders that "
            "cite only IS 456."
        ),
        "aliases": {
            "en": ["ductile detailing", "ductility", "seismic reinforcement",
                   "earthquake detailing", "confining reinforcement"],
            "hi": ["डक्टाइल डिटेलिंग", "भूकंपीय सुदृढ़ीकरण"],
            "ta": ["டக்டைல் விவரமைப்பு"],
        },
        "allied": [
            {"code": "IS 456", "relation": "code — general concrete practice"},
            {"code": "IS 1893", "relation": "loading — seismic demand"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1077",
        "title": "Common Burnt Clay Building Bricks — Specification",
        "version": "1992 (5th revision)",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Masonry materials",
        "summary": (
            "Specification for common burnt clay building bricks including strength "
            "classes and water absorption limits."
        ),
        "aliases": {
            "en": ["bricks", "clay bricks", "red bricks", "masonry bricks",
                   "burnt clay bricks", "building bricks"],
            "hi": ["ईंटें", "ईंट", "लाल ईंट"],
            "ta": ["செங்கல்", "மண் செங்கல்"],
            "te": ["ఇటుకలు"],
        },
        "allied": [
            {"code": "IS 3495 (Parts 1–4)", "relation": "method — brick test methods"},
            {"code": "IS 1905", "relation": "code — structural masonry"},
            {"code": "IS 2212", "relation": "code — brickwork practice"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1200",
        "title": "Method of Measurement of Building and Civil Engineering Works",
        "version": "Part-wise (multiple editions)",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Contracts & measurement",
        "summary": (
            "Multi-part code standardising how building and civil works are measured "
            "for billing. Referencing the correct part in the measurement schedule "
            "prevents payment disputes."
        ),
        "aliases": {
            "en": ["measurement of works", "billing measurements", "method of measurement",
                   "civil measurements"],
            "hi": ["कार्य मापन", "मापन विधि"],
            "ta": ["அளவீட்டு முறைகள்"],
        },
        "allied": [],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 303",
        "title": "Plywood for General Purposes — Specification",
        "version": "Edition as notified (verify current consolidated edition)",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Wood-based panels",
        "summary": (
            "Specification for plywood for general purposes, including bonding "
            "quality classes. Several wood-based panel products have been brought "
            "under BIS Quality Control Orders in recent notifications."
        ),
        "aliases": {
            "en": ["plywood", "ply", "wooden panels", "plywood sheets", "board panels"],
            "hi": ["प्लाईवुड", "प्लाई"],
            "ta": ["பிளைவுட்"],
        },
        "allied": [
            {"code": "IS 1734", "relation": "method — tests for plywood"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — QCO (verify applicability)",
                "authority": "BIS",
                "note": "Wood-based panel products have been progressively notified under "
                        "Quality Control Orders; confirm the current scope before tendering.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    # ------------------------------------------------------------- ELECTRICAL & ELECTRONICS
    {
        "code": "IS 13252 (Part 1)",
        "title": "Information Technology Equipment — Safety — General Requirements",
        "version": "2010 (aligned with IEC 60950-1, with subsequent amendments)",
        "amendments": ["Several amendments since 2010 — verify consolidated edition"],
        "status": "active",
        "sector": "electronics",
        "category": "IT & office equipment",
        "summary": (
            "Safety standard for IT equipment (computers, printers, adapters, "
            "office electronics). Every covered item must additionally carry a valid "
            "MeitY CRS registration number before procurement."
        ),
        "aliases": {
            "en": ["it equipment", "computers", "laptops", "printers", "office electronics",
                   "it hardware", "power adapters", "electronic devices"],
            "hi": ["आईटी उपकरण", "कंप्यूटर", "प्रिंटर"],
            "ta": ["கணினி", "ஐடி உபகரணங்கள்"],
            "te": ["కంప్యూటర్", "ప్రింటర్"],
        },
        "allied": [
            {"code": "IS 616", "relation": "related — audio/video apparatus safety"},
            {"code": "IEC 62368-1", "relation": "related — newer hazard-based AV/ICT safety standard"},
        ],
        "certifications": [
            {
                "scheme": "Compulsory Registration Scheme (CRS)",
                "authority": "MeitY (Ministry of Electronics & IT)",
                "note": "IT equipment falls under MeitY CRS — require a valid CRS "
                        "registration number and BIS registration mark in the contract.",
            }
        ],
        "examples": [
            {
                "bad": "Citing only 'IS 13252' with no registration requirement",
                "good": "Specify IS 13252 (Part 1) and require a valid MeitY CRS registration number",
                "note": "Tenders that omit CRS registration have accepted non-registered electronics.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 616",
        "title": "Audio, Video and Similar Electronic Apparatus — Safety",
        "version": "2017 (aligned with IEC 60065) — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "electronics",
        "category": "Audio-visual equipment",
        "summary": (
            "Safety standard for televisions, speakers, set-top boxes and similar "
            "AV apparatus; covered items require MeitY CRS registration."
        ),
        "aliases": {
            "en": ["television", "tv", "speakers", "audio systems", "set top box",
                   "av equipment", "audio visual"],
            "hi": ["टेलीविजन", "टीवी", "स्पीकर"],
            "ta": ["தொலைக்காட்சி", "ஒலிபெருக்கி"],
        },
        "allied": [
            {"code": "IS 13252 (Part 1)", "relation": "related — IT equipment safety"},
            {"code": "IEC 62368-1", "relation": "related — successor hazard-based standard"},
        ],
        "certifications": [
            {
                "scheme": "Compulsory Registration Scheme (CRS)",
                "authority": "MeitY",
                "note": "Audio/video apparatus is a CRS item — registration mandatory before sale.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 10322 (Part 5)",
        "title": "Luminaires — Part 5: Particular Requirements (Fixed General Purpose Luminaires)",
        "version": "1988 (with amendments) — LED luminaires additionally assessed per notified requirements",
        "amendments": ["Verify current amendments for LED categories"],
        "status": "active",
        "sector": "electronics",
        "category": "Lighting",
        "summary": (
            "Safety standard for fixed luminaires. LED luminaires and LED lamps are "
            "MeitY CRS items — safety assessment plus registration applies."
        ),
        "aliases": {
            "en": ["luminaires", "led lights", "lighting fixtures", "street lights",
                   "office lighting", "led lamps", "lights"],
            "hi": ["बत्तियाँ", "एलईडी लाइट", "प्रकाश जुड़नार"],
            "ta": ["விளக்குகள்", "எல்இடி விளக்குகள்"],
        },
        "allied": [
            {"code": "IS 3646", "relation": "code — interior illumination practice"},
        ],
        "certifications": [
            {
                "scheme": "Compulsory Registration Scheme (CRS)",
                "authority": "MeitY",
                "note": "LED luminaires/lamps are CRS items — registration mandatory.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1554 (Part 1)",
        "title": "PVC Insulated (Heavy Duty) Electric Cables — Specification (up to 1100 V)",
        "version": "1988 (with amendments) — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "electronics",
        "category": "Cables & conductors",
        "summary": (
            "Heavy-duty PVC insulated cables for power distribution up to 1100 V. "
            "For internal house wiring up to 750 V, IS 694 is the matching standard."
        ),
        "aliases": {
            "en": ["cables", "pvc cables", "electrical cables", "power cables",
                   "low voltage cables", "wiring cables"],
            "hi": ["केबल", "बिजली के तार", "पावर केबल"],
            "ta": ["கேபிள்", "மின் கம்பிகள்"],
        },
        "allied": [
            {"code": "IS 694", "relation": "related — internal wiring cables up to 750 V"},
            {"code": "IS 7098", "relation": "related — XLPE cables (higher ratings)"},
            {"code": "IS 5831", "relation": "material — PVC insulation & sheath specification"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 694",
        "title": "PVC Insulated Cables for Internal Wiring of Electric Equipment — Specification (up to 750 V)",
        "version": "2010 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "electronics",
        "category": "Cables & conductors",
        "summary": (
            "House-wiring PVC cables up to 750 V — the standard commonly intended "
            "when tenders vaguely say 'electrical wiring cables'."
        ),
        "aliases": {
            "en": ["house wiring cables", "internal wiring", "wires", "electrical wires",
                   "building wiring"],
            "hi": ["घरेलू वायरिंग", "इलेक्ट्रिक वायर"],
            "ta": ["மின் கம்பி", "வீட்டு வயரிங்"],
        },
        "allied": [
            {"code": "IS 1554 (Part 1)", "relation": "related — heavy-duty cables to 1100 V"},
            {"code": "IS 1293", "relation": "related — plugs & socket-outlets"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1293",
        "title": "Plugs and Socket-Outlets of Rated Voltage up to and Including 250 V and Rated Current up to and Including 16 A",
        "version": "2019 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "electronics",
        "category": "Electrical accessories",
        "summary": (
            "Specification for domestic plugs and socket-outlets (6 A / 16 A). "
            "Long-standing mandatory BIS certification (ISI mark) applies."
        ),
        "aliases": {
            "en": ["sockets", "plugs", "plug points", "power sockets", "switches and sockets",
                   "electrical fittings", "switch sockets"],
            "hi": ["प्लग", "सॉकेट", "स्विच", "प्लग पॉइंट"],
            "ta": ["பிளக்", "சாக்கெட்"],
        },
        "allied": [
            {"code": "IS 3854", "relation": "related — switches for domestic purposes"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark)",
                "authority": "BIS",
                "note": "Plugs and socket-outlets carry long-standing mandatory "
                        "certification — ISI mark required.",
            }
        ],
        "examples": [
            {
                "bad": "'Electrical fittings as per applicable BIS standards'",
                "good": "Plugs/socket-outlets per IS 1293 (6 A / 16 A as applicable); switches per IS 3854",
                "note": "Open-ended 'applicable standards' clauses leave acceptance criteria unenforceable.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    # ------------------------------------------------------- CONSUMER APPLIANCES & ENERGY
    {
        "code": "IS 1391 (Part 1)",
        "title": "Room Air Conditioners — Specification (Unitary Type)",
        "version": "Part 1 edition as notified — verify current consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "appliances",
        "category": "Cooling appliances",
        "summary": (
            "Specification for unitary (window) room air conditioners; split units "
            "are covered by Part 2. Star labelling under BEE is mandatory for "
            "room air conditioners."
        ),
        "aliases": {
            "en": ["air conditioner", "ac", "split ac", "window ac", "cooling unit",
                   "air conditioning", "hvac units", "room cooler"],
            "hi": ["एयर कंडीशनर", "एसी", "ठंडा करने की मशीन", "कूलिंग यूनिट"],
            "ta": ["காற்றுச் சீரமைப்பான்", "ஏசி"],
            "te": ["ఎయిర్ కండిషనర్", "ఏసీ"],
        },
        "allied": [
            {"code": "IS 1391 (Part 2)", "relation": "related — split room air conditioners"},
        ],
        "certifications": [
            {
                "scheme": "BEE Star Rating",
                "authority": "Bureau of Energy Efficiency",
                "note": "Room air conditioners carry mandatory BEE star labelling — "
                        "specify the minimum star rating (e.g. 3-star) in the tender.",
            }
        ],
        "examples": [
            {
                "bad": "Query: 'cooling units for the new office block'",
                "good": "Room air conditioners → IS 1391 (Part 1)/(Part 2) + mandatory BEE star rating",
                "note": "Colloquial words like 'cooling unit' never match keyword search — "
                        "intent-based matching is exactly what this engine adds.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 15750",
        "title": "Household Refrigerating Appliances — Refrigerators and Freezers — Specification",
        "version": "2008 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "appliances",
        "category": "Cooling appliances",
        "summary": (
            "Household refrigerators and freezers; BEE star labelling is mandatory "
            "for this category."
        ),
        "aliases": {
            "en": ["refrigerator", "fridge", "freezer", "deep freezer",
                   "refridgerator", "frige", "cold storage cabinet"],
            "hi": ["फ्रिज", "रेफ्रिजरेटर", "फ्रीज़र"],
            "ta": ["குளிர்பதனப் பெட்டி", "ஃப்ரிட்ஜ்"],
        },
        "allied": [],
        "certifications": [
            {
                "scheme": "BEE Star Rating",
                "authority": "Bureau of Energy Efficiency",
                "note": "Refrigerators carry mandatory BEE star labelling.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    # ------------------------------------------------------------- WATER SUPPLY & SANITATION
    {
        "code": "IS 4984",
        "title": "High Density Polyethylene Pipes for Water Supply — Specification",
        "version": "2016 (5th revision) — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "water",
        "category": "Pipes & fittings",
        "summary": (
            "HDPE pipes for potable water supply — the standard intended by "
            "queries like 'drinking water pipes' or 'plastic water pipes'."
        ),
        "aliases": {
            "en": ["hdpe pipes", "drinking water pipes", "water pipes", "water supply pipes",
                   "plastic pipes", "polyethylene pipes", "pe pipes", "mdpe pipes"],
            "hi": ["पानी के पाइप", "एचडीपीई पाइप", "पेयजल पाइप"],
            "ta": ["நீர் குழாய்கள்", "குடிநீர் குழாய்"],
            "te": ["నీటి పైపులు", "పైపులు", "తాగునీటి పైపులు"],
        },
        "allied": [
            {"code": "IS 4985", "relation": "related — uPVC pipes for water supply"},
            {"code": "IS 10500", "relation": "normative context — drinking water quality"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 458",
        "title": "Prestressed Concrete Pipes (Non-Cylindrical and Cylindrical) — Specification",
        "version": "2003 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "water",
        "category": "Pipes & fittings",
        "summary": (
            "Prestressed concrete pipes for water mains and sewerage; allied test "
            "and laying codes are routinely missed in tenders."
        ),
        "aliases": {
            "en": ["concrete pipes", "cement pipes", "rc pipes", "drainage pipes",
                   "water mains", "sewer pipes"],
            "hi": ["सीमेंट पाइप", "कंक्रीट पाइप"],
            "ta": ["கான்க்ரீட் குழாய்"],
        },
        "allied": [
            {"code": "IS 3597", "relation": "method — tests for concrete pipes"},
            {"code": "IS 783", "relation": "code — laying of concrete pipes"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 10500",
        "title": "Drinking Water — Specification",
        "version": "2012 (with subsequent amendments) — verify consolidated edition",
        "amendments": ["Multiple amendments after 2012 — verify"],
        "status": "active",
        "sector": "water",
        "category": "Water quality",
        "summary": (
            "Acceptable limits for drinking water quality. The 1983 edition is "
            "superseded — legacy tenders still cite it."
        ),
        "aliases": {
            "en": ["drinking water quality", "water quality standards", "potable water"],
            "hi": ["पेयजल गुणवत्ता"],
            "ta": ["குடிநீர் தரம்"],
            "te": ["తాగునీటి నాణ్యత"],
        },
        "allied": [
            {"code": "IS 3025", "relation": "method — water analysis test methods (parts)"},
            {"code": "IS 14543", "relation": "related — packaged drinking water"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    # ------------------------------------------------------------------- FOOD & AGRICULTURE
    {
        "code": "IS 14543",
        "title": "Packaged Drinking Water (Other Than Packaged Natural Mineral Water) — Specification",
        "version": "2004 (with amendments) — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "food",
        "category": "Packaged foods",
        "summary": (
            "Packaged drinking water specification. Distinct from packaged natural "
            "MINERAL water (IS 13428) — the two categories are legally different "
            "and citing the wrong one invites disputes."
        ),
        "aliases": {
            "en": ["packaged drinking water", "bottled water", "water bottles",
                   "water pouches", "drinking water supply"],
            "hi": ["बोतलबंद पानी", "पैकेज्ड पेय जल"],
            "ta": ["குடிநீர் பாட்டில்", "அருந்ததுபவர் நீர்"],
            "te": ["ప్యాకెడ్ డ్రింకింగ్ వాటర్"],
        },
        "allied": [
            {"code": "IS 13428", "relation": "related — packaged natural mineral water (distinct standard)"},
            {"code": "IS 3025", "relation": "method — water analysis test methods"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) + FSSAI licence",
                "authority": "BIS / FSSAI",
                "note": "BIS certification is mandatory for packaged drinking water; "
                        "ISI mark required on every unit along with FSSAI licensing.",
            }
        ],
        "examples": [
            {
                "bad": "'Mineral water' specification citing IS 14543",
                "good": "Packaged drinking water → IS 14543; packaged natural mineral water → IS 13428",
                "note": "Mineral water and packaged drinking water are legally distinct categories.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    # ----------------------------------------------------------- INDUSTRIAL & SAFETY SUPPLIES
    {
        "code": "IS 2062",
        "title": "Hot Rolled Medium and High Tensile Structural Steel — Specification",
        "version": "2011 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "steel",
        "category": "Steel & metals",
        "summary": (
            "Structural steel plates, sheets and sections (E250 grades and above) "
            "for structural use. Several steel product categories fall under BIS "
            "Quality Control Orders — verify applicability for the specific form."
        ),
        "aliases": {
            "en": ["structural steel", "ms plates", "steel sections", "mild steel",
                   "steel plates", "steel beams", "ms steel"],
            "hi": ["स्टील", "इस्पात", "संरचनात्मक स्टील"],
            "ta": ["ஸ்டீல்", "கட்டமைப்பு எஃகு"],
        },
        "allied": [
            {"code": "IS 808", "relation": "related — steel section dimensions"},
            {"code": "IS 1786", "relation": "related — reinforcement bars (TMT)"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — QCO (verify scope)",
                "authority": "BIS",
                "note": "Iron & steel products have been notified under Quality Control "
                        "Orders in batches; confirm the current scope for the exact product form.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1786",
        "title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement — Specification",
        "version": "2008 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "steel",
        "category": "Steel & metals",
        "summary": (
            "TMT / high-strength deformed bars (Fe 415, Fe 500, Fe 550 grades) for "
            "concrete reinforcement — the standard intended by 'TMT bars' or "
            "'sariya' in everyday usage."
        ),
        "aliases": {
            "en": ["tmt bars", "tmt", "rebar", "reinforcement steel", "deformed bars",
                   "fe 500", "fe500", "reinforcement", "sariya", "saria"],
            "te": ["టీఎంటీ స్టీల్", "సరియా"],
            "hi": ["सरिया", "टीएमटी", "सुदृढ़ीकरण स्टील", "सरिया की छड़ें"],
            "ta": ["டிஎம்டி இரும்புக் கம்பிகள்", "இரும்புக் கம்பிகள்"],
        },
        "allied": [
            {"code": "IS 456", "relation": "usage — concrete works"},
            {"code": "IS 2751", "relation": "code — welding of reinforcement bars"},
            {"code": "IS 2502", "relation": "code — bending & fixing of reinforcement"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — QCO (verify scope)",
                "authority": "BIS",
                "note": "Reinforcement bars fall under notified steel QCO batches; "
                        "confirm current applicability.",
            }
        ],
        "examples": [
            {
                "bad": "'FE-415 bars as per IS 1139'",
                "good": "TMT bars per IS 1786, grade Fe 415/Fe 500 as specified",
                "note": "IS 1139 covers hot-rolled mild steel deformed bars; TMT "
                        "high-strength bars are specified by IS 1786.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 2925",
        "title": "Industrial Safety Helmets — Specification",
        "version": "1984 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "safety",
        "category": "Personal protective equipment",
        "summary": (
            "Industrial safety helmets (hard hats) — absorption and penetration "
            "resistance requirements for head protection at worksites."
        ),
        "aliases": {
            "en": ["safety helmet", "hard hat", "helmets", "head protection",
                   "safety caps", "ppe head protection"],
            "hi": ["सुरक्षा हेलमेट", "हेलमेट"],
            "ta": ["பாதுகாப்பு ஹெல்மெட்"],
        },
        "allied": [
            {"code": "IS 6994", "relation": "related — industrial safety belts & harnesses"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — verify scope",
                "authority": "BIS",
                "note": "Confirm current QCO applicability for the helmet category before tendering.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 15683",
        "title": "Portable Fire Extinguishers — Performance and Construction",
        "version": "2007 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "safety",
        "category": "Fire safety",
        "summary": (
            "Portable fire extinguishers (water, foam, CO2, dry powder types) — "
            "performance and construction requirements. Mandatory ISI certification "
            "applies to this category."
        ),
        "aliases": {
            "en": ["fire extinguisher", "extinguishers", "fire safety equipment",
                   "fire fighting", "fire safety"],
            "hi": ["अग्निशामक", "अग्नि सुरक्षा", "आग बुझाने का यंत्र"],
            "ta": ["தீயணைப்பி", "தீ பாதுகாப்பு"],
        },
        "allied": [
            {"code": "IS 2190", "relation": "code — maintenance of fire extinguishers"},
            {"code": "IS 2189", "relation": "code — fire alarm system design & installation"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark)",
                "authority": "BIS",
                "note": "Fire-fighting equipment has long been under mandatory BIS "
                        "certification — ISI mark required.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    # -------------------------------------------------------------------------- CEMENT
    {
        "code": "IS 269",
        "title": "Ordinary Portland Cement, 33 Grade — Specification",
        "version": "2015 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "cement",
        "category": "Cement",
        "summary": (
            "Ordinary Portland Cement, 33 grade. When specifying OPC, always state the "
            "grade explicitly (33/43/53) — 'OPC' alone leaves acceptance criteria open."
        ),
        "aliases": {
            "en": ["ordinary portland cement", "opc 33", "33 grade cement", "opc cement 33"],
            "hi": ["सीमेंट", "ओपीसी सीमेंट"],
            "ta": ["சிமெண்ட்"],
            "te": ["సిమెంట్"],
        },
        "allied": [
            {"code": "IS 4031", "relation": "method — physical tests of cement"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark)",
                "authority": "BIS",
                "note": "Cement is under long-standing mandatory BIS certification — "
                        "ISI mark required. Verify the current QCO schedule for the grade.",
            }
        ],
        "examples": [
            {
                "bad": "'OPC shall be used' (no grade, no standard)",
                "good": "OPC 43 per IS 8112 (or the grade actually intended), with test methods per IS 4031",
                "note": "Grade-less cement clauses make compressive-strength acceptance unenforceable.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 8112",
        "title": "Ordinary Portland Cement, 43 Grade — Specification",
        "version": "2013 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "cement",
        "category": "Cement",
        "summary": (
            "Ordinary Portland Cement, 43 grade — the workhorse grade for general "
            "construction. Verify the current consolidated edition before citation."
        ),
        "aliases": {
            "en": ["opc 43", "43 grade cement", "ordinary portland cement 43"],
            "hi": ["ओपीसी 43"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 4031", "relation": "method — physical tests of cement"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark)",
                "authority": "BIS",
                "note": "Cement is under long-standing mandatory BIS certification — ISI mark required.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 12269",
        "title": "Ordinary Portland Cement, 53 Grade — Specification",
        "version": "2013 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "cement",
        "category": "Cement",
        "summary": (
            "Ordinary Portland Cement, 53 grade — specified where higher early "
            "strength is required (precast, prestressed work). Verify edition."
        ),
        "aliases": {
            "en": ["opc 53", "53 grade cement", "ordinary portland cement 53"],
            "hi": ["ओपीसी 53"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 4031", "relation": "method — physical tests of cement"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark)",
                "authority": "BIS",
                "note": "Cement is under long-standing mandatory BIS certification — ISI mark required.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1489 (Part 1)",
        "title": "Portland Pozzolana Cement — Specification (Part 1: Fly Ash Based)",
        "version": "2015 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "cement",
        "category": "Cement",
        "summary": (
            "Portland Pozzolana Cement (fly-ash based). Distinct from OPC — cement "
            "type affects strength-gain schedule and acceptance tests, so BOQ items "
            "must name the type and the standard separately."
        ),
        "aliases": {
            "en": ["ppc", "ppc cement", "portland pozzolana cement", "fly ash cement"],
            "hi": ["पीपीसी सीमेंट"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 4031", "relation": "method — physical tests of cement"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark)",
                "authority": "BIS",
                "note": "Cement is under long-standing mandatory BIS certification — ISI mark required.",
            }
        ],
        "examples": [
            {
                "bad": "'PPC and OPC used interchangeably in the BOQ'",
                "good": "State cement type per item: OPC 43/53 per IS 8112/IS 12269; PPC per IS 1489 (Part 1)",
                "note": "Interchangeable cement clauses blur strength and durability obligations.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 455",
        "title": "Portland Slag Cement — Specification",
        "version": "2015 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "cement",
        "category": "Cement",
        "summary": (
            "Portland Slag Cement — used in marine and aggressive-environment "
            "concreting. Verify the current consolidated edition before citation."
        ),
        "aliases": {
            "en": ["slag cement", "portland slag cement", "psc cement"],
            "hi": ["स्लैग सीमेंट"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 4031", "relation": "method — physical tests of cement"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark)",
                "authority": "BIS",
                "note": "Cement is under long-standing mandatory BIS certification — ISI mark required.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 4031",
        "title": "Methods of Physical Tests for Hydraulic Cement (Parts 1–15)",
        "version": "Part-wise editions — verify part applicability",
        "amendments": [],
        "status": "active",
        "sector": "cement",
        "category": "Test methods",
        "summary": (
            "Multi-part test-method code for cement (fineness, setting time, "
            "soundness, compressive strength, etc.). Tenders that specify cement "
            "without IS 4031 leave acceptance testing undefined — cite the parts "
            "your acceptance schedule relies on."
        ),
        "aliases": {
            "en": ["cement test methods", "testing of cement", "cement laboratory tests",
                   "cement strength test"],
            "hi": ["सीमेंट परीक्षण"],
            "ta": [],
        },
        "allied": [],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    # ---------------------------------------------------- STEEL, FOUNDATIONS, ROADS
    {
        "code": "IS 800",
        "title": "General Construction in Steel — Code of Practice",
        "version": "2007 (3rd revision)",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Structural steel design",
        "summary": (
            "The limit-state code of practice for structural steel design. Any steel "
            "structure tender should pair it with the material standard (IS 2062) "
            "and relevant welding codes."
        ),
        "aliases": {
            "en": ["steel structure", "steel design", "structural steelwork",
                   "steel construction", "steel building", "limit state design steel"],
            "hi": ["स्टील संरचना", "इस्पात डिज़ाइन"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 2062", "relation": "material — structural steel"},
            {"code": "IS 875", "relation": "loading — design loads"},
            {"code": "IS 1893", "relation": "loading — earthquake loads"},
        ],
        "certifications": [],
        "examples": [
            {
                "bad": "IS 800:1984",
                "good": "IS 800:2007",
                "note": "The 1984 (working-stress) edition still appears in legacy schedules; "
                        "the 2007 limit-state edition replaced it.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 2911",
        "title": "Design and Construction of Pile Foundations — Code of Practice (Parts 1–4)",
        "version": "Part-wise editions — verify part applicability",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Foundations",
        "summary": (
            "Multi-part code covering driven, bored and under-reamed pile foundations. "
            "Cite the part matching the pile type; concrete in piles also falls under "
            "IS 456 general practice."
        ),
        "aliases": {
            "en": ["pile foundation", "piling", "bored piles", "driven piles",
                   "under reamed piles", "pile caps"],
            "hi": ["पाइल फाउंडेशन", "स्तंभ नींव"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 456", "relation": "usage — concrete works"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 73",
        "title": "Paving Bitumen — Specification",
        "version": "2013 (viscosity grading, VG grades)",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Road works",
        "summary": (
            "Paving bitumen for road works. The 2013 edition replaced penetration "
            "grading (80/100, 60/70) with viscosity grading (VG-10/20/30/40) — legacy "
            "penetration-grade citations reference the withdrawn scheme."
        ),
        "aliases": {
            "en": ["bitumen", "paving bitumen", "vg 30", "vg 10", "road bitumen",
                   "asphalt binder"],
            "hi": ["बिटुमेन", "डामर"],
            "ta": ["தார்"],
        },
        "allied": [],
        "certifications": [],
        "examples": [
            {
                "bad": "Bitumen grade 80/100 (penetration) per IS 73:1992",
                "good": "Paving bitumen VG-30 (as appropriate) per IS 73:2013",
                "note": "Penetration grading was withdrawn by the 2013 revision — "
                        "viscosity grades (VG-10/20/30/40) apply.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    # --------------------------------------------------------- WIRING & SWITCHGEAR
    {
        "code": "IS 7098 (Part 1)",
        "title": "Cross-Linked Polyethylene (XLPE) Insulated Cables — Specification (Part 1)",
        "version": "Part-wise editions — verify the part for your voltage rating",
        "amendments": [],
        "status": "active",
        "sector": "electronics",
        "category": "Cables & conductors",
        "summary": (
            "XLPE insulated power cables — commonly specified where higher operating "
            "temperature than PVC (IS 1554) is needed. Verify the part covering the "
            "voltage rating in your tender."
        ),
        "aliases": {
            "en": ["xlpe cables", "xlpe", "cross linked polyethylene cables",
                   "ht cables", "medium voltage cables"],
            "hi": ["एक्सएलपीई केबल"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 1554 (Part 1)", "relation": "related — PVC insulated cables"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 732",
        "title": "Code of Practice for Electrical Wiring Installations",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "electronics",
        "category": "Installations",
        "summary": (
            "Code of practice governing how electrical wiring installations are "
            "designed and executed — pairs naturally with the cable standards "
            "(IS 694, IS 1554) in building-services tenders."
        ),
        "aliases": {
            "en": ["wiring installation", "electrical installation code", "wiring code",
                   "house wiring practice", "installation practice electrical"],
            "hi": ["वायरिंग संहिता"],
            "ta": ["மின் வயரிங் முறை"],
        },
        "allied": [
            {"code": "IS 694", "relation": "material — internal wiring cables"},
            {"code": "IS 1554 (Part 1)", "relation": "material — heavy-duty cables"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 8828",
        "title": "Miniature Circuit-Breakers (MCB) for Household and Similar Installations",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "electronics",
        "category": "Electrical accessories",
        "summary": (
            "Miniature circuit-breakers for overcurrent protection in household and "
            "similar installations. Verify the current edition and certification "
            "applicability before tendering."
        ),
        "aliases": {
            "en": ["mcb", "mcbs", "circuit breaker", "miniature circuit breaker",
                   "distribution board breaker"],
            "hi": ["सर्किट ब्रेकर", "एमसीबी"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 1293", "relation": "related — plugs & socket-outlets"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    # -------------------------------------------------------------------- TOYS, PPE
    {
        "code": "IS 9873 (Part 1)",
        "title": "Safety of Toys — Part 1: Safety Aspects (Mechanical and Physical)",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "safety",
        "category": "Toys",
        "summary": (
            "Safety requirements for toys (mechanical and physical aspects). Toys "
            "have been notified under mandatory BIS certification via Quality Control "
            "Order — ISI mark applies."
        ),
        "aliases": {
            "en": ["toys", "children toys", "kids toys", "play items", "toy safety"],
            "hi": ["खिलौने", "खिलौना"],
            "ta": ["பொம்மைகள்"],
        },
        "allied": [],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — QCO",
                "authority": "BIS",
                "note": "Toys are covered under a mandatory certification Quality Control "
                        "Order — verify the current scheme requirements and exemptions.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 5983",
        "title": "Eye Protectors for Industrial Use — Specification",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "safety",
        "category": "Personal protective equipment",
        "summary": (
            "Industrial eye protection (goggles, face shields). Confirm current QCO "
            "applicability for the specific protector type before tendering."
        ),
        "aliases": {
            "en": ["safety goggles", "eye protection", "industrial goggles",
                   "safety glasses", "protective eyewear"],
            "hi": ["सुरक्षा चश्मा", "आंखों की सुरक्षा"],
            "ta": ["கண் பாதுகாப்பு"],
        },
        "allied": [
            {"code": "IS 2925", "relation": "related — industrial safety helmets"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    # --------------------------------------------------------------- HOUSEHOLD PPE
    {
        "code": "IS 302 (Part 1)",
        "title": "Household and Similar Electrical Appliances — Safety (Part 1: General Requirements)",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "appliances",
        "category": "Appliance safety",
        "summary": (
            "General safety requirements for household electrical appliances; "
            "part-two sections cover specific appliance families — verify the "
            "section matching your product, and check for energy-labelling "
            "obligations separately."
        ),
        "aliases": {
            "en": ["household appliances", "electrical appliance safety", "home appliances"],
            "hi": ["घरेलू उपकरण"],
            "ta": [],
        },
        "allied": [],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 2082",
        "title": "Electric Storage Water Heaters (Geysers) — Specification",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "appliances",
        "category": "Water heating",
        "summary": (
            "Electric storage water heaters for domestic and institutional use. "
            "Verify the current edition and any labelling obligations before tendering."
        ),
        "aliases": {
            "en": ["geyser", "geysers", "water heater", "hot water unit",
                   "storage water heater"],
            "hi": ["गीज़र", "पानी गर्म करने का उपकरण"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 302 (Part 1)", "relation": "safety — household appliance general safety"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },

    # =========================================================================
    # v0.2 EXPANSION (2026-09) — four new sectors (steel, pumps, furniture,
    # medical) plus entry versions of every allied/normative code the original
    # 40 entries referenced, so the allied graph is CLOSED: every IS code in
    # `allied` resolves to a catalogue entry (guarded by an integrity test).
    # =========================================================================

    # ------------------------------------------------------------- STEEL & METALS
    {
        "code": "IS 808",
        "title": "Dimensions of Hot Rolled Steel Beam, Column, Channel and Angle Sections",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "steel",
        "category": "Steel sections",
        "summary": (
            "Dimensional standard for hot-rolled structural sections (ISMB beams, "
            "channels, angles). Tenders that write 'ISMB 200' without this standard "
            "and the material standard (IS 2062) leave both geometry and grade open."
        ),
        "aliases": {
            "en": ["ismb", "steel beams", "i beams", "steel channels", "steel angles",
                   "steel sections", "column sections", "structural sections"],
            "hi": ["आई बीम", "इस्पात सेक्शन"],
            "ta": ["ஸ்டீல் கற்றைகள்"],
            "te": ["స్టీల్ సెక్షన్లు"],
        },
        "allied": [
            {"code": "IS 800", "relation": "usage — steel design code"},
            {"code": "IS 2062", "relation": "material — structural steel grade"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — QCO (verify scope)",
                "authority": "BIS",
                "note": "Hot-rolled steel products fall under notified steel QCO batches; "
                        "confirm applicability for the exact section type.",
            }
        ],
        "examples": [
            {
                "bad": "'Provide ISMB sections of standard make'",
                "good": "Sections per IS 808 in steel grade E250 per IS 2062",
                "note": "A section size without a material grade standard is not enforceable.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1239 (Part 1)",
        "title": "Steel Tubes for Water, Gas and Steam Purposes — Specification (Part 1: Hot Finished Welded Tubes)",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "steel",
        "category": "Steel tubes",
        "summary": (
            "The 'MS pipe' standard of everyday procurement — ERW mild steel tubes for "
            "plumbing, gas lines and general engineering. Specify the class (light / "
            "medium / heavy) alongside the standard."
        ),
        "aliases": {
            "en": ["ms pipes", "steel pipes", "erw pipes", "plumbing pipes", "gas pipes",
                   "mild steel tubes", "water steel pipes"],
            "hi": ["एमएस पाइप", "स्टील पाइप"],
            "ta": ["எஃகு குழாய்"],
            "te": ["స్టీల్ పైపులు"],
        },
        "allied": [
            {"code": "IS 1161", "relation": "related — structural steel tubes"},
            {"code": "IS 2062", "relation": "material — base steel grades"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — QCO (verify scope)",
                "authority": "BIS",
                "note": "Steel tubes are covered under notified steel QCO batches; verify "
                        "current applicability.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1161",
        "title": "Steel Tubes for Structural Purposes — Specification",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "steel",
        "category": "Steel tubes",
        "summary": (
            "Structural hollow/tube sections used in trusses, scaffolding supports and "
            "tubular structures — distinct from the water/gas tubes of IS 1239."
        ),
        "aliases": {
            "en": ["structural tubes", "hollow sections", "scaffolding tubes",
                   "square tubes", "circular hollow sections", "tube trusses"],
            "hi": ["स्ट्रक्चरल ट्यूब"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 1239 (Part 1)", "relation": "related — water/gas service tubes"},
            {"code": "IS 2062", "relation": "material — base steel grades"},
            {"code": "IS 808", "relation": "related — open sections"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 816",
        "title": "Code of Practice for Use of Metal Arc Welding for General Construction",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "steel",
        "category": "Welding",
        "summary": (
            "Governs how metal-arc welding is executed in steel construction. Steel "
            "fabrication tenders that cite only the material standard omit the welding "
            "code, electrode standard and weld inspection — all three are allied here."
        ),
        "aliases": {
            "en": ["welding code", "metal arc welding", "welding practice",
                   "arc welding", "fabrication welding"],
            "hi": ["वेल्डिंग संहिता"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 814", "relation": "material — covered electrodes"},
            {"code": "IS 9595", "relation": "method — welding procedure recommendations"},
            {"code": "IS 822", "relation": "method — inspection of welds"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 814",
        "title": "Covered Electrodes for Manual Metal Arc Welding of Carbon and Carbon Manganese Steels — Specification",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "steel",
        "category": "Welding",
        "summary": (
            "Specification for welding electrodes. Fabrication tenders that forget to "
            "specify electrodes accept any rod on site — a classic quality loophole."
        ),
        "aliases": {
            "en": ["welding electrodes", "ms electrodes", "welding rods", "electrodes"],
            "hi": ["वेल्डिंग इलेक्ट्रोड"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 816", "relation": "usage — welding code of practice"},
            {"code": "IS 9595", "relation": "method — welding procedure"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — verify applicability",
                "authority": "BIS",
                "note": "Welding consumables have been progressively notified under "
                        "Quality Control Orders — confirm the current scope.",
            }
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 9595",
        "title": "Metal-Arc Welding of Carbon and Carbon Manganese Steels — Recommendations",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "steel",
        "category": "Welding",
        "summary": "Procedure recommendations that IS 816 and electrode supply depend on.",
        "aliases": {
            "en": ["welding procedure", "wps recommendations", "welding recommendations"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 816", "relation": "usage — welding code of practice"},
            {"code": "IS 814", "relation": "material — electrodes"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 822",
        "title": "Code of Procedure for Inspection of Welds",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "steel",
        "category": "Welding",
        "summary": (
            "How welded joints are inspected and accepted. Without this code a steel "
            "tender has no weld acceptance criteria at all."
        ),
        "aliases": {
            "en": ["weld inspection", "weld acceptance", "inspection of welds"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 816", "relation": "usage — welding code of practice"},
            {"code": "IS 814", "relation": "material — electrodes"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 4759",
        "title": "Hot-Dip Zinc Coatings on Structural Steel and Other Related Products — Specification",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "steel",
        "category": "Protective coatings",
        "summary": (
            "Galvanizing requirements for structural steel. Corrosion protection is "
            "routinely forgotten in outdoor steel tenders until the first repaint bill."
        ),
        "aliases": {
            "en": ["galvanizing", "galvanised coating", "zinc coating",
                   "hot dip galvanizing", "galvanized steel work"],
            "hi": ["गैल्वनाइज़िंग"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 2062", "relation": "material — base structural steel"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },

    # ------------------------------------------------- PUMPS & FLUID MACHINERY
    {
        "code": "IS 9079",
        "title": "Monoset Pumps for Clear, Cold Water for Agricultural and Water Supply Purposes — Specification",
        "version": "2018 (3rd revision)",
        "amendments": [],
        "status": "active",
        "sector": "pumps",
        "category": "Pumps",
        "summary": (
            "The monoblock/monoset pump standard — what 'water pump' or 'agricultural "
            "pump' almost always means in procurement. Covered by the Pumps Quality "
            "Control Order along with IS 8034 and IS 8472."
        ),
        "aliases": {
            "en": ["monoblock pump", "monobloc pump", "monoset pump", "monoset pumps",
                   "centrifugal monoblock pumps", "agricultural pumps", "water pumps"],
            "hi": ["मोनोब्लॉक पंप", "पानी का पंप", "कृषि पंप"],
            "ta": ["மோனோபிளாக் பம்ப்"],
            "te": ["మోనోబ్లాక్ పంపు"],
        },
        "allied": [
            {"code": "IS 5120", "relation": "method — technical requirements for rotodynamic pumps"},
            {"code": "IS 11346", "relation": "method — efficiency testing of pumpsets"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — Pumps QCO",
                "authority": "BIS",
                "note": "Water pumps are covered by the Pumps (Quality Control) Order — "
                        "ISI-marked units are mandatory. Verify the current schedule.",
            },
            {
                "scheme": "BEE Star Rating — pumpsets (verify schedule)",
                "authority": "Bureau of Energy Efficiency",
                "note": "Energy labelling obligations for pumpsets have been progressively "
                        "notified — confirm the current BEE schedule.",
            },
        ],
        "examples": [
            {
                "bad": "'Supply of water pumps of reputed make'",
                "good": "Monoset pumpsets per IS 9079:2018, ISI-marked, with efficiency tests per IS 11346",
                "note": "'Reputed make' is unenforceable; the QCO makes ISI marking non-negotiable.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 8034",
        "title": "Submersible Pumpsets — Specification",
        "version": "2018 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "pumps",
        "category": "Pumps",
        "summary": (
            "Borewell submersible pumpsets — the standard behind 'borewell pump' "
            "queries. Pumps QCO item; specify stage count and discharge class explicitly."
        ),
        "aliases": {
            "en": ["submersible pump", "borewell pump", "submersible pumpset",
                   "bore well pumps", "borewell pumps"],
            "hi": ["सबमर्सिबल पंप", "बोरवेल पंप"],
            "ta": ["மூழ்கும் பம்ப்"],
            "te": ["సబ్మర్సిబుల్ పంపు"],
        },
        "allied": [
            {"code": "IS 11346", "relation": "method — efficiency testing of pumpsets"},
            {"code": "IS 5120", "relation": "method — technical requirements"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — Pumps QCO",
                "authority": "BIS",
                "note": "Submersible pumpsets are Pumps QCO items — ISI mark mandatory.",
            },
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 8472",
        "title": "Regenerative Self-Priming Pumps for Clear, Cold Fresh Water — Specification",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "pumps",
        "category": "Pumps",
        "summary": (
            "Self-priming domestic and small-community water pumps; Pumps QCO item."
        ),
        "aliases": {
            "en": ["self priming pump", "regenerative pumps", "domestic water pumps"],
            "hi": ["सेल्फ प्राइमिंग पंप"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 5120", "relation": "method — technical requirements"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — Pumps QCO",
                "authority": "BIS",
                "note": "Listed among pumps covered by the Quality Control Order.",
            },
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 5120",
        "title": "Technical Requirements for Rotodynamic Pumps",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "pumps",
        "category": "Pump methods",
        "summary": (
            "Cross-cutting technical requirements the pump product standards lean on — "
            "routine companion code in pump tenders."
        ),
        "aliases": {
            "en": ["pump technical requirements", "rotodynamic pumps"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 9079", "relation": "product — monoset pumps"},
            {"code": "IS 8034", "relation": "product — submersible pumpsets"},
            {"code": "IS 8472", "relation": "product — self-priming pumps"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 11346",
        "title": "Tests for Agricultural and Water Supply Pumpsets — Method",
        "version": "2002 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "pumps",
        "category": "Pump methods",
        "summary": (
            "Efficiency and performance testing of pumpsets. Cite it whenever a pump "
            "tender promises an efficiency figure — otherwise acceptance is unmeasurable."
        ),
        "aliases": {
            "en": ["pump efficiency test", "pump testing", "pumpset tests"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 9079", "relation": "product — monoset pumps"},
            {"code": "IS 8034", "relation": "product — submersible pumpsets"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },

    # --------------------------------------- FURNITURE & OFFICE EQUIPMENT
    {
        "code": "IS 11525",
        "title": "Wooden Chairs for Office Purposes — Specification",
        "version": "1986 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "furniture",
        "category": "Office furniture",
        "summary": (
            "Wooden office chairs. Furniture purchases without a standard accept "
            "staple-glued assemblies that fail within a year."
        ),
        "aliases": {
            "en": ["office chairs", "wooden chairs", "staff chairs", "executive chairs",
                   "work chairs"],
            "hi": ["कुर्सी", "ऑफिस कुर्सी", "कार्यालय कुर्सी"],
            "ta": ["நாற்காலி", "அலுவலக நாற்காலி"],
            "te": ["కుర్చీ", "ఆఫీస్ కుర్చీలు"],
        },
        "allied": [
            {"code": "IS 11679", "relation": "related — office tables"},
            {"code": "IS 303", "relation": "material — plywood components"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 11679",
        "title": "Wooden Tables for Office Use — Specification",
        "version": "1986 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "furniture",
        "category": "Office furniture",
        "summary": (
            "Wooden office tables/desks — workmanship, dimensions, glue-adhesion and "
            "finish requirements. Pair with IS 11525 for full office furniture supply."
        ),
        "aliases": {
            "en": ["office tables", "wooden tables", "office desks", "study tables"],
            "hi": ["मेज", "ऑफिस मेज", "डेस्क"],
            "ta": ["மேசை"],
            "te": ["టేబుల్", "ఆఫీస్ టేబుల్"],
        },
        "allied": [
            {"code": "IS 11525", "relation": "related — office chairs"},
            {"code": "IS 303", "relation": "material — plywood components"},
        ],
        "certifications": [],
        "examples": [
            {
                "bad": "'Wooden furniture as per approved sample'",
                "good": "Office tables per IS 11679 and chairs per IS 11525",
                "note": "Sample-only furniture clauses give no testable acceptance criteria.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },

    # ------------------------------------------ MEDICAL & HOSPITAL SUPPLIES
    {
        "code": "IS 16289",
        "title": "Medical Textiles — Surgical Face Masks — Specification",
        "version": "2014 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "medical",
        "category": "Medical textiles",
        "summary": (
            "Surgical face masks (bacterial filtration, splash resistance). Mask "
            "tenders must state the standard AND registration status — '3-ply masks' "
            "alone is not a specification."
        ),
        "aliases": {
            "en": ["face masks", "surgical masks", "3 ply masks", "medical masks",
                   "surgical face masks"],
            "hi": ["फेस मास्क", "सर्जिकल मास्क"],
            "ta": ["முகக்கவசம்"],
            "te": ["ఫేస్ మాస్క్", "సర్జికల్ మాస్క్"],
        },
        "allied": [],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — verify applicability",
                "authority": "BIS",
                "note": "Confirm current QCO/registration scope for the mask category "
                        "before tendering; medical devices additionally fall under the "
                        "Drugs and Cosmetics Rules/MDR 2017 (CDSCO).",
            },
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 13422",
        "title": "Single-Use Sterile Rubber Surgical Gloves — Specification",
        "version": "2024 (first revision, aligned with ISO 10282:2023)",
        "amendments": [],
        "status": "active",
        "sector": "medical",
        "category": "Hospital consumables",
        "summary": (
            "Sterile surgical gloves for operation theatres. A 2024 revision replaced "
            "the 1992 edition — legacy tenders still cite IS 13422:1992. A QCO for "
            "medical gloves has been notified/drafted (verify current status)."
        ),
        "aliases": {
            "en": ["surgical gloves", "sterile gloves", "operation theatre gloves",
                   "ot gloves"],
            "hi": ["सर्जिकल दस्ताने"],
            "ta": ["அறுவை கையுறைகள்"],
            "te": ["సర్జికల్ గ్లవ్స్"],
        },
        "allied": [
            {"code": "IS 15354 (Part 1)", "relation": "related — examination gloves"},
            {"code": "IS 4905", "relation": "method — random sampling for acceptance"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — Medical Gloves QCO (verify)",
                "authority": "BIS",
                "note": "A Quality Control Order covering surgical and examination gloves "
                        "has been progressed — verify the current notification before "
                        "tendering.",
            },
        ],
        "examples": [
            {
                "bad": "IS 13422:1992",
                "good": "IS 13422:2024 (single-use sterile rubber surgical gloves)",
                "note": "The 1992 disposable-glove edition is superseded by the 2024 revision.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 15354 (Part 1)",
        "title": "Single-Use Medical Examination Gloves — Specification (Part 1: Rubber)",
        "version": "2023 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "medical",
        "category": "Hospital consumables",
        "summary": (
            "Non-sterile examination gloves (Part 1 covers rubber; verify the part for "
            "other materials such as nitrile). Distinct from sterile surgical gloves "
            "(IS 13422) — hospital tenders routinely blur the two."
        ),
        "aliases": {
            "en": ["examination gloves", "disposable gloves", "latex gloves",
                   "medical examination gloves"],
            "hi": ["परीक्षण दस्ताने"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 13422", "relation": "related — sterile surgical gloves"},
            {"code": "IS 4905", "relation": "method — random sampling"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — Medical Gloves QCO (verify)",
                "authority": "BIS",
                "note": "Covered by the medical-gloves QCO process — verify current status.",
            },
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 4905",
        "title": "Methods for Random Sampling",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "medical",
        "category": "Test & sampling methods",
        "summary": (
            "Statistical random-sampling method referenced by acceptance schedules "
            "for consumables such as gloves and masks."
        ),
        "aliases": {
            "en": ["random sampling", "sampling method", "acceptance sampling"],
            "hi": [],
            "ta": [],
        },
        "allied": [],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },

    # ------------------------------------------- DOORS (QCO-NOTIFIED, CONSTRUCTION)
    {
        "code": "IS 2191 (Part 1)",
        "title": "Wooden Flush Door Shutters (Cellular and Hollow Core Type) with Plywood Face Panels — Specification",
        "version": "2022",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Doors & shutters",
        "summary": (
            "Flush door shutters with plywood faces — notified under BIS mandatory "
            "certification for furniture/wood products; ISI mark applies."
        ),
        "aliases": {
            "en": ["flush doors", "wooden doors", "door shutters", "hollow core doors"],
            "hi": ["दरवाजे", "लकड़ी के दरवाजे"],
            "ta": ["கதவுகள்"],
            "te": ["తలుపులు"],
        },
        "allied": [
            {"code": "IS 303", "relation": "material — plywood face panels"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — QCO",
                "authority": "BIS",
                "note": "Wooden flush door shutters are under mandatory certification — "
                        "ISI mark required.",
            },
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 2191 (Part 2)",
        "title": "Wooden Flush Door Shutters (Cellular and Hollow Core Type) with Particle Board and Hardboard Face Panels — Specification",
        "version": "2022",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Doors & shutters",
        "summary": (
            "Flush door shutters with particle-board/hardboard faces — QCO-notified "
            "companion to IS 2191 (Part 1)."
        ),
        "aliases": {
            "en": ["flush doors", "wooden doors", "door shutters", "particle board doors"],
            "hi": ["दरवाजे", "लकड़ी के दरवाजे"],
            "ta": ["கதவுகள்"],
            "te": ["తలుపులు"],
        },
        "allied": [
            {"code": "IS 303", "relation": "related — plywood alternative faces"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) — QCO",
                "authority": "BIS",
                "note": "Wooden flush door shutters are under mandatory certification.",
            },
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },

    # ---------------------------------- KITCHEN APPLIANCES (QCO-LONG-STANDING)
    {
        "code": "IS 2347",
        "title": "Domestic Pressure Cookers — Specification",
        "version": "2023 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "appliances",
        "category": "Kitchen appliances",
        "summary": (
            "Domestic pressure cookers — among the longest-standing mandatory BIS "
            "certification items; only ISI-marked cookers may be sold in India."
        ),
        "aliases": {
            "en": ["pressure cooker", "pressure cookers", "cookers", "domestic pressure cookers"],
            "hi": ["प्रेशर कुकर", "कुकर"],
            "ta": ["பிரஷர் குக்கர்"],
            "te": ["ప్రెషర్ కుక్కర్"],
        },
        "allied": [],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark)",
                "authority": "BIS",
                "note": "Domestic pressure cookers cannot legally be sold without BIS "
                        "certification — insist on the ISI mark in the contract.",
            },
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },

    # ------------------------------------------------------------------ CONCRETE METHODS
    {
        "code": "IS 516",
        "title": "Method of Tests for Strength of Concrete",
        "version": "2021 (Part 1, Section 1 — compressive strength) — verify part applicability",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Test methods",
        "summary": (
            "Cube/cylinder strength testing of concrete. The 2021 revision restructured "
            "it into parts — blanket 'IS 516' citations should name the part relied on."
        ),
        "aliases": {
            "en": ["concrete testing", "compressive strength test", "concrete cube test",
                   "strength of concrete", "concrete strength"],
            "hi": ["कंक्रीट परीक्षण"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 456", "relation": "usage — concrete code of practice"},
            {"code": "IS 10262", "relation": "related — mix proportioning"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 10262",
        "title": "Guidelines for Concrete Mix Design Proportioning",
        "version": "2019 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Test methods",
        "summary": (
            "How designed mixes are proportioned for specified grades — the companion "
            "to IS 456 acceptance requirements."
        ),
        "aliases": {
            "en": ["mix design", "concrete mix proportioning", "mix proportioning"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 456", "relation": "usage — concrete code of practice"},
            {"code": "IS 516", "relation": "method — strength verification"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 2386",
        "title": "Methods of Test for Aggregates for Concrete (Parts 1–8)",
        "version": "1963 (reaffirmed) — verify part applicability",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Test methods",
        "summary": "The multi-part test battery behind IS 383 aggregate acceptance.",
        "aliases": {
            "en": ["aggregate testing", "aggregate tests", "aggregate quality tests"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 383", "relation": "material — aggregate specification"},
            {"code": "IS 2430", "relation": "method — sampling of aggregates"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 2430",
        "title": "Methods for Sampling of Aggregates for Concrete",
        "version": "1986 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Test methods",
        "summary": "How aggregate lots are sampled before IS 2386 testing.",
        "aliases": {
            "en": ["aggregate sampling"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 2386", "relation": "method — aggregate tests"},
            {"code": "IS 383", "relation": "material — aggregate specification"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },

    # ------------------------------------------------------------------ MASONRY METHODS
    {
        "code": "IS 3495 (Parts 1–4)",
        "title": "Methods of Tests of Burnt Clay Building Bricks (Parts 1–4)",
        "version": "1992 — verify part applicability",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Test methods",
        "summary": (
            "Determination of compressive strength, water absorption, efflorescence "
            "and warpage of bricks — the acceptance battery for IS 1077 supplies."
        ),
        "aliases": {
            "en": ["brick testing", "brick water absorption test",
                   "brick compressive strength", "brick tests"],
            "hi": ["ईंट परीक्षण"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 1077", "relation": "material — brick specification"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1905",
        "title": "Code of Practice for Structural Use of Unreinforced Masonry",
        "version": "1987 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Masonry design",
        "summary": "Structural design rules for masonry built from IS 1077 bricks.",
        "aliases": {
            "en": ["masonry design", "structural masonry", "masonry code"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 1077", "relation": "material — bricks"},
            {"code": "IS 2212", "relation": "code — brickwork execution"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 2212",
        "title": "Code of Practice for Brickwork",
        "version": "1991 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Masonry construction",
        "summary": "Execution practice for brickwork — mortar, bonds, tolerances.",
        "aliases": {
            "en": ["brickwork", "brick laying", "masonry construction"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 1077", "relation": "material — bricks"},
            {"code": "IS 1905", "relation": "code — masonry design"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1734",
        "title": "Methods of Test for Plywood (Parts 1–20)",
        "version": "Part-wise editions — verify part applicability",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Test methods",
        "summary": "The test battery behind IS 303 plywood acceptance (glue adhesion etc.).",
        "aliases": {
            "en": ["plywood testing", "plywood tests"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 303", "relation": "material — plywood specification"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 3646 (Part 1)",
        "title": "Code of Practice for Interior Illumination (Part 1)",
        "version": "1992 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "electronics",
        "category": "Lighting design",
        "summary": (
            "Interior illumination design practice — pairs with luminaire safety "
            "(IS 10322) in lighting tenders."
        ),
        "aliases": {
            "en": ["interior illumination", "lighting design", "illumination code"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 10322 (Part 5)", "relation": "product — luminaires"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 5831",
        "title": "PVC Insulation and Sheath of Electric Cables — Specification",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "electronics",
        "category": "Cable materials",
        "summary": "The insulation/sheath material standard behind IS 694 and IS 1554 cables.",
        "aliases": {
            "en": ["pvc compound", "cable insulation material", "pvc insulation"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 1554 (Part 1)", "relation": "usage — heavy-duty cables"},
            {"code": "IS 694", "relation": "usage — internal wiring cables"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 3854",
        "title": "Switches for Domestic Purposes — Specification",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "electronics",
        "category": "Electrical accessories",
        "summary": (
            "Domestic switches (light/board switches). Long-standing mandatory ISI "
            "certification applies."
        ),
        "aliases": {
            "en": ["switches", "light switches", "electrical switches", "board switches",
                   "modular switches"],
            "hi": ["स्विच", "बोर्ड स्विच"],
            "ta": ["ஸ்விச்"],
            "te": ["స్విచ్"],
        },
        "allied": [
            {"code": "IS 1293", "relation": "related — plugs & socket-outlets"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark)",
                "authority": "BIS",
                "note": "Domestic switches carry long-standing mandatory BIS certification.",
            },
        ],
        "examples": [
            {
                "bad": "'Modular switches of reputed make'",
                "good": "Switches per IS 3854 with valid ISI mark",
                "note": "'Reputed make' cannot be enforced; the ISI mark can.",
            }
        ],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 1391 (Part 2)",
        "title": "Room Air Conditioners — Specification (Part 2: Split Type)",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "appliances",
        "category": "Cooling appliances",
        "summary": "Split room air conditioners — mandatory BEE star labelling applies.",
        "aliases": {
            "en": ["split ac", "split air conditioner", "split units"],
            "hi": ["स्प्लिट एसी"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 1391 (Part 1)", "relation": "related — unitary (window) units"},
        ],
        "certifications": [
            {
                "scheme": "BEE Star Rating",
                "authority": "Bureau of Energy Efficiency",
                "note": "Room air conditioners carry mandatory BEE star labelling — state "
                        "the minimum star rating in the tender.",
            },
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },

    # ------------------------------------------------------------ WATER METHODS & PIPES
    {
        "code": "IS 4985",
        "title": "Unplasticized PVC (uPVC) Pipes for Water Supply — Specification",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "water",
        "category": "Pipes & fittings",
        "summary": (
            "uPVC water-supply pipes — what many 'PVC pipe' tenders actually need; "
            "distinct from HDPE (IS 4984)."
        ),
        "aliases": {
            "en": ["upvc pipes", "pvc pipes", "pvc water pipes"],
            "hi": ["पीवीसी पाइप"],
            "te": ["పీవీసీ పైపులు"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 4984", "relation": "related — HDPE pipes"},
            {"code": "IS 10500", "relation": "normative context — drinking water quality"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 3597",
        "title": "Method of Hydrostatic Testing of Concrete Pipes",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "water",
        "category": "Test methods",
        "summary": "Acceptance testing behind IS 458 concrete pipe supplies.",
        "aliases": {
            "en": ["hydrostatic testing", "pipe testing"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 458", "relation": "material — concrete pipes"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 783",
        "title": "Code of Practice for Laying of Concrete Pipes",
        "version": "1985 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "water",
        "category": "Installation",
        "summary": "Bedding, laying and jointing practice for concrete pipe mains.",
        "aliases": {
            "en": ["pipe laying", "concrete pipe laying", "pipeline construction"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 458", "relation": "material — concrete pipes"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 3025",
        "title": "Methods of Sampling and Test (Physical and Chemical) for Water (Parts 1–60+)",
        "version": "Part-wise editions — verify part applicability",
        "amendments": [],
        "status": "active",
        "sector": "water",
        "category": "Test methods",
        "summary": (
            "The water-analysis test battery behind IS 10500 (drinking water) and "
            "packaged-water acceptance. Name the parts your acceptance schedule uses."
        ),
        "aliases": {
            "en": ["water testing", "water analysis methods", "water quality tests"],
            "hi": ["जल परीक्षण"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 10500", "relation": "context — drinking water limits"},
            {"code": "IS 14543", "relation": "context — packaged drinking water"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 13428",
        "title": "Packaged Natural Mineral Water — Specification",
        "version": "2005 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "food",
        "category": "Packaged foods",
        "summary": (
            "Packaged natural MINERAL water — the legally distinct category from "
            "packaged drinking water (IS 14543). Both are BIS-mandatory."
        ),
        "aliases": {
            "en": ["mineral water", "packaged mineral water"],
            "hi": ["खनिज जल"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 14543", "relation": "related — packaged drinking water (distinct)"},
            {"code": "IS 3025", "relation": "method — water analysis"},
        ],
        "certifications": [
            {
                "scheme": "BIS Product Certification (ISI Mark) + FSSAI licence",
                "authority": "BIS / FSSAI",
                "note": "BIS certification is mandatory for packaged natural mineral water; "
                        "ISI mark on every unit plus FSSAI licensing.",
            },
        ],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },

    # ----------------------------------------------------- REINFORCEMENT & FIRE PRACTICE
    {
        "code": "IS 2751",
        "title": "Code of Practice for Welding of Mild Steel Bars Used in Reinforced Concrete Construction",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Reinforcement practice",
        "summary": "Rules for welding reinforcement bars — cited whenever bars are butted or spliced.",
        "aliases": {
            "en": ["bar welding", "reinforcement welding"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 1786", "relation": "material — high strength deformed bars"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 2502",
        "title": "Code of Practice for Bending and Fixing of Bars for Concrete Reinforcement",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "construction",
        "category": "Reinforcement practice",
        "summary": "Bar-bending schedule practice — pairs with IS 1786 material supply.",
        "aliases": {
            "en": ["bar bending", "bar bending schedule", "reinforcement fixing"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 1786", "relation": "material — reinforcement bars"},
            {"code": "IS 456", "relation": "usage — concrete works"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 6994",
        "title": "Industrial Safety Belts and Harnesses — Specification",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "safety",
        "category": "Personal protective equipment",
        "summary": "Fall-protection belts and harnesses for work at height.",
        "aliases": {
            "en": ["safety belts", "safety harness", "full body harness", "fall protection"],
            "hi": ["सुरक्षा बेल्ट", "हार्नेस"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 2925", "relation": "related — safety helmets"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 2190",
        "title": "Code of Practice for Selection, Installation and Maintenance of Portable First-Aid Fire Extinguishers",
        "version": "1992 — verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "safety",
        "category": "Fire safety",
        "summary": "How extinguishers are placed, inspected and maintained after purchase.",
        "aliases": {
            "en": ["fire extinguisher maintenance", "extinguisher installation",
                   "extinguisher placement"],
            "hi": [],
            "ta": [],
        },
        "allied": [
            {"code": "IS 15683", "relation": "product — portable extinguishers"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
    {
        "code": "IS 2189",
        "title": "Code of Practice for Selection, Installation and Maintenance of Automatic Fire Alarm Systems",
        "version": "verify consolidated edition",
        "amendments": [],
        "status": "active",
        "sector": "safety",
        "category": "Fire safety",
        "summary": "Fire alarm system design/installation — the missed companion in fire-safety packages.",
        "aliases": {
            "en": ["fire alarm", "fire alarm system", "smoke detectors", "alarm installation"],
            "hi": ["फायर अलार्म"],
            "ta": [],
        },
        "allied": [
            {"code": "IS 15683", "relation": "related — extinguishers"},
        ],
        "certifications": [],
        "examples": [],
        "last_reviewed": "2026-09-29",
    },
]


# ------------------------------------------------------------- snapshot merge
# Offline-imported rows (bis_engine/data/generated/bis_catalog.json, produced by
# `python -m bis_engine.data.importers.bis_snapshot`) extend the seed at import
# time. Seed records stay authoritative: snapshot rows never shadow them unless
# the importer ran with --force (recorded as "force": true in the payload).
_GENERATED_PATH = Path(__file__).resolve().parent / "generated" / "bis_catalog.json"


def _load_generated_payload() -> dict:
    try:
        payload = json.loads(_GENERATED_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _merge_snapshot_records(seed: list[dict]) -> list[dict]:
    payload = _load_generated_payload()
    records = payload.get("records", [])
    if not isinstance(records, list):
        return list(seed)

    def _nc(code: str) -> str:  # normalize_code is defined further below
        return re.sub(r"\s+", " ", str(code).strip().lower())

    merged = list(seed)
    by_key = {_nc(s["code"]): i for i, s in enumerate(merged)}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        key = _nc(str(rec.get("code", "")))
        if not key:
            continue
        if key in by_key:
            if rec.get("force"):
                merged[by_key[key]] = {**seed[by_key[key]], **rec}
            continue
        by_key[key] = len(merged)
        merged.append(rec)
    return merged


_snapshot_payload = _load_generated_payload()
_snapshot_count = len(_snapshot_payload.get("records", []) or [])

STANDARDS = _merge_snapshot_records(_SEED_STANDARDS)

SYNC_HEALTH = {
    "mode": "seed+snapshot" if _snapshot_count else "seed",
    "last_synced": _snapshot_payload.get("imported_on") or LAST_SYNCED,
    "source_note": (
        f"Curated seed catalogue + {_snapshot_count} offline-imported snapshot record(s) "
        "(demo). Live BIS reconciliation not configured."
    ) if _snapshot_count else
    "Curated seed catalogue (demo). Live BIS reconciliation not configured.",
    "snapshot_records": _snapshot_count,
}


def all_standards() -> list[dict]:
    return STANDARDS


_PART_SUFFIX_RE = re.compile(r"\s*\(\s*part\s*\d+\s*\)\s*$", re.IGNORECASE)


def get_by_code(code: str) -> dict | None:
    """Loose code match.

    'IS 13252' matches 'IS 13252 (Part 1)' (part-less citation resolves to the
    part entry); 'IS 13252 (Part 1)' matches exactly; case/spacing-insensitive.
    """
    norm = normalize_code(code)
    for std in STANDARDS:
        if normalize_code(std["code"]) == norm:
            return std
    for std in STANDARDS:
        base = _PART_SUFFIX_RE.sub("", std["code"]).strip().lower()
        if normalize_code(base) == norm:
            return std
    return None


def normalize_code(code: str) -> str:
    return re.sub(r"\s+", " ", code.strip().lower())
