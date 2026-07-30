import os
import json
import re

SRC = r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src"

def update_locales():
    en_path = os.path.join(SRC, 'i18n', 'locales', 'en.json')
    mr_path = os.path.join(SRC, 'i18n', 'locales', 'mr.json')
    
    with open(en_path, 'r', encoding='utf-8') as f:
        en = json.load(f)
    with open(mr_path, 'r', encoding='utf-8') as f:
        mr = json.load(f)

    # Add missing keys to dashboard
    new_dash_en = {
        "totalOpenCases": "Total Open Cases",
        "slaBreached": "SLA Breached",
        "totalAtRisk": "Total At Risk",
        "totalRecovered": "Total Recovered",
        "slaBreachedCases": "SLA Breached Cases (Unit-wide)",
        "networkSummary": "Network & Cluster Summary",
        "totalClusters": "Total Clusters",
        "highRisk": "High Risk >70",
        "officerWorkload": "Officer Workload",
        "activeCount": "{{count}} Active",
        "externalPanel": "External-System Status Panel",
        "simulated": "Simulated",
        "notConnected": "Not connected",
        "noBreached": "No breached cases currently.",
        "active": "Active",
        "tracing": "Tracing",
        "intakeComplete": "Intake Complete",
        "other": "OTHER"
    }
    
    new_dash_mr = {
        "totalOpenCases": "एकूण प्रलंबित प्रकरणे",
        "slaBreached": "SLA उल्लंघित",
        "totalAtRisk": "एकूण धोक्यात रक्कम",
        "totalRecovered": "एकूण परत मिळवलेली रक्कम",
        "slaBreachedCases": "SLA उल्लंघित प्रकरणे (संपूर्ण युनिट)",
        "networkSummary": "नेटवर्क आणि क्लस्टर सारांश",
        "totalClusters": "एकूण क्लस्टर्स",
        "highRisk": "उच्च धोका >७०",
        "officerWorkload": "अधिकाऱ्यांचे कामाचे स्वरूप",
        "activeCount": "{{count}} सक्रीय",
        "externalPanel": "बाह्य प्रणाली स्थिती पॅनेल",
        "simulated": "सिम्युलेटेड",
        "notConnected": "जोडलेले नाही",
        "noBreached": "सध्या कोणतीही उल्लंघित प्रकरणे नाहीत.",
        "active": "सक्रीय",
        "tracing": "शोध सुरू",
        "intakeComplete": "नोंदणी पूर्ण",
        "other": "इतर"
    }
    
    en["dashboard"].update(new_dash_en)
    mr["dashboard"].update(new_dash_mr)

    # Add cases
    if "casesList" not in en:
        en["casesList"] = {}
        mr["casesList"] = {}
        
    en["casesList"].update({
        "newestFirst": "Newest first",
        "oldestFirst": "Oldest first",
        "highestRisk": "Highest Risk"
    })
    mr["casesList"].update({
        "newestFirst": "सर्वात नवीन प्रथम",
        "oldestFirst": "सर्वात जुने प्रथम",
        "highestRisk": "सर्वाधिक धोका"
    })
    
    # Add watchlist
    en["watchlist"].update({
        "target": "TARGET",
        "reason": "REASON",
        "status": "STATUS",
        "actions": "ACTIONS",
        "active": "Active",
        "deactivate": "Deactivate",
        "delete": "Delete",
        "addTitle": "Add to Watchlist",
        "accNumber": "Account Number",
        "ifsc": "IFSC Code",
        "upi": "UPI ID",
        "phone": "Phone",
        "reasonLabel": "Reason",
        "addBtn": "Add Entry",
        "loading": "Loading..."
    })
    mr["watchlist"].update({
        "target": "लक्ष्य",
        "reason": "कारण",
        "status": "स्थिती",
        "actions": "क्रिया",
        "active": "सक्रीय",
        "deactivate": "निष्क्रिय करा",
        "delete": "हटवा",
        "addTitle": "वॉचलिस्टमध्ये जोडा",
        "accNumber": "खाते क्रमांक",
        "ifsc": "IFSC कोड",
        "upi": "UPI आयडी",
        "phone": "फोन",
        "reasonLabel": "कारण",
        "addBtn": "प्रविष्ट करा",
        "loading": "लोड होत आहे..."
    })

    # Add ingestion
    if "ingestion" not in en:
        en["ingestion"] = {}
        mr["ingestion"] = {}
        
    en["ingestion"].update({
        "title": "Bulk Transaction Ingestion Engine",
        "subtitle": "Ingest multi-hop bank replies into a case. Case ID is required (H5).",
        "targetPlaceholder": "Target case_id (required)",
        "launchBtn": "Launch Ingestion",
        "templates": "Official Templates",
        "templatesSub": "Authenticated download via cookie session (M4).",
        "csv": "CSV Template",
        "xlsx": "XLSX Template",
        "recent": "Recent Import Jobs",
        "recentSub": "queued -> processing -> completed / failed",
        "refresh": "Refresh",
        "processing": "PROCESSING",
        "completed": "COMPLETED",
        "failed": "FAILED",
        "queued": "QUEUED",
        "graphSynced": "graph: synced",
        "graphDeferred": "graph: deferred"
    })
    mr["ingestion"].update({
        "title": "बल्क ट्रान्झॅक्शन इनजेशन इंजिन",
        "subtitle": "मल्टी-हॉप बँक उत्तरे प्रकरणात जोडा. प्रकरण आयडी आवश्यक आहे (H5).",
        "targetPlaceholder": "लक्ष्य case_id (आवश्यक)",
        "launchBtn": "इनजेशन सुरू करा",
        "templates": "अधिकृत टेम्पलेट्स",
        "templatesSub": "कुकी सत्राद्वारे प्रमाणित डाउनलोड (M4).",
        "csv": "CSV टेम्पलेट",
        "xlsx": "XLSX टेम्पलेट",
        "recent": "अलीकडील आयात कार्ये",
        "recentSub": "रांगेत -> प्रक्रिया करत आहे -> पूर्ण झाले / अयशस्वी",
        "refresh": "रिफ्रेश करा",
        "processing": "प्रक्रिया करत आहे",
        "completed": "पूर्ण झाले",
        "failed": "अयशस्वी",
        "queued": "रांगेत",
        "graphSynced": "ग्राफ: सिंक झाले",
        "graphDeferred": "ग्राफ: पुढे ढकलले"
    })

    with open(en_path, 'w', encoding='utf-8') as f:
        json.dump(en, f, indent=2)
    with open(mr_path, 'w', encoding='utf-8') as f:
        json.dump(mr, f, indent=2, ensure_ascii=False)

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    for old, new in replacements:
        content = content.replace(old, new)
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {os.path.basename(filepath)}")

def fix_components():
    # 1. DashboardPage.tsx
    replace_in_file(os.path.join(SRC, "pages", "DashboardPage.tsx"), [
        ('>Total Open Cases<', '>{t("dashboard.totalOpenCases")}<'),
        ('>SLA Breached<', '>{t("dashboard.slaBreached")}<'),
        ('>Total At Risk<', '>{t("dashboard.totalAtRisk")}<'),
        ('>Total Recovered<', '>{t("dashboard.totalRecovered")}<'),
        ('"SLA Breached Cases (Unit-wide)"', 't("dashboard.slaBreachedCases")'),
        ('"No breached cases currently."', 't("dashboard.noBreached")'),
        ('>Network & Cluster Summary<', '>{t("dashboard.networkSummary")}<'),
        ('>Total Clusters<', '>{t("dashboard.totalClusters")}<'),
        ('>High Risk &gt;70<', '>{t("dashboard.highRisk")}<'),
        ('>Officer Workload<', '>{t("dashboard.officerWorkload")}<'),
        ('>{w.active_cases} Active<', '>{t("dashboard.activeCount", { count: w.active_cases })}<'),
        ('>External-System Status Panel<', '>{t("dashboard.externalPanel")}<'),
        ('>Simulated<', '>{t("dashboard.simulated")}<'),
        ('>Not connected<', '>{t("dashboard.notConnected")}<')
    ])

    # 2. CasesListPage.tsx
    replace_in_file(os.path.join(SRC, "pages", "CasesListPage.tsx"), [
        ('>Newest first<', '>{t("casesList.newestFirst")}<'),
        ('>Oldest first<', '>{t("casesList.oldestFirst")}<'),
        ('>Highest Risk<', '>{t("casesList.highestRisk")}<')
    ])

    # 3. WatchlistPage.tsx
    replace_in_file(os.path.join(SRC, "pages", "WatchlistPage.tsx"), [
        ('>TARGET<', '>{t("watchlist.target")}<'),
        ('>REASON<', '>{t("watchlist.reason")}<'),
        ('>STATUS<', '>{t("watchlist.status")}<'),
        ('>ACTIONS<', '>{t("watchlist.actions")}<'),
        ('>Active<', '>{t("watchlist.active")}<'),
        ('>Deactivate<', '>{t("watchlist.deactivate")}<'),
        ('>Delete<', '>{t("watchlist.delete")}<'),
        ('>Add to Watchlist<', '>{t("watchlist.addTitle")}<'),
        ('>Account Number<', '>{t("watchlist.accNumber")}<'),
        ('>IFSC Code<', '>{t("watchlist.ifsc")}<'),
        ('>UPI ID<', '>{t("watchlist.upi")}<'),
        ('>Phone<', '>{t("watchlist.phone")}<'),
        ('>Reason<', '>{t("watchlist.reasonLabel")}<'),
        ('>Add Entry<', '>{t("watchlist.addBtn")}<'),
        ('>Loading...<', '>{t("watchlist.loading")}<')
    ])

    # 4. IngestionQueuePage.tsx
    replace_in_file(os.path.join(SRC, "pages", "IngestionQueuePage.tsx"), [
        ('const { t } = useTranslation();', 'const { t } = useTranslation();\n'),
        ('>Bulk Transaction Ingestion Engine<', '>{t("ingestion.title")}<'),
        ('>Ingest multi-hop bank replies into a case. Case ID is required (H5).<', '>{t("ingestion.subtitle")}<'),
        ('placeholder="Target case_id (required)"', 'placeholder={t("ingestion.targetPlaceholder")}'),
        ('>Launch Ingestion<', '>{t("ingestion.launchBtn")}<'),
        ('>Official Templates<', '>{t("ingestion.templates")}<'),
        ('>Authenticated download via cookie session (M4).<', '>{t("ingestion.templatesSub")}<'),
        ('>CSV Template<', '>{t("ingestion.csv")}<'),
        ('>XLSX Template<', '>{t("ingestion.xlsx")}<'),
        ('>Recent Import Jobs<', '>{t("ingestion.recent")}<'),
        ('>queued -&gt; processing -&gt; completed / failed<', '>{t("ingestion.recentSub")}<'),
        ('>Refresh<', '>{t("ingestion.refresh")}<'),
        ('{job.status.toUpperCase()}', '{job.status === "processing" ? t("ingestion.processing") : job.status === "completed" ? t("ingestion.completed") : job.status === "failed" ? t("ingestion.failed") : t("ingestion.queued")}'),
        ('>graph: synced<', '>{t("ingestion.graphSynced")}<'),
        ('>graph: deferred<', '>{t("ingestion.graphDeferred")}<')
    ])

if __name__ == "__main__":
    update_locales()
    fix_components()
    print("Done applying i18n fixes.")
