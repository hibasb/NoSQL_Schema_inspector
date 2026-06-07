import os
import re
import sys

# Reconfigure stdout to use utf-8 if possible
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

emoji_pattern = re.compile(
    r'[\U00010000-\U0010ffff]'  # Astral planes
    r'|[\u2600-\u27BF]'          # Miscellaneous Symbols and Dingbats
    r'|[\u2B05-\u2B07\u2B1B\u2B1C\u2B50\u2B55]'  # Arrows / Stars
    r'|[\u231A\u231B\u23E9-\u23EC\u23F0\u23F3]'  # Watch, Hourglass, media buttons
    r'|[\u2934\u2935]'            # Arrows
    r'|[\u3030\u303D]'            # Alternation mark
    r'|[\u3297\u3299]'            # Enclosed CJK
)

exclude_dirs = {'.git', '__pycache__', 'node_modules', '.streamlit', '.vscode'}
exclude_files = {'serviceAccountKey.json', 'snapshots.json', 'check_emojis.py', 'remove_emojis.py'}

def scan_for_emojis():
    findings = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file in exclude_files:
                continue
            filepath = os.path.join(root, file)
            if not file.endswith(('.py', '.tsx', '.ts', '.js', '.jsx', '.html', '.css', '.md')):
                continue
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for line_idx, line in enumerate(lines, 1):
                    matches = emoji_pattern.findall(line)
                    if matches:
                        findings.append(f"{filepath}:{line_idx} -> Matches: {repr(matches)} | Content: {line.strip()}")
            except Exception as e:
                findings.append(f"Error reading {filepath}: {e}")
                
    with open('emoji_findings.txt', 'w', encoding='utf-8') as out:
        out.write('\n'.join(findings))
    print(f"Done scanning. Found {len(findings)} lines with emojis. Saved to emoji_findings.txt")

if __name__ == '__main__':
    scan_for_emojis()
