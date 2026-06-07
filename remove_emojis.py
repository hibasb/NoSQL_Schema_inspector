import os
import re

# Regex to match emojis
emoji_pattern = re.compile(
    r'[\U00010000-\U0010ffff]',
    flags=re.UNICODE
)

def remove_emojis_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = emoji_pattern.sub('', content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Removed emojis from {filepath}")

for filename in os.listdir('.'):
    if filename.endswith('.py'):
        remove_emojis_from_file(filename)
