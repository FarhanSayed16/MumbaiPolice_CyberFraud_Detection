import os
import json
import re

SRC = r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src"

def add_keys():
    en_path = os.path.join(SRC, 'i18n', 'locales', 'en.json')
    mr_path = os.path.join(SRC, 'i18n', 'locales', 'mr.json')
    
    with open(en_path, 'r', encoding='utf-8') as f:
        en = json.load(f)
    with open(mr_path, 'r', encoding='utf-8') as f:
        mr = json.load(f)

    # Health
    en["health"] = {
        "title": "System Health & Observability Cockpit",
        "subtitle": "Real-time diagnostics for relational database, graph engine, and background worker queues.",
        "refresh": "Probes Refresh",
        "statusHealthy": "SYSTEM STATUS: HEALTHY",
        "statusDegraded": "SYSTEM STATUS: DEGRADED",
        "statusDown": "SYSTEM STATUS: DOWN",
        "platformName": "Mumbai Police Cyber Fraud Detection Platform",
        "environment": "Environment:",
        "checked": "Checked:",
        "sentryNotConfig": "Sentry: NOT CONFIGURED",
        "sentrySub": "Sentry not configured (local console logging only). Hosted uptime monitor deferred until real deploy (H17/H18).",
        "postgres": "PostgreSQL (Relational)",
        "canonicalSchema": "Canonical Schema:",
        "evidentiaryTriggers": "Evidentiary Triggers:",
        "probeLatency": "Probe Latency:",
        "neo4j": "Neo4j (Graph DB)",
        "graphEngine": "Graph Engine:",
        "nodeIndexes": "Node Indexes:",
        "redis": "Redis (Worker Queue)",
        "taskEngine": "Task Engine:",
        "rateLimitStore": "Rate Limit Store:",
        "incidentTitle": "System Down & Incident Reporting Protocol",
        "incidentSub": "Statutory escalation procedures for law enforcement officers and station house supervisors during outages.",
        "immediateReporting": "1. Immediate Reporting & Hotline",
        "techOutage": "2. Technical Outage Ticket Submission"
    }
    
    mr["health"] = {
        "title": "प्रणाली आरोग्य आणि निरीक्षण कॉकपिट",
        "subtitle": "रिलेशनल डेटाबेस, ग्राफ इंजिन आणि पार्श्वभूमी वर्कर क्यूजसाठी रिअल-टाइम डायग्नोस्टिक्स.",
        "refresh": "प्रोब्स रिफ्रेश करा",
        "statusHealthy": "प्रणाली स्थिती: निरोगी (HEALTHY)",
        "statusDegraded": "प्रणाली स्थिती: खराब (DEGRADED)",
        "statusDown": "प्रणाली स्थिती: बंद (DOWN)",
        "platformName": "मुंबई पोलीस सायबर फसवणूक शोध मंच",
        "environment": "वातावरण:",
        "checked": "तपासले:",
        "sentryNotConfig": "सेंट्री: कॉन्फिगर केलेले नाही",
        "sentrySub": "सेंट्री कॉन्फिगर केलेले नाही (केवळ स्थानिक कन्सोल लॉगिंग).",
        "postgres": "PostgreSQL (रिलेशनल)",
        "canonicalSchema": "कॅनोनिकल स्कीमा:",
        "evidentiaryTriggers": "पुरावा ट्रिगर्स:",
        "probeLatency": "प्रोब लेटेंसी:",
        "neo4j": "Neo4j (ग्राफ DB)",
        "graphEngine": "ग्राफ इंजिन:",
        "nodeIndexes": "नोड इंडेक्सेस:",
        "redis": "Redis (वर्कर क्यू)",
        "taskEngine": "टास्क इंजिन:",
        "rateLimitStore": "रेट लिमिट स्टोअर:",
        "incidentTitle": "प्रणाली डाऊन आणि घटना अहवाल प्रोटोकॉल",
        "incidentSub": "बिघाड दरम्यान कायदा अंमलबजावणी अधिकारी आणि स्टेशन हाऊस पर्यवेक्षकांसाठी वैधानिक वाढीव प्रक्रिया.",
        "immediateReporting": "१. तात्काळ अहवाल आणि हेल्पलाइन",
        "techOutage": "२. तांत्रिक बिघाड तिकीट सबमिशन"
    }

    # Audit Trail
    en["auditTrail"] = {
        "title": "Immutable Governance Audit Trail",
        "subtitle": "Evidentiary chain of custody. This table is strictly append-only; database-level triggers block any UPDATE or DELETE operations.",
        "refresh": "Refresh Trail",
        "complianceGuar": "BNSS & IT Act Section 65B Compliance Guarantee",
        "complianceSub": "Every login, statutory notice generation, evidence upload, and user administration event is recorded permanently. No user or system administrator can alter or erase these records once written.",
        "filterTitle": "Filter Governance Records",
        "officerEmail": "OFFICER / ADMIN EMAIL",
        "actionString": "ACTION STRING",
        "resourceType": "RESOURCE TYPE",
        "allResources": "All Resource Types",
        "applyFilter": "Apply Filters",
        "clear": "Clear",
        "tableTitle": "Audit Log Chronological Trail",
        "tableSub": "Displaying top 200 immutable events ordered by timestamp descending.",
        "ts": "TIMESTAMP (UTC)",
        "actor": "ACTOR / EMAIL",
        "action": "ACTION",
        "resourceId": "RESOURCE & ID",
        "clientIp": "CLIENT IP",
        "eventDetails": "EVENT DETAILS"
    }
    
    mr["auditTrail"] = {
        "title": "अपरिवर्तनीय प्रशासन ऑडिट ट्रेल",
        "subtitle": "पुराव्यांची साखळी. हा तक्ता काटेकोरपणे केवळ जोडण्यासाठी आहे; डेटाबेस-स्तरीय ट्रिगर्स कोणत्याही अद्यतन (UPDATE) किंवा हटविण्याच्या (DELETE) क्रियांना अवरोधित करतात.",
        "refresh": "ट्रेल रिफ्रेश करा",
        "complianceGuar": "BNSS आणि माहिती तंत्रज्ञान कायदा कलम ६५B अनुपालन हमी",
        "complianceSub": "प्रत्येक लॉगिन, कायदेशीर नोटीस निर्मिती, पुरावा अपलोड आणि वापरकर्ता प्रशासन घटना कायमस्वरूपी रेकॉर्ड केली जाते. एकदा लिहिल्यानंतर कोणताही वापरकर्ता किंवा प्रणाली प्रशासक या नोंदी बदलू किंवा मिटवू शकत नाही.",
        "filterTitle": "प्रशासन रेकॉर्ड फिल्टर करा",
        "officerEmail": "अधिकारी / अ‍ॅडमिन ईमेल",
        "actionString": "कृती स्ट्रिंग",
        "resourceType": "संसाधन प्रकार",
        "allResources": "सर्व संसाधन प्रकार",
        "applyFilter": "फिल्टर्स लागू करा",
        "clear": "क्लिअर करा",
        "tableTitle": "ऑडिट लॉग कालक्रमानुसार ट्रेल",
        "tableSub": "वेळेनुसार उतरत्या क्रमाने शीर्ष 200 अपरिवर्तनीय घटना दर्शवित आहे.",
        "ts": "वेळ (UTC)",
        "actor": "कर्ता / ईमेल",
        "action": "कृती",
        "resourceId": "संसाधन आणि आयडी",
        "clientIp": "क्लायंट IP",
        "eventDetails": "घटनेचा तपशील"
    }

    # Notifications
    en["notifications"] = {
        "title": "Notifications",
        "new": "{{count}} new",
        "viewCase": "View Case",
        "markRead": "Mark as read",
        "noNotifications": "No new notifications"
    }
    mr["notifications"] = {
        "title": "सूचना",
        "new": "{{count}} नवीन",
        "viewCase": "प्रकरण पहा",
        "markRead": "वाचलेले म्हणून खूण करा",
        "noNotifications": "कोणत्याही नवीन सूचना नाहीत"
    }

    with open(en_path, 'w', encoding='utf-8') as f:
        json.dump(en, f, indent=2)
    with open(mr_path, 'w', encoding='utf-8') as f:
        json.dump(mr, f, indent=2, ensure_ascii=False)


def fix_health():
    path = os.path.join(SRC, "pages", "HealthPage.tsx")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if "useTranslation" not in content:
        content = "import { useTranslation } from 'react-i18next';\n" + content
    
    if "const { t } = useTranslation();" not in content:
        content = re.sub(r'(export const HealthPage: React.FC = \(\) => {)', r'\1\n  const { t } = useTranslation();', content)

    replacements = [
        (r'System Health &amp; Observability Cockpit|System Health & Observability Cockpit', '{t("health.title")}'),
        (r'Real-time diagnostics for relational database, graph engine, and background worker queues\.', '{t("health.subtitle")}'),
        (r'>Probes Refresh<', '>{t("health.refresh")}<'),
        (r'SYSTEM STATUS: HEALTHY', '{t("health.statusHealthy")}'),
        (r'SYSTEM STATUS: DEGRADED', '{t("health.statusDegraded")}'),
        (r'SYSTEM STATUS: DOWN', '{t("health.statusDown")}'),
        (r'Mumbai Police Cyber Fraud Detection Platform', '{t("health.platformName")}'),
        (r'>Environment: ', '>{t("health.environment")} '),
        (r' Checked: ', ' {t("health.checked")} '),
        (r'Sentry: NOT CONFIGURED', '{t("health.sentryNotConfig")}'),
        (r'Sentry not configured \(local console logging only\)\. Hosted uptime monitor deferred until real deploy \(H17/H18\)\.', '{t("health.sentrySub")}'),
        (r'>PostgreSQL \(Relational\)<', '>{t("health.postgres")}<'),
        (r'>Canonical Schema:<', '>{t("health.canonicalSchema")}<'),
        (r'>Evidentiary Triggers:<', '>{t("health.evidentiaryTriggers")}<'),
        (r'>Probe Latency:<', '>{t("health.probeLatency")}<'),
        (r'>Neo4j \(Graph DB\)<', '>{t("health.neo4j")}<'),
        (r'>Graph Engine:<', '>{t("health.graphEngine")}<'),
        (r'>Node Indexes:<', '>{t("health.nodeIndexes")}<'),
        (r'>Redis \(Worker Queue\)<', '>{t("health.redis")}<'),
        (r'>Task Engine:<', '>{t("health.taskEngine")}<'),
        (r'>Rate Limit Store:<', '>{t("health.rateLimitStore")}<'),
        (r'>System Down &amp; Incident Reporting Protocol<', '>{t("health.incidentTitle")}<'),
        (r'Statutory escalation procedures for law enforcement officers and station house supervisors during outages\.', '{t("health.incidentSub")}'),
        (r'>1\. Immediate Reporting &amp; Hotline<', '>{t("health.immediateReporting")}<'),
        (r'>2\. Technical Outage Ticket Submission<', '>{t("health.techOutage")}<')
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_audit():
    path = os.path.join(SRC, "pages", "AuditLogPage.tsx")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if "useTranslation" not in content:
        content = "import { useTranslation } from 'react-i18next';\n" + content
    
    if "const { t } = useTranslation();" not in content:
        content = re.sub(r'(export const AuditLogPage: React.FC = \(\) => {)', r'\1\n  const { t } = useTranslation();', content)

    replacements = [
        (r'>Immutable Governance Audit Trail<', '>{t("auditTrail.title")}<'),
        (r'Evidentiary chain of custody\. This table is strictly append-only; database-level triggers block any UPDATE or DELETE operations\.', '{t("auditTrail.subtitle")}'),
        (r'>Refresh Trail<', '>{t("auditTrail.refresh")}<'),
        (r'BNSS &amp; IT Act Section 65B Compliance Guarantee|BNSS & IT Act Section 65B Compliance Guarantee', '{t("auditTrail.complianceGuar")}'),
        (r'Every login, statutory notice generation, evidence upload, and user administration event is recorded permanently\. No user or system administrator can alter or erase these records once written\.', '{t("auditTrail.complianceSub")}'),
        (r'>Filter Governance Records<', '>{t("auditTrail.filterTitle")}<'),
        (r'>OFFICER / ADMIN EMAIL<', '>{t("auditTrail.officerEmail")}<'),
        (r'>ACTION STRING<', '>{t("auditTrail.actionString")}<'),
        (r'>RESOURCE TYPE<', '>{t("auditTrail.resourceType")}<'),
        (r'>All Resource Types<', '>{t("auditTrail.allResources")}<'),
        (r'>Apply Filters<', '>{t("auditTrail.applyFilter")}<'),
        (r'>Clear<', '>{t("auditTrail.clear")}<'),
        (r'>Audit Log Chronological Trail<', '>{t("auditTrail.tableTitle")}<'),
        (r'Displaying top 200 immutable events ordered by timestamp descending\.', '{t("auditTrail.tableSub")}'),
        (r'>TIMESTAMP \(UTC\)<', '>{t("auditTrail.ts")}<'),
        (r'>ACTOR / EMAIL<', '>{t("auditTrail.actor")}<'),
        (r'>ACTION<', '>{t("auditTrail.action")}<'),
        (r'>RESOURCE &amp; ID<', '>{t("auditTrail.resourceId")}<'),
        (r'>CLIENT IP<', '>{t("auditTrail.clientIp")}<'),
        (r'>EVENT DETAILS<', '>{t("auditTrail.eventDetails")}<')
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_notifications():
    path = os.path.join(SRC, "components", "layout", "Navbar.tsx")
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = [
        (r'>Notifications<', '>{t("notifications.title")}<'),
        (r'>View Case<', '>{t("notifications.viewCase")}<'),
        (r'\{unreadCount\} new', '{t("notifications.new", { count: unreadCount })}'),
        (r'title="Mark as read"', 'title={t("notifications.markRead")}'),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    add_keys()
    fix_health()
    fix_audit()
    fix_notifications()
    print("Fixed health, audit, notifications.")
