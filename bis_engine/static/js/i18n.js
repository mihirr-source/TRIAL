/* i18n: English / हिन्दी / తెలుగు — attribute-driven translation layer.
 *
 * Usage: put data-i18n="key" on elements (textContent), data-i18n-ph="key"
 * for placeholders, data-i18n-title="key" for title attributes. Dynamic
 * strings come from window.t(key). Choice persists in localStorage and is
 * re-applied on every page (loaded before the page scripts).
 */
"use strict";

const I18N = {
  en: {
    "nav.home": "Home",
    "nav.standards": "Explore Standards",
    "nav.analyzer": "Tender Analyzer",
    "nav.alerts": "Compliance Alerts",
    "nav.assistant": "AI Assistant",
    "nav.docs": "API Docs",
    "brand": "BIS Standards Assistant",
    "home.hero.title": "Find the right Indian Standard — in plain language.",
    "home.hero.sub": "Describe a product the way you'd say it in a meeting. The engine maps your words to Indian Standards (BIS codes), bundles the allied test and material standards, and warns you about mandatory certifications before a tender goes out.",
    "home.search.ph": "e.g. cooling units for the new office block, drinking water pipes, TMT bars…",
    "home.search.btn": "Search",
    "home.chip1": "cooling unit for office",
    "home.chip2": "drinking water pipes",
    "home.chip3": "TMT bars for slab",
    "home.chip4": "पानी के पाइप",
    "home.chip5": "fire extinguishers for server room",
    "home.chip6": "sockets and switches",
    "home.syncchip": "⚠ Seed catalogue demo — verify against official BIS before tender citation",
    "home.features.title": "What this assistant does",
    "home.f1.t": "Semantic search",
    "home.f1.d": "\"Cooling unit\", \"geyser\" or AC — intent-based matching, not keyword lookup.",
    "home.f2.t": "Allied standard bundling",
    "home.f2.d": "Normative references, test methods and companion codes suggested with every primary hit.",
    "home.f3.t": "Certification alerts",
    "home.f3.d": "Mandatory schemes (CRS, ISI mark, BEE star labelling) flagged where applicable.",
    "an.title": "Tender Analyzer",
    "an.sub": "Paste a product description, technical specification or draft tender text. The engine identifies relevant Indian Standards, missing allied/normative standards, mandatory certification requirements and outdated code references.",
    "an.spec.label": "Specification text (min 10 characters, max 20,000)",
    "an.spec.ph": "Example:\nSupply and installation of room air conditioners for the office block. Units shall be window type, 1.5 ton, with copper condenser. TMT bars Fe 500 per IS 1786:2008 shall be used for the plinth. Supply of packaged drinking water in 20 L jars for staff.",
    "an.analyze.btn": "Analyze specification",
    "an.sample.btn": "Load sample tender text",
    "an.upload.label": "…or upload a tender document (PDF / DOCX, max 10 MB)",
    "an.upload.btn": "Analyze file",
    "an.upload.drop": "Drop a PDF/DOCX here",
    "std.title": "Explore Standards",
    "std.sub": "Catalogue, grouped by sector. Each entry shows the current version we hold, allied standards, and certification requirements where applicable.",
    "std.all": "All sectors",
    "alerts.title": "Compliance Alerts",
    "alerts.sub": "Some product categories cannot be procured without a mandatory certification — a technically compliant tender that omits the certificate requirement still fails. Below are the schemes mapped in the current catalogue and the standards they apply to.",
    "asst.title": "AI Assistant",
    "asst.sub": "Ask about Indian Standards in simple words — English, हिन्दी or తెలుగు. The assistant answers only from the standards catalogue and never invents codes.",
    "asst.ph": "Ask anything… e.g. “Which standard for drinking water pipes?”",
    "asst.send": "Send",
    "asst.suggest1": "What is IS 456?",
    "asst.suggest2": "Which standard for drinking water pipes?",
    "asst.suggest3": "Does a pressure cooker need ISI mark?",
    "asst.suggest4": "Latest version of IS 1786?",
    "docs.title": "API Reference",
    "docs.sub": "All endpoints are JSON over HTTP. Interactive OpenAPI docs:",
    "report.health": "Specification health check",
    "report.primaries": "Relevant standards identified",
    "report.allied": "⚠ Missing allied / normative standards",
    "report.allied.note": "These are cross-referenced by the standards above but never appear in your text.",
    "report.certs": "Mandatory certification requirements",
    "report.obsolete": "✗ Outdated / unverified references",
    "report.copy": "Copy as specification",
    "report.copied": "Copied!",
    "report.export.md": "Download report (Markdown)",
    "report.export.json": "Download report (JSON)",
    "report.print": "Print report",
    "report.none": "No standards could be matched. Rephrase with product words (e.g. \"cables\", \"pipes\", \"helmets\").",
    "report.detected": "Detected language:",
    "report.th.code": "Code",
    "report.th.title": "Title",
    "report.th.reqby": "Required by",
    "report.th.relation": "Relation",
    "report.noallied": "No missing allied standards detected",
    "status.analyzing": "Analyzing…",
    "status.uploading": "Extracting text and analyzing…",
    "status.searching": "Searching…",
    "status.tooshort": "Please enter at least 10 characters.",
    "status.toolong": "Text exceeds 20,000 characters.",
    "footer.demo": "Demo · seed catalogue · verify against official BIS.",
    "lang.label": "Language",
  },
  hi: {
    "nav.home": "होम",
    "nav.standards": "मानक देखें",
    "nav.analyzer": "टेंडर विश्लेषक",
    "nav.alerts": "अनुपालन चेतावनियाँ",
    "nav.assistant": "एआई सहायक",
    "nav.docs": "एपीआई दस्तावेज़",
    "brand": "BIS मानक सहायक",
    "home.hero.title": "सही भारतीय मानक खोजें — आसान भाषा में।",
    "home.hero.sub": "उत्पाद का वर्णन वैसे करें जैसे आप बैठक में कहेंगे। इंजन आपके शब्दों को भारतीय मानकों (BIS कोड) से जोड़ता है, संबंधित परीक्षण और सामग्री मानक जोड़ता है, और टेंडर निकलने से पहले अनिवार्य प्रमाणन की चेतावनी देता है।",
    "home.search.ph": "जैसे: ऑफिस के लिए कूलिंग यूनिट, पानी के पाइप, टीएमटी सरिया…",
    "home.search.btn": "खोजें",
    "home.chip1": "ऑफिस के लिए कूलिंग यूनिट",
    "home.chip2": "पानी के पाइप",
    "home.chip3": "छत के लिए टीएमटी सरिया",
    "home.chip4": "पानी के पाइप",
    "home.chip5": "सर्वर रूम के लिए अग्निशामक",
    "home.chip6": "प्लग और स्विच",
    "home.syncchip": "⚠ सीड सूची डेमो — टेंडर में उद्धृत करने से पहले आधिकारिक BIS से जाँच करें",
    "home.features.title": "यह सहायक क्या करता है",
    "home.f1.t": "अर्थ-आधारित खोज",
    "home.f1.d": "\"कूलिंग यूनिट\", \"गीज़र\" या एसी — शब्द नहीं, इरादा पहचाना जाता है।",
    "home.f2.t": "संबद्ध मानक बंडलिंग",
    "home.f2.d": "हर मुख्य मानक के साथ परीक्षण विधि और सामग्री मानक सुझाए जाते हैं।",
    "home.f3.t": "प्रमाणन चेतावनी",
    "home.f3.d": "अनिवार्य योजनाएँ (CRS, ISI चिह्न, BEE स्टार रेटिंग) जहाँ लागू हों, चिह्नित।",
    "an.title": "टेंडर विश्लेषक",
    "an.sub": "उत्पाद विवरण, तकनीकी विनिर्देश या टेंडर का मसौदा चिपकाएँ। इंजन संबंधित भारतीय मानक, छूटे हुए संबद्ध मानक, अनिवार्य प्रमाणन और पुराने संदर्भ पहचानता है।",
    "an.spec.label": "विनिर्देश पाठ (न्यूनतम 10, अधिकतम 20,000 अक्षर)",
    "an.spec.ph": "उदाहरण:\nऑफिस ब्लॉक के लिए रूम एयर कंडीशनर की आपूर्ति और स्थापना। सभी यूनिट विंडो टाइप, 1.5 टन, कॉपर कंडेंसर। प्लिंथ में IS 1786:2008 के टीएमटी सरिया Fe 500। स्टाफ हेतु 20 लीटर बोतलबंद पेय जल।",
    "an.analyze.btn": "विश्लेषण करें",
    "an.sample.btn": "नमूना टेंडर पाठ लोड करें",
    "an.upload.label": "…या टेंडर दस्तावेज़ अपलोड करें (PDF / DOCX, अधिकतम 10 MB)",
    "an.upload.btn": "फ़ाइल विश्लेषण",
    "an.upload.drop": "PDF/DOCX यहाँ छोड़ें",
    "std.title": "मानक देखें",
    "std.sub": "क्षेत्र-वार सूची। प्रत्येक प्रविष्टि में दर्ज संस्करण, संबद्ध मानक और लागू प्रमाणन आवश्यकताएँ दिखती हैं।",
    "std.all": "सभी क्षेत्र",
    "alerts.title": "अनुपालन चेतावनियाँ",
    "alerts.sub": "कुछ उत्पाद श्रेणियाँ अनिवार्य प्रमाणन के बिना खरीदी नहीं जा सकतीं — तकनीकी रूप से उपयुक्त टेंडर भी प्रमाण-पत्र की शर्त छोड़ने पर असफल होता है। नीचे सूची में मैप की गई योजनाएँ और उनके मानक हैं।",
    "asst.title": "एआई सहायक",
    "asst.sub": "भारतीय मानकों के बारे में आसान भाषा में पूछें — हिन्दी में। सहायक केवल मानक सूची से उत्तर देता है और कभी कोड नहीं गढ़ता।",
    "asst.ph": "कुछ भी पूछें… जैसे “पीने के पानी के पाइप के लिए कौन सा मानक?”",
    "asst.send": "भेजें",
    "asst.suggest1": "IS 456 क्या है?",
    "asst.suggest2": "पीने के पानी के पाइप के लिए कौन सा मानक?",
    "asst.suggest3": "प्रेशर कुकर पर ISI अनिवार्य है?",
    "asst.suggest4": "IS 1786 का नवीनतम संस्करण?",
    "docs.title": "एपीआई संदर्भ",
    "docs.sub": "सभी एंडपॉइंट HTTP पर JSON लौटाते हैं। इंटरैक्टिव OpenAPI दस्तावेज़:",
    "report.health": "विनिर्देश स्वास्थ्य जाँच",
    "report.primaries": "पहचाने गए संबंधित मानक",
    "report.allied": "⚠ छूटे हुए संबद्ध / अधिनियमित मानक",
    "report.allied.note": "ये ऊपर के मानकों द्वारा संदर्भित हैं पर आपके पाठ में नहीं आए।",
    "report.certs": "अनिवार्य प्रमाणन आवश्यकताएँ",
    "report.obsolete": "✗ पुराने / असत्यापित संदर्भ",
    "report.copy": "विनिर्देश के रूप में कॉपी करें",
    "report.copied": "कॉपी हो गया!",
    "report.export.md": "रिपोर्ट डाउनलोड करें (Markdown)",
    "report.export.json": "रिपोर्ट डाउनलोड करें (JSON)",
    "report.print": "रिपोर्ट प्रिंट करें",
    "report.none": "कोई मानक मेल नहीं खाया। उत्पाद शब्दों (जैसे \"केबल\", \"पाइप\", \"हेलमेट\") से फिर प्रयास करें।",
    "report.detected": "पहचानी गई भाषा:",
    "report.th.code": "कोड",
    "report.th.title": "शीर्षक",
    "report.th.reqby": "किसे आवश्यक",
    "report.th.relation": "संबंध",
    "report.noallied": "कोई छूटा हुआ संबद्ध मानक नहीं मिला",
    "status.analyzing": "विश्लेषण हो रहा है…",
    "status.uploading": "पाठ निकाला और विश्लेषण हो रहा है…",
    "status.searching": "खोजा जा रहा है…",
    "status.tooshort": "कृपया कम से कम 10 अक्षर दर्ज करें।",
    "status.toolong": "पाठ 20,000 अक्षरों से अधिक है।",
    "footer.demo": "डेमो · सीड सूची · आधिकारिक BIS से जाँच करें।",
    "lang.label": "भाषा",
  },
  te: {
    "nav.home": "హోమ్",
    "nav.standards": "ప్రమదాలు చూడండి",
    "nav.analyzer": "టెండర్ విశ్లేషకం",
    "nav.alerts": "అనుగుణ్యత హెచ్చరికలు",
    "nav.assistant": "AI సహాయకుడు",
    "nav.docs": "API పత్రాలు",
    "brand": "BIS ప్రమద సహాయకుడు",
    "home.hero.title": "సరైన భారతీయ ప్రమదాన్ని కనుగొనండి — సులభ భాషలో.",
    "home.hero.sub": "ఉత్పత్తిని మీరు సమావేశంలో చెప్పే విధంగా వర్ణించండి. ఇంజన్ మీ మాటలను భారతీయ ప్రమదాలకు (BIS కోడ్‌లు) అనుసంధానిస్తుంది, సంబంధిత పరీక్ష మరియు పదార్థ ప్రమదాలను కలుపుతుంది, టెండర్ వెలువడే ముందే తప్పనిసరి ధృవీకరణల గురించి హెచ్చరిస్తుంది.",
    "home.search.ph": "ఉదా: ఆఫీస్ కోసం కూలింగ్ యూనిట్, నీటి పైపులు, టీఎంటీ స్టీల్…",
    "home.search.btn": "వెతకండి",
    "home.chip1": "ఆఫీస్ కోసం కూలింగ్ యూనిట్",
    "home.chip2": "నీటి పైపులు",
    "home.chip3": "స్లాబ్ కోసం టీఎంటీ స్టీల్",
    "home.chip4": "నీటి పైపులు",
    "home.chip5": "సర్వర్ రూమ్ కు అగ్నిమాపకం",
    "home.chip6": "ప్లగ్‌లు, స్విచ్‌లు",
    "home.syncchip": "⚠ సీడ్ జాబితా డెమో — టెండర్‌లో ఉదహరించే ముందు అధికారిక BIS తో సరిచూసుకోండి",
    "home.features.title": "ఈ సహాయకుడు ఏం చేస్తాడు",
    "home.f1.t": "అర్థ-ఆధారిత శోధన",
    "home.f1.d": "\"కూలింగ్ యూనిట్\", \"గీజర్\" లేదా ఏసీ — పదాలు కాదు, ఉద్దేశం గుర్తించబడుతుంది.",
    "home.f2.t": "సంబంధిత ప్రమద బండ్లింగ్",
    "home.f2.d": "ప్రతి ప్రధాన ప్రమదంతో పరీక్ష పద్ధతులు, పదార్థ ప్రమదాలు సూచించబడతాయి.",
    "home.f3.t": "ధృవీకరణ హెచ్చరికలు",
    "home.f3.d": "తప్పనిసరి పథకాలు (CRS, ISI మార్క్, BEE స్టార్ రేటింగ్) వర్తించే చోట గుర్తించబడతాయి.",
    "an.title": "టెండర్ విశ్లేషకం",
    "an.sub": "ఉత్పత్తి వివరణ, సాంకేతిక వివరణ లేదా టెండర్ ముసాయిదా అతికించండి. ఇంజన్ సంబంధిత భారతీయ ప్రమదాలు, వదిలిన సంబంధిత ప్రమదాలు, తప్పనిసరి ధృవీకరణలు, పాత ప్రస్తావనలు గుర్తిస్తుంది.",
    "an.spec.label": "వివరణ పాఠ్యం (కనీసం 10, గరిష్ఠంగా 20,000 అక్షరాలు)",
    "an.spec.ph": "ఉదాహరణ:\nఆఫీస్ బ్లాక్ కు రూమ్ ఎయిర్ కండిషనర్ల సరఫరా, అమరిక. అన్ని యూనిట్లు విండో రకం, 1.5 టన్ను, కాపర్ కండెన్సర్. ప్లింత్ కు IS 1786:2008 టీఎంటీ స్టీల్ Fe 500. సిబ్బందికి 20 లీటర్ల ప్యాకెడ్ డ్రింకింగ్ వాటర్.",
    "an.analyze.btn": "విశ్లేషించండి",
    "an.sample.btn": "నమూనా టెండర్ పాఠ్యం లోడ్ చేయండి",
    "an.upload.label": "…లేదా టెండర్ పత్రాన్ని అప్‌లోడ్ చేయండి (PDF / DOCX, గరిష్ఠం 10 MB)",
    "an.upload.btn": "ఫైల్ విశ్లేషణ",
    "an.upload.drop": "PDF/DOCX ఇక్కడ వదలండి",
    "std.title": "ప్రమదాలు చూడండి",
    "std.sub": "రంగం-వారీ జాబితా. ప్రతి నమోదులో మా వద్ద ఉన్న ఎడిషన్, సంబంధిత ప్రమదాలు, వర్తించే ధృవీకరణ అవసరాలు కనిపిస్తాయి.",
    "std.all": "అన్ని రంగాలు",
    "alerts.title": "అనుగుణ్యత హెచ్చరికలు",
    "alerts.sub": "కొన్ని ఉత్పత్తి వర్గాలు తప్పనిసరి ధృవీకరణ లేకుండా కొనుగోలు చేయలేము — సాంకేతికంగా సరైన టెండర్ కూడా ధృవీకరణ పత్ర నిబంధన వదిలేస్తే విఫలమవుతుంది. క్రింద జాబితాలో మ్యాప్ చేసిన పథకాలు, వాటి ప్రమదాలు.",
    "asst.title": "AI సహాయకుడు",
    "asst.sub": "భారతీయ ప్రమదాల గురించి సులభ భాషలో అడగండి — తెలుగులో. సహాయకుడు ప్రమద జాబితా నుంచి మాత్రమే సమాధానం ఇస్తాడు, కోడ్‌లు కల్పించడు.",
    "asst.ph": "ఏదైనా అడగండి… ఉదా: “తాగునీటి పైపులకు ఏ ప్రమద?”",
    "asst.send": "పంపండి",
    "asst.suggest1": "IS 456 అంటే ఏమిటి?",
    "asst.suggest2": "తాగునీటి పైపులకు ఏ ప్రమద?",
    "asst.suggest3": "ప్రెషర్ కుక్కర్‌కి ISI తప్పనిసరా?",
    "asst.suggest4": "IS 1786 తాజా ఎడిషన్?",
    "docs.title": "API సూచన",
    "docs.sub": "అన్ని ఎండ్‌పాయింట్‌లు HTTP పై JSON ఇస్తాయి. ఇంటరాక్టివ్ OpenAPI పత్రాలు:",
    "report.health": "వివరణ ఆరోగ్య తనిఖీ",
    "report.primaries": "గుర్తించిన సంబంధిత ప్రమదాలు",
    "report.allied": "⚠ వదిలిన సంబంధిత / నిర్దేశిత ప్రమదాలు",
    "report.allied.note": "ఇవి పై ప్రమదాలు సూచించేవి, మీ పాఠ్యంలో కనిపించలేదు.",
    "report.certs": "తప్పనిసరి ధృవీకరణ అవసరాలు",
    "report.obsolete": "✗ పాత / ధృవీకరించని ప్రస్తావనలు",
    "report.copy": "వివరణగా కాపీ చేయండి",
    "report.copied": "కాపీ అయింది!",
    "report.export.md": "రిపోర్ట్ డౌన్‌లోడ్ (Markdown)",
    "report.export.json": "రిపోర్ట్ డౌన్‌లోడ్ (JSON)",
    "report.print": "రిపోర్ట్ ప్రింట్",
    "report.none": "ఏ ప్రమదం సరిపోలలేదు. ఉత్పత్తి పదాలతో (\"కేబుల్స్\", \"పైపులు\", \"హెల్మెట్‌లు\") మళ్లీ ప్రయత్నించండి.",
    "report.detected": "గుర్తించిన భాష:",
    "report.th.code": "కోడ్",
    "report.th.title": "శీర్షిక",
    "report.th.reqby": "ఎవరికోసం",
    "report.th.relation": "సంబంధం",
    "report.noallied": "వదిలిన సంబంధిత ప్రమదాలు ఏవీ లేవు",
    "status.analyzing": "విశ్లేషణ జరుగుతోంది…",
    "status.uploading": "పాఠ్యం తీసి విశ్లేషణ జరుగుతోంది…",
    "status.searching": "వెతుకుతోంది…",
    "status.tooshort": "దయచేసి కనీసం 10 అక్షరాలు నమోదు చేయండి.",
    "status.toolong": "పాఠ్యం 20,000 అక్షరాలు మించింది.",
    "footer.demo": "డెమో · సీడ్ జాబితా · అధికారిక BIS తో సరిచూసుకోండి.",
    "lang.label": "భాష",
  },
};

function i18nLang() {
  return localStorage.getItem("bis_lang") || "en";
}

function t(key, fallback) {
  const lang = i18nLang();
  return (I18N[lang] && I18N[lang][key]) || (I18N.en && I18N.en[key]) || fallback || key;
}

function applyI18n() {
  const lang = i18nLang();
  document.documentElement.setAttribute("lang", lang === "en" ? "en" : (lang === "hi" ? "hi" : "te"));
  $$("[data-i18n]").forEach((el) => { el.textContent = t(el.getAttribute("data-i18n")); });
  $$("[data-i18n-ph]").forEach((el) => { el.setAttribute("placeholder", t(el.getAttribute("data-i18n-ph"))); });
  $$("[data-i18n-title]").forEach((el) => { el.setAttribute("title", t(el.getAttribute("data-i18n-title"))); });
}

function setLang(lang) {
  localStorage.setItem("bis_lang", lang);
  applyI18n();
  document.dispatchEvent(new CustomEvent("bis:langchange", { detail: { lang } }));
}

// Language switcher is injected into every header.
function injectLangSwitcher() {
  const nav = $(".main-nav");
  if (!nav || $("#lang-switch")) return;
  const wrap = document.createElement("label");
  wrap.id = "lang-switch";
  wrap.className = "lang-switch";
  wrap.innerHTML = `
    <span class="visually-hidden" data-i18n-title="lang.label">🌐</span>
    <select aria-label="${t("lang.label")}">
      <option value="en">English</option>
      <option value="hi">हिन्दी</option>
      <option value="te">తెలుగు</option>
    </select>`;
  wrap.querySelector("select").value = i18nLang();
  wrap.querySelector("select").addEventListener("change", (e) => setLang(e.target.value));
  nav.appendChild(wrap);
}

document.addEventListener("DOMContentLoaded", () => {
  injectLangSwitcher();
  applyI18n();
});
