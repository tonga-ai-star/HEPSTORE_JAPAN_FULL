#!/usr/bin/env python3
"""Render docs/ERD_Hep_Bookstore.html (from gen_erd.py) to ERD_Hep_Bookstore.png and .pdf with Playwright + Chrome."""
from pathlib import Path

from playwright.sync_api import sync_playwright

DOCS = Path(__file__).resolve().parent
SRC = DOCS / 'ERD_Hep_Bookstore.html'

with sync_playwright() as pw:
    try:
        browser = pw.chromium.launch(channel='chrome')
    except Exception:
        browser = pw.chromium.launch()
    page = browser.new_page(viewport={'width': 2400, 'height': 1600}, device_scale_factor=2)
    page.goto(SRC.as_uri())
    page.wait_for_selector('.mermaid svg', timeout=30000)
    page.locator('.mermaid svg').screenshot(path=str(DOCS / 'ERD_Hep_Bookstore.png'))
    # Print with the PNG in place of the live SVG so the diagram fits one page.
    page.evaluate("""() => { const pre = document.querySelector('.mermaid');
        pre.outerHTML = '<img src="ERD_Hep_Bookstore.png" alt="ERD">'; }""")
    page.wait_for_function("document.querySelector('.diagram img').complete")
    page.pdf(path=str(DOCS / 'ERD_Hep_Bookstore.pdf'), prefer_css_page_size=True, print_background=True)
    browser.close()
print('docs/ERD_Hep_Bookstore.png, docs/ERD_Hep_Bookstore.pdf')
