import os
import re

SRC = r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src"

def fix_dashboard():
    path = os.path.join(SRC, "pages", "DashboardPage.tsx")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # ensure t is imported
    if "useTranslation" not in content:
        content = "import { useTranslation } from 'react-i18next';\n" + content
    
    # check if t is initialized
    if "const { t } = useTranslation();" not in content:
        content = re.sub(r'(export const DashboardPage: React.FC = \(\) => {)', r'\1\n  const { t } = useTranslation();', content)

    # replace strings
    replacements = [
        (r'Total Open Cases', '{t("dashboard.totalOpenCases")}'),
        (r'SLA Breached(?! Cases)', '{t("dashboard.slaBreached")}'),
        (r'Total At Risk', '{t("dashboard.totalAtRisk")}'),
        (r'Total Recovered', '{t("dashboard.totalRecovered")}'),
        (r'"SLA Breached Cases \(Unit-wide\)"', 't("dashboard.slaBreachedCases")'),
        (r'"No breached cases currently."', 't("dashboard.noBreached")'),
        (r'Network &amp; Cluster Summary|Network & Cluster Summary', '{t("dashboard.networkSummary")}'),
        (r'Total Clusters', '{t("dashboard.totalClusters")}'),
        (r'High Risk &gt;70|High Risk >70', '{t("dashboard.highRisk")}'),
        (r'Officer Workload', '{t("dashboard.officerWorkload")}'),
        (r'External-System Status Panel', '{t("dashboard.externalPanel")}'),
        (r'>Simulated<', '>{t("dashboard.simulated")}<'),
        (r'>Not connected<', '>{t("dashboard.notConnected")}<'),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)

    # Fix Active case count carefully
    content = re.sub(r'\{w\.active_cases\} Active', '{t("dashboard.activeCount", { count: w.active_cases })}', content)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_watchlist():
    path = os.path.join(SRC, "pages", "WatchlistPage.tsx")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = [
        (r'>TARGET<', '>{t("watchlist.target")}<'),
        (r'>REASON<', '>{t("watchlist.reason")}<'),
        (r'>STATUS<', '>{t("watchlist.status")}<'),
        (r'>ACTIONS<', '>{t("watchlist.actions")}<'),
        (r'>Active<', '>{t("watchlist.active")}<'),
        (r'>Deactivate<', '>{t("watchlist.deactivate")}<'),
        (r'>Delete<', '>{t("watchlist.delete")}<'),
        (r'>Add to Watchlist<', '>{t("watchlist.addTitle")}<'),
        (r'>Account Number<', '>{t("watchlist.accNumber")}<'),
        (r'>IFSC Code<', '>{t("watchlist.ifsc")}<'),
        (r'>UPI ID<', '>{t("watchlist.upi")}<'),
        (r'>Phone<', '>{t("watchlist.phone")}<'),
        (r'>Reason<', '>{t("watchlist.reasonLabel")}<'),
        (r'>Add Entry<', '>{t("watchlist.addBtn")}<'),
        (r'>Loading\.\.\.<', '>{t("watchlist.loading")}<')
    ]
    for old, new in replacements:
        content = re.sub(old, new, content)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_cases_list():
    path = os.path.join(SRC, "pages", "CasesListPage.tsx")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = [
        (r'>Newest first<', '>{t("casesList.newestFirst")}<'),
        (r'>Oldest first<', '>{t("casesList.oldestFirst")}<'),
        (r'>Highest Risk<', '>{t("casesList.highestRisk")}<')
    ]
    for old, new in replacements:
        content = re.sub(old, new, content)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_ingestion():
    path = os.path.join(SRC, "pages", "IngestionQueuePage.tsx")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if "useTranslation" not in content:
        content = "import { useTranslation } from 'react-i18next';\n" + content
    
    if "const { t } = useTranslation();" not in content:
        content = re.sub(r'(export const IngestionQueuePage: React.FC = \(\) => {)', r'\1\n  const { t } = useTranslation();', content)

    # Re-read line by line for safer replacements of long strings
    replacements = [
        (r'Bulk Transaction Ingestion Engine', '{t("ingestion.title")}'),
        (r'Ingest multi-hop bank replies into a case\. Case ID is required \(H5\)\.', '{t("ingestion.subtitle")}'),
        (r'placeholder="Target case_id \(required\)"', 'placeholder={t("ingestion.targetPlaceholder") as string}'),
        (r'Launch Ingestion', '{t("ingestion.launchBtn")}'),
        (r'Official Templates', '{t("ingestion.templates")}'),
        (r'Authenticated download via cookie session \(M4\)\.', '{t("ingestion.templatesSub")}'),
        (r'>CSV Template<', '>{t("ingestion.csv")}<'),
        (r'>XLSX Template<', '>{t("ingestion.xlsx")}<'),
        (r'Recent Import Jobs', '{t("ingestion.recent")}'),
        (r'queued -&gt; processing -&gt; completed / failed', '{t("ingestion.recentSub")}'),
        (r'>Refresh<', '>{t("ingestion.refresh")}<'),
        (r'\{job\.status\.toUpperCase\(\)\}', '{job.status === "processing" ? t("ingestion.processing") : job.status === "completed" ? t("ingestion.completed") : job.status === "failed" ? t("ingestion.failed") : t("ingestion.queued")}'),
        (r'graph: synced', '{t("ingestion.graphSynced")}'),
        (r'graph: deferred', '{t("ingestion.graphDeferred")}')
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == "__main__":
    fix_dashboard()
    fix_watchlist()
    fix_cases_list()
    fix_ingestion()
    print("Fixed all pages with regex.")
