import os
import re

directory = r"d:\MumbaiPolice_CyberFraud_Detection\frontend\src"

# Mapping of light mode classes to their corresponding dark mode classes
mappings = {
    r'\bbg-white\b': 'bg-white dark:bg-slate-900',
    r'\bbg-slate-50\b': 'bg-slate-50 dark:bg-slate-950',
    r'\btext-slate-900\b': 'text-slate-900 dark:text-slate-100',
    r'\btext-slate-800\b': 'text-slate-800 dark:text-slate-200',
    r'\btext-slate-700\b': 'text-slate-700 dark:text-slate-300',
    r'\btext-slate-600\b': 'text-slate-600 dark:text-slate-400',
    r'\btext-slate-500\b': 'text-slate-500 dark:text-slate-400',
    r'\border-slate-200\b': 'border-slate-200 dark:border-slate-800',
    r'\border-slate-300\b': 'border-slate-300 dark:border-slate-700',
    # Handle specifically colored backgrounds (e.g. the ones we just added)
    r'\bbg-blue-50\b': 'bg-blue-50 dark:bg-blue-900/40',
    r'\border-blue-200\b': 'border-blue-200 dark:border-blue-500/30',
    r'\bbg-red-50\b': 'bg-red-50 dark:bg-red-900/40',
    r'\border-red-200\b': 'border-red-200 dark:border-red-500/30',
    r'\bbg-emerald-50\b': 'bg-emerald-50 dark:bg-emerald-900/40',
    r'\border-emerald-200\b': 'border-emerald-200 dark:border-emerald-500/30',
    r'\bbg-amber-50\b': 'bg-amber-50 dark:bg-amber-900/40',
    r'\border-amber-200\b': 'border-amber-200 dark:border-amber-500/30'
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Iterate through each mapping
    for light_pattern, replacement in mappings.items():
        # Find all occurrences of the light class
        # But we only want to replace it if it's NOT already followed by the dark variant.
        # This is a bit tricky with regex, so we'll do a simpler approach:
        # 1. First, temporarily replace the correct combination with a placeholder
        # 2. Then replace the light pattern with the new combination
        # 3. Restore the placeholder
        
        dark_class = replacement.split(' ')[1]
        
        # We need to make sure we don't duplicate `dark:bg-slate-900` if it's already there
        # For simplicity, let's just do a string replace on exact matches that might happen if we ran it twice,
        # but since we are doing this once, we can just use regex carefully.
        
        # A safer approach for a one-off script: just replace `bg-white` with `bg-white dark:bg-slate-900`
        # and then clean up any `bg-white dark:bg-slate-900 dark:bg-slate-900` mistakes.
        content = re.sub(light_pattern, replacement, content)
        
        # Clean up duplicates that might have existed
        duplicate_pattern = re.escape(replacement) + r'(?:\s+' + re.escape(dark_class) + r')+'
        content = re.sub(duplicate_pattern, replacement, content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            process_file(os.path.join(root, file))

print("Dark mode classes injected successfully.")
