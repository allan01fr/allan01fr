# Gera a imagem de cada tópico do BCF (verificacao/bcf_snapshots/DIV-xxx.png) a partir do HTML autocontido,
# com a mesma câmera gravada no viewpoint.bcfv (verificacao/bcf_cameras.json, escrito por build_ifc.py).
# Ordem: build_ifc.py -> bcf_snapshots.py -> build_ifc.py (empacota as imagens).
import asyncio, json, os
from playwright.async_api import async_playwright
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HTML = "file://" + os.path.join(ROOT, "saida", "modelo_3d_tubulacoes.html")
OUT = os.path.join(HERE, "bcf_snapshots"); os.makedirs(OUT, exist_ok=True)
CAM = json.load(open(os.path.join(HERE, "bcf_cameras.json")))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

async def main():
    async with async_playwright() as pw:
        br = await pw.chromium.launch(executable_path=CHROME, args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        page = await (await br.new_context(viewport={"width": 1280, "height": 800}, color_scheme="light")).new_page()
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        await page.goto(HTML); await page.wait_for_timeout(2500)
        await page.add_style_tag(content="#left,#right,#legend,#tip,#mhint,#mbar{display:none!important}")
        await page.evaluate("window.dispatchEvent(new Event('resize'))"); await page.wait_for_timeout(300)
        for did, c in CAM.items():
            await page.evaluate(f"__app.gotoDiv('{did}')"); await page.wait_for_timeout(700)
            await page.evaluate(f"""(()=>{{const cam=__app.camera(), ctl=__app.controls(); cam.fov=60; cam.clearViewOffset(); cam.updateProjectionMatrix();
                ctl.target.set({c['alvo'][0]},{c['alvo'][1]},{c['alvo'][2]}); cam.position.set({c['olho'][0]},{c['olho'][1]},{c['olho'][2]}); ctl.update();}})()""")
            await page.wait_for_timeout(500)
            r = await page.evaluate("(()=>{const b=document.querySelector('#gl').getBoundingClientRect(); return {x:b.left,y:b.top,width:b.width,height:b.height};})()")
            await page.screenshot(path=os.path.join(OUT, did + ".png"), clip=r)
            im = Image.open(os.path.join(OUT, did + ".png")).convert("RGB"); im.thumbnail((960, 960))
            im.quantize(256, method=Image.Quantize.MEDIANCUT).save(os.path.join(OUT, did + ".png"), optimize=True)
        await br.close()
    print(len(CAM), "imagens em", OUT)
asyncio.run(main())
