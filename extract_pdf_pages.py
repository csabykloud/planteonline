import os
import pypdf
from PIL import Image

pdf_path = os.path.join('import_produse', 'documente_pdf', 'Catalog Mont Rose 2026 .pdf')
out_dir = os.path.join('import_produse', 'pdf_pages')
os.makedirs(out_dir, exist_ok=True)

reader = pypdf.PdfReader(pdf_path)
print(f"Total pages: {len(reader.pages)}")

for i, page in enumerate(reader.pages):
    for j, img in enumerate(page.images):
        ext = img.name.rsplit('.', 1)[-1]
        out_name = f"page_{i+1:02d}.{ext}"
        out_path = os.path.join(out_dir, out_name)
        with open(out_path, 'wb') as f:
            f.write(img.data)
        print(f"Extracted Page {i+1} -> {out_name} ({len(img.data)} bytes)")
