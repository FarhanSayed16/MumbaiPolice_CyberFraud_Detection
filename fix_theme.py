import os

files = [
    r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src\pages\AuditLogPage.tsx",
    r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src\pages\HealthPage.tsx"
]

replacements = [
    ('className="space-y-6 bg-slate-950 -m-8 p-8 min-h-[calc(100vh-64px)] text-slate-200"', 'className="space-y-6"'),
    ('text-white', 'text-slate-900'),
    ('bg-slate-950', 'bg-slate-50'),
    ('bg-slate-900', 'bg-white'),
    ('border-slate-800', 'border-slate-200'),
    ('border-slate-700', 'border-slate-300'),
    ('text-slate-400', 'text-slate-500'),
    ('text-slate-300', 'text-slate-600'),
    ('text-slate-200', 'text-slate-700'),
    ('bg-slate-800', 'bg-slate-100'),
]

for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

print("Theme fixed!")
