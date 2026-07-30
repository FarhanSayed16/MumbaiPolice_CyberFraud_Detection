import os

def apply_replacements(fpath, replacements):
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

# Fix LoginPage
login_replacements = [
    ('bg-blue-900/40 border border-blue-500/30 text-blue-400', 'bg-blue-50 border border-blue-200 text-blue-600'),
    ('hover:bg-blue-500 text-slate-900', 'hover:bg-blue-500 text-white'), # Fix Login button text
    ('bg-slate-50 hover:bg-white text-blue-300', 'bg-slate-50 hover:bg-slate-100 text-slate-600'), # Seed Roles button
    ('text-blue-300', 'text-blue-700'),
    ('text-purple-300', 'text-purple-700'),
    ('text-emerald-300', 'text-emerald-700'),
    ('text-blue-400', 'text-blue-600') # Fix lock icon
]
apply_replacements(r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src\pages\LoginPage.tsx", login_replacements)

# Fix NotificationBell
notif_replacements = [
    ('text-indigo-400 hover:underline', 'text-indigo-600 hover:underline'),
    ('bg-indigo-500/20 text-indigo-400', 'bg-indigo-100 text-indigo-700')
]
apply_replacements(r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src\components\layout\NotificationBell.tsx", notif_replacements)

print("Fixed specific UI colors for light theme!")
