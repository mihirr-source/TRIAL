"""Tests for the BIS Standards Recommendation Engine MVP.

Run from project root:  python -m pytest tests/bis_engine/ -v
"""

import pytest

from bis_engine.data.catalog import SECTORS, all_standards, get_by_code
from bis_engine.engine.analyzer import TenderAnalyzer
from bis_engine.engine.normalize import detect_script, normalize_text
from bis_engine.engine.retriever import StandardsRetriever


@pytest.fixture(scope="module")
def retriever():
    return StandardsRetriever()


@pytest.fixture(scope="module")
def analyzer(retriever):
    return TenderAnalyzer(retriever)


# --------------------------------------------------------------------- data
def test_catalogue_loads_with_required_fields():
    standards = all_standards()
    assert len(standards) >= 80
    required = {"code", "title", "version", "amendments", "status", "sector",
                "aliases", "allied", "certifications", "examples", "last_reviewed"}
    for std in standards:
        missing = required - set(std)
        assert not missing, f"{std.get('code')} missing {missing}"
        # Guard against tuple/None slips from hand-edited entries:
        for field in ("title", "summary", "version", "category"):
            assert isinstance(std.get(field), str), f"{std['code']}.{field} must be a string"
        assert std["sector"] in SECTORS, f"{std['code']} has unknown sector {std['sector']}"
        assert isinstance(std["allied"], list) and isinstance(std["certifications"], list)


def test_v02_expansion_sectors_present():
    """v0.2 adds steel / pumps / furniture / medical coverage."""
    sectors = {s["sector"] for s in all_standards()}
    assert {"steel", "pumps", "furniture", "medical"} <= sectors


def test_allied_graph_is_closed():
    """Every IS code referenced in `allied` must resolve to a catalogue entry.

    (Non-IS references such as IEC codes are allowed to stay external.)
    """
    for std in all_standards():
        for ref in std["allied"]:
            code = ref["code"]
            if code.upper().startswith("IS"):
                assert get_by_code(code) is not None, (
                    f"{std['code']} references unknown allied code {code}")


def test_aliases_have_english_vocabulary():
    """Retrieval depends on the alias vocabulary — every entry needs English words."""
    for std in all_standards():
        assert std["aliases"].get("en"), f"{std['code']} has no English aliases"


def test_get_by_code_loose_matching():
    assert get_by_code("IS 13252")["code"] == "IS 13252 (Part 1)"
    assert get_by_code("is 4984")["code"] == "IS 4984"
    assert get_by_code("IS 99999") is None


# ---------------------------------------------------------------- normalization
def test_normalize_text():
    assert normalize_text("TMT  Bars  Fe-500") == "tmt bars fe-500"
    assert normalize_text("pipes/pipe;slabs") == "pipes pipe slabs"


def test_detect_script():
    assert detect_script("pure english text") == "en"
    assert detect_script("पानी के पाइप") == "hi"
    assert detect_script("நீர் குழாய்") == "ta"
    assert detect_script("12345 !!!") == "unknown"


# ------------------------------------------------- feature 1: semantic search
def test_search_maps_cooling_unit_to_ac(retriever):
    """Colloquial 'cooling unit' must reach the air-conditioner standard."""
    res = retriever.search("cooling unit for the new office block")
    assert res["primary"] is not None
    assert res["primary"]["standard"]["code"] == "IS 1391 (Part 1)"
    assert res["primary"]["score"] >= 0.4


def test_search_drinking_water_pipes(retriever):
    res = retriever.search("drinking water pipes")
    assert res["primary"]["standard"]["code"] == "IS 4984"


def test_search_colloquial_sariya(retriever):
    res = retriever.search("sariya for roof casting")
    assert res["primary"]["standard"]["code"] == "IS 1786"


def test_search_colloquial_ms_pipes(retriever):
    res = retriever.search("ms pipes for plumbing lines")
    assert res["primary"]["standard"]["code"] == "IS 1239 (Part 1)"


def test_search_water_pump_maps_to_is_9079(retriever):
    res = retriever.search("monoblock water pumps for the lift irrigation scheme")
    assert res["primary"]["standard"]["code"] == "IS 9079"


def test_search_telugu_query(retriever):
    res = retriever.search("నీటి పైపులు")
    assert res["primary"] is not None
    assert res["primary"]["standard"]["sector"] == "water"


def test_search_pressure_cooker_isi(retriever):
    res = retriever.search("pressure cookers for staff quarters")
    assert res["primary"]["standard"]["code"] == "IS 2347"
    assert res["primary"]["standard"]["certifications"]


def test_search_hindi_query(retriever):
    """Multilingual support: Hindi input resolves to the right standard."""
    res = retriever.search("पानी के पाइप")
    assert res["primary"] is not None
    assert res["primary"]["standard"]["code"] == "IS 4984"
    assert res["primary"]["matched_aliases"]


def test_search_tamil_query(retriever):
    res = retriever.search("நீர் குழாய்")
    assert res["primary"] is not None
    assert res["primary"]["standard"]["sector"] == "water"


def test_search_returns_alternatives(retriever):
    res = retriever.search("electrical cables for building wiring")
    assert res["primary"]["standard"]["code"] in {"IS 1554 (Part 1)", "IS 694"}
    assert len(res["alternatives"]) >= 1


def test_search_empty_query(retriever):
    assert retriever.search_all("   ") == []


# --------------------------------------------- feature 2: allied mapping
def test_analyzer_flags_missing_allied_standards(analyzer):
    """Concrete + bricks without test/measurement standards => allied gaps."""
    report = analyzer.analyze("Supply of common burnt clay bricks for the boundary wall.")
    codes = [a["code"] for a in report["allied_missing"]]
    assert "IS 3495 (Parts 1–4)" in codes  # brick test methods
    assert all(a["required_by"] == "IS 1077" for a in report["allied_missing"] if a["code"] == "IS 3495")


def test_analyzer_no_allied_gap_when_cited(analyzer):
    """Citing the allied standard in the text suppresses the gap."""
    report = analyzer.analyze(
        "Supply of common burnt clay bricks. Tests as per IS 3495 shall be done.")
    codes = [a["code"] for a in report["allied_missing"]]
    assert "IS 3495" not in codes


# ------------------------------------- feature 3: version control / obsolete
def test_analyzer_flags_outdated_edition(analyzer):
    report = analyzer.analyze(
        "Concrete works for the lab building shall conform to IS 456:1978.")
    flagged_codes = [f["code"] for f in report["obsolete_flags"]]
    assert "IS 456" in flagged_codes
    assert report["checks"][3]["status"] == "fail"


def test_analyzer_flags_unknown_code(analyzer):
    report = analyzer.analyze("Steel structure shall conform to IS 12345.")
    assert any(f["code"].startswith("IS 12345") for f in report["obsolete_flags"])


def test_analyzer_latest_version_in_results(analyzer):
    """Recommendations carry the version and amendments we hold."""
    report = analyzer.analyze("Supply of HDPE pipes for the drinking water scheme.")
    primary = report["primaries"][0]
    assert primary["code"] == "IS 4984"
    assert primary["version"]
    assert "version" in primary and "amendments" in primary


# ------------------------------------ feature 4: mandatory certification alerts
def test_analyzer_alerts_for_crs_electronics(analyzer):
    report = analyzer.analyze(
        "Supply and installation of desktop computers and printers for the office.")
    schemes = [c["scheme"] for c in report["certifications"]]
    assert any("CRS" in s for s in schemes)
    assert any(s["authority"].startswith("MeitY") for s in report["certifications"])


def test_analyzer_alerts_for_bee_appliances(analyzer):
    report = analyzer.analyze("Split type air conditioners for the new training hall.")
    schemes = " ".join(c["scheme"] for c in report["certifications"])
    assert "BEE" in schemes


def test_analyzer_alerts_for_isi_packaged_water(analyzer):
    report = analyzer.analyze("Supply of packaged drinking water 20 litre jars.")
    assert report["certifications"], "packaged drinking water must raise BIS/FSSAI alert"
    schemes = " ".join(c["scheme"] for c in report["certifications"])
    assert "ISI" in schemes or "FSSAI" in schemes


def test_certifications_endpoint_data():
    from bis_engine.main import certifications
    data = certifications()
    assert data["count"] >= 3  # grouped: BIS Product Certification, CRS, BEE
    schemes = {s["scheme"] for s in data["schemes"]}
    assert any("CRS" in s for s in schemes)
    assert any("BEE" in s for s in schemes)
    isi = next(s for s in data["schemes"] if "ISI" in s["scheme"])
    assert len(isi["standards"]) >= 2  # grouped across standards


# ----------------------------------------- report structure and edge cases
def test_report_structure(analyzer):
    report = analyzer.analyze(
        "Supply of safety helmets and fire extinguishers for the warehouse.")
    for key in ("meta", "primaries", "allied_missing", "certifications",
                "obsolete_flags", "checks"):
        assert key in report
    assert report["meta"]["disclaimer"]
    assert len(report["checks"]) == 4
    found = {p["code"] for p in report["primaries"]}
    assert "IS 2925" in found and "IS 15683" in found


def test_analyzer_min_length_enforced(analyzer):
    with pytest.raises(ValueError):
        analyzer.analyze("short")


def test_analyzer_detects_language_label(analyzer):
    report = analyzer.analyze("पेयजल हेतु प्लास्टिक के पाइप की आपूर्ति कीजिए।")
    assert report["meta"]["detected_language"] == "hi"
    assert "Devanagari" in report["meta"]["detected_language_label"]


# --------------------------------------------------- expansion coverage (v0.2)
def test_cement_flow_includes_test_methods(analyzer):
    """Cement mentions must surface IS 4031 as a missing allied test-method code."""
    report = analyzer.analyze("Supply of OPC 43 grade cement in bags for all concrete works.")
    codes = [p["code"] for p in report["primaries"]]
    assert "IS 8112" in codes
    missing = [a["code"] for a in report["allied_missing"]]
    assert "IS 4031" in missing


def test_bitumen_penetration_grade_flagged(analyzer):
    """Legacy penetration-grade bitumen citations must be flagged."""
    report = analyzer.analyze(
        "Paving bitumen for the BT road works shall conform to IS 73:1992, grade 80/100.")
    codes = [p["code"] for p in report["primaries"]]
    assert "IS 73" in codes
    assert any(f["code"] == "IS 73" and "penetration" in f.get("reason", "").lower()
               for f in report["obsolete_flags"])


def test_geyser_colloquialism_maps_to_water_heater(retriever):
    res = retriever.search("geysers for staff quarters")
    assert res["primary"]["standard"]["code"] == "IS 2082"


def test_wiring_flow_bundles_materials_and_practice(analyzer):
    report = analyzer.analyze(
        "Complete internal wiring of the office building with PVC insulated cables.")
    codes = {p["code"] for p in report["primaries"]}
    assert codes & {"IS 694", "IS 732"}
    missing = [a["code"] for a in report["allied_missing"]]
    assert "IS 1554 (Part 1)" in missing or "IS 732" in missing
