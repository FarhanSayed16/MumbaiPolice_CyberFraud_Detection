"""
Comprehensive Dark Mode Fix Script
Fixes all remaining dark mode issues across the entire frontend.
"""
import os
import re

SRC = r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src"

def fix_file(filepath, replacements):
    """Apply a list of (old, new) string replacements to a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    for old, new in replacements:
        content = content.replace(old, new)
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Fixed: {os.path.basename(filepath)}")
    return content != original


# ============================================================
# 1. SIDEBAR - fix hover states and border for dark
# ============================================================
fix_file(os.path.join(SRC, "components", "layout", "Sidebar.tsx"), [
    # Fix sidebar border
    ("w-64 border-r bg-white dark:bg-slate-900", "w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900"),
    # Fix non-active link hover - remove duplicate dark:text-slate-100
    ("text-slate-600 dark:text-slate-400 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-100",
     "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"),
    # Fix active link text for dark
    ("bg-blue-50 dark:bg-blue-900/40 text-blue-700 font-semibold border-l-4 border-blue-600",
     "bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400 font-semibold border-l-4 border-blue-600"),
    # Fix the bottom section border
    ("p-4 border-t bg-slate-50 dark:bg-slate-950/50",
     "p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50"),
    # Fix disabled items
    ("text-slate-300", "text-slate-300 dark:text-slate-600"),
    # Fix "Phase 7+" badge
    ("bg-slate-100 text-slate-500 dark:text-slate-400",
     "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"),
])

# ============================================================
# 2. NAVBAR - fix remaining user section classes
# ============================================================
fix_file(os.path.join(SRC, "components", "layout", "Navbar.tsx"), [
    # Fix user name
    ("font-semibold text-slate-800 leading-none",
     "font-semibold text-slate-800 dark:text-white leading-none"),
    # Fix badge number / email
    ('text-xs text-slate-500 mt-0.5',
     'text-xs text-slate-500 dark:text-slate-400 mt-0.5'),
    # Fix settings icon
    ('text-slate-400 hover:text-slate-600',
     'text-slate-400 hover:text-slate-600 dark:hover:text-white'),
    # Fix sign out button
    ('text-xs text-slate-600 hover:text-red-600 hover:bg-red-50 border-slate-200',
     'text-xs text-slate-600 dark:text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 border-slate-200 dark:border-slate-700'),
    # Fix "Not logged in" text
    ('text-xs text-slate-500 italic',
     'text-xs text-slate-500 dark:text-slate-400 italic'),
    # Fix user avatar
    ('bg-blue-100 border border-blue-300 rounded-full flex items-center justify-center text-blue-700',
     'bg-blue-100 dark:bg-blue-900/50 border border-blue-300 dark:border-blue-600 rounded-full flex items-center justify-center text-blue-700 dark:text-blue-400'),
])

# ============================================================
# 3. DASHBOARD - fix dividers, inner borders, hover states
# ============================================================
fix_file(os.path.join(SRC, "pages", "DashboardPage.tsx"), [
    # Fix dividers in case lists
    ("divide-y divide-slate-100",
     "divide-y divide-slate-100 dark:divide-slate-800"),
    # Fix hover on case items - currently has dark:bg-slate-950 always active (not just hover)
    ("hover:bg-slate-50 dark:bg-slate-950 transition-colors",
     "hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"),
    # Fix case link color for dark
    ("text-blue-700 font-medium hover:underline",
     "text-blue-700 dark:text-blue-400 font-medium hover:underline"),
    # Fix inner stat card borders
    ("border border-slate-100",
     "border border-slate-100 dark:border-slate-800"),
    # Fix inner red card border
    ("border border-red-100",
     "border border-red-100 dark:border-red-800/40"),
    # Fix amber badges
    ("bg-amber-100 text-amber-700",
     "bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400"),
    # Fix amber border on external status
    ("border border-amber-100",
     "border border-amber-100 dark:border-amber-800/40"),
    # Fix blue inner badge border
    ("border border-blue-100",
     "border border-blue-100 dark:border-blue-800/40"),
])

# ============================================================
# 4. CASES LIST PAGE - fix input, badges, hover, NCRP badge
# ============================================================
fix_file(os.path.join(SRC, "pages", "CasesListPage.tsx"), [
    # Fix search input
    ("w-full pl-9 pr-4 py-2 border rounded-md text-sm focus:outline-none",
     "w-full pl-9 pr-4 py-2 border border-slate-200 dark:border-slate-700 rounded-md text-sm bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none"),
    # Fix case hover
    ("hover:bg-slate-50 dark:bg-slate-950 transition-colors",
     "hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"),
    # Fix NCRP badge
    ("font-mono bg-slate-100 px-1.5 py-0.5 rounded",
     "font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-1.5 py-0.5 rounded"),
    # Fix "Phase 8 Active" badge
    ("bg-slate-100 text-slate-700 dark:text-slate-300",
     "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"),
    # Fix red error text in dark
    ("text-red-800 text-sm",
     "text-red-800 dark:text-red-200 text-sm"),
    # Fix FIR badge border
    ("border border-blue-200",
     "border border-blue-200 dark:border-blue-700"),
    # Fix duplicate case warning
    ("bg-amber-100 text-amber-800 border border-amber-300",
     "bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-700"),
    # Fix pagination area
    ("border-t bg-slate-50 dark:bg-slate-950/50",
     "border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900"),
    # Fix select dropdown border
    ("py-2 px-3 border rounded-md text-sm bg-white dark:bg-slate-900",
     "py-2 px-3 border border-slate-200 dark:border-slate-700 rounded-md text-sm bg-white dark:bg-slate-800"),
])

# ============================================================
# 5. WATCHLIST PAGE - heavy gray→slate migration + dark variants
# ============================================================
fix_file(os.path.join(SRC, "pages", "WatchlistPage.tsx"), [
    # Fix tab borders
    ("border-b border-gray-200",
     "border-b border-slate-200 dark:border-slate-700"),
    # Fix inactive tab text
    ("border-transparent text-gray-500 hover:text-gray-700",
     "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white"),
    # Fix active tab
    ("border-indigo-500 text-indigo-600",
     "border-indigo-500 text-indigo-600 dark:text-indigo-400"),
    # Fix form labels
    ('block text-sm font-medium text-gray-700',
     'block text-sm font-medium text-slate-700 dark:text-slate-300'),
    # Fix all form inputs
    ("mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
     "mt-1 block w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"),
    # Fix table header
    ("bg-gray-50",
     "bg-slate-50 dark:bg-slate-800"),
    # Fix table header text
    ("text-xs font-medium text-gray-500 uppercase",
     "text-xs font-medium text-slate-500 dark:text-slate-400 uppercase"),
    # Fix table body
    ("bg-white dark:bg-slate-900 divide-y divide-gray-200",
     "bg-white dark:bg-slate-900 divide-y divide-slate-200 dark:divide-slate-800"),
    # Fix table divider at thead level
    ("divide-y divide-gray-200",
     "divide-y divide-slate-200 dark:divide-slate-800"),
    # Fix table cell text - target cell
    ("text-sm font-medium text-gray-900",
     "text-sm font-medium text-slate-900 dark:text-slate-100"),
    # Fix table cell text - reason and status
    ("text-sm text-gray-500",
     "text-sm text-slate-500 dark:text-slate-400"),
    # Fix active/inactive badges
    ("bg-green-100 text-green-800",
     "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300"),
    ("bg-red-100 text-red-800",
     "bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300"),
    # Fix loading/empty text
    ("text-center text-gray-500",
     "text-center text-slate-500 dark:text-slate-400"),
    # Fix action links
    ("text-indigo-600 hover:text-indigo-900",
     "text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300"),
    ("text-red-600 hover:text-red-900",
     "text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"),
    # Fix form card shadow
    ("bg-white dark:bg-slate-900 shadow rounded-lg p-6",
     "bg-white dark:bg-slate-900 shadow dark:shadow-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-800 p-6"),
    # Fix table card shadow
    ("bg-white dark:bg-slate-900 shadow rounded-lg overflow-hidden",
     "bg-white dark:bg-slate-900 shadow dark:shadow-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden"),
])

# ============================================================
# 6. HEALTH PAGE - fix badge text, purple text, blue info bar
# ============================================================
fix_file(os.path.join(SRC, "pages", "HealthPage.tsx"), [
    # Fix OK/ERROR badge text color from dark text on green bg
    ("bg-emerald-600 text-slate-900 dark:text-slate-100",
     "bg-emerald-600 text-white"),
    ("bg-red-600 text-slate-900 dark:text-slate-100",
     "bg-red-600 text-white"),
    # Fix purple text values in service cards
    ("font-mono text-purple-300",
     "font-mono text-purple-600 dark:text-purple-400"),
    # Fix blue-600 text for rate limit
    ("font-mono text-blue-600",
     "font-mono text-blue-600 dark:text-blue-400"),
    # Fix header border
    ("border-b border-slate-200 pb-5",
     "border-b border-slate-200 dark:border-slate-800 pb-5"),
    # Fix blue-900 banner text
    ("text-blue-900 flex items-center justify-between",
     "text-blue-900 dark:text-blue-200 flex items-center justify-between"),
    # Fix blue-100 pill badge
    ("font-mono text-[11px] bg-blue-100 px-2 py-0.5 rounded border border-blue-300 text-blue-800",
     "font-mono text-[11px] bg-blue-100 dark:bg-blue-900/60 px-2 py-0.5 rounded border border-blue-300 dark:border-blue-600 text-blue-800 dark:text-blue-300"),
    # Fix protocol card border
    ("border-amber-200 bg-white dark:bg-slate-900",
     "border-amber-200 dark:border-amber-800/40 bg-white dark:bg-slate-900"),
    # Fix protocol titles
    ("font-semibold text-blue-700 flex",
     "font-semibold text-blue-700 dark:text-blue-400 flex"),
    ("font-semibold text-purple-700 flex",
     "font-semibold text-purple-700 dark:text-purple-400 flex"),
    # Fix hover on refresh button
    ("hover:bg-slate-100 text-slate-700",
     "hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700"),
])

# ============================================================
# 7. LOGIN PAGE - fix shield icon, input styling
# ============================================================
fix_file(os.path.join(SRC, "pages", "LoginPage.tsx"), [
    # Fix background for whole page
    ("min-h-screen flex items-center justify-center bg-slate-50 p-4",
     "min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4"),
    # Fix shield circle
    ("bg-blue-50 border border-blue-200 text-blue-600",
     "bg-blue-50 dark:bg-blue-900/40 border border-blue-200 dark:border-blue-600 text-blue-600 dark:text-blue-400"),
    # Fix card bg
    ("border-slate-200 bg-white",
     "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900"),
    # Fix label text
    ("text-xs font-semibold uppercase tracking-wider text-slate-600",
     "text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400"),
    # Fix input fields
    ("w-full pl-9 pr-3 py-2 rounded-md bg-white border border-slate-200 text-slate-900",
     "w-full pl-9 pr-3 py-2 rounded-md bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"),
    # Fix login button text
    ("text-white font-medium",
     "!text-white font-medium"),
    # Fix error box
    ("bg-red-50 border border-red-200 text-red-900",
     "bg-red-50 dark:bg-red-900/40 border border-red-200 dark:border-red-700 text-red-900 dark:text-red-200"),
    # Fix seed status box
    ("bg-emerald-50 border border-emerald-200 text-emerald-900",
     "bg-emerald-50 dark:bg-emerald-900/40 border border-emerald-200 dark:border-emerald-700 text-emerald-900 dark:text-emerald-200"),
    # Fix seed roles button
    ("border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-600",
     "border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300"),
    # Fix demo role buttons
    ("bg-white hover:bg-slate-100 border border-slate-200",
     "bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700"),
    # Fix title text
    ("text-2xl font-bold tracking-tight text-slate-900",
     "text-2xl font-bold tracking-tight text-slate-900 dark:text-white"),
    # Fix subtitle
    ("text-sm text-slate-500",
     "text-sm text-slate-500 dark:text-slate-400"),
    # Fix portal title
    ("text-lg font-semibold text-slate-900",
     "text-lg font-semibold text-slate-900 dark:text-white"),
    # Fix portal description
    ("CardDescription className=\"text-slate-500\"",
     "CardDescription className=\"text-slate-500 dark:text-slate-400\""),
    # Fix icon colors
    ("text-blue-600", "text-blue-600 dark:text-blue-400"),
    # Fix demo text colors for role buttons
    ("text-blue-700", "text-blue-700 dark:text-blue-400"),
    ("text-purple-700", "text-purple-700 dark:text-purple-400"),
    ("text-emerald-700", "text-emerald-700 dark:text-emerald-400"),
    # Fix separator
    ("border-t border-slate-200/80",
     "border-t border-slate-200/80 dark:border-slate-700"),
    # Fix demo only text
    ("text-xs text-slate-500",
     "text-xs text-slate-500 dark:text-slate-400"),
])

# ============================================================
# 8. NOTIFICATION BELL - fix hover states
# ============================================================
fix_file(os.path.join(SRC, "components", "layout", "NotificationBell.tsx"), [
    # Fix dropdown border
    ("border border-slate-200 rounded-lg shadow-xl",
     "border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl dark:shadow-slate-900/50"),
    # Fix header border
    ("border-b border-slate-200 flex justify-between",
     "border-b border-slate-200 dark:border-slate-700 flex justify-between"),
    # Fix notification item borders
    ("border-b border-slate-200/50 hover:bg-slate-50",
     "border-b border-slate-200/50 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800"),
    # Fix unread bg
    ("bg-slate-100", "bg-slate-100 dark:bg-slate-800"),
    # Fix dropdown bg
    ("bg-white border border-slate-200 dark:border-slate-700",
     "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700"),
])

# ============================================================
# 9. GLOBAL SEARCH - fix search bar
# ============================================================
fix_file(os.path.join(SRC, "components", "layout", "GlobalSearch.tsx"), [
    # Fix search input background/border
    ("bg-slate-50 dark:bg-slate-950 border-slate-200",
     "bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700"),
    # If there are gray classes
    ("bg-gray-50", "bg-slate-50 dark:bg-slate-800"),
    ("border-gray-200", "border-slate-200 dark:border-slate-700"),
    ("text-gray-500", "text-slate-500 dark:text-slate-400"),
    ("text-gray-900", "text-slate-900 dark:text-slate-100"),
])

# ============================================================
# 10. APP.tsx - fix the 403 error card
# ============================================================
fix_file(os.path.join(SRC, "App.tsx"), [
    ("p-8 bg-slate-900 rounded-lg border border-red-500/40 text-center",
     "p-8 bg-red-50 dark:bg-slate-900 rounded-lg border border-red-200 dark:border-red-500/40 text-center"),
    ("text-red-400 font-bold text-lg",
     "text-red-600 dark:text-red-400 font-bold text-lg"),
    ("text-sm text-slate-300",
     "text-sm text-slate-600 dark:text-slate-300"),
])

# ============================================================
# 11. AUDIT LOG PAGE - fix any remaining issues
# ============================================================
fix_file(os.path.join(SRC, "pages", "AuditLogPage.tsx"), [
    ("bg-gray-50", "bg-slate-50 dark:bg-slate-800"),
    ("text-gray-500", "text-slate-500 dark:text-slate-400"),
    ("text-gray-900", "text-slate-900 dark:text-slate-100"),
    ("text-gray-700", "text-slate-700 dark:text-slate-300"),
    ("border-gray-200", "border-slate-200 dark:border-slate-700"),
    ("divide-gray-200", "divide-slate-200 dark:divide-slate-800"),
])

# ============================================================
# 12. ADMIN USER PAGE - fix any remaining issues
# ============================================================
fix_file(os.path.join(SRC, "pages", "AdminUserPage.tsx"), [
    ("bg-gray-50", "bg-slate-50 dark:bg-slate-800"),
    ("text-gray-500", "text-slate-500 dark:text-slate-400"),
    ("text-gray-900", "text-slate-900 dark:text-slate-100"),
    ("text-gray-700", "text-slate-700 dark:text-slate-300"),
    ("border-gray-200", "border-slate-200 dark:border-slate-700"),
    ("divide-gray-200", "divide-slate-200 dark:divide-slate-800"),
])

# ============================================================
# 13. INGESTION QUEUE PAGE
# ============================================================
fix_file(os.path.join(SRC, "pages", "IngestionQueuePage.tsx"), [
    ("bg-gray-50", "bg-slate-50 dark:bg-slate-800"),
    ("text-gray-500", "text-slate-500 dark:text-slate-400"),
    ("text-gray-900", "text-slate-900 dark:text-slate-100"),
    ("text-gray-700", "text-slate-700 dark:text-slate-300"),
    ("border-gray-200", "border-slate-200 dark:border-slate-700"),
])

# ============================================================
# 14. PROFILE PREFERENCES PAGE
# ============================================================
fix_file(os.path.join(SRC, "pages", "ProfilePreferencesPage.tsx"), [
    ("bg-gray-50", "bg-slate-50 dark:bg-slate-800"),
    ("text-gray-500", "text-slate-500 dark:text-slate-400"),
    ("text-gray-900", "text-slate-900 dark:text-slate-100"),
    ("text-gray-700", "text-slate-700 dark:text-slate-300"),
    ("border-gray-200", "border-slate-200 dark:border-slate-700"),
])

# ============================================================
# 15. BULK IMPORT MODAL
# ============================================================
fix_file(os.path.join(SRC, "components", "ingestion", "BulkImportModal.tsx"), [
    ("bg-gray-50", "bg-slate-50 dark:bg-slate-800"),
    ("text-gray-500", "text-slate-500 dark:text-slate-400"),
    ("text-gray-900", "text-slate-900 dark:text-slate-100"),
    ("text-gray-700", "text-slate-700 dark:text-slate-300"),
    ("border-gray-200", "border-slate-200 dark:border-slate-700"),
    ("border-gray-300", "border-slate-300 dark:border-slate-600"),
])

# ============================================================
# 16. CASE INTAKE MODAL
# ============================================================
fix_file(os.path.join(SRC, "components", "cases", "CaseIntakeModal.tsx"), [
    ("bg-gray-50", "bg-slate-50 dark:bg-slate-800"),
    ("text-gray-500", "text-slate-500 dark:text-slate-400"),
    ("text-gray-900", "text-slate-900 dark:text-slate-100"),
    ("text-gray-700", "text-slate-700 dark:text-slate-300"),
    ("border-gray-200", "border-slate-200 dark:border-slate-700"),
    ("border-gray-300", "border-slate-300 dark:border-slate-600"),
])

# ============================================================
# 17. CLUSTER LIST and PSP HEAT TABLE
# ============================================================
for comp_name in ["ClusterList.tsx", "PspHeatTable.tsx", "ClusterGraph.tsx"]:
    fp = os.path.join(SRC, "components", "network", comp_name)
    if os.path.exists(fp):
        fix_file(fp, [
            ("bg-gray-50", "bg-slate-50 dark:bg-slate-800"),
            ("text-gray-500", "text-slate-500 dark:text-slate-400"),
            ("text-gray-900", "text-slate-900 dark:text-slate-100"),
            ("text-gray-700", "text-slate-700 dark:text-slate-300"),
            ("border-gray-200", "border-slate-200 dark:border-slate-700"),
            ("divide-gray-200", "divide-slate-200 dark:divide-slate-800"),
        ])

# ============================================================
# 18. CASE DETAIL PAGE and sub-tabs
# ============================================================
for comp_name in ["CaseDetailPage.tsx"]:
    fp = os.path.join(SRC, "pages", comp_name)
    if os.path.exists(fp):
        fix_file(fp, [
            ("bg-gray-50", "bg-slate-50 dark:bg-slate-800"),
            ("text-gray-500", "text-slate-500 dark:text-slate-400"),
            ("text-gray-900", "text-slate-900 dark:text-slate-100"),
            ("text-gray-700", "text-slate-700 dark:text-slate-300"),
            ("border-gray-200", "border-slate-200 dark:border-slate-700"),
            ("divide-gray-200", "divide-slate-200 dark:divide-slate-800"),
        ])

for comp_name in ["CaseEvidenceTab.tsx", "CaseNoticesTab.tsx", "CaseRiskTab.tsx", "CaseTimelineTab.tsx", "CaseTrailGraph.tsx", "RelatedCasesPanel.tsx"]:
    fp = os.path.join(SRC, "components", "cases", comp_name)
    if os.path.exists(fp):
        fix_file(fp, [
            ("bg-gray-50", "bg-slate-50 dark:bg-slate-800"),
            ("text-gray-500", "text-slate-500 dark:text-slate-400"),
            ("text-gray-900", "text-slate-900 dark:text-slate-100"),
            ("text-gray-700", "text-slate-700 dark:text-slate-300"),
            ("border-gray-200", "border-slate-200 dark:border-slate-700"),
            ("divide-gray-200", "divide-slate-200 dark:divide-slate-800"),
            ("border-gray-300", "border-slate-300 dark:border-slate-600"),
        ])

print("\n✅ Comprehensive dark mode fix complete!")
