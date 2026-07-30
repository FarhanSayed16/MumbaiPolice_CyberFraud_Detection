import os
import json

SRC = r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src"

def add_dynamic():
    en_path = os.path.join(SRC, 'i18n', 'locales', 'en.json')
    mr_path = os.path.join(SRC, 'i18n', 'locales', 'mr.json')
    
    with open(en_path, 'r', encoding='utf-8') as f:
        en = json.load(f)
    with open(mr_path, 'r', encoding='utf-8') as f:
        mr = json.load(f)

    if "dynamic" not in en["notifications"]:
        en["notifications"]["dynamic"] = {}
        mr["notifications"]["dynamic"] = {}
        
    en["notifications"]["dynamic"].update({
        "High Risk Case Alert": "High Risk Case Alert",
        "High Risk Account Detected": "High Risk Account Detected"
    })
    mr["notifications"]["dynamic"].update({
        "High Risk Case Alert": "उच्च धोका असलेले प्रकरण अलर्ट",
        "High Risk Account Detected": "उच्च धोका असलेले खाते आढळले"
    })

    with open(en_path, 'w', encoding='utf-8') as f:
        json.dump(en, f, indent=2)
    with open(mr_path, 'w', encoding='utf-8') as f:
        json.dump(mr, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    add_dynamic()
    print("Added dynamic.")
