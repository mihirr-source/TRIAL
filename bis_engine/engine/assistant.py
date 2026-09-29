"""Plain-language standards assistant.

Two modes:
  1. **Template mode (default, offline):** intent detection over the user's
     message, then a reply composed *only* from the catalogue — title, simple
     explanation, version, allied standards, certifications. Deterministic,
     zero API keys, demo-safe, and structurally incapable of inventing codes.
  2. **LLM mode (optional):** if BIS_LLM_API_KEY is set, Gemini models are used to
     give plain, direct, and conversational explanations grounded by verified
     catalogue standards.

Languages: en / hi / te (matches the UI switcher).
"""

from __future__ import annotations

import os
import re

from bis_engine.data.catalog import get_by_code
from bis_engine.engine.normalize import detect_script

_LANGS = ("en", "hi", "te")

# ---------------------------------------------------------------- intents
_CODE_RE = re.compile(r"\bis\s*\d{1,5}(?:\s*\(\s*part\s*\d+\s*\))?", re.IGNORECASE)
_EXPLAIN_RE = re.compile(r"\b(what|explain|tell|about|mean|kya|क्या|అంటే)\b", re.IGNORECASE)
_RECOMMEND_RE = re.compile(
    r"(which|what)\s+(standard|is\s*code|code)s?\b.*\b(for|ke\s*liye|के\s*लिए|కోసం)\b"
    r"|\bstandard\s+for\b|\bcode\s+for\b|के\s*लिए\s*(कौन|कोन)|కోసం\s*ఏ", re.IGNORECASE)
_CERT_RE = re.compile(r"\b(certifi|isi\s*mark|crs|hallmark|star\s*rating|qco|"
                      r"प्रमाण|गुणवत्ता\s*चिह्न)\w*", re.IGNORECASE)
_VERSION_RE = re.compile(r"\b(latest|current\s*version|new\s*edition|नवीनतम|తాజా)\b", re.IGNORECASE)

# ------------------------------------------------- simple-language explainers
_SIMPLE: dict[str, dict[str, str]] = {
    "IS 456": {
        "en": "the rulebook for reinforced concrete work — how concrete structures are designed and built safely.",
        "hi": "कंक्रीट निर्माण का मूल नियम-पुस्तक — सुरक्षित ढांचे कैसे डिज़ाइन और निर्मित होते हैं।",
        "te": "కాంక్రీటు నిర్మాణానికి ప్రాథమిక నియమావళి — భద్రతగల నిర్మాణాలు ఎలా రూపొందించబడతాయి.",
    },
    "IS 1786": {
        "en": "the standard for TMT/reinforcement steel bars (Fe 415/500/550) that give concrete its strength.",
        "hi": "कंक्रीट को मज़बूती देने वाली टीएमटी सरिया (Fe 415/500/550) का मानक।",
        "te": "కాంక్రీటుకు బలం ఇచ్చే టీఎంటీ స్టీల్ కడతల (Fe 415/500/550) ప్రమద.",
    },
    "IS 4984": {
        "en": "the standard for HDPE plastic pipes used to carry drinking water.",
        "hi": "पीने के पानी ले जाने वाले HDPE प्लास्टिक पाइप का मानक।",
        "te": "తాగునీరు తీసుకెళ్లే HDPE ప్లాస్టిక్ పైపుల ప్రమద.",
    },
    "IS 1391 (Part 1)": {
        "en": "the specification for window-type room air conditioners; split ACs are covered by Part 2.",
        "hi": "विंडो-टाइप एयर कंडीशनर की विनिर्देशिका; स्प्लिट एसी पार्ट 2 में आते हैं।",
        "te": "విండో రకం ఎయిర్ కండిషనర్ల వివరణ; స్ప్లిట్ ఏసీలు పార్ట్ 2లో ఉంటాయి.",
    },
    "IS 13252 (Part 1)": {
        "en": "the safety standard for computers, printers and similar IT equipment — they also need MeitY CRS registration.",
        "hi": "कंप्यूटर, प्रिंटर जैसे आईटी उपकरणों का सुरक्षा मानक — MeitY CRS पंजीकरण भी अनिवार्य है।",
        "te": "కంప్యూటర్లు, ప్రింటర్ల భద్రతా ప్రమద — MeitY CRS నమోదు కూడా తప్పనిసరి.",
    },
    "IS 14543": {
        "en": "the standard for packaged drinking water (bottles/jars) — BIS certification is mandatory, plus FSSAI licence.",
        "hi": "बोतलबंद पेय जल का मानक — BIS प्रमाणन अनिवार्य है, FSSAI लाइसेंस भी चाहिए।",
        "te": "ప్యాకెడ్ డ్రింకింగ్ వాటర్ ప్రమద — BIS ధృవీకరణ తప్పనిసరి, FSSAI లైసెన్స్ కూడా.",
    },
    "IS 694": {
        "en": "the standard for house-wiring cables (up to 750 V) — what 'electrical wire' usually means.",
        "hi": "घर की वायरिंग केबल (750 V तक) का मानक — 'बिजली का तार' से यही तात्पर्य होता है।",
        "te": "ఇంటి వైరింగ్ కేబుల్స్ (750 V వరకు) ప్రమద.",
    },
    "IS 1077": {
        "en": "the specification for common burnt clay building bricks and their strength classes.",
        "hi": "ईंटों की विनिर्देशिका — शक्ति श्रेणियों सहित।",
        "te": "ఇటుకల వివరణ — బల శ్రేణులతో సహా.",
    },
    "IS 9079": {
        "en": "the standard for monoblock water pumps used in farms and water supply — ISI mark is mandatory under the Pumps QCO.",
        "hi": "कृषि और जल आपूर्ति के मोनोब्लॉक पंप का मानक — पंप QCO के अंतर्गत ISI चिह्न अनिवार्य है।",
        "te": "వ్యవసాయం, నీటి సరఫరా మోనోబ్లాక్ పంపుల ప్రమద — Pumps QCO కింద ISI మార్క్ తప్పనిసరి.",
    },
    "IS 8034": {
        "en": "the standard for borewell submersible pumpsets.",
        "hi": "बोरवेल सबमर्सिबल पंपसेट का मानक।",
        "te": "బోర్‌వెల్ సబ్మర్సిబుల్ పంపుల ప్రమద.",
    },
    "IS 2347": {
        "en": "the standard for domestic pressure cookers — they cannot legally be sold in India without the ISI mark.",
        "hi": "घरेलू प्रेशर कुकर का मानक — ISI चिह्न के बिना भारत में बिकना कानूनन वर्जित है।",
        "te": "గృహ ప్రెషర్ కుక్కర్ల ప్రమద — ISI మార్క్ లేకుండా భారతదేశంలో అమ్మడం చట్టవిరుద్ధం.",
    },
    "IS 13422": {
        "en": "the standard for single-use sterile surgical gloves used in operation theatres (2024 revision).",
        "hi": "ऑपरेशन थिएटर के स्टेराइल सर्जिकल दस्तानों का मानक (2024 संशोधन)।",
        "te": "ఆపరేషన్ థియేటర్ల శస్త్రచికిత్స గ్లవ్స్ ప్రమద (2024 సవరణ).",
    },
    "IS 2062": {
        "en": "the standard for structural steel plates and sections (E250 grades and above).",
        "hi": "संरचनात्मक इस्पात प्लेटों और सेक्शन का मानक (E250 ग्रेड और ऊपर)।",
        "te": "నిర్మాణ స్టీల్ ప్లేట్లు, సెక్షన్ల ప్రమద (E250 గ్రేడ్ మరియు అంతకు పైను).",
    },
    "IS 1239 (Part 1)": {
        "en": "the 'MS pipe' standard — mild steel tubes for plumbing and gas lines.",
        "hi": "'एमएस पाइप' का मानक — प्लंबिंग और गैस लाइनों के लिए।",
        "te": "'ఎంఎస్ పైప్' ప్రమద — ప్లంబింగ్, గ్యాస్ లైన్ల కోసం.",
    },
    "IS 10500": {
        "en": "the drinking-water quality standard — the limits water must meet to be safe.",
        "hi": "पेयजल गुणवत्ता का मानक — सुरक्षित पानी की सीमाएँ।",
        "te": "తాగునీటి నాణ్యత ప్రమద — సురక్షిత నీటి పరిమితులు.",
    },
    "IS 383": {
        "en": "the standard for sand and coarse aggregates (crushed stone) used in concrete.",
        "hi": "कंक्रीट में प्रयुक्त रेत और गिट्टी (एग्रीगेट) का मानक।",
        "te": "కాంక్రీటులో వాడే ఇసుక, గుల్లల (అగ్రిగేట్) ప్రమద.",
    },
    "IS 1554 (Part 1)": {
        "en": "the standard for heavy-duty PVC power cables (up to 1100 V).",
        "hi": "भारी-दायित्व पीवीसी पावर केबल (1100 V तक) का मानक।",
        "te": "హెవీ-డ్యూటీ PVC పవర్ కేబుల్స్ (1100 V వరకు) ప్రమద.",
    },
    "IS 3854": {
        "en": "the standard for domestic electrical switches — long-standing mandatory ISI certification.",
        "hi": "घरेलू बिजली के स्विच का मानक — लंबे समय से ISI प्रमाणन अनिवार्य।",
        "te": "గృహ విద్యుత్ స్విచ్‌ల ప్రమద — ISI ధృవీకరణ చాలా కాలంగా తప్పనిసరి.",
    },
    "IS 4985": {
        "en": "the standard for uPVC (PVC) pipes used for water supply.",
        "hi": "जल आपूर्ति के uPVC (पीवीसी) पाइप का मानक।",
        "te": "నీటి సరఫరా uPVC (PVC) పైపుల ప్రమద.",
    },
    "IS 8112": {
        "en": "the standard for OPC 43-grade cement — the common general-construction grade.",
        "hi": "OPC 43-ग्रेड सीमेंट का मानक — सामान्य निर्माण का प्रचलित ग्रेड।",
        "te": "OPC 43-గ్రేడ్ సిమెంట్ ప్రమద — సాధారణ నిర్మాణ గ్రేడ్.",
    },
}

# ------------------------------------------------------------------ templates
_T = {
    "explain": {
        "en": ("**{code} — {title}**\n\n{simple}\n\n"
               "Current Version: {version}.{cert}"),
        "hi": ("**{code} — {title}**\n\n{simple}\n\n"
               "वर्तमान संस्करण: {version}।{cert}"),
        "te": ("**{code} — {title}**\n\n{simple}\n\n"
               "ప్రస్తుత ఎడిషన్: {version}.{cert}"),
    },
    "recommend": {
        "en": ("For “{topic}”, the standard is **{code} — {title}** ({version}).\n\n{extras}"),
        "hi": ("“{topic}” के लिए मानक **{code} — {title}** ({version}) है।\n\n{extras}"),
        "te": ("“{topic}” కోసం ప్రమద **{code} — {title}** ({version}).\n\n{extras}"),
    },
    "cert": {
        "en": ("Products under **{code} — {title}** require mandatory certification:\n{list}"),
        "hi": ("**{code} — {title}** के उत्पादों के लिए अनिवार्य प्रमाणन:\n{list}"),
        "te": ("**{code} — {title}** కింద ఉత్పత్తులకు తప్పనిసరి ధృవీకరణ:\n{list}"),
    },
    "version": {
        "en": ("**{code}** — current edition is {version}.{amd}\n\n{example}"),
        "hi": ("**{code}** — वर्तमान संस्करण {version} है।{amd}\n\n{example}"),
        "te": ("**{code}** — ప్రస్తుత ఎడిషన్ {version}.{amd}\n\n{example}"),
    },
    "help": {
        "en": ("I can explain any Indian Standard in plain words. For example:\n"
               "• “What is IS 456?”\n• “Which standard for drinking water pipes?”\n"
               "• “Does a pressure cooker need ISI mark?”\n• “Latest version of IS 1786?”"),
        "hi": ("मैं किसी भी भारतीय मानक को आसान भाषा में समझा सकता हूँ। उदाहरण:\n"
               "• “IS 456 क्या है?”\n• “पीने के पानी के पाइप के लिए मानक?”\n"
               "• “प्रेशर कुकर पर ISI अनिवार्य है?”\n• “IS 1786 का नया संस्करण?”"),
        "te": ("నేను భారతీయ ప్రమదాలను సులభ భాషలో వివరిస్తాను. ఉదాహరణకు:\n"
               "• “IS 456 అంటే ఏమిటి?”\n• “తాగునీటి పైపులకు ఏ ప్రమద?”\n"
               "• “ప్రెషర్ కుక్కర్‌కి ISI తప్పనిసరా?”\n• “IS 1786 తాజా ఎడిషన్?”"),
    },
}


def _norm_lang(lang: str | None, message: str) -> str:
    key = (lang or "").strip().lower()
    if key in _LANGS:
        return key
    detected = detect_script(message)
    return detected if detected in _LANGS else "en"


def _cert_lines(std: dict, lang: str) -> str:
    certs = std.get("certifications", [])
    if not certs:
        return ""
    lead = {"en": " Certification: ", "hi": " प्रमाणन: ", "te": " ధృవీకరణ: "}[lang]
    return lead + "; ".join(c["scheme"] for c in certs) + "."


def _allied_line(std: dict, lang: str) -> str:
    allied = std.get("allied", []) or []
    if not allied:
        return ""
    lead = {"en": "Allied standards: ", "hi": "संबद्ध मानक: ", "te": "అనుబంధ ప్రమదాలు: "}[lang]
    refs = ", ".join(a["code"] for a in allied[:5])
    return f"{lead}{refs}."


class StandardsAssistant:
    """Grounded, plain-language Q&A over the standards catalogue."""

    def __init__(self, retriever):
        self.retriever = retriever
        self.llm_enabled = bool(os.environ.get("BIS_LLM_API_KEY"))
        self.llm_model = os.environ.get("BIS_LLM_MODEL", "gemini-2.5-flash")

    # ------------------------------------------------------------------ public
    def answer(self, message: str, lang: str | None = None,
               history: list[dict] | None = None) -> dict:
        message = (message or "").strip()
        lang_key = _norm_lang(lang, message)
        intent, payload = self._route(message)

        # Retrieve relevant catalogue standards as grounded context
        hits = self.retriever.search_all(payload or message, top_k=3)
        sources = [h["standard"]["code"] for h in hits if "standard" in h]

        # 1. LLM mode (Active when BIS_LLM_API_KEY is configured):
        if self.llm_enabled:
            llm_text = self._llm_reply(message, lang_key, sources, history)
            if llm_text:
                return {"reply": llm_text, "sources": sources, "mode": "llm",
                        "intent": intent, "lang": lang_key}

        # 2. Template / Grounded mode fallback:
        if intent == "explain":
            reply, src = self._explain(payload, lang_key)
        elif intent == "certification":
            reply, src = self._certification(payload, lang_key)
        elif intent == "version":
            reply, src = self._version(payload, lang_key)
        elif intent == "recommend":
            reply, src = self._recommend(payload, lang_key)
        else:
            if hits:
                best = hits[0]["standard"]
                reply, src = self._explain(best["code"], lang_key)
            else:
                reply, src = self._help(lang_key)
        
        if src:
            sources = src

        return {"reply": reply, "sources": sources, "mode": "template",
                "intent": intent, "lang": lang_key}

    # ----------------------------------------------------------------- routing
    def _route(self, message: str) -> tuple[str, str]:
        code_match = _CODE_RE.search(message)
        if _CERT_RE.search(message):
            topic = code_match.group(0) if code_match else self._topic_after(message)
            return "certification", topic
        if _VERSION_RE.search(message) and code_match:
            return "version", code_match.group(0)
        if code_match and (_EXPLAIN_RE.search(message) or len(message) <= 40):
            return "explain", code_match.group(0)
        if _RECOMMEND_RE.search(message):
            return "recommend", self._topic_after(message)
        if code_match:
            return "explain", code_match.group(0)
        return "general", message

    @staticmethod
    def _topic_after(message: str) -> str:
        """Extract the product topic from a recommendation question."""
        before = re.search(r"(.+?)\s*(?:के\s*लिए|కోసం)", message)
        if before:
            return before.group(1).strip(" ?.!।")
        after = re.search(r"(?:\bfor\b|కోసం)\s+(.+?)[?.!।]*$", message, re.IGNORECASE)
        if after:
            return after.group(1).strip(" ?.!।")
        cleaned = re.sub(r"\b(which|what|standard|code|is)\b", " ", message,
                         flags=re.IGNORECASE).strip(" ?.!।")
        return cleaned or message

    # ---------------------------------------------------------------- builders
    def _explain(self, code: str, lang: str) -> tuple[str, list[str]]:
        std = get_by_code(code)
        if not std:
            hits = self.retriever.search_all(code, top_k=1)
            std = hits[0]["standard"] if hits else None
        if not std:
            return self._help(lang)
        simple = _SIMPLE.get(std["code"], {}).get(lang) or _SIMPLE.get(std["code"], {}).get("en")
        if not simple:
            summary = (std.get("summary") or std["title"]).split(". ")[0].rstrip(".") + "."
            simple = {"en": summary, "hi": f"सारांश: {summary}", "te": f"సారాంశం: {summary}"}[lang]
        reply = _T["explain"][lang].format(
            code=std["code"], title=std["title"], simple=simple,
            version=std.get("version", "—"), cert=_cert_lines(std, lang))
        return reply, [std["code"]]

    def _recommend(self, topic: str, lang: str) -> tuple[str, list[str]]:
        hits = self.retriever.search_all(topic, top_k=3)
        if not hits:
            return self._help(lang)
        best = hits[0]["standard"]
        extras = _allied_line(best, lang).rstrip("\n")
        cert = _cert_lines(best, lang).strip()
        if cert:
            extras = (extras + "\n\n" + cert) if extras else cert
        reply = _T["recommend"][lang].format(
            topic=topic[:120], code=best["code"], title=best["title"],
            version=best.get("version", "—"), extras=extras)
        return reply, [h["standard"]["code"] for h in hits]

    def _certification(self, code_or_topic: str, lang: str) -> tuple[str, list[str]]:
        std = get_by_code(code_or_topic) if _CODE_RE.search(code_or_topic or "") else None
        if std is None:
            hits = self.retriever.search_all(code_or_topic or "", top_k=1)
            std = hits[0]["standard"] if hits else None
        if std is None or not std.get("certifications"):
            return self._help(lang)
        items = "\n".join(f"• {c['scheme']} ({c['authority']})" for c in std["certifications"])
        reply = _T["cert"][lang].format(code=std["code"], title=std["title"], list=items)
        return reply, [std["code"]]

    def _version(self, code: str, lang: str) -> tuple[str, list[str]]:
        std = get_by_code(code)
        if not std:
            return self._help(lang)
        example = ""
        for ex in std.get("examples", []):
            if ex.get("bad"):
                example = f"⚠ Known pitfall: `{ex['bad']}` → use **{ex['good']}**."
                break
        amd = ""
        if std.get("amendments"):
            amd = " Amendments: " + "; ".join(std["amendments"]) + "."
        reply = _T["version"][lang].format(
            code=std["code"], version=std.get("version", "—"), amd=amd, example=example)
        return reply, [std["code"]]

    def _help(self, lang: str) -> tuple[str, list[str]]:
        return _T["help"][lang], []

    # -------------------------------------------------------------- LLM (opt.)
    def _llm_reply(self, message: str, lang: str, sources: list[str],
                   history: list[dict] | None) -> str | None:
        """Plain-language LLM generation via Gemini. Returns None on failure."""
        api_key = os.environ.get("BIS_LLM_API_KEY")
        if not api_key:
            return None

        context = []
        for code in (sources or [])[:4]:
            std = get_by_code(code)
            if std:
                certs = [c["scheme"] for c in std.get("certifications", [])]
                allied = [a["code"] for a in std.get("allied", [])[:3]]
                context.append(f"- {std['code']}: {std['title']} (Version: {std.get('version', '—')}; Certifications: {certs}; Allied: {allied})")

        lang_name = {"en": "English", "hi": "Hindi (Devanagari script)",
                     "te": "Telugu (Telugu script)"}.get(lang, "English")

        prompt = (
            "You are a helpful, clear, and direct standards assistant for Indian Standards (Bureau of Indian Standards / BIS).\n"
            f"Target Language: {lang_name}\n\n"
            "Guidelines:\n"
            "1. Give plain, straightforward, and direct answers in easy-to-understand language.\n"
            "2. Explain what the standard is for, relevant specifications, materials, or certification requirements (such as ISI mark, CRS, BEE, etc.).\n"
            "3. Cite verified Indian Standards (IS codes) clearly.\n"
            "4. Keep the explanation natural, concise, and easy for any person or procurement officer to understand.\n\n"
        )
        if context:
            prompt += "Reference Catalogue Standards:\n" + "\n".join(context) + "\n\n"
        
        prompt += f"User Question: {message}\n\nPlain Answer:"

        # Try google.generativeai
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.llm_model)
            resp = model.generate_content(prompt)
            text = (getattr(resp, "text", "") or "").strip()
            if text:
                return text
        except Exception:
            pass

        # Try google.genai client fallback
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            resp = client.models.generate_content(model=self.llm_model, contents=prompt)
            text = (getattr(resp, "text", "") or "").strip()
            if text:
                return text
        except Exception:
            pass

        return None
