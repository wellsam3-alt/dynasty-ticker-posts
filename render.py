# Renders every slides/**/*.html file to out/**/*.png at Instagram's 1080x1440 size.
# Images can't be pushed through the GitHub connector, so they live in assets/ as
# base64 text (name.ext.b64, or name.ext.b64.part1, .part2 ...). Before rendering,
# each one is rebuilt into its binary file next to it. An optional name.ext.b64.patch.json
# lists [position, delete_count, insert_text] fixes applied to the joined text first.
import asyncio, base64, glob, json, pathlib, re
from playwright.async_api import async_playwright

def decode_assets():
    groups = {}
    for p in pathlib.Path('assets').rglob('*.b64*'):
        if p.name.endswith('.patch.json'):
            continue
        target = re.sub(r'\.b64(\.part\d+)?$', '', str(p))
        groups.setdefault(target, []).append(p)
    for target, parts in groups.items():
        parts.sort(key=lambda p: int(re.search(r'part(\d+)$', p.name).group(1)) if 'part' in p.name else 0)
        text = re.sub(r'\s', '', ''.join(p.read_text() for p in parts))
        patch = pathlib.Path(target + '.b64.patch.json')
        if patch.exists():
            for pos, delete, insert in sorted(json.loads(patch.read_text()), reverse=True):
                text = text[:pos] + insert + text[pos + delete:]
        pathlib.Path(target).write_bytes(base64.b64decode(text))
        print('decoded', target)

async def main():
    decode_assets()
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
