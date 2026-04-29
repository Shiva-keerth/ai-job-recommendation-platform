import os
import re

files_to_fix = [
    r"c:\Users\ganti\chart\8 sem project\modules\ui_candidate.py",
    r"c:\Users\ganti\chart\8 sem project\modules\ui_employer.py",
    r"c:\Users\ganti\chart\8 sem project\modules\ui_admin.py",
    r"c:\Users\ganti\chart\8 sem project\modules\salary_estimator.py",
    r"c:\Users\ganti\chart\8 sem project\modules\resume_scorecard.py",
    r"c:\Users\ganti\chart\8 sem project\modules\profile_strength.py",
]

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Replacements for f-string template variables
    text = re.sub(r'\{SURFACE\}', r"{T()['SURFACE']}", text)
    text = re.sub(r'\{CARD_BORDER\}', r"{T()['CARD_BORDER']}", text)
    text = re.sub(r'\{MUTED\}', r"{T()['MUTED']}", text)
    text = re.sub(r'\{SUCCESS\}', r"{T()['SUCCESS']}", text)
    text = re.sub(r'\{WARNING\}', r"{T()['WARNING']}", text)
    text = re.sub(r'\{INFO\}', r"{T()['INFO']}", text)
    text = re.sub(r'\{PRIMARY\}', r"{T()['PRIMARY']}", text)
    
    # Also fix some hardcoded colors that might still be left
    text = re.sub(r'color:#f0f6fc', r"color:{T()['TEXT_HEADING']}", text)
    text = re.sub(r'color:#1a1a2e', r"color:{T()['TEXT_HEADING']}", text)
    text = re.sub(r'color:white', r"color:{T()['TEXT']}", text)
    text = re.sub(r'color:#ffffff', r"color:{T()['TEXT']}", text, flags=re.IGNORECASE)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

print("Done fixing files!")
