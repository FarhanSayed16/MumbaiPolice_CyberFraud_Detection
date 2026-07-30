import os

SRC = r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src"

def fix_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    for old, new in replacements:
        content = content.replace(old, new)
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {os.path.basename(filepath)}")

# 1. AuditLogPage.tsx
fix_file(os.path.join(SRC, "pages", "AuditLogPage.tsx"), [
    ("bg-purple-50 border border-purple-200 text-purple-900",
     "bg-purple-50 dark:bg-purple-900/40 border border-purple-200 dark:border-purple-700 text-purple-900 dark:text-purple-200"),
    ("text-slate-900 dark:text-slate-100\">BNSS & IT",
     "text-purple-900 dark:text-purple-100\">BNSS & IT"),
    ("text-slate-600 dark:text-slate-400 mt-0.5\">\n            Every login",
     "text-purple-800 dark:text-purple-200 mt-0.5\">\n            Every login"),
    ("divide-y divide-slate-200",
     "divide-y divide-slate-200 dark:divide-slate-800"),
    ("border-b border-slate-200",
     "border-b border-slate-200 dark:border-slate-800"),
    ("hover:bg-slate-100/40 transition-colors",
     "hover:bg-slate-100/40 dark:hover:bg-slate-800/40 transition-colors"),
    ("text-blue-700 font-semibold",
     "text-blue-700 dark:text-blue-400 font-semibold"),
])

# 2. AdminUserPage.tsx
fix_file(os.path.join(SRC, "pages", "AdminUserPage.tsx"), [
    ("divide-y divide-slate-200",
     "divide-y divide-slate-200 dark:divide-slate-800"),
    ("border-b border-slate-200",
     "border-b border-slate-200 dark:border-slate-800"),
    ("hover:bg-slate-50 dark:bg-slate-950 transition-colors",
     "hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"),
    ("bg-slate-50 dark:bg-slate-950 text-xs",
     "bg-slate-50 dark:bg-slate-900/50 text-xs"),
])

# 3. RelatedCasesPanel.tsx
fix_file(os.path.join(SRC, "components", "cases", "RelatedCasesPanel.tsx"), [
    ("text-blue-600 hover:underline",
     "text-blue-600 dark:text-blue-400 hover:underline"),
    ("hover:bg-slate-50 dark:bg-slate-950",
     "hover:bg-slate-50 dark:hover:bg-slate-800/50"),
    ("divide-y divide-slate-100",
     "divide-y divide-slate-100 dark:divide-slate-800"),
    ("border-b flex items-center justify-between",
     "border-b border-slate-200 dark:border-slate-800 flex items-center justify-between"),
    ("bg-slate-100 text-slate-700 dark:text-slate-300 px-2 py-1 rounded-full border",
     "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-1 rounded-full border border-slate-200 dark:border-slate-700"),
])
