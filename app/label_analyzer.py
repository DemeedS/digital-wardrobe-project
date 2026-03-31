# ============================================================
# LABEL ANALYZER - Phase 2 AI label reading
#
# Flow:
#   1. Claude Vision reads the tag photo → extracts raw fields
#   2. DuckDuckGo search enriches with online product data
#   3. FTC RN database lookup (fallback)
#
# Fallback chain (determines confidence score):
#   brand + item_number  → online search   → confidence: high
#   brand + material     → online search   → confidence: medium
#   rn_number only       → FTC lookup      → confidence: medium
#   nothing matched      → label data only → confidence: low
# ============================================================

import re
import io
import json
import base64
import requests
import anthropic
from PIL import Image
from duckduckgo_search import DDGS

CLAUDE_MODEL = 'claude-sonnet-4-6'

PRESET_COLORS = [
    'Black', 'White', 'Blue', 'Red', 'Green', 'Grey', 'Brown', 'Beige',
    'Navy', 'Pink', 'Yellow', 'Orange', 'Purple', 'Cream', 'Khaki',
]

# ---- Size normalizer: maps label text → form dropdown value ----
SIZE_MAP = {
    'EXTRA SMALL': 'XS', 'X-SMALL': 'XS', 'XS': 'XS',
    'SMALL': 'S', 'S': 'S',
    'MEDIUM': 'M', 'M': 'M',
    'LARGE': 'L', 'L': 'L',
    'X-LARGE': 'XL', 'EXTRA LARGE': 'XL', 'XL': 'XL',
    'XX-LARGE': 'XXL', 'EXTRA EXTRA LARGE': 'XXL',
    'XXL': 'XXL', '2XL': 'XXL', 'DOUBLE XL': 'XXL',
}

# ---- Category keywords: map search result text → form Type dropdown ----
CATEGORY_KEYWORDS = {
    'Shirt':  ['shirt', 't-shirt', 'tee', 'top', 'blouse', 'polo', 'tank'],
    'Pants':  ['pants', 'trousers', 'jeans', 'shorts', 'leggings', 'chinos'],
    'Jacket': ['jacket', 'coat', 'hoodie', 'sweatshirt', 'sweater', 'cardigan', 'parka'],
    'Dress':  ['dress', 'skirt', 'gown', 'romper', 'jumpsuit'],
    'Shoes':  ['shoes', 'sneakers', 'boots', 'sandals', 'loafers', 'trainers'],
    'Socks':  ['socks', 'sock'],
    'Hat':    ['hat', 'cap', 'beanie', 'snapback'],
}

# ---- Materials that match the form's Material dropdown options ----
KNOWN_MATERIALS = [
    'Cotton', 'Wool', 'Polyester', 'Leather', 'Denim',
    'Silk', 'Linen', 'Nylon', 'Cashmere', 'Spandex',
    'Elastane', 'Viscose', 'Rayon', 'Fleece',
]


# ============================================================
# HELPERS
# ============================================================

def _compress_for_api(image_bytes, max_bytes=4 * 1024 * 1024):
    """
    Resize/compress image to stay under Anthropic's 5 MB base64 limit.
    Returns (compressed_bytes, 'image/jpeg').
    """
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    quality = 85
    while True:
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality)
        if buf.tell() <= max_bytes or quality <= 20:
            return buf.getvalue(), 'image/jpeg'
        # Still too large: drop quality then halve dimensions
        if quality > 20:
            quality -= 15
        else:
            w, h = img.size
            img = img.resize((w // 2, h // 2), Image.LANCZOS)
            quality = 70


def _normalize_size(raw):
    """Map label size text to XS/S/M/L/XL/XXL, or return raw if no match."""
    if not raw:
        return ''
    return SIZE_MAP.get(raw.strip().upper(), raw.strip())


def _main_material(raw):
    """
    Extract the dominant material from a composition string.
    '60% Cotton 40% Polyester' → 'Cotton'
    Falls back to title-casing the first word found after a % sign.
    """
    if not raw:
        return ''
    low = raw.lower()
    for mat in KNOWN_MATERIALS:
        if mat.lower() in low:
            return mat
    # Generic: grab text after the first percentage
    parts = re.split(r'\d+\s*%', raw)
    for part in parts:
        clean = part.strip().strip(',').strip()
        if clean:
            return clean.title()
    return raw.strip().title()


def _infer_category(text):
    """Infer clothing category from free text (search result titles/snippets)."""
    text = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return cat
    return ''


def _extract_color_from_text(text):
    """Return the first PRESET_COLORS match found in text (case-insensitive), or ''."""
    text_lower = text.lower()
    for color in PRESET_COLORS:
        if color.lower() in text_lower:
            return color
    return ''


def _extract_size_from_text(text):
    """
    Find a size pattern in text. Checked in order:
      1. Standard labels: XS, S, M, L, XL, XXL, 2XL, 3XL
      2. "size: X" patterns
      3. Numeric like 32x30
      4. US sizing like "US 10"
    Returns the raw matched string, or ''.
    """
    patterns = [
        r'\b(3XL|2XL|XXL|XL|XS|S|M|L)\b',
        r'\bsize[:\s]+(\S+)',
        r'\b(\d{2}[xX]\d{2})\b',
        r'\bUS\s+(\d+(?:\.\d+)?)\b',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1) if m.lastindex else m.group(0)
    return ''


# ============================================================
# STEP 1 — Claude Vision: extract raw label fields
# ============================================================

def _extract_from_label(image_bytes, media_type, api_key):
    """
    Send the tag photo to Claude Vision.
    Returns a dict with keys:
      brand, item_number, size, material, country_of_origin, rn_number, care_instructions
    """
    # Compress to stay under Anthropic's 5 MB base64 image limit
    if len(image_bytes) > 4 * 1024 * 1024:
        image_bytes, media_type = _compress_for_api(image_bytes)

    client = anthropic.Anthropic(api_key=api_key)
    image_b64 = base64.standard_b64encode(image_bytes).decode('utf-8')

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        messages=[{
            'role': 'user',
            'content': [
                {
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': media_type,
                        'data': image_b64,
                    },
                },
                {
                    'type': 'text',
                    'text': (
                        'Read every line of text on this clothing label. '
                        'Extract the fields below and return them as a JSON object. '
                        'Use "" for any field you cannot find.\n\n'
                        '- brand: brand or manufacturer name\n'
                        '- item_number: style/model/item number (e.g. "DV3456-010", "AB1234")\n'
                        '- size: size exactly as printed on label\n'
                        '- material: full fabric composition '
                        '  (e.g. "100% Cotton" or "60% Cotton 40% Polyester")\n'
                        '- color: color of the garment if stated on the label, '
                        '  or infer from the label/tag background/print if obvious, '
                        '  otherwise ""\n'
                        '- garment_type: type of clothing (e.g. "Shirt", "Pants", "Jacket", '
                        '  "Dress", "Shoes", "Socks", "Hat") inferred from the label text, '
                        '  brand, or any visible garment — use "" if cannot determine\n'
                        '- country_of_origin: country where garment was made\n'
                        '- rn_number: RN or CA number if present (e.g. "RN 123456")\n'
                        '- care_instructions: any care text or symbols described in words'
                    ),
                },
            ],
        }],
    )
    text = response.content[0].text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    return json.loads(text)


# ============================================================
# STEP 2a — DuckDuckGo: search for product online
# ============================================================

def _search_product(brand, item_number=None, material=None):
    """
    Search DuckDuckGo for product info.
    Returns: { product_name, category, product_url, source, color, size }
    """
    result = {
        'product_name': '',
        'category': '',
        'product_url': '',
        'source': 'label_only',
        'color': '',
        'size': '',
    }

    if brand and item_number:
        query = f'{brand} {item_number}'
    elif brand and material:
        query = f'{brand} {material} clothing'
    else:
        return result

    try:
        hits = list(DDGS().text(query, max_results=5))
        if not hits:
            return result

        top = hits[0]
        result['product_url']  = top.get('href', '')
        result['product_name'] = top.get('title', '')
        result['source']       = 'online_search'

        # Infer category, color, size from combined titles + snippets
        combined = ' '.join(
            h.get('title', '') + ' ' + h.get('body', '') for h in hits
        )
        result['category'] = _infer_category(combined)
        result['color']    = _extract_color_from_text(combined)
        result['size']     = _extract_size_from_text(combined)

    except Exception:
        pass

    return result


# ============================================================
# STEP 2b — FTC RN database lookup (fallback)
# ============================================================

def _lookup_rn(rn_number):
    """
    Query the FTC Registered Number database.
    Returns { rn_company } or {} on failure.
    """
    if not rn_number:
        return {}
    nums = re.findall(r'\d+', rn_number)
    if not nums:
        return {}
    try:
        resp = requests.get(
            f'https://rn.ftc.gov/account/GetRNInfo?rn={nums[0]}',
            timeout=5,
            headers={'User-Agent': 'Mozilla/5.0'},
        )
        if resp.ok:
            data = resp.json()
            company = data.get('companyName', '')
            if company:
                return {'rn_company': company}
    except Exception:
        pass
    return {}


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def analyze_label(image_bytes, media_type='image/jpeg', api_key=None):
    """
    Analyze a clothing label photo.

    Args:
        image_bytes: raw bytes of the tag image
        media_type:  MIME type (e.g. 'image/jpeg', 'image/png')
        api_key:     Anthropic API key

    Returns:
        dict with keys split into two groups:
          Form-fillable  → brand, size, material, category
          Info-only      → item_number, material_full, country_of_origin,
                           rn_number, rn_company, care_instructions,
                           product_name, product_url
          Meta           → confidence ('high'/'medium'/'low'), source
    """
    # Step 1 — Claude Vision
    raw = _extract_from_label(image_bytes, media_type, api_key)

    brand         = raw.get('brand', '').strip()
    item_number   = raw.get('item_number', '').strip()
    material_raw  = raw.get('material', '').strip()
    rn_number     = raw.get('rn_number', '').strip()
    color_raw     = raw.get('color', '').strip()
    garment_type  = raw.get('garment_type', '').strip()

    # Step 2 — Online enrichment (fallback chain)
    confidence = 'low'
    online = {}

    if brand and item_number:
        online     = _search_product(brand, item_number=item_number)
        confidence = 'high'
    elif brand and material_raw:
        online     = _search_product(brand, material=material_raw)
        confidence = 'medium'
    elif rn_number:
        online     = _lookup_rn(rn_number)
        confidence = 'medium'

    # Step 3 — Build result
    # Use DuckDuckGo category if found, otherwise fall back to Vision-inferred garment_type
    category = online.get('category', '') or garment_type

    return {
        # ---- Form-fillable (maps directly to Add Item dropdowns) ----
        'brand':    brand,
        'size':     _normalize_size(raw.get('size', '')) if raw.get('size', '').strip() else online.get('size', ''),
        'material': _main_material(material_raw),
        'color':    color_raw if color_raw else online.get('color', ''),
        'category': category,   # → Type dropdown

        # ---- Info-only (shown in UI panel, not saved to DB) ----
        'item_number':       item_number,
        'material_full':     material_raw,
        'country_of_origin': raw.get('country_of_origin', ''),
        'rn_number':         rn_number,
        'rn_company':        online.get('rn_company', ''),
        'care_instructions': raw.get('care_instructions', ''),
        'product_name':      online.get('product_name', ''),
        'product_url':       online.get('product_url', ''),

        # ---- Meta ----
        'confidence': confidence,
        'source':     online.get('source', 'label_only'),
    }
