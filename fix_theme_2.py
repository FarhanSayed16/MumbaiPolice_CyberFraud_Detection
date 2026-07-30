import os

health_replacements = [
    ('bg-emerald-950/20', 'bg-emerald-50'),
    ('border-emerald-500/40', 'border-emerald-200'),
    ('bg-red-950/20', 'bg-red-50'),
    ('border-red-500/40', 'border-red-200'),
    ('border-amber-500/40', 'border-amber-200'),
    ('text-blue-300 flex items-center', 'text-blue-700 flex items-center'),
    ('text-purple-300 flex items-center', 'text-purple-700 flex items-center'),
    ('bg-blue-950/30 border border-blue-500/30 text-blue-200', 'bg-blue-50 border border-blue-200 text-blue-900'),
    ('bg-blue-900/60 px-2 py-0.5 rounded border border-blue-400/40', 'bg-blue-100 px-2 py-0.5 rounded border border-blue-300 text-blue-800'),
    ('text-blue-300', 'text-blue-600')
]

audit_replacements = [
    ('bg-purple-950/40 border border-purple-500/30 text-purple-200', 'bg-purple-50 border border-purple-200 text-purple-900'),
    ('bg-red-950/60 border border-red-500/40 text-red-300', 'bg-red-50 border border-red-200 text-red-900'),
    ('bg-emerald-950/60 text-emerald-300 border border-emerald-500/30', 'bg-emerald-50 text-emerald-700 border border-emerald-200'),
    ('bg-red-950/60 text-red-300 border border-red-500/30', 'bg-red-50 text-red-700 border border-red-200'),
    ('text-blue-300 font-semibold', 'text-blue-700 font-semibold'),
    ('divide-slate-800/60', 'divide-slate-200'),
    ('text-blue-400', 'text-blue-600'),
    ('text-purple-400', 'text-purple-600'),
    ('text-red-400', 'text-red-600')
]

def apply_replacements(fpath, replacements):
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

apply_replacements(r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src\pages\HealthPage.tsx", health_replacements)
apply_replacements(r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src\pages\AuditLogPage.tsx", audit_replacements)

print("Inner component themes fixed!")
