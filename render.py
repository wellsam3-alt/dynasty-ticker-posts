# Renders every slides/**/*.html file to out/**/*.png at Instagram's 1080x1440 size.
import asyncio, pathlib
from playwright.async_api import async_playwright

async def main():
    files = sorted(pathlib.Path('slides').rglob('*.html'))
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1080, 'height': 1440})
        for f in files:
            out = pathlib.Path('out') / f.relative_to('slides').with_suffix('.png')
            out.parent.mkdir(parents=True, exist_ok=True)
            await page.goto(f.resolve().as_uri(), wait_until='networkidle')
            await page.evaluate('document.fonts.ready')
            await page.wait_for_timeout(300)
            await page.screenshot(path=str(out), clip={'x': 0, 'y': 0, 'width': 1080, 'height': 1440})
            print('rendered', out)
        await browser.close()

asyncio.run(main())
