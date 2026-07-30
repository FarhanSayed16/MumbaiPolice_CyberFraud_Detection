import os
import json

SRC = r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src"

def add_keys():
    en_path = os.path.join(SRC, 'i18n', 'locales', 'en.json')
    mr_path = os.path.join(SRC, 'i18n', 'locales', 'mr.json')
    
    with open(en_path, 'r', encoding='utf-8') as f:
        en = json.load(f)
    with open(mr_path, 'r', encoding='utf-8') as f:
        mr = json.load(f)

    # Add missing keys to dashboard
    new_dash_en = {
        "noActiveWorkload": "No active workload.",
        "awaitingBank": "Awaiting Bank",
        "noticeSent": "Notice Sent",
        "myPortfolioRisk": "My Portfolio Risk",
        "myBreachedCases": "My Breached Cases",
        "myPrioritizedQueue": "My Prioritized Queue",
        "noOpenCases": "No open cases assigned."
    }
    
    new_dash_mr = {
        "noActiveWorkload": "सक्रीय काम नाही.",
        "awaitingBank": "बँकेच्या प्रतीक्षेत",
        "noticeSent": "नोटीस पाठवली",
        "myPortfolioRisk": "माझा पोर्टफोलिओ धोका",
        "myBreachedCases": "माझी उल्लंघित प्रकरणे",
        "myPrioritizedQueue": "माझी प्राधान्य रांग",
        "noOpenCases": "कोणतीही प्रलंबित प्रकरणे नियुक्त केलेली नाहीत."
    }
    
    en["dashboard"].update(new_dash_en)
    mr["dashboard"].update(new_dash_mr)

    with open(en_path, 'w', encoding='utf-8') as f:
        json.dump(en, f, indent=2)
    with open(mr_path, 'w', encoding='utf-8') as f:
        json.dump(mr, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    add_keys()
    print("Added new keys.")
