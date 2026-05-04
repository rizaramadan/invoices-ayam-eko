#!/usr/bin/env python3
"""Generate per-customer invoice HTML files (with stable random-looking 2-char postfix)
plus a listing page. PDFs/JPGs are local-only via Chrome headless + pdftoppm."""
import os, subprocess, hashlib, json
from pathlib import Path

HERE = Path(__file__).parent
MONTH_DIR = HERE.parent
DATE = "04/05/2026"

customers = [
    (1,  "Vita",   [("Bebek Panggang", 0.5, 300000)]),
    (2,  "Arum",   [("Ayam Panggang", 1, 140000), ("Ayam Rebus", 1, 140000), ("Acar Cabe Ijo", 1, 15000)]),
    (3,  "Nabila", [("Ayam Panggang", 1, 140000), ("Char Siu Ayam", 1, 140000), ("Chilli Oil Botol", 1, 15000), ("Hoisim Sauce", 2, 15000)]),
    (4,  "Andona", [("Ayam Klungkung", 3, 100000), ("Chilli Oil 100gr", 2, 15000), ("Sambel Bodo", 3, 0)]),
    (5,  "Ajeng",  [("Ayam Panggang", 1, 140000), ("Chilli Oil Botol", 1, 15000)]),
    (6,  "Yuan",   [("Ayam Lombok", 1, 100000), ("Ayam Djogja", 1, 100000), ("Sambel Hejo", 1, 0), ("Sambel Terasi", 1, 0)]),
    (7,  "Gilang", [("Ayam Kremes", 1, 100000), ("Sambel Bodo (extra)", 2, 15000), ("Sambel Bodo", 1, 0)]),
    (8,  "Yanti",  [("Ayam Panggang", 1, 140000), ("Chilli Oil Botol", 1, 15000)]),
    (9,  "Sahara", [("Ayam Rebus", 2, 140000), ("Bebek Panggang", 0.5, 300000)]),
    (10, "Femi",   [("Ayam Rebus", 1, 140000), ("Ayam Klungkung", 1, 100000), ("Chilli Oil Botol", 1, 15000), ("Sambel Bali", 1, 0)]),
    (11, "Mitha",  [("Ayam Rebus", 1, 140000), ("Ayam Klungkung", 1, 100000), ("Sambel Bodo", 1, 0)]),
    (12, "Silmi",  [("Ayam Rebus", 1, 140000), ("Chilli Oil 100gr", 1, 15000), ("Sambel Bodo (extra)", 1, 15000)]),
    (13, "Shima",  [("Ayam Rebus", 1, 140000), ("Ayam Klungkung", 1, 100000), ("Sambel Bodo", 1, 0)]),
    (14, "Krista", [("Ayam Klungkung", 1, 100000), ("Ayam Lombok", 1, 100000), ("Sambel Bodo", 1, 0), ("Sambel Bali", 1, 0)]),
    (15, "Nia",    [("Ayam Kremes", 1, 100000), ("Ayam Serundeng", 1, 100000), ("Ayam Djogja", 1, 100000), ("Sambel Hejo", 1, 0), ("Sambel Bali", 1, 0), ("Sambel Terasi", 1, 0)]),
]

def postfix(no, name):
    seed = f"{no}-{name}-maseko-mei2026"
    h = hashlib.md5(seed.encode()).hexdigest()
    a = chr(ord('a') + int(h[0:2], 16) % 26).upper()
    b = chr(ord('a') + int(h[2:4], 16) % 26)
    return a + b

def fmt_qty(q):
    return str(int(q)) if q == int(q) else str(q)

def fmt_money(n):
    return f"{int(round(n)):,}".replace(",", ".")

INVOICE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Courier New', 'Menlo', monospace; background: #eee; color: #1a1a1a; padding: 16px 8px; }
.receipt { background: white; max-width: 360px; margin: 0 auto; padding: 24px 22px; box-shadow: 0 2px 12px rgba(0,0,0,0.12); border-radius: 6px; font-size: 13px; }
.shop { text-align: center; font-size: 24px; font-weight: 900; letter-spacing: 3px; }
.tagline { text-align: center; font-size: 11px; color: #666; letter-spacing: 1px; margin-top: 2px; }
.sline { border-top: 2px solid #111; margin: 10px 0; }
.dline { border-top: 1.5px dashed #333; margin: 8px 0; }
.info { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 2px; }
.item { margin: 6px 0; }
.item-name { font-weight: 700; font-size: 13px; }
.item-detail { display: flex; justify-content: space-between; font-size: 12px; padding-left: 6px; color: #333; }
.total { display: flex; justify-content: space-between; font-weight: 900; font-size: 16px; margin: 6px 0; }
.footer { text-align: center; margin-top: 12px; font-size: 11px; color: #555; line-height: 1.6; }
.heart { font-size: 14px; }
@media print {
  body { background: white; padding: 0; }
  .receipt { box-shadow: none; max-width: 100%; }
}
"""

def render(no, name, items):
    total = sum(q*p for _, q, p in items)
    rows = ""
    for label, qty, price in items:
        sub = qty * price
        if price == 0:
            left, right = f"{fmt_qty(qty)} pcs", "GRATIS"
        else:
            left, right = f"{fmt_qty(qty)} × {fmt_money(price)}", fmt_money(sub)
        rows += f"""
    <div class="item">
      <div class="item-name">{label}</div>
      <div class="item-detail">
        <span>{left}</span>
        <span>{right}</span>
      </div>
    </div>"""
    return f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Invoice — {name}</title>
<style>{INVOICE_CSS}</style></head><body>
<div class="receipt">
<div class="shop">AYAM MASEKO</div>
<div class="tagline">Catering Ayam &amp; Bebek</div>
<div class="sline"></div>
<div class="info"><span>No. Order</span><span>: {no:03d}</span></div>
<div class="info"><span>Nama</span><span>: {name}</span></div>
<div class="info"><span>Tanggal</span><span>: {DATE}</span></div>
<div class="dline"></div>
{rows}
<div class="dline"></div>
<div class="total"><span>TOTAL</span><span>Rp {fmt_money(total)}</span></div>
<div class="sline"></div>
<div class="footer">
  <span class="heart">★</span> Terima kasih <span class="heart">★</span><br>
  Pesenan Mas Eko &mdash; Mei 2026<br>
  BCA 1371352258 a.n. Siti Maryati
</div>
</div></body></html>"""

LISTING_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; color: #333; line-height: 1.5; }
.header { background: #b71c1c; color: white; padding: 24px 16px; text-align: center; }
.header h1 { font-size: 22px; font-weight: 700; }
.header p { font-size: 13px; opacity: 0.85; margin-top: 4px; }
.container { max-width: 600px; margin: 0 auto; padding: 16px; }
.list { list-style: none; }
.list li { background: white; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 10px; }
.list a { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; text-decoration: none; color: #333; font-weight: 500; }
.list a:hover { background: #fce4ec; border-radius: 8px; }
.no { color: #b71c1c; font-weight: 700; min-width: 32px; }
.name { flex: 1; padding: 0 12px; }
.amount { color: #555; font-size: 13px; font-variant-numeric: tabular-nums; }
.totals { background: white; border-radius: 8px; padding: 14px 16px; margin-top: 16px; font-size: 14px; }
.totals strong { color: #b71c1c; font-size: 16px; }
.back { display: inline-block; margin-top: 14px; color: #b71c1c; text-decoration: none; font-size: 13px; }
"""

def render_listing(rows):
    items_html = ""
    grand = 0
    for no, name, items, file in rows:
        total = sum(q*p for _, q, p in items)
        grand += total
        items_html += f"""
        <li><a href="./invoices/{file}" target="_blank">
          <span class="no">{no:02d}.</span>
          <span class="name">{name}</span>
          <span class="amount">Rp {fmt_money(total)}</span>
        </a></li>"""
    return f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mei 2026 — Invoice Ayam Maseko</title>
<style>{LISTING_CSS}</style></head><body>
<div class="header">
  <h1>Mei 2026</h1>
  <p>Daftar invoice per nama</p>
</div>
<div class="container">
  <ul class="list">{items_html}
  </ul>
  <div class="totals">Grand Total: <strong>Rp {fmt_money(grand)}</strong> · {len(rows)} pesanan</div>
  <a class="back" href="../">← Kembali</a>
</div>
</body></html>"""

# Generate
html_dir = HERE
listing_rows = []
for no, name, items in customers:
    pf = postfix(no, name)
    safe = name.replace(" ", "_")
    fname = f"{no:02d}_{safe}__{pf}.html"
    (html_dir / fname).write_text(render(no, name, items), encoding="utf-8")
    listing_rows.append((no, name, items, fname))
    print(f"✓ {fname}")

(MONTH_DIR / "index.html").write_text(render_listing(listing_rows), encoding="utf-8")
print(f"\n✓ {MONTH_DIR / 'index.html'}")
print(f"\nDone. {len(customers)} invoices generated.")
