#!/usr/bin/env python3
"""Debug: inspect ECHA table page + capture the real export request."""
import json
from playwright.sync_api import sync_playwright

URL = "https://echa.europa.eu/candidate-list-table"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"))
    reqs = []
    page.on("request", lambda r: reqs.append((r.method, r.url)) if "export" in r.url.lower() or "portlet" in r.url.lower() else None)
    page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(12000)
    print("TITLE:", page.title())
    # table rows?
    rows = page.locator("tbody tr").count()
    print("table rows:", rows)
    # find export buttons/links
    for sel in ["a:has-text('CSV')", "a:has-text('XLS')", "button:has-text('CSV')", "a[href*='export']"]:
        print(sel, "->", page.locator(sel).count())
    # dump any export-ish links
    hrefs = page.eval_on_selector_all("a", "as => as.map(a => a.href).filter(h => /export|csv|xls/i.test(h))")
    print("export hrefs:", hrefs[:5])
    print("captured reqs:", reqs[:10])
    # try GET on a guessed export url in page context
    for u in [
        "https://echa.europa.eu/candidate-list-table?p_p_id=disslists_WAR_disslistsportlet&p_p_resource_id=exportResults&exportType=csv",
    ]:
        r = page.evaluate("async u => { const r = await fetch(u, {method:'GET'}); return {s: r.status, t: (await r.text()).slice(0,200)}; }", u)
        print("GET try:", r)
    browser.close()
