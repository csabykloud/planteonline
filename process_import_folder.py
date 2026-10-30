import os
import sys
from match_products_and_build import build_products

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMPORT_DIR = os.path.join(BASE_DIR, 'import_produse')
SHOWCASE_PATH = os.path.join(IMPORT_DIR, 'termek_bemutato')
PDF_DIR = os.path.join(IMPORT_DIR, 'documente_pdf')


def run_import():
    products = build_products()

    showcase_count = 0
    if os.path.exists(SHOWCASE_PATH):
        showcase_count = len([
            f for f in os.listdir(SHOWCASE_PATH)
            if f.rsplit('.', 1)[-1].lower() in {'jpg', 'jpeg', 'png', 'webp', 'gif'}
        ])

    doc_files = []
    if os.path.exists(PDF_DIR):
        doc_files = os.listdir(PDF_DIR)

    message = (
        f"Sincronizare finalizată cu succes! "
        f"Produse asociate cu 'Descriere Produse.txt': {len(products)}; "
        f"Imagini de prezentare (showcase) active: {showcase_count}."
    )
    return {
        'pdf_processed': True,
        'pdf_files': doc_files,
        'new_products_from_pdf': len(products),
        'product_images_copied': len(products),
        'showcase_images_found': showcase_count,
        'message': message
    }


if __name__ == '__main__':
    res = run_import()
    print(res['message'])
