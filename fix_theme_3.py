import os

def apply_replacements(fpath, replacements):
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

# Fix MainLayout
main_layout_replacements = [
    ('bg-slate-950 text-white', 'bg-slate-50 text-slate-900')
]
apply_replacements(r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src\components\layout\MainLayout.tsx", main_layout_replacements)

# Fix NotificationBell
notif_replacements = [
    ('text-slate-400 hover:text-white', 'text-slate-500 hover:text-slate-900'),
    ('bg-slate-800', 'bg-white'),
    ('border-slate-700', 'border-slate-200'),
    ('text-white', 'text-slate-900'),
    ('text-slate-400', 'text-slate-500'),
    ('text-slate-300', 'text-slate-700'),
    ('bg-slate-700/30', 'bg-slate-50'),
    ('bg-slate-700/10', 'bg-slate-100'),
    ('border-slate-700/50', 'border-slate-100')
]
apply_replacements(r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src\components\layout\NotificationBell.tsx", notif_replacements)

# Fix LoginPage
login_replacements = [
    ('bg-slate-950 p-4', 'bg-slate-50 p-4'),
    ('text-white', 'text-slate-900'),
    ('text-slate-400', 'text-slate-500'),
    ('text-slate-300', 'text-slate-600'),
    ('border-slate-800', 'border-slate-200'),
    ('bg-slate-900', 'bg-white'),
    ('bg-slate-950', 'bg-white'),
    ('bg-red-950/60 border border-red-500/40 text-red-300', 'bg-red-50 border border-red-200 text-red-900'),
    ('bg-emerald-950/60 border border-emerald-500/40 text-emerald-300', 'bg-emerald-50 border border-emerald-200 text-emerald-900'),
    ('bg-slate-800/50', 'bg-slate-50'),
    ('bg-slate-800', 'bg-white'),
    ('border-slate-700', 'border-slate-200'),
    ('hover:bg-slate-700', 'hover:bg-slate-100')
]
apply_replacements(r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src\pages\LoginPage.tsx", login_replacements)

print("Fixed Login Page, Notifications, and Layout!")
