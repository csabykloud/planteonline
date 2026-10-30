import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('import_produse/pdf_extracted_text.txt', encoding='utf-8-sig') as f:
    text = f.read()

print(f"Total characters: {len(text)}")
pages = text.split('=== page_')
for p in pages:
    if p.strip():
        lines = [l.strip() for l in p.splitlines() if l.strip()]
        page_title = lines[0] if lines else '?'
        print(f"\n=================== PAGE {page_title} ===================")
        print('\n'.join(lines[1:12]))
