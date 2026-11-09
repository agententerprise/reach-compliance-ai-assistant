#!/usr/bin/env python3
"""Fetch ECHA list export via headless Chromium: click the CSV button, capture the download.

Usage: python3 fetch_echa.py <table-url> <out.csv> [button-text]
"""
import asyncio
import os
import sys

from playwright.async_api import async_playwright


async def fetch_csv(table_url: str, out_path: str, button_text: str = "CSV") -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            accept_downloads=True,
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
        )
        page = await ctx.new_page()
        await page.goto(table_url, wait_until="domcontentloaded", timeout=90_000)
        await page.wait_for_selector("tbody tr", timeout=90_000)
        await page.wait_for_timeout(4000)
        # dismiss legal-notice / cookie overlays if present
        for sel in ("#legal_notice_overlay button", "button:has-text('Accept')",
                    "button:has-text('Agree')", "button:has-text('OK')",
                    ".cookie-accept", "#cookie-accept"):
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=2000):
                    await loc.click(timeout=3000)
                    await page.wait_for_timeout(1000)
            except Exception:
                pass
        await page.evaluate("""() => { for (const id of ['legal_notice_overlay']) {
            const el = document.getElementById(id); if (el) el.remove(); } }""")
        btn = page.locator(f"button:has-text('{button_text}')").first
        await btn.wait_for(timeout=30_000)
        async with page.expect_download(timeout=120_000) as dl_info:
            await btn.click()
        download = await dl_info.value
        await download.save_as(out_path)
        await browser.close()
    print(f"saved {out_path}: {os.path.getsize(out_path)} bytes")


if __name__ == "__main__":
    btn = sys.argv[3] if len(sys.argv) > 3 else "CSV"
    asyncio.run(fetch_csv(sys.argv[1], sys.argv[2], btn))
