import os
import json
import random
import datetime
import time
import re
import urllib.parse
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, session, abort, Response
from markupsafe import escape
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from recommendation_engine import recommend_products_for_plant, recommend_for_article

app = Flask(__name__)
app.secret_key = os.environ.get('PLANTEONLINE_SECRET_KEY', 'planteonline-secret-key-modern-2026-hardened-9f8e7d6c')

# Hardened Session Cookie Configuration
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('HTTPS_ENABLED', '0') == '1',
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(hours=8),
    TEMPLATES_AUTO_RELOAD=True
)
app.jinja_env.auto_reload = True

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
IMPORT_DIR = os.path.join(os.path.dirname(__file__), 'import_produse')
PRODUSE_DIR = os.path.join(IMPORT_DIR, 'produse_recomandate')
SHOWCASE_DIR = os.path.join(IMPORT_DIR, 'termek_bemutato')
PDF_DIR = os.path.join(IMPORT_DIR, 'documente_pdf')

# Strictly raster image extensions only (removed 'svg' to prevent Stored SVG/XML XSS; blocked .php/.phtml/.phar)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
FORBIDDEN_DOUBLE_EXT_PATTERN = re.compile(
    r'\.(php[0-9]?|phtml|phar|inc|pl|py|rb|sh|cgi|fcgi|asp|aspx|jsp|jspx|exe|dll|bat|cmd|ps1|vbs|js|mjs|html|htm|svg|htaccess|htpasswd)(\.|$)',
    re.IGNORECASE
)

for d in [DATA_DIR, UPLOAD_FOLDER, IMPORT_DIR, PRODUSE_DIR, SHOWCASE_DIR, PDF_DIR]:
    os.makedirs(d, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size (DoS protection)

def allowed_file(filename, file_obj=None):
    """
    Validates filename extension, blocks dangerous double extensions (e.g. shell.php.jpg),
    and optionally inspects file header magic bytes to reject disguised PHP/HTML/script payloads
    or non-image files.
    """
    if not filename or '.' not in filename or '\x00' in filename:
        return False
    if FORBIDDEN_DOUBLE_EXT_PATTERN.search(filename):
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    if file_obj is not None and hasattr(file_obj, 'stream'):
        try:
            pos = file_obj.stream.tell()
            head = file_obj.stream.read(512)
            file_obj.stream.seek(pos)
            if not head:
                return False
            head_lower = head.lower()
            if b'<?php' in head_lower or b'<script' in head_lower or b'#!/usr' in head_lower or b'#!/bin' in head_lower:
                return False
            # Verify genuine raster image magic-byte signatures (PNG, JPEG, GIF, WEBP)
            is_png = head.startswith(b'\x89PNG\r\n\x1a\n')
            is_jpg = head.startswith(b'\xff\xd8\xff')
            is_gif = head.startswith((b'GIF87a', b'GIF89a'))
            is_webp = len(head) >= 12 and head[:4] == b'RIFF' and head[8:12] == b'WEBP'
            if not (is_png or is_jpg or is_gif or is_webp):
                return False
        except Exception:
            return False
    return True

def sanitize_external_url(raw_url):
    """Allows only safe http://, https://, or relative / paths; blocks javascript:, data:, php:, file: schemes."""
    if not raw_url:
        return ''
    u = raw_url.strip()
    if not u:
        return ''
    parsed = urllib.parse.urlsplit(u)
    if parsed.scheme and parsed.scheme.lower() not in ('http', 'https'):
        return ''
    if u.lower().startswith(('javascript:', 'data:', 'vbscript:', 'php:', 'file:', 'expect:')):
        return ''
    return u

def is_safe_redirect_url(target):
    """Prevents Open Redirect attacks on login `next` parameter."""
    if not target:
        return False
    target = target.strip().replace('\\', '/')
    if target.startswith('//'):
        return False
    ref_url = urllib.parse.urlparse(request.host_url)
    test_url = urllib.parse.urlparse(urllib.parse.urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# Helpers to load and save data
def load_json(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return [] if 's.json' in filename else {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filename, data):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- ANALYTICS & STATS HELPERS ---
def get_analytics():
    data = load_json('analytics.json')
    if not data or not isinstance(data, dict) or 'traffic' not in data:
        data = {
            'traffic': {
                'total_visits': 0,
                'sources': {'google': 0, 'facebook': 0, 'instagram': 0, 'tiktok': 0, 'pinterest': 0, 'direct': 0},
                'recent_visits': []
            },
            'searches': {
                'total_searches': 0,
                'queries': {},
                'recent': []
            },
            'products': {
                'total_views': 0,
                'total_clicks': 0,
                'items': {}
            }
        }
    return data

def save_analytics(data):
    save_json('analytics.json', data)

def classify_referrer(referrer, utm_source):
    ref_lower = (referrer or '').lower()
    utm_lower = (utm_source or '').lower()

    if 'google' in ref_lower or 'google' in utm_lower:
        return 'google'
    elif 'facebook' in ref_lower or 'fb.me' in ref_lower or 'facebook' in utm_lower or utm_lower == 'fb':
        return 'facebook'
    elif 'instagram' in ref_lower or 'instagram' in utm_lower or utm_lower == 'ig':
        return 'instagram'
    elif 'tiktok' in ref_lower or 'tiktok' in utm_lower:
        return 'tiktok'
    elif 'pinterest' in ref_lower or 'pin.it' in ref_lower or 'pinterest' in utm_lower:
        return 'pinterest'
    else:
        return 'direct'

def record_visit(source, path, referrer):
    try:
        data = get_analytics()
        traffic = data.setdefault('traffic', {})
        traffic['total_visits'] = traffic.get('total_visits', 0) + 1
        sources = traffic.setdefault('sources', {'google': 0, 'facebook': 0, 'instagram': 0, 'tiktok': 0, 'pinterest': 0, 'direct': 0})
        sources[source] = sources.get(source, 0) + 1

        recent = traffic.setdefault('recent_visits', [])
        now_str = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        clean_ref = referrer.replace('https://', '').replace('http://', '').strip('/') if referrer else 'Direct / Marcaj'
        recent.insert(0, {
            'timestamp': now_str,
            'source': source,
            'path': path,
            'referrer': clean_ref[:60]
        })
        traffic['recent_visits'] = recent[:35]
        save_analytics(data)
    except Exception as e:
        app.logger.error(f"Error in record_visit: {e}")

def record_search(query, target='plante', results_count=0):
    if not query or len(query.strip()) < 2:
        return
    q = query.strip().lower()
    try:
        data = get_analytics()
        searches = data.setdefault('searches', {})
        searches['total_searches'] = searches.get('total_searches', 0) + 1
        queries = searches.setdefault('queries', {})
        now_str = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')

        if q in queries:
            queries[q]['count'] = queries[q].get('count', 0) + 1
            queries[q]['last_searched'] = now_str
            queries[q]['results_found'] = results_count
            queries[q]['target'] = target
        else:
            queries[q] = {
                'count': 1,
                'last_searched': now_str,
                'results_found': results_count,
                'target': target
            }

        recent = searches.setdefault('recent', [])
        recent.insert(0, {
            'query': q,
            'target': target,
            'timestamp': now_str,
            'results': results_count
        })
        searches['recent'] = recent[:35]
        save_analytics(data)
    except Exception as e:
        app.logger.error(f"Error in record_search: {e}")

def record_product_interaction(prod_id, interaction_type='view'):
    try:
        data = get_analytics()
        prods = data.setdefault('products', {})
        if interaction_type == 'click':
            prods['total_clicks'] = prods.get('total_clicks', 0) + 1
        else:
            prods['total_views'] = prods.get('total_views', 0) + 1

        items = prods.setdefault('items', {})
        pid_str = str(prod_id)
        now_str = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')

        catalog_prods = load_json('products.json')
        p_info = next((p for p in catalog_prods if p['id'] == prod_id), None)
        p_name = p_info['name'] if p_info else f"Produs #{prod_id}"
        p_brand = p_info.get('brand', 'Florasol') if p_info else 'Florasol'
        p_img = p_info.get('image_url', '') if p_info else ''

        if pid_str in items:
            if interaction_type == 'click':
                items[pid_str]['clicks'] = items[pid_str].get('clicks', 0) + 1
            else:
                items[pid_str]['views'] = items[pid_str].get('views', 0) + 1
            items[pid_str]['last_interacted'] = now_str
            if p_img and not items[pid_str].get('image_url'):
                items[pid_str]['image_url'] = p_img
        else:
            items[pid_str] = {
                'name': p_name,
                'brand': p_brand,
                'views': 1 if interaction_type == 'view' else 0,
                'clicks': 1 if interaction_type == 'click' else 0,
                'last_interacted': now_str,
                'image_url': p_img
            }
        save_analytics(data)
    except Exception as e:
        app.logger.error(f"Error in record_product_interaction: {e}")

# --- WAF & PHP VULNERABILITY / PROBE SHIELD (CVE-2024-4577, PHP-CGI, PHP-FPM, PHPUnit, Path Traversal) ---
PHP_EXPLOIT_QUERY_PATTERNS = re.compile(
    r'(%ad|\xad|allow_url_include|auto_prepend_file|auto_append_file|php://|data://|expect://|phar://|zip://|'
    r'eval-stdin\.php|invokefunction|call_user_func_array|think\\app|\.\./|%2e%2e|%00)',
    re.IGNORECASE
)
FORBIDDEN_PROBE_PATHS = (
    '/wp-admin', '/wp-login', '/wp-content', '/wp-includes', '/xmlrpc.php',
    '/vendor/phpunit', '/phpunit', '/.env', '/.git', '/.htaccess', '/.htpasswd',
    '/phpinfo', '/phpmyadmin', '/pma', '/adminer', '/cgi-bin'
)
LEGACY_PHP_REDIRECTS = {
    '/index.php': '/',
    '/calendar.php': '/calendar',
    '/articole.php': '/articole',
    '/plante.php': '/plante-az',
    '/despre_noi.php': '/despre-noi',
    '/despre.php': '/despre-noi',
}

@app.before_request
def security_waf_and_php_shield():
    path = request.path or ''
    path_lower = path.lower()
    raw_qs = request.query_string.decode('latin-1', errors='ignore')

    # 1. Block PHP-CGI Argument Injection (CVE-2024-4577 soft-hyphen %ADd), stream wrappers, and RCE payloads
    if PHP_EXPLOIT_QUERY_PATTERNS.search(raw_qs) or PHP_EXPLOIT_QUERY_PATTERNS.search(path_lower):
        abort(403)

    # 2. Block common vulnerability scanner & botnet probe paths
    if any(path_lower.startswith(p) for p in FORBIDDEN_PROBE_PATHS):
        abort(403)

    # 3. Handle .php/.phtml/.phar requests safely:
    #    - 301-redirect known legacy PlanteOnline.ro pages (calendar.php, articole.php, etc.)
    #    - Block all unknown/malicious .php/.phtml/.phar probes with 403 Forbidden
    if path_lower.endswith(('.php', '.phtml', '.phar', '.php5', '.php7', '.php8', '.inc', '.cgi')):
        if path_lower in LEGACY_PHP_REDIRECTS and request.method in ('GET', 'HEAD'):
            return redirect(LEGACY_PHP_REDIRECTS[path_lower], code=301)
        abort(403)

    # 4. CSRF Same-Origin Verification for Admin & Upload POST requests
    if request.method == 'POST' and (path_lower.startswith('/admin') or path_lower.startswith('/api/upload')):
        origin = request.headers.get('Origin') or request.headers.get('Referer')
        if origin:
            parsed_origin = urllib.parse.urlparse(origin)
            parsed_host = urllib.parse.urlparse(request.host_url)
            if parsed_origin.netloc and parsed_origin.netloc != parsed_host.netloc:
                abort(403)

@app.errorhandler(404)
def page_not_found_handler(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resursa solicitată nu a fost găsită (404).'}), 404
    return (
        '<!DOCTYPE html><html lang="ro"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '<title>404 - Pagina nu a fost găsită | PlanteOnline.ro</title></head>'
        '<body style="background:#F4F7F4;font-family:Inter,system-ui,sans-serif;color:#1c1917;display:flex;align-items:center;justify-content:center;min-height:90vh;margin:0;padding:1rem;">'
        '<div style="background:#fff;border:1px solid #e7e5e4;border-radius:1.5rem;padding:2.5rem;max-width:440px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,0.05);">'
        '<div style="font-size:2.5rem;font-weight:800;color:#15803d;margin-bottom:0.5rem;">404</div>'
        '<h1 style="font-size:1.25rem;margin:0 0 0.75rem;">Pagina solicitată nu a fost găsită</h1>'
        '<p style="font-size:0.85rem;color:#57534e;line-height:1.6;margin-bottom:1.5rem;">Adresa pe care încercați să o accesați nu există sau a fost mutată în noul catalog PlanteOnline.ro.</p>'
        '<a href="/" style="display:inline-block;background:#15803d;color:#fff;text-decoration:none;padding:0.65rem 1.4rem;border-radius:0.75rem;font-size:0.8rem;font-weight:600;">Înapoi la Pagina Principală</a>'
        '</div></body></html>'
    ), 404

@app.errorhandler(413)
def request_entity_too_large(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Fișierul încărcat depășește limita maximă admisă (16 MB).'}), 413
    flash('Fișierul încărcat este prea mare! Limita maximă admisă este de 16 MB.', 'danger')
    return redirect(request.referrer or url_for('home'))

@app.after_request
def add_security_headers(response):
    # Prevent MIME-sniffing (stops disguised image uploads from executing as HTML/JS/PHP)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Prevent Clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Strict Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Cross-domain policy & permissions hardening
    response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self'; object-src 'none'; base-uri 'self';"
    # Hide underlying server details
    response.headers.pop('Server', None)
    response.headers.pop('X-Powered-By', None)
    return response

@app.before_request
def auto_track_visitor():
    path = request.path
    if (path.startswith('/static') or 
        path.startswith('/api') or 
        path.startswith('/admin') or 
        path.startswith('/showcase_img') or 
        path == '/favicon.ico' or
        path.lower().endswith(('.php', '.phtml', '.phar', '.env'))):
        return

    referrer = request.referrer or ''
    utm = request.args.get('utm_source') or request.args.get('ref') or ''
    
    # Track when user starts session or visits with a distinct UTM campaign
    if 'tracked_source' not in session or utm:
        source = classify_referrer(referrer, utm)
        session['tracked_source'] = source
        record_visit(source, path[:120], referrer)

# Template filter to render articles in clean, readable typography matching product descriptions
@app.template_filter('format_article')
def format_article_filter(content):
    if not content:
        return ""
    
    lines = content.strip().split('\n')
    html_parts = []
    in_list = False
    
    for raw_line in lines:
        # Escape raw HTML characters first to prevent Stored XSS when combined with |safe
        line = str(escape(raw_line.strip()))
        if not line:
            if in_list:
                html_parts.append('</div>')
                in_list = False
            continue
            
        # Check for H3 heading (### Title)
        if line.startswith('### '):
            if in_list:
                html_parts.append('</div>')
                in_list = False
            title = line[4:].strip()
            html_parts.append(
                f'<div class="mt-8 mb-3 pt-4 border-t border-stone-100">'
                f'<h3 class="text-base sm:text-lg font-serif font-bold text-stone-900 flex items-center">'
                f'<span class="w-2.5 h-2.5 rounded-full bg-botanic-600 mr-2.5 shrink-0"></span>'
                f'<span>{title}</span>'
                f'</h3>'
                f'</div>'
            )
        # Check for bold subheading (**Title**)
        elif (line.startswith('**') and line.endswith('**')) or (line.startswith('**') and ':' in line and line.count('**') >= 2):
            if in_list:
                html_parts.append('</div>')
                in_list = False
            sub_text = line
            if sub_text.startswith('**') and sub_text.endswith('**') and sub_text.count('**') == 2:
                sub_text = sub_text[2:-2].strip()
            else:
                sub_text = re.sub(r'\*\*(.*?)\*\*', r'<span class="font-bold text-stone-900">\1</span>', sub_text)
            html_parts.append(
                f'<h4 class="text-xs sm:text-sm font-bold text-stone-900 mt-5 mb-2 text-botanic-950 flex items-center">'
                f'<span class="w-1.5 h-1.5 rounded-full bg-amber-500 mr-2 shrink-0"></span>'
                f'<span>{sub_text}</span>'
                f'</h4>'
            )
        # Check for bullet point (• or -)
        elif line.startswith('• ') or line.startswith('- '):
            if not in_list:
                html_parts.append('<div class="space-y-2.5 my-3 pl-1 sm:pl-2">')
                in_list = True
            item_text = line[2:].strip()
            bold_match = re.match(r'^\*\*(.*?)\*\*(.*)', item_text)
            if bold_match:
                item_content = f'<strong class="text-stone-900 font-semibold">{bold_match.group(1)}</strong>{bold_match.group(2)}'
            else:
                item_content = re.sub(r'\*\*(.*?)\*\*', r'<strong class="text-stone-900 font-semibold">\1</strong>', item_text)
            html_parts.append(
                f'<div class="flex items-start space-x-2.5">'
                f'<span class="w-1.5 h-1.5 rounded-full bg-botanic-500 mt-2 shrink-0"></span>'
                f'<p class="text-stone-600 text-xs sm:text-sm leading-relaxed text-justify flex-1 m-0">{item_content}</p>'
                f'</div>'
            )
        else:
            if in_list:
                html_parts.append('</div>')
                in_list = False
            formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<strong class="text-stone-900 font-semibold">\1</strong>', line)
            html_parts.append(
                f'<p class="text-stone-600 text-xs sm:text-sm leading-relaxed text-justify mb-4">{formatted_line}</p>'
            )
            
    if in_list:
        html_parts.append('</div>')
        
    return '\n'.join(html_parts)


@app.template_filter('format_product_desc')
def format_product_desc_filter(content):
    if not content:
        return ""

    SECTION_HEADINGS = (
        'avantaje principale', 'beneficii principale',
        'compoziție și caracteristici tehnice', 'compozitie si caracteristici tehnice',
        'compoziție(npk)', 'compozitie(npk)',
        'mod de aplicare și instrucțiuni pas cu pas',
        'mod de aplicare și sfaturi de utilizare',
        'mod de aplicare', 'mod de utilizare și dozare',
        'sfaturi de utilizare', 'recomandări de utilizare',
    )
    INLINE_LABELS = (
        'Utilizare:', 'Dozare:', 'Mod de administrare:',
        'Compoziţie:', 'Compoziție:', 'Substanță activă:',
        'Efect nutritiv:', 'Ambalare disponibilă:'
    )

    lines = str(content).strip().split('\n')
    html_parts = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            html_parts.append('</ul>')
            in_list = False

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            close_list()
            continue

        safe_line = str(escape(stripped))
        lower_no_colon = stripped.rstrip(':').strip().lower()

        # 1. Standalone section headings (e.g., "Avantaje principale:", "Compoziție și caracteristici tehnice:")
        if lower_no_colon in SECTION_HEADINGS or (stripped.endswith(':') and len(stripped) <= 52 and not stripped.startswith(('•', '-', 'Pasul'))):
            close_list()
            heading_text = safe_line.rstrip(':')
            html_parts.append(
                f'<h4 class="text-xs sm:text-sm font-bold text-botanic-950 mt-4 mb-2 pt-2.5 border-t border-stone-200/70 flex items-center">'
                f'<span class="w-2 h-2 rounded-full bg-botanic-600 mr-2 shrink-0"></span>'
                f'<span>{heading_text}</span>'
                f'</h4>'
            )
            continue

        # 2. Inline labeled section (e.g., "Utilizare: ...", "Dozare: ...", "Compoziţie: ...")
        matched_inline = False
        for lbl in INLINE_LABELS:
            if stripped.startswith(lbl):
                close_list()
                rest = str(escape(stripped[len(lbl):].strip()))
                safe_lbl = str(escape(lbl))
                if lbl == 'Ambalare disponibilă:':
                    html_parts.append(
                        f'<div class="mt-3 pt-2.5 border-t border-stone-200/70 text-xs sm:text-sm text-stone-800">'
                        f'<strong class="font-bold text-botanic-900">{safe_lbl}</strong> <span class="font-semibold">{rest}</span>'
                        f'</div>'
                    )
                else:
                    html_parts.append(
                        f'<div class="my-2.5 p-3 rounded-xl bg-white border border-stone-200/80 text-xs sm:text-sm text-stone-700 leading-relaxed text-justify">'
                        f'<strong class="font-bold text-botanic-900">{safe_lbl}</strong> {rest}'
                        f'</div>'
                    )
                matched_inline = True
                break
        if matched_inline:
            continue

        # 3. Bullet points or step-by-step instructions
        if stripped.startswith(('•', '- ', 'Pasul ')):
            if not in_list:
                html_parts.append('<ul class="space-y-2 my-2.5 pl-1 list-none">')
                in_list = True
            item_raw = stripped.lstrip('•-\t ').strip()
            step_match = re.match(r'^(Pasul\s+\d+)\s*:\s*(.*)', item_raw, flags=re.IGNORECASE)
            if step_match:
                step_badge = str(escape(step_match.group(1)))
                step_body = str(escape(step_match.group(2)))
                html_parts.append(
                    f'<li class="flex items-start space-x-2 text-xs sm:text-sm text-stone-700 leading-relaxed text-justify">'
                    f'<span class="inline-flex items-center px-2 py-0.5 rounded-md bg-botanic-100 text-botanic-800 text-[11px] font-bold shrink-0 mt-0.5">{step_badge}</span>'
                    f'<span class="flex-1">{step_body}</span>'
                    f'</li>'
                )
            else:
                colon_idx = item_raw.find(':')
                if 0 < colon_idx <= 38:
                    prefix = str(escape(item_raw[:colon_idx + 1]))
                    body = str(escape(item_raw[colon_idx + 1:].strip()))
                    item_html = f'<strong class="font-semibold text-stone-900">{prefix}</strong> {body}'
                else:
                    item_html = str(escape(item_raw))
                html_parts.append(
                    f'<li class="flex items-start space-x-2 text-xs sm:text-sm text-stone-700 leading-relaxed text-justify">'
                    f'<span class="w-1.5 h-1.5 rounded-full bg-botanic-600 mt-2 shrink-0"></span>'
                    f'<span class="flex-1">{item_html}</span>'
                    f'</li>'
                )
            continue

        # 4. Standard paragraph
        close_list()
        html_parts.append(
            f'<p class="text-stone-700 text-xs sm:text-sm leading-relaxed text-justify mb-2.5">{safe_line}</p>'
        )

    close_list()
    return '\n'.join(html_parts)


@app.template_filter('format_advice')
def format_advice_filter(text):
    if not text:
        return []
    lines = [line.strip() for line in str(text).split('\n') if line.strip()]
    items = []
    for line in lines:
        cleaned = line.lstrip('•-* ').strip()
        if not cleaned:
            continue
        colon_pos = cleaned.find(':')
        if 0 < colon_pos <= 55:
            prefix = cleaned[:colon_pos+1]
            content = cleaned[colon_pos+1:].strip()
            items.append({'prefix': prefix, 'content': content})
        else:
            items.append({'prefix': '', 'content': cleaned})
    return items

def is_vitaflora_solutie_nutritiva(name):
    if not name:
        return False
    clean = name.lower()
    for src, dst in [('ț', 't'), ('ș', 's'), ('ă', 'a'), ('â', 'a'), ('î', 'i')]:
        clean = clean.replace(src, dst)
    return 'vitaflora solutie nutritiva' in clean

def shuffle_products_with_constraints(products, prev_was_v=False):
    """
    Randomizes products obeying two strict user rules:
    Rule 1: All products appear once before any product repeats (complete cycle).
    Rule 2: 'Vitaflora Solutie Nutritiva' products cannot appear consecutively,
            unless no other non-Vitaflora products remain in the cycle.
    """
    if not products:
        return []
    
    tagged = []
    for p in products:
        p_copy = dict(p)
        p_copy['is_vitaflora_solutie'] = is_vitaflora_solutie_nutritiva(p_copy.get('name', ''))
        tagged.append(p_copy)
        
    v_items = [p for p in tagged if p['is_vitaflora_solutie']]
    other_items = [p for p in tagged if not p['is_vitaflora_solutie']]
    
    v_shuffled = list(v_items)
    other_shuffled = list(other_items)
    random.shuffle(v_shuffled)
    random.shuffle(other_shuffled)
    
    total_slots = len(other_shuffled) + 1
    available_slots = list(range(total_slots))
    if prev_was_v and 0 in available_slots:
        available_slots.remove(0)
        
    num_v = len(v_shuffled)
    slot_counts = {s: 0 for s in range(total_slots)}
    
    if num_v <= len(available_slots):
        for s in random.sample(available_slots, num_v):
            slot_counts[s] = 1
    else:
        for s in available_slots:
            slot_counts[s] = 1
        rem = num_v - len(available_slots)
        pool = available_slots if available_slots else list(range(total_slots))
        for _ in range(rem):
            slot_counts[random.choice(pool)] += 1
            
    result = []
    v_idx = 0
    for slot in range(total_slots):
        for _ in range(slot_counts.get(slot, 0)):
            result.append(v_shuffled[v_idx])
            v_idx += 1
        if slot < len(other_shuffled):
            result.append(other_shuffled[slot])
            
    return result

# Product Menu Categories for "Produse Recomandate" Navigation & Catalog Page
PRODUCT_MENU_CATEGORIES = [
    {
        'slug': 'pamant-flori',
        'name': 'Amestec turbă / Pământ de flori',
        'short_name': 'Amestec turbă / Pământ de flori',
        'icon': 'layers',
        'description': 'Substraturi profesionale și pământ de flori universal sau specializat (Florasol, Humiflor, Plantasol, Nutrisol) cu pH controlat și structură optimă de aerisire.'
    },
    {
        'slug': 'solutii-nutritive',
        'name': 'Soluții Nutritive / Îngrășăminte lichide',
        'short_name': 'Soluții Nutritive / Îngrășăminte lichide',
        'icon': 'droplets',
        'description': 'Îngrășăminte lichide concentrate cu macro- și microelemente esențiale (Florasol, Nutrisol, Humiflor, Vitaflora) pentru plante de apartament, balcon, mușcate și grădină.'
    },
    {
        'slug': 'ingrijire-plante',
        'name': 'Soluții de îngrijire plante',
        'short_name': 'Soluții de îngrijire plante',
        'icon': 'shield-check',
        'description': 'Soluții ecologice și organice cu pulverizator (Florasol, Nutrisol) pentru curățarea frunzelor, fortificarea plantelor și protecție naturală.'
    },
    {
        'slug': 'batoane-fertilizante',
        'name': 'Batoane fertilizante / Îngrășăminte solide',
        'short_name': 'Batoane fertilizante / Îngrășăminte solide',
        'icon': 'sparkles',
        'description': 'Batoane nutritive cu eliberare treptată timp de 3 luni (Vitaflora) pentru plante decorative cu flori, plante cu frunze și orhidee.'
    }
]

# Context processor for global template variables
@app.context_processor
def inject_globals():
    articles = load_json('articles.json')
    products = load_json('products.json')
    about = load_json('about.json')
    plants = load_json('plants.json')
    total_catalog_plants = len(plants) if isinstance(plants, list) else 468
    plants_count_badge = f"{(total_catalog_plants // 10) * 10}+"
    
    # Calculate categories with dynamic counts
    category_counts = {}
    for a in articles:
        cat = (a.get('category') or 'Diverse').strip()
        if cat:
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Sort categories with primary ones first
    priority = [
        'Plante de interior', 'Plante de exterior', 'Intretinere', 
        'Amenajari', 'Fertilizant', 'Turba', 'Fructe', 
        'Doctorul gradinii', 'Gradina', 'Aranjamente florale', 
        'Seminte', 'Sisteme de irigatie', 'Accesorii'
    ]
    sorted_categories = []
    for cat in priority:
        if cat in category_counts:
            sorted_categories.append({'name': cat, 'count': category_counts[cat]})
    for cat, count in category_counts.items():
        if cat not in priority:
            sorted_categories.append({'name': cat, 'count': count})

    # Current month
    now = datetime.datetime.now()
    month_names = {
        1: 'Ianuarie', 2: 'Februarie', 3: 'Martie', 4: 'Aprilie',
        5: 'Mai', 6: 'Iunie', 7: 'Iulie', 8: 'August',
        9: 'Septembrie', 10: 'Octombrie', 11: 'Noiembrie', 12: 'Decembrie'
    }

    # Showcase images from import_produse/termek_bemutato
    showcase_items = []
    if os.path.exists(SHOWCASE_DIR):
        for f in sorted(os.listdir(SHOWCASE_DIR)):
            if allowed_file(f):
                clean_title = f.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
                showcase_items.append({
                    'image_url': f"/showcase_img/{f}",
                    'title': clean_title,
                    'desc': 'Demonstrație & utilizare practică în grădinărit.'
                })
    if not showcase_items:
        showcase_items = [
            {
                'image_url': 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&w=600&q=80',
                'title': 'Nutriție Avansată Vitaflora',
                'desc': 'Eficiență dovedită pentru plante decorative și citrice viguroase.'
            },
            {
                'image_url': 'https://images.unsplash.com/photo-1592417817098-8f3d6910985c?auto=format&fit=crop&w=600&q=80',
                'title': 'Substraturi Profesionale Florimo',
                'desc': 'Amestec de turbă cu pH controlat și calitate superioară certificată.'
            },
            {
                'image_url': 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?auto=format&fit=crop&w=600&q=80',
                'title': 'Protecție Fitocontrol Planto',
                'desc': 'Combaterea ecologică și eficientă a insectelor și paraziților.'
            }
        ]

    # Shuffle products and showcase items with constraint-based rotation
    # Rule 1: All products appear once before any repeats.
    # Rule 2: Vitaflora Solutie Nutritiva never appears consecutively unless no other products remain.
    sidebar_prods = shuffle_products_with_constraints(products)

    sc_items = list(showcase_items)
    random.shuffle(sc_items)

    social = load_json('social.json')
    if not social:
        social = {
            'enabled': True,
            'title': 'Urmărește-ne pe Social Media',
            'subtitle': 'Inspirație, noutăți și sfaturi practice pentru plante și grădinărit.',
            'facebook_enabled': True,
            'facebook_url': 'https://www.facebook.com/planteonline.ro',
            'instagram_enabled': True,
            'instagram_url': 'https://www.instagram.com/planteonline.ro',
            'tiktok_enabled': True,
            'tiktok_url': 'https://www.tiktok.com/@planteonline.ro',
            'pinterest_enabled': True,
            'pinterest_url': 'https://www.pinterest.com/planteonline'
        }

    # Count products per menu category for dropdown badges
    prod_cat_counts = {}
    for p in products:
        mc = p.get('menu_category', 'solutii-nutritive')
        prod_cat_counts[mc] = prod_cat_counts.get(mc, 0) + 1
    product_menu_cats = []
    for c in PRODUCT_MENU_CATEGORIES:
        c_copy = dict(c)
        c_copy['count'] = prod_cat_counts.get(c['slug'], 0)
        product_menu_cats.append(c_copy)

    return {
        'all_categories': sorted_categories,
        'product_menu_categories': product_menu_cats,
        'sidebar_products': sidebar_prods,  # All products in random order for carousel
        'all_products': products,
        'showcase_items': sc_items,
        'current_year': now.year,
        'current_month_num': now.month,
        'current_month_name': month_names.get(now.month, 'Octombrie'),
        'about_meta': about,
        'social_media': social,
        'total_catalog_plants': total_catalog_plants,
        'plants_count_badge': plants_count_badge
    }

# --- ROUTES ---

@app.route('/showcase_img/<path:filename>')
def serve_showcase_img(filename):
    safe_name = os.path.basename(filename)
    if not allowed_file(safe_name):
        abort(404)
    return send_from_directory(SHOWCASE_DIR, safe_name)

@app.route('/')
def home():
    articles = load_json('articles.json')
    calendar = load_json('calendar.json')
    plants = load_json('plants.json')
    products = load_json('products.json')

    # Selected month (defaults to current month, e.g. 10 for October)
    now = datetime.datetime.now()
    month_arg = request.args.get('luna', default=now.month, type=int)
    if month_arg < 1 or month_arg > 12:
        month_arg = now.month

    selected_calendar = calendar.get(str(month_arg), calendar.get("10", {}))
    
    # Find full calendar article if available
    calendar_article = None
    cal_art_id = selected_calendar.get('article_id', 184)
    for a in articles:
        if a['id'] == cal_art_id:
            calendar_article = a
            break

    # Featured articles
    featured_articles = articles[:6]

    # Category highlights (2 articles from interior, 2 from exterior, 2 from maintenance)
    cat_highlights = {
        'interior': [a for a in articles if 'interior' in a.get('category', '').lower()][:3],
        'exterior': [a for a in articles if 'exterior' in a.get('category', '').lower()][:3],
        'intretinere': [a for a in articles if 'intretinere' in a.get('category', '').lower() or 'fertilizant' in a.get('category', '').lower()][:3],
    }

    # Group plants by letter for interactive A-Z carousel on home page
    plants_by_letter = {}
    for p in plants:
        p_name = (p.get('name') or '').strip()
        if not p_name:
            continue
        first_char = p_name[0].upper()
        if first_char in ['Ă', 'Â']:
            first_char = 'A'
        elif first_char == 'Î':
            first_char = 'I'
        elif first_char == 'Ș':
            first_char = 'S'
        elif first_char == 'Ț':
            first_char = 'T'
        
        if first_char not in plants_by_letter:
            plants_by_letter[first_char] = []
        
        raw_desc = (p.get('description', '') or p.get('requirements', '') or 'Specie botanică decorativă cu cerințe specifice de îngrijire.').strip()
        short_desc = (raw_desc[:162] + '...') if len(raw_desc) > 165 else raw_desc
        plants_by_letter[first_char].append({
            'id': p.get('id'),
            'name': p.get('name', ''),
            'latin_name': p.get('latin_name', ''),
            'category': p.get('category', 'Plante'),
            'origin': p.get('origin', 'Global'),
            'image': p.get('images', [''])[0] if p.get('images') else '',
            'fallback_image': p.get('images', ['', ''])[1] if p.get('images') and len(p.get('images')) > 1 else '',
            'description': short_desc
        })

    import string
    all_letters = list(string.ascii_uppercase)
    active_letters = [l for l in all_letters if len(plants_by_letter.get(l, [])) > 0]
    letter_counts = {l: len(plants_by_letter.get(l, [])) for l in all_letters}
    initial_letter = 'A' if 'A' in active_letters else active_letters[0]
    initial_plants = plants_by_letter.get(initial_letter, [])[:6]

    return render_template(
        'index.html',
        selected_month=month_arg,
        calendar_info=selected_calendar,
        calendar_article=calendar_article,
        featured_articles=featured_articles,
        cat_highlights=cat_highlights,
        plants_by_letter=plants_by_letter,
        all_letters=all_letters,
        active_letters=active_letters,
        letter_counts=letter_counts,
        initial_plants=initial_plants,
        recommended_products=products
    )

@app.route('/articole')
def articles_list():
    articles = load_json('articles.json')
    category_filter = request.args.get('categorie', '').strip()
    search_query = request.args.get('q', '').strip().lower()
    
    filtered = articles
    if category_filter:
        filtered = [a for a in filtered if a.get('category', '').lower() == category_filter.lower()]
    
    if search_query:
        filtered = [
            a for a in filtered 
            if search_query in a.get('title', '').lower() or search_query in a.get('content', '').lower()
        ]
        if len(search_query) >= 2:
            record_search(search_query, target='articole', results_count=len(filtered))

    # Pagination
    page = request.args.get('pagina', default=1, type=int)
    per_page = 12
    total_articles = len(filtered)
    total_pages = (total_articles + per_page - 1) // per_page
    start = (page - 1) * per_page
    paginated = filtered[start:start + per_page]

    return render_template(
        'articles.html',
        articles=paginated,
        current_category=category_filter,
        search_query=search_query,
        page=page,
        total_pages=total_pages,
        total_articles=total_articles,
        total_all_articles=len(articles)
    )

@app.route('/articol/<int:article_id>')
def article_detail(article_id):
    articles = load_json('articles.json')
    products = load_json('products.json')
    
    target = None
    for a in articles:
        if a['id'] == article_id:
            target = a
            # Increment view count
            a['views'] = a.get('views', 0) + 1
            break
    
    if not target:
        flash('Articolul căutat nu a fost găsit.', 'warning')
        return redirect(url_for('articles_list'))
    
    # Save view count increment safely
    try:
        save_json('articles.json', articles)
    except OSError:
        pass

    # Related articles
    related = [a for a in articles if a['id'] != article_id and a.get('category') == target.get('category')][:4]
    if len(related) < 4:
        related = [a for a in articles if a['id'] != article_id][:4]

    # Intelligent botanical matching for related plants and recommended products (SEO internal linking)
    plants = load_json('plants.json')
    matched_plants, matched_products = recommend_for_article(target, plants, products)

    # Parse publication date to ISO 8601 for Schema.org BlogPosting
    raw_date = target.get('date', '')
    m_date = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', raw_date)
    if m_date:
        iso_date = f"{m_date.group(3)}-{int(m_date.group(2)):02d}-{int(m_date.group(1)):02d}"
    else:
        iso_date = "2026-10-20"

    return render_template(
        'article_detail.html',
        article=target,
        iso_date=iso_date,
        related_articles=related,
        related_plants=matched_plants[:4],
        recommended_products=matched_products[:3]
    )

@app.route('/plante-az')
def plants_az():
    plants = load_json('plants.json')
    selected_letter = request.args.get('l', '').upper().strip()
    search_query = request.args.get('q', '').strip().lower()
    subtype_filter = request.args.get('subtip', '').strip()

    # Calculate letter counts
    letters = {}
    for p in plants:
        l = p.get('letter', 'A').upper()
        letters[l] = letters.get(l, 0) + 1

    filtered = plants
    if selected_letter and selected_letter != 'ALL':
        filtered = [p for p in filtered if p.get('letter', '').upper() == selected_letter]
    elif not selected_letter and not search_query and not subtype_filter:
        # Default to letter 'A' if no search or filter
        selected_letter = 'A'
        filtered = [p for p in filtered if p.get('letter', '').upper() == 'A']

    if search_query:
        filtered = [
            p for p in plants
            if search_query in p.get('name', '').lower() 
            or search_query in p.get('latin_name', '').lower()
            or search_query in p.get('origin', '').lower()
        ]
        if len(search_query) >= 2:
            record_search(search_query, target='plante', results_count=len(filtered))

    if subtype_filter:
        filtered = [p for p in filtered if subtype_filter.lower() in p.get('category', '').lower()]

    # Pagination
    page = request.args.get('pagina', default=1, type=int)
    per_page = 24
    total_plants = len(filtered)
    total_pages = max(1, (total_plants + per_page - 1) // per_page)
    start = (page - 1) * per_page
    paginated = filtered[start:start + per_page]

    # Unique subtypes
    subtypes = sorted(list(set([p.get('category', '') for p in plants if p.get('category')])))

    return render_template(
        'plants_az.html',
        plants=paginated,
        letters=sorted(letters.items()),
        selected_letter=selected_letter,
        search_query=search_query,
        subtypes=subtypes,
        selected_subtype=subtype_filter,
        page=page,
        total_pages=total_pages,
        total_plants=total_plants,
        filtered_count=total_plants,
        total_catalog_plants=len(plants)
    )

@app.route('/planta/<int:plant_id>')
def plant_detail(plant_id):
    plants = load_json('plants.json')
    products = load_json('products.json')
    prod_map = {p['id']: p for p in products}
    
    plant = next((p for p in plants if p['id'] == plant_id), None)
    if not plant:
        flash('Planta solicitată nu a fost găsită în catalog.', 'warning')
        return redirect(url_for('plants_az'))
    
    # Run botanical recommendation engine
    recs = recommend_products_for_plant(plant, products)
    
    # Check if plant has specific saved recommended products
    saved_prods = []
    for rp in plant.get('recommended_products', []):
        pid = rp.get('id') if isinstance(rp, dict) else rp
        if pid in prod_map and prod_map[pid] not in saved_prods:
            saved_prods.append(prod_map[pid])

    if saved_prods:
        # Determine primary substrate and primary fertilizer from saved products or engine
        primary_substrate = next((p for p in saved_prods if 'turba' in p['name'].lower() or 'substrat' in p['name'].lower()), recs['primary_substrate'])
        if recs['primary_fertilizer'] is None:
            primary_fertilizer = None
        else:
            primary_fertilizer = next((p for p in saved_prods if 'solutie' in p['name'].lower() or 'batoane' in p['name'].lower() or 'ingrijire' in p['name'].lower()), recs['primary_fertilizer'])
        
        excluded_ids = {p['id'] for p in [primary_substrate, primary_fertilizer] if p}
        alternatives = [p for p in saved_prods if p['id'] not in excluded_ids]
        all_display_prods = [p for p in [primary_substrate, primary_fertilizer] if p] + alternatives
    else:
        primary_substrate = recs['primary_substrate']
        primary_fertilizer = recs['primary_fertilizer']
        alternatives = recs['alternatives']
        all_display_prods = [p for p in [primary_substrate, primary_fertilizer] if p] + alternatives

    # Recommended articles for this plant
    recommended_articles = plant.get('recommended_articles')
    if not recommended_articles:
        try:
            from knowledge_base import get_recommended_articles_for_plant
            recommended_articles = get_recommended_articles_for_plant(plant)
        except Exception:
            recommended_articles = []

    # Similar plants
    similar = [p for p in plants if p['id'] != plant_id and p.get('category') == plant.get('category')][:4]

    return render_template(
        'plant_detail.html',
        plant=plant,
        primary_substrate=primary_substrate,
        primary_fertilizer=primary_fertilizer,
        alternatives=alternatives,
        recommended_products=all_display_prods,
        recommended_articles=recommended_articles,
        similar_plants=similar
    )

@app.route('/calendar')
def calendar_view():
    calendar = load_json('calendar.json')
    articles = load_json('articles.json')
    
    now = datetime.datetime.now()
    selected_month = request.args.get('luna', default=now.month, type=int)
    if selected_month < 1 or selected_month > 12:
        selected_month = now.month

    selected_info = calendar.get(str(selected_month), calendar.get("10", {}))
    
    # Find corresponding full article
    art_id = selected_info.get('article_id', 184)
    cal_article = next((a for a in articles if a['id'] == art_id), None)

    return render_template(
        'calendar.html',
        calendar=calendar,
        selected_month=selected_month,
        current_info=selected_info,
        article=cal_article
    )

@app.route('/produse')
def products_view():
    products = load_json('products.json')
    selected_cat_slug = request.args.get('categorie', '').strip().lower()
    valid_slugs = [c['slug'] for c in PRODUCT_MENU_CATEGORIES]
    if selected_cat_slug not in valid_slugs and selected_cat_slug != 'toate':
        selected_cat_slug = 'pamant-flori' if not selected_cat_slug else 'toate'

    # Sort products by sort_order
    sorted_prods = sorted(products, key=lambda x: (x.get('sort_order', 9999), x.get('id', 0)))

    # Group by category -> ordered subgroups -> products
    categories_grouped = []
    for cat_meta in PRODUCT_MENU_CATEGORIES:
        if selected_cat_slug != 'toate' and cat_meta['slug'] != selected_cat_slug:
            continue
        cat_prods = [p for p in sorted_prods if p.get('menu_category', 'solutii-nutritive') == cat_meta['slug']]
        if not cat_prods:
            continue

        subgroups = []
        subgroup_map = {}
        for p in cat_prods:
            sg_title = p.get('subgroup_title') or cat_meta['name']
            if sg_title not in subgroup_map:
                sg_obj = {'title': sg_title, 'products': []}
                subgroup_map[sg_title] = sg_obj
                subgroups.append(sg_obj)
            # Parse packaging string into clean badges
            raw_pkg = p.get('packaging', '')
            pkg_badges = [x.strip() for x in re.split(r'[,;]', raw_pkg) if x.strip()]
            p_enriched = dict(p)
            p_enriched['packaging_badges'] = pkg_badges
            subgroup_map[sg_title]['products'].append(p_enriched)

        categories_grouped.append({
            'slug': cat_meta['slug'],
            'name': cat_meta['name'],
            'icon': cat_meta['icon'],
            'description': cat_meta['description'],
            'total_products': len(cat_prods),
            'subgroups': subgroups
        })

    active_category_meta = next((c for c in PRODUCT_MENU_CATEGORIES if c['slug'] == selected_cat_slug), None)

    return render_template(
        'products.html',
        categories_grouped=categories_grouped,
        selected_category=selected_cat_slug,
        active_category_meta=active_category_meta,
        all_product_categories=PRODUCT_MENU_CATEGORIES
    )

@app.route('/produs/<int:product_id>')
def product_detail(product_id):
    products = load_json('products.json')
    plants = load_json('plants.json')
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        flash('Produsul solicitat nu a fost găsit în catalog.', 'warning')
        return redirect(url_for('products_view'))

    # Matched plants that recommend this product
    matched_plants = []
    p_name_lower = product.get('name', '').lower()
    p_words = [w for w in p_name_lower.split() if len(w) >= 5 and w not in ('pentru', 'plante', 'solutie', 'substrat', 'amestec', 'universal')]
    for plant in plants:
        recs = plant.get('recommended_products', [])
        is_match = False
        for r in recs:
            rid = r.get('id') if isinstance(r, dict) else r
            rname = (r.get('name') or '').lower() if isinstance(r, dict) else ''
            if rid == product_id or (rname and p_name_lower in rname):
                is_match = True
                break
        if not is_match and p_words:
            req_text = ((plant.get('description') or '') + ' ' + (plant.get('requirements') or '')).lower()
            if any(w in req_text for w in p_words):
                is_match = True
        if is_match and plant not in matched_plants:
            matched_plants.append(plant)

    # Related products from same menu category or brand
    cat_slug = product.get('menu_category', 'pamant-flori')
    related = [p for p in products if p['id'] != product_id and (p.get('menu_category') == cat_slug or p.get('brand') == product.get('brand'))][:4]

    cat_meta = next((c for c in PRODUCT_MENU_CATEGORIES if c['slug'] == cat_slug), None)

    # Packaging badges
    packaging_badges = []
    if product.get('packaging'):
        packaging_badges = [b.strip() for b in re.split(r'[,;]', product['packaging']) if b.strip()]

    return render_template(
        'product_detail.html',
        product=product,
        cat_meta=cat_meta,
        matched_plants=matched_plants[:12],
        related_products=related,
        packaging_badges=packaging_badges
    )

@app.route('/despre-noi')
def about_view():
    about = load_json('about.json')
    products = load_json('products.json')
    return render_template('about.html', about=about, featured_products=products[:4])

# --- SEO & GEO ENDPOINTS (robots.txt, sitemap.xml, llms.txt) ---

@app.route('/robots.txt')
def robots_txt():
    base_url = request.url_root.rstrip('/')
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin",
        "Disallow: /api/upload",
        "",
        "User-agent: GPTBot",
        "Allow: /",
        "",
        "User-agent: OAI-SearchBot",
        "Allow: /",
        "",
        "User-agent: Google-Extended",
        "Allow: /",
        "",
        "User-agent: PerplexityBot",
        "Allow: /",
        "",
        "User-agent: ClaudeBot",
        "Allow: /",
        "",
        f"Sitemap: {base_url}/sitemap.xml",
    ]
    return Response("\n".join(lines), mimetype="text/plain; charset=utf-8")

@app.route('/sitemap.xml')
def sitemap_xml():
    base_url = request.url_root.rstrip('/')
    plants = load_json('plants.json')
    articles = load_json('articles.json')
    today = datetime.date.today().isoformat()

    urls = [
        (f"{base_url}/", "daily", "1.0"),
        (f"{base_url}/plante-az", "weekly", "0.9"),
        (f"{base_url}/articole", "weekly", "0.9"),
        (f"{base_url}/produse", "weekly", "0.9"),
        (f"{base_url}/produse?categorie=pamant-flori", "weekly", "0.9"),
        (f"{base_url}/produse?categorie=solutii-nutritive", "weekly", "0.9"),
        (f"{base_url}/produse?categorie=ingrijire-plante", "weekly", "0.8"),
        (f"{base_url}/produse?categorie=batoane-fertilizante", "weekly", "0.8"),
        (f"{base_url}/calendar", "monthly", "0.8"),
        (f"{base_url}/despre-noi", "monthly", "0.7"),
    ]
    for m in range(1, 13):
        urls.append((f"{base_url}/calendar?luna={m}", "monthly", "0.7"))
    for p in plants:
        pid = p.get('id')
        if pid is not None:
            urls.append((f"{base_url}/planta/{pid}", "monthly", "0.8"))
    for a in articles:
        aid = a.get('id')
        if aid is not None:
            urls.append((f"{base_url}/articol/{aid}", "monthly", "0.7"))
    products = load_json('products.json')
    for pr in products:
        pr_id = pr.get('id')
        if pr_id is not None:
            urls.append((f"{base_url}/produs/{pr_id}", "weekly", "0.8"))

    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for loc, changefreq, priority in urls:
        safe_loc = str(escape(loc))
        xml_parts.append(
            f"  <url><loc>{safe_loc}</loc><lastmod>{today}</lastmod>"
            f"<changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>"
        )
    xml_parts.append('</urlset>')
    return Response("\n".join(xml_parts), mimetype="application/xml; charset=utf-8")

@app.route('/llms.txt')
def llms_txt():
    base_url = request.url_root.rstrip('/')
    plants = load_json('plants.json')
    articles = load_json('articles.json')
    products = load_json('products.json')
    about = load_json('about.json')

    lines = [
        "# PlanteOnline.ro - Enciclopedie Botanică, Calendarul Grădinarului & Produse Horticultură",
        "",
        "> Portal educațional și ghid botanic fondat în 2001 de Societatea Mont Rose S.R.L. (România).",
        "> Producător oficial al mărcii Florasol și distribuitor al mărcilor Humiflor, Nutrisol, Plantasol, Vitaflora și Florimo.",
        "",
        "## Secțiuni Principale",
        f"- [Pagina Principală]({base_url}/): Indexul Plantelor A-Z, Calendarul Grădinarului, Articole Recomandate.",
        f"- [Enciclopedia Plantelor A-Z ({len(plants)} specii)]({base_url}/plante-az): Fișe botanice cu denumire științifică în latină, origine, lumină, temperatură, udare, substrat și fertilizare.",
        f"- [Calendarul Grădinarului (12 luni)]({base_url}/calendar): Lucrări lunare în grădină, balcon și apartament.",
        f"- [Articole & Ghiduri Horticultură ({len(articles)} articole)]({base_url}/articole): Sfaturi practice pentru plante de interior, exterior și protecția plantelor.",
        f"- [Produse Recomandate - Catalog Oficial ({len(products)} produse)]({base_url}/produse): Amestec turbă / Pământ de flori, Soluții Nutritive lichide, Soluții de îngrijire plante și Batoane fertilizante.",
        f"- [Despre Societatea Mont Rose S.R.L.]({base_url}/despre-noi): Istoric, mărci și date de contact.",
        "",
        f"## Gama de Produse Profesionale ({len(products)} produse - Substraturi, Pământ de Flori & Fertilizanți)",
    ]
    for prod in products:
        p_name = prod.get('name', '')
        p_brand = prod.get('brand', 'Florasol')
        p_desc = (prod.get('description') or '').replace('\n', ' ').strip()
        if len(p_desc) > 260:
            p_desc = p_desc[:257] + "..."
        p_detail = f"{base_url}/produs/{prod['id']}"
        p_ext = prod.get('external_url') or "https://www.montrose.ro"
        p_pkg = f" [Ambalaje: {prod.get('packaging')}]" if prod.get('packaging') else ""
        lines.append(f"- **{p_name}** ({p_brand}){p_pkg}: {p_desc} [Fișă Produs PlanteOnline]({p_detail}) | [Comandă Magazin Oficial]({p_ext})")

    return Response("\n".join(lines), mimetype="text/plain; charset=utf-8")

# --- ADMIN PANEL & AUTHENTICATION ---

def get_admin_credentials():
    config = load_json('admin_config.json')
    if not config or 'username' not in config:
        config = {
            'username': 'montrose',
            'password_hash': generate_password_hash('rosemont@1')
        }
        save_json('admin_config.json', config)
    return config

def check_admin_credentials(username, password):
    config = get_admin_credentials()
    if username != config.get('username'):
        return False
    pwd_hash = config.get('password_hash')
    if not pwd_hash:
        return False
    if check_password_hash(pwd_hash, password):
        return True
    if pwd_hash == password:
        config['password_hash'] = generate_password_hash(password)
        save_json('admin_config.json', config)
        return True
    return False

def update_admin_password(new_password):
    config = get_admin_credentials()
    config['password_hash'] = generate_password_hash(new_password)
    save_json('admin_config.json', config)
    return True

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Trebuie să vă autentificați pentru a accesa panoul de administrare.', 'warning')
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/process_import', methods=['POST'])
@admin_required
def admin_process_import():
    import process_import_folder
    report = process_import_folder.run_import()
    flash(report['message'], 'success')
    return redirect(url_for('admin_panel', tab='products'))

_LOGIN_ATTEMPTS = {}  # ip -> [timestamps]
MAX_LOGIN_ATTEMPTS = 8
LOGIN_WINDOW_SECONDS = 300  # 5 minutes

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_panel'))
    
    if request.method == 'POST':
        client_ip = request.remote_addr or '127.0.0.1'
        now_ts = time.time()
        attempts = [t for t in _LOGIN_ATTEMPTS.get(client_ip, []) if now_ts - t < LOGIN_WINDOW_SECONDS]
        _LOGIN_ATTEMPTS[client_ip] = attempts

        if len(attempts) >= MAX_LOGIN_ATTEMPTS:
            flash('Prea multe încercări eșuate de autentificare. Vă rugăm să așteptați 5 minute.', 'danger')
            return render_template('admin_login.html'), 429

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if check_admin_credentials(username, password):
            _LOGIN_ATTEMPTS.pop(client_ip, None)
            session.permanent = True
            session['admin_logged_in'] = True
            session['admin_user'] = username
            flash(f'Bun venit în panoul de administrare, {username}!', 'success')
            raw_next = request.args.get('next')
            next_url = raw_next if is_safe_redirect_url(raw_next) else url_for('admin_panel')
            return redirect(next_url)
        else:
            attempts.append(now_ts)
            _LOGIN_ATTEMPTS[client_ip] = attempts
            flash('Nume de utilizator sau parolă incorectă. Vă rugăm să încercați din nou.', 'danger')
            
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_user', None)
    flash('Ați fost deconectat cu succes din panoul de administrare.', 'success')
    return redirect(url_for('home'))

@app.route('/admin/change-password', methods=['POST'])
@admin_required
def admin_change_password():
    current_password = request.form.get('current_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    config = get_admin_credentials()
    if not check_admin_credentials(config['username'], current_password):
        flash('Parola actuală introdusă este incorectă!', 'danger')
        return redirect(url_for('admin_panel', tab='password'))
        
    if len(new_password) < 6:
        flash('Noua parolă trebuie să aibă cel puțin 6 caractere!', 'warning')
        return redirect(url_for('admin_panel', tab='password'))
        
    if new_password != confirm_password:
        flash('Noua parolă și confirmarea acesteia nu coincid!', 'danger')
        return redirect(url_for('admin_panel', tab='password'))
        
    update_admin_password(new_password)
    flash('Parola a fost schimbată cu succes! Noua parolă este activă.', 'success')
    return redirect(url_for('admin_panel', tab='password'))

@app.route('/admin')
@admin_required
def admin_panel():
    articles = load_json('articles.json')
    plants = load_json('plants.json')
    products = load_json('products.json')
    about = load_json('about.json')
    calendar = load_json('calendar.json')

    tab = request.args.get('tab', 'overview')
    edit_id = request.args.get('edit_id', type=int) or request.args.get('edit_plant', type=int)
    edit_item = None

    if edit_id:
        if tab == 'articles':
            edit_item = next((a for a in articles if a['id'] == edit_id), None)
        elif tab == 'products':
            edit_item = next((p for p in products if p['id'] == edit_id), None)
        elif tab == 'plants':
            edit_item = next((p for p in plants if p['id'] == edit_id), None)

    # Gather Showcase / Ghid Vizual images
    showcase_files = []
    if os.path.exists(SHOWCASE_DIR):
        for f in os.listdir(SHOWCASE_DIR):
            if allowed_file(f):
                full_path = os.path.join(SHOWCASE_DIR, f)
                try:
                    size_kb = round(os.path.getsize(full_path) / 1024, 1)
                    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{(size_kb/1024):.2f} MB"
                    mtime_ts = os.path.getmtime(full_path)
                    mtime_str = datetime.datetime.fromtimestamp(mtime_ts).strftime('%d.%m.%Y %H:%M')
                except OSError:
                    size_str = "N/A"
                    mtime_str = "N/A"
                    mtime_ts = 0
                clean_title = f.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
                showcase_files.append({
                    'filename': f,
                    'title': clean_title,
                    'image_url': f"/showcase_img/{f}",
                    'size_str': size_str,
                    'mtime_str': mtime_str,
                    'mtime_ts': mtime_ts
                })
        showcase_files.sort(key=lambda x: x['mtime_ts'], reverse=True)

    stats = {
        'total_articles': len(articles),
        'total_plants': len(plants),
        'total_products': len(products),
        'total_showcase': len(showcase_files),
        'total_views': sum(a.get('views', 0) for a in articles)
    }

    # Distinct categories and attributes for admin filter bars
    article_categories = sorted(list(set(a.get('category', 'Diverse') for a in articles if a.get('category'))))
    plant_categories = sorted(list(set(p.get('category', 'Diverse') for p in plants if p.get('category'))))
    plant_letters = sorted(list(set(p.get('letter', 'A') for p in plants if p.get('letter'))))
    product_brands = sorted(list(set(p.get('brand', 'Florasol') for p in products if p.get('brand'))))
    social = load_json('social.json')

    # Analytics data preparation for stats tab
    analytics_raw = get_analytics()
    traffic_data = analytics_raw.get('traffic', {})
    total_v = traffic_data.get('total_visits', 0)
    sources_dict = traffic_data.get('sources', {})

    social_sources = ['facebook', 'instagram', 'tiktok', 'pinterest']
    social_total = sum(sources_dict.get(s, 0) for s in social_sources)
    social_pct = round((social_total / total_v * 100), 1) if total_v > 0 else 0
    google_total = sources_dict.get('google', 0)
    google_pct = round((google_total / total_v * 100), 1) if total_v > 0 else 0

    platform_configs = [
        {'key': 'google', 'name': 'Google Căutare', 'color': 'indigo', 'icon': 'search', 'desc': 'Trafic organic din motorul Google'},
        {'key': 'facebook', 'name': 'Facebook', 'color': 'blue', 'icon': 'facebook', 'desc': 'Postări, share-uri și grupuri Facebook'},
        {'key': 'instagram', 'name': 'Instagram', 'color': 'pink', 'icon': 'instagram', 'desc': 'Link în bio, stories și postări Instagram'},
        {'key': 'tiktok', 'name': 'TikTok', 'color': 'stone', 'icon': 'video', 'desc': 'Videoclipuri și profil oficial TikTok'},
        {'key': 'pinterest', 'name': 'Pinterest', 'color': 'red', 'icon': 'pin', 'desc': 'Pin-uri salvate și panouri de inspirație'},
        {'key': 'direct', 'name': 'Direct / Altele', 'color': 'emerald', 'icon': 'globe', 'desc': 'Accesare directă, marcaje și alte surse'}
    ]

    sources_stats = []
    for p in platform_configs:
        cnt = sources_dict.get(p['key'], 0)
        pct = round((cnt / total_v * 100), 1) if total_v > 0 else 0
        sources_stats.append({
            'key': p['key'],
            'name': p['name'],
            'count': cnt,
            'percent': pct,
            'color': p['color'],
            'icon': p['icon'],
            'desc': p['desc']
        })

    # Prepare Top Searches
    searches_raw = analytics_raw.get('searches', {})
    total_searches = searches_raw.get('total_searches', 0)
    queries_dict = searches_raw.get('queries', {})
    sorted_queries = []
    for q_term, q_meta in queries_dict.items():
        sorted_queries.append({
            'query': q_term,
            'count': q_meta.get('count', 0),
            'last_searched': q_meta.get('last_searched', ''),
            'results_found': q_meta.get('results_found', 0),
            'target': q_meta.get('target', 'plante')
        })
    sorted_queries.sort(key=lambda x: x['count'], reverse=True)

    # Prepare Top Products Interacted
    products_raw = analytics_raw.get('products', {})
    total_prod_views = products_raw.get('total_views', 0)
    total_prod_clicks = products_raw.get('total_clicks', 0)
    prod_items_dict = products_raw.get('items', {})
    sorted_products = []
    for pid_k, p_meta in prod_items_dict.items():
        v = p_meta.get('views', 0)
        c = p_meta.get('clicks', 0)
        total_inter = v + c
        ctr = round((c / v * 100), 1) if v > 0 else 0
        sorted_products.append({
            'id': pid_k,
            'name': p_meta.get('name', f"Produs #{pid_k}"),
            'brand': p_meta.get('brand', 'Florasol'),
            'views': v,
            'clicks': c,
            'total_interactions': total_inter,
            'ctr': ctr,
            'last_interacted': p_meta.get('last_interacted', ''),
            'image_url': p_meta.get('image_url', '')
        })
    sorted_products.sort(key=lambda x: (x['views'], x['clicks']), reverse=True)

    analytics_prepared = {
        'total_visits': total_v,
        'google_total': google_total,
        'google_pct': google_pct,
        'social_total': social_total,
        'social_pct': social_pct,
        'sources_stats': sources_stats,
        'recent_visits': traffic_data.get('recent_visits', []),
        'total_searches': total_searches,
        'top_queries': sorted_queries,
        'recent_searches': searches_raw.get('recent', []),
        'total_prod_views': total_prod_views,
        'total_prod_clicks': total_prod_clicks,
        'total_prod_interactions': total_prod_views + total_prod_clicks,
        'top_products': sorted_products
    }

    return render_template(
        'admin.html',
        active_tab=tab,
        stats=stats,
        articles=articles,
        article_categories=article_categories,
        plants=plants,
        plant_categories=plant_categories,
        plant_letters=plant_letters,
        products=products,
        product_brands=product_brands,
        showcase_list=showcase_files,
        about=about,
        calendar=calendar,
        social=social,
        analytics=analytics_prepared,
        edit_item=edit_item
    )

# --- ADMIN API / ACTION ROUTES ---

@app.route('/admin/article/save', methods=['POST'])
@admin_required
def admin_save_article():
    articles = load_json('articles.json')
    article_id = request.form.get('id', type=int)
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'Plante de interior').strip()
    summary = request.form.get('summary', '').strip()
    content = request.form.get('content', '').strip()
    image_url = sanitize_external_url(request.form.get('image_url', '').strip())

    # Check for image file upload
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename and allowed_file(file.filename, file):
            filename = secure_filename(file.filename)
            unique_name = f"art_{int(datetime.datetime.now().timestamp())}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
            image_url = f"/static/uploads/{unique_name}"

    if not title or not content:
        flash('Titlul și conținutul articolului sunt obligatorii!', 'danger')
        return redirect(url_for('admin_panel', tab='articles'))

    now_str = datetime.datetime.now().strftime("%d.%m.%Y")

    if article_id:
        # Edit existing
        for a in articles:
            if a['id'] == article_id:
                a['title'] = title
                a['category'] = category
                a['summary'] = summary if summary else content[:200] + '...'
                a['content'] = content
                if image_url:
                    a['image_url'] = image_url
                flash('Articolul a fost actualizat cu succes!', 'success')
                break
    else:
        # Create new
        new_id = max([a['id'] for a in articles], default=0) + 1
        new_article = {
            'id': new_id,
            'title': title,
            'category': category,
            'date': now_str,
            'views': 1,
            'summary': summary if summary else content[:200] + '...',
            'content': content,
            'image_url': image_url
        }
        articles.insert(0, new_article)
        flash('Articolul nou a fost publicat cu succes!', 'success')

    save_json('articles.json', articles)
    try:
        from knowledge_base import on_article_saved
        saved_art = next((a for a in articles if a['id'] == (article_id if article_id else new_id)), None)
        if saved_art:
            on_article_saved(saved_art)
    except Exception as e:
        print(f"Error syncing knowledge base for article: {e}")

    return redirect(url_for('admin_panel', tab='articles'))

@app.route('/admin/article/delete/<int:article_id>', methods=['POST'])
@admin_required
def admin_delete_article(article_id):
    articles = load_json('articles.json')
    articles = [a for a in articles if a['id'] != article_id]
    save_json('articles.json', articles)
    try:
        from knowledge_base import sync_database_from_json
        sync_database_from_json()
    except Exception as e:
        print(f"Error syncing database after article deletion: {e}")
    flash(f'Articolul #{article_id} a fost șters.', 'info')
    return redirect(url_for('admin_panel', tab='articles'))

@app.route('/admin/product/save', methods=['POST'])
@admin_required
def admin_save_product():
    products = load_json('products.json')
    prod_id = request.form.get('id', type=int)
    name = request.form.get('name', '').strip()
    brand = request.form.get('brand', 'Florasol').strip()
    code = request.form.get('code', '').strip()
    packaging = request.form.get('packaging', '').strip()
    menu_category = request.form.get('menu_category', '').strip()
    subgroup_title = request.form.get('subgroup_title', '').strip()
    description = request.form.get('description', '').strip()
    external_url = request.form.get('external_url', '').strip()
    image_url = request.form.get('image_url', '').strip()

    if external_url and not external_url.startswith(('http://', 'https://', '#', '/')):
        external_url = 'https://' + external_url
    external_url = sanitize_external_url(external_url)
    image_url = sanitize_external_url(image_url)

    # Image upload
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename and allowed_file(file.filename, file):
            filename = secure_filename(file.filename)
            unique_name = f"prod_{int(datetime.datetime.now().timestamp())}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
            image_url = f"/static/uploads/{unique_name}"

    if not name:
        flash('Numele produsului este obligatoriu!', 'danger')
        return redirect(url_for('admin_panel', tab='products'))

    if prod_id:
        for p in products:
            if p['id'] == prod_id:
                p['name'] = name
                p['brand'] = brand
                p['code'] = code
                p.pop('price', None)
                if packaging:
                    p['packaging'] = packaging
                if menu_category:
                    p['menu_category'] = menu_category
                if subgroup_title:
                    p['subgroup_title'] = subgroup_title
                p['description'] = description
                p['external_url'] = external_url if external_url else p.get('external_url', '')
                if image_url:
                    p['image_url'] = image_url
                    if 'images' in p:
                        p['images'].insert(0, image_url)
                flash('Produsul a fost actualizat cu succes (atât în fereastra pop-up, cât și în meniul Produse Recomandate)!', 'success')
                break
    else:
        new_id = max([p['id'] for p in products], default=0) + 1
        new_product = {
            'id': new_id,
            'name': name,
            'brand': brand,
            'code': code if code else f"MR-{new_id:03d}",
            'packaging': packaging if packaging else '1 L',
            'menu_category': menu_category if menu_category else 'solutii-nutritive',
            'subgroup_title': subgroup_title if subgroup_title else '1. Soluții Nutritive Universale',
            'sort_order': 950 + new_id,
            'description': description,
            'external_url': external_url if external_url else "https://www.montrose.ro",
            'image_url': image_url,
            'images': [image_url] if image_url else []
        }
        products.append(new_product)
        flash('Produsul recomandat a fost adăugat cu succes!', 'success')

    save_json('products.json', products)
    return redirect(url_for('admin_panel', tab='products'))

@app.route('/admin/product/delete/<int:prod_id>', methods=['POST'])
@admin_required
def admin_delete_product(prod_id):
    products = load_json('products.json')
    products = [p for p in products if p['id'] != prod_id]
    save_json('products.json', products)
    flash(f'Produsul #{prod_id} a fost șters.', 'info')
    return redirect(url_for('admin_panel', tab='products'))

@app.route('/admin/showcase/upload', methods=['POST'])
@admin_required
def admin_upload_showcase():
    if 'showcase_files' not in request.files:
        flash('Nu a fost selectat niciun fișier!', 'danger')
        return redirect(url_for('admin_panel', tab='showcase'))
    
    files = request.files.getlist('showcase_files')
    if not files or all(f.filename == '' for f in files):
        flash('Vă rugăm să alegeți cel puțin o imagine de pe calculator!', 'warning')
        return redirect(url_for('admin_panel', tab='showcase'))
    
    uploaded_count = 0
    for file in files:
        if file and file.filename and allowed_file(file.filename, file):
            orig_name = secure_filename(file.filename)
            if not orig_name:
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
                orig_name = f"ghid_vizual_{int(datetime.datetime.now().timestamp())}.{ext}"
            
            target_path = os.path.join(SHOWCASE_DIR, orig_name)
            if os.path.exists(target_path):
                base, ext = os.path.splitext(orig_name)
                orig_name = f"{base}_{int(datetime.datetime.now().timestamp())}_{random.randint(100, 999)}{ext}"
                target_path = os.path.join(SHOWCASE_DIR, orig_name)
                
            file.save(target_path)
            uploaded_count += 1
            
    if uploaded_count > 0:
        flash(f'Succes! {uploaded_count} imagine(i) au fost adăugate în secțiunea Ghid Vizual.', 'success')
    else:
        flash('Nicio imagine validă nu a putut fi încărcată. Formate acceptate: JPG, PNG, WEBP, GIF.', 'danger')
        
    return redirect(url_for('admin_panel', tab='showcase'))

@app.route('/admin/showcase/delete/<path:filename>', methods=['POST'])
@admin_required
def admin_delete_showcase(filename):
    safe_filename = os.path.basename(filename)
    target_path = os.path.join(SHOWCASE_DIR, safe_filename)
    
    if os.path.exists(target_path) and os.path.isfile(target_path):
        try:
            os.remove(target_path)
            flash(f'Imaginea „{safe_filename}” a fost ștearsă din Ghidul Vizual.', 'success')
        except Exception as e:
            flash(f'Eroare la ștergerea imaginii: {str(e)}', 'danger')
    else:
        flash('Imaginea nu a fost găsită.', 'danger')
        
    return redirect(url_for('admin_panel', tab='showcase'))

@app.route('/api/plant/suggest-products', methods=['GET', 'POST'])
def api_suggest_plant_products():
    products = load_json('products.json')
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form.to_dict()
    else:
        data = request.args.to_dict()
        
    recs = recommend_products_for_plant(data, products)
    return jsonify({
        'success': True,
        'primary_substrate': recs['primary_substrate'],
        'primary_fertilizer': recs['primary_fertilizer'],
        'alternatives': recs['alternatives'],
        'recommended_product_ids': recs['recommended_product_ids'],
        'recommended_products_list': recs['recommended_products_list']
    })

@app.route('/api/plant/autofill', methods=['GET', 'POST'])
def api_plant_autofill():
    from plant_autofill import autofill_plant_info
    plants = load_json('plants.json')
    products = load_json('products.json')

    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form.to_dict()
    else:
        data = request.args.to_dict()

    name_input = (data.get('name') or '').strip()
    latin_input = (data.get('latin_name') or '').strip()
    raw_id = data.get('id')
    exclude_id = int(raw_id) if (raw_id is not None and str(raw_id).isdigit()) else None

    res = autofill_plant_info(
        name_input=name_input,
        latin_input=latin_input,
        catalog_plants=plants,
        catalog_products=products,
        exclude_id=exclude_id
    )
    if not res.get('success'):
        return jsonify(res), 400

    p_data = res['plant']
    # Also run product recommendation engine so Sol, Fertilizare, and checkboxes are 100% aligned
    recs = recommend_products_for_plant(p_data, products)
    sub_name = recs['primary_substrate']['name'] if recs.get('primary_substrate') else ''
    fert_name = recs['primary_fertilizer']['name'] if recs.get('primary_fertilizer') else ''

    if sub_name and sub_name.lower() not in (p_data.get('sol') or '').lower():
        p_data['sol'] = f"{p_data['sol'].rstrip('.')} – Recomandat: {sub_name}."
    if fert_name and fert_name.lower() not in (p_data.get('fertilizare') or '').lower():
        p_data['fertilizare'] = f"{p_data['fertilizare'].rstrip('.')} – Recomandat: {fert_name}."

    return jsonify({
        'success': True,
        'source': res.get('source', 'Wikipedia + iNaturalist'),
        'already_exists': res.get('already_exists', False),
        'existing_plant': res.get('existing_plant'),
        'plant': p_data,
        'recommended_product_ids': recs['recommended_product_ids'],
        'primary_substrate': recs['primary_substrate'],
        'primary_fertilizer': recs['primary_fertilizer']
    })

def normalize_plant_image_url(raw_url):
    if not raw_url:
        return ''
    import urllib.parse
    url = raw_url.strip()

    # 1. Convert Wikipedia/Wikimedia MediaViewer links: .../wiki/...#/media/Fișier:Example.jpg
    if '#/media/' in url:
        try:
            after_media = url.split('#/media/', 1)[1].split('?')[0].split('&')[0]
            decoded = urllib.parse.unquote(after_media)
            file_name = decoded.split(':', 1)[1] if ':' in decoded else decoded
            file_name = file_name.strip().replace(' ', '_')
            if file_name:
                return f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(file_name)}"
        except Exception:
            pass

    # 2. Convert Wikipedia/Wikimedia File page links: .../wiki/Fișier:Example.jpg or .../wiki/File:Example.jpg
    if ('wikipedia.org/wiki/' in url or 'wikimedia.org/wiki/' in url) and 'Special:FilePath' not in url:
        try:
            wiki_part = url.split('/wiki/', 1)[1].split('?')[0].split('#')[0]
            decoded = urllib.parse.unquote(wiki_part)
            m = re.match(r'^(?:Fișier|Fisier|File|Imagine|Image|Fájl|Datei|Fichier|Archivo|Plik):(.+)$', decoded, re.IGNORECASE)
            if m and m.group(1):
                file_name = m.group(1).strip().replace(' ', '_')
                return f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(file_name)}"
        except Exception:
            pass

    return sanitize_external_url(url)

@app.route('/admin/plant/save', methods=['POST'])
@admin_required
def admin_save_plant():
    plants = load_json('plants.json')
    products = load_json('products.json')
    prod_map = {p['id']: p for p in products}

    plant_id = request.form.get('id', type=int)
    name = request.form.get('name', '').strip()
    latin_name = request.form.get('latin_name', '').strip()
    category = request.form.get('category', 'Plante de apartament').strip()
    origin = request.form.get('origin', '').strip()
    flowers = request.form.get('flowers', '').strip()
    leaves = request.form.get('leaves', '').strip()
    shape = request.form.get('shape', '').strip()
    lumina = request.form.get('lumina', '').strip()
    temperatura = request.form.get('temperatura', '').strip()
    udare = request.form.get('udare', '').strip()
    sol = request.form.get('sol', '').strip()
    fertilizare = request.form.get('fertilizare', '').strip()
    description = request.form.get('description', '').strip()
    slot_urls = [
        normalize_plant_image_url(request.form.get('image_url', '').strip()),
        normalize_plant_image_url(request.form.get('image_url_2', '').strip()),
        normalize_plant_image_url(request.form.get('image_url_3', '').strip())
    ]
    plants_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'plants')
    os.makedirs(plants_upload_dir, exist_ok=True)
    for idx in range(3):
        f_key = f"image_file_{idx + 1}"
        if f_key in request.files:
            f_obj = request.files[f_key]
            if f_obj and f_obj.filename and allowed_file(f_obj.filename, f_obj):
                safe_name = secure_filename(f_obj.filename)
                unique_name = f"plant_{int(datetime.datetime.now().timestamp())}_{idx + 1}_{safe_name}"
                f_obj.save(os.path.join(plants_upload_dir, unique_name))
                slot_urls[idx] = f"/static/uploads/plants/{unique_name}"

    collected_images = [u for u in slot_urls if u]

    if not name:
        flash('Denumirea plantei este obligatorie!', 'danger')
        return redirect(url_for('admin_panel', tab='plants'))

    # Prevent duplicate plants in the database when adding or renaming
    from plant_autofill import find_existing_plant_in_catalog
    dup_plant = find_existing_plant_in_catalog(
        name_input=name,
        latin_input=latin_name,
        catalog_plants=plants,
        exclude_id=plant_id
    )
    if dup_plant:
        flash(f'Atenție! Planta / floarea „{dup_plant["name"]}” (#{dup_plant["id"]}) este deja adăugată în baza de date! Am deschis fișa existentă pentru editare.', 'warning')
        return redirect(url_for('admin_panel', tab='plants', edit_plant=dup_plant['id']))

    letter = name[0].upper()
    care_guide = {
        'lumina': lumina or 'Lumină adecvată speciei.',
        'udare': udare or 'Udare moderată menținând solul reavăn.',
        'sol': sol or 'Sol bine drenat și fertil. Se recomandă Amestec turbă Florasol.',
        'temperatura': temperatura or 'Temperatură adaptată speciei.',
        'fertilizare': fertilizare or 'Fertilizare periodică cu Soluții Nutritive Florasol.'
    }
    requirements = lumina if lumina else 'Lumină și îngrijire conform fișei.'

    # Handle recommended products from form or run auto recommendation engine
    rec_ids = request.form.getlist('recommended_product_ids', type=int)
    if rec_ids:
        saved_recs = [{'id': pid, 'name': prod_map[pid]['name']} for pid in rec_ids if pid in prod_map]
    else:
        temp_plant = {
            'name': name, 'latin_name': latin_name, 'category': category,
            'origin': origin, 'flowers': flowers, 'leaves': leaves,
            'shape': shape, 'description': description, 'care_guide': care_guide
        }
        engine_recs = recommend_products_for_plant(temp_plant, products)
        saved_recs = [{'id': pid, 'name': prod_map[pid]['name']} for pid in engine_recs['recommended_product_ids'] if pid in prod_map]

    if plant_id:
        for p in plants:
            if p['id'] == plant_id:
                p['name'] = name
                p['latin_name'] = latin_name
                p['letter'] = letter
                p['category'] = category
                p['origin'] = origin
                p['flowers'] = flowers
                p['leaves'] = leaves
                p['shape'] = shape
                p['description'] = description
                p['care_guide'] = care_guide
                p['requirements'] = requirements
                p['recommended_products'] = saved_recs
                p['images'] = collected_images[:3]
                flash('Planta a fost actualizată conform noului șablon!', 'success')
                break
    else:
        new_id = max([p['id'] for p in plants], default=0) + 1
        new_plant = {
            'id': new_id,
            'slug': name.lower().replace(' ', '-'),
            'name': name,
            'latin_name': latin_name,
            'letter': letter,
            'category': category,
            'origin': origin,
            'flowers': flowers,
            'leaves': leaves,
            'shape': shape,
            'description': description,
            'care_guide': care_guide,
            'requirements': requirements,
            'images': collected_images[:3],
            'recommended_products': saved_recs
        }
        plants.append(new_plant)
        plants.sort(key=lambda x: (x.get('letter', 'A'), x.get('name', '')))
        flash('Planta nouă a fost adăugată conform noului șablon!', 'success')

    save_json('plants.json', plants)
    try:
        from knowledge_base import on_plant_saved
        target_pid = plant_id if plant_id else new_id
        saved_plant = next((p for p in plants if p['id'] == target_pid), None)
        if saved_plant:
            on_plant_saved(saved_plant)
    except Exception as e:
        print(f"Error syncing knowledge base for plant: {e}")

    return redirect(url_for('admin_panel', tab='plants'))

@app.route('/admin/plant/delete/<int:plant_id>', methods=['POST'])
@admin_required
def admin_delete_plant(plant_id):
    plants = load_json('plants.json')
    plants = [p for p in plants if p['id'] != plant_id]
    save_json('plants.json', plants)
    try:
        from knowledge_base import sync_database_from_json
        sync_database_from_json()
    except Exception as e:
        print(f"Error syncing knowledge base after plant delete: {e}")
    flash(f'Specia #{plant_id} a fost ștearsă din catalog.', 'info')
    return redirect(url_for('admin_panel', tab='plants'))

@app.route('/admin/about/save', methods=['POST'])
@admin_required
def admin_save_about():
    about = load_json('about.json')
    about['title'] = request.form.get('title', about.get('title', '')).strip()
    about['subtitle'] = request.form.get('subtitle', about.get('subtitle', '')).strip()
    about['company_name'] = request.form.get('company_name', about.get('company_name', '')).strip()
    about['founded_year'] = request.form.get('founded_year', about.get('founded_year', 2001))
    about['quality_standards'] = request.form.get('quality_standards', about.get('quality_standards', '')).strip()
    about['description'] = request.form.get('description', about.get('description', '')).strip()
    about['mission'] = request.form.get('mission', about.get('mission', '')).strip()
    about['contact_email'] = request.form.get('contact_email', about.get('contact_email', '')).strip()
    about['contact_phone'] = request.form.get('contact_phone', about.get('contact_phone', '')).strip()
    about['address'] = request.form.get('address', about.get('address', '')).strip()

    save_json('about.json', about)
    flash('Secțiunea Despre Noi a fost actualizată cu succes!', 'success')
    return redirect(url_for('admin_panel', tab='about'))

@app.route('/admin/calendar/save', methods=['POST'])
@admin_required
def admin_save_calendar():
    calendar = load_json('calendar.json')
    month = request.form.get('month', type=int)
    title = request.form.get('title', '').strip()
    subtitle = request.form.get('subtitle', '').strip()
    exterior = request.form.get('exterior_advice', '').strip()
    interior = request.form.get('interior_advice', '').strip()
    content = request.form.get('full_content', '').strip()

    if str(month) in calendar:
        calendar[str(month)]['title'] = title
        if ': ' in title:
            parts = title.split(': ', 1)
            calendar[str(month)]['main_title'] = parts[0].strip()
            calendar[str(month)]['topic'] = parts[1].strip()
        elif ':' in title:
            parts = title.split(':', 1)
            calendar[str(month)]['main_title'] = parts[0].strip()
            calendar[str(month)]['topic'] = parts[1].strip()
        else:
            calendar[str(month)]['main_title'] = f"Calendarul Grădinarului - Luna {calendar[str(month)]['month_name']}"
            calendar[str(month)]['topic'] = title
        calendar[str(month)]['subtitle'] = subtitle
        calendar[str(month)]['exterior_advice'] = exterior
        calendar[str(month)]['interior_advice'] = interior
        calendar[str(month)]['full_content'] = content
        save_json('calendar.json', calendar)
        flash(f'Sfaturile pentru luna {calendar[str(month)]["month_name"]} au fost actualizate!', 'success')
    else:
        flash('Lună invalidă.', 'danger')

    return redirect(url_for('admin_panel', tab='calendar'))

@app.route('/admin/social/save', methods=['POST'])
@admin_required
def admin_save_social():
    social = load_json('social.json') or {}
    social['enabled'] = ('enabled' in request.form)
    social['title'] = request.form.get('title', 'Urmărește-ne pe Social Media').strip()
    social['subtitle'] = request.form.get('subtitle', '').strip()
    social['facebook_enabled'] = ('facebook_enabled' in request.form)
    social['facebook_url'] = sanitize_external_url(request.form.get('facebook_url', '').strip())
    social['instagram_enabled'] = ('instagram_enabled' in request.form)
    social['instagram_url'] = sanitize_external_url(request.form.get('instagram_url', '').strip())
    social['tiktok_enabled'] = ('tiktok_enabled' in request.form)
    social['tiktok_url'] = sanitize_external_url(request.form.get('tiktok_url', '').strip())
    social['pinterest_enabled'] = ('pinterest_enabled' in request.form)
    social['pinterest_url'] = sanitize_external_url(request.form.get('pinterest_url', '').strip())
    save_json('social.json', social)
    flash('Setările pentru Social Media au fost actualizate cu succes!', 'success')
    return redirect(url_for('admin_panel', tab='social'))

@app.route('/admin/stats/reset', methods=['POST'])
@admin_required
def admin_reset_stats():
    section = request.form.get('section', 'all')
    data = get_analytics()
    if section in ['traffic', 'all']:
        data['traffic'] = {'total_visits': 0, 'sources': {'google': 0, 'facebook': 0, 'instagram': 0, 'tiktok': 0, 'pinterest': 0, 'direct': 0}, 'recent_visits': []}
    if section in ['searches', 'all']:
        data['searches'] = {'total_searches': 0, 'queries': {}, 'recent': []}
    if section in ['products', 'all']:
        data['products'] = {'total_views': 0, 'total_clicks': 0, 'items': {}}
    save_analytics(data)
    flash('Datele statistice au fost resetate cu succes!', 'success')
    return redirect(url_for('admin_panel', tab='stats'))

@app.route('/api/upload', methods=['POST'])
@admin_required
def api_upload_media():
    if 'file' not in request.files:
        return jsonify({'error': 'Niciun fișier selectat'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Niciun fișier selectat'}), 400
    if file and allowed_file(file.filename, file):
        filename = secure_filename(file.filename)
        unique_name = f"upload_{int(datetime.datetime.now().timestamp())}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
        return jsonify({
            'success': True,
            'url': f"/static/uploads/{unique_name}",
            'filename': unique_name
        })
    return jsonify({'error': 'Format de fișier nepermis'}), 400

@app.route('/api/product/<int:prod_id>')
def api_get_product(prod_id):
    products = load_json('products.json')
    p = next((item for item in products if item['id'] == prod_id), None)
    if p:
        record_product_interaction(prod_id, 'view')
        return jsonify(p)
    return jsonify({'error': 'Produsul nu a fost găsit'}), 404

@app.route('/api/track/product/<int:prod_id>', methods=['POST'])
def api_track_product_click(prod_id):
    record_product_interaction(prod_id, 'click')
    return jsonify({'success': True})

@app.route('/api/plant/<int:plant_id>')
def api_get_plant(plant_id):
    plants = load_json('plants.json')
    p = next((item for item in plants if item['id'] == plant_id), None)
    if p:
        return jsonify(p)
    return jsonify({'error': 'Planta nu a fost găsită'}), 404

if __name__ == '__main__':
    print("Pornire server PlanteOnline Modern pe http://127.0.0.1:5000")
    is_debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='127.0.0.1', port=5000, debug=is_debug)
