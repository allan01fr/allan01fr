# Teste headless (Playwright + Chromium). As URLs de CDN são servidas a partir de cópias locais
# idênticas (three@0.128.0 do npm), porque o container não acessa cdnjs/jsdelivr.
import asyncio, json, os, sys
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
VENDOR = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("THREE_VENDOR")
HTML = "file://" + os.path.join(ROOT, "saida", "modelo_3d_tubulacoes.html")
OUT = os.path.join(HERE, "screenshots"); os.makedirs(OUT, exist_ok=True)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results = []
def ok(name, cond, info=""):
    results.append((name, bool(cond), info)); print(("OK  " if cond else "FALHA ") + name, info)

async def route(page):
    async def h(r):
        u = r.request.url
        if "three.min.js" in u: await r.fulfill(path=os.path.join(VENDOR, "build", "three.min.js"), content_type="application/javascript")
        elif "OrbitControls.js" in u: await r.fulfill(path=os.path.join(VENDOR, "examples", "js", "controls", "OrbitControls.js"), content_type="application/javascript")
        elif "fonts.g" in u: await r.fulfill(body="", content_type="text/css")
        else: await r.continue_()
    await page.route("**/*", h)

async def run_theme(pw, scheme, tag):
    br = await pw.chromium.launch(executable_path=CHROME, args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
    ctx = await br.new_context(viewport={"width":1440,"height":900}, color_scheme=scheme, accept_downloads=True, device_scale_factor=1)
    page = await ctx.new_page(); errs = []
    page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(str(e)))
    await route(page)
    await page.goto(HTML); await page.wait_for_timeout(2500)
    ok(f"[{tag}] sem erro de console", not errs, "; ".join(errs[:3]))
    await page.screenshot(path=os.path.join(OUT, f"01_visao_geral_{tag}.png"))
    if tag != "claro":
        await br.close(); return
    # seleção por ID e painel de campo
    await page.evaluate("__app.gotoId(__app.M.pontos.find(p=>p.amb==='LAVL' && p.tipo==='AF').id)"); await page.wait_for_timeout(1600)
    reg = await page.inner_text("#rbody")
    ok("seleção abre o painel de campo", "Altura do piso" in reg and "Até a parede" in reg, reg[:80].replace("\n"," | "))
    ok("painel aberto (não minimizado)", not await page.evaluate("document.querySelector('#right').classList.contains('min')"))
    await page.screenshot(path=os.path.join(OUT, "05_painel_campo_lavagem.png"))
    # close dos banheiros/áreas molhadas: lavagem de louças e lavagem de panelas
    await page.evaluate("__app.setSel(null)")
    for i,(amb,nm) in enumerate((("LAVL","lavagem_loucas"),("LAVP","lavagem_panelas"))):
        await page.evaluate(f"""(()=>{{const p=__app.M.pontos.filter(p=>p.amb==='{amb}'); const x=p.reduce((a,q)=>a+q.x,0)/p.length, y=p.reduce((a,q)=>a+q.y,0)/p.length;
          __app.setSel(null); document.querySelector('#minbtn').click(); __app.center(x, y, -2.0, 8.5);}})()"""); await page.wait_for_timeout(1800)
        await page.screenshot(path=os.path.join(OUT, f"02_close_{nm}.png"))
    # clique real por proximidade em tela num ponto
    pid = await page.evaluate("__app.M.pontos.find(p=>p.amb==='LAVP' && p.tipo==='AQ').id")
    await page.evaluate(f"__app.gotoId('{pid}')"); await page.wait_for_timeout(1600)
    sc = await page.evaluate(f"(()=>{{const m=__app.ptById['{pid}']; return __app.toScreen(m.position);}})()")
    box = await page.evaluate("(()=>{const r=document.querySelector('#gl').getBoundingClientRect(); return [r.left,r.top];})()")
    await page.evaluate("__app.setSel(null)")
    await page.mouse.click(box[0]+sc["x"]+6, box[1]+sc["y"]+5); await page.wait_for_timeout(400)
    sel = await page.evaluate("__app.state.sel && __app.state.sel.id")
    ok("clique por proximidade (6 px ao lado) seleciona o ponto", sel == pid, f"{sel} vs {pid}")
    # filtros por disciplina: divergências somem e voltam
    await page.evaluate("__app.state.tab='div'; document.querySelector('[data-tab=div]').click()"); await page.wait_for_timeout(200)
    n0 = await page.evaluate("document.querySelectorAll('#rbody .dv').length")
    m0 = await page.evaluate("__app.M.divergencias.filter(d=>d.disciplinas.includes('SAN')).length")
    await page.click("input[data-sis='SAN-ESG']"); await page.wait_for_timeout(200)
    n1 = await page.evaluate("document.querySelectorAll('#rbody .dv').length")
    vis_markers = await page.evaluate("__app.labels.filter(l=>l.owner.kind==='divlbl' && l.owner.m.visible).length")
    await page.click("input[data-sis='SAN-ESG']"); await page.wait_for_timeout(200)
    n2 = await page.evaluate("document.querySelectorAll('#rbody .dv').length")
    ok("filtro Esgoto esconde divergências SAN e as traz de volta", n1 < n0 and n2 == n0, f"{n0} → {n1} → {n2} (SAN={m0}, marcadores visíveis c/ filtro: {vis_markers})")
    await page.click("input[data-lay='arq']"); await page.wait_for_timeout(150)
    n3 = await page.evaluate("document.querySelectorAll('#rbody .dv').length")
    await page.click("input[data-lay='arq']")
    ok("divergência só-ARQ segue a camada de arquitetura", n3 < n0, f"{n0} → {n3}")
    # clicar divergência liga disciplinas e centraliza
    await page.click("input[data-sis='DRE']"); await page.wait_for_timeout(100)
    did = await page.evaluate("__app.M.divergencias.find(d=>d.disciplinas.includes('DRE') && d.pos).id")
    await page.evaluate(f"__app.gotoDiv('{did}')"); await page.wait_for_timeout(1600)
    ok("clicar divergência religa a disciplina", await page.evaluate("__app.state.sis['DRE']===true"))
    await page.screenshot(path=os.path.join(OUT, "06_divergencia_dreno.png"))
    # planta com corte
    await page.evaluate("__app.setView('plan')"); await page.wait_for_timeout(300)
    await page.evaluate("document.querySelector('#cut').value='-1.20'; document.querySelector('#cut').dispatchEvent(new Event('input'))"); await page.wait_for_timeout(700)
    ok("corte ativo", await page.evaluate("__app.state.cut===true && Math.abs(__app.state.cutZ+1.2)<1e-6"))
    await page.screenshot(path=os.path.join(OUT, "03_planta_com_corte.png"))
    await page.evaluate("document.querySelector('#cutOn').click()")
    # sob o piso
    await page.evaluate("__app.setView('under')"); await page.wait_for_timeout(1600)
    await page.screenshot(path=os.path.join(OUT, "04_sob_o_piso.png"))
    # medição com Shift (trava de eixo) e Esc
    await page.evaluate("__app.setView('persp')"); await page.wait_for_timeout(300)
    a = await page.evaluate("__app.M.pontos.find(p=>p.amb==='COZ' && p.tipo==='GAS').id")
    b = await page.evaluate("__app.M.pontos.filter(p=>p.amb==='COZ' && p.tipo==='GAS')[3].id")
    await page.evaluate(f"(()=>{{const A=__app.ptById['{a}'].position, B=__app.ptById['{b}'].position; __app.setSel(null); __app.center((A.x+B.x)/2,(A.y+B.y)/2,(A.z+B.z)/2, 7);}})()"); await page.wait_for_timeout(1800)
    await page.click("#minbtn") if not await page.evaluate("document.querySelector('#right').classList.contains('min')") else None
    await page.click("#measure")
    sa = await page.evaluate(f"__app.toScreen(__app.ptById['{a}'].position)")
    sb = await page.evaluate(f"__app.toScreen(__app.ptById['{b}'].position)")
    await page.mouse.click(box[0]+sa["x"], box[1]+sa["y"]); await page.wait_for_timeout(150)
    await page.keyboard.down("Shift")
    await page.mouse.move(box[0]+sb["x"], box[1]+sb["y"]); await page.wait_for_timeout(150)
    await page.mouse.click(box[0]+sb["x"], box[1]+sb["y"]); await page.keyboard.up("Shift"); await page.wait_for_timeout(300)
    c = await page.evaluate("__app.state.cotas[__app.state.cotas.length-1]")
    nz = sum(1 for k in ("dx","dy","dz") if abs(c[k]) > 1e-6) if c else -1
    ok("medição com Shift trava em um eixo", c and nz == 1, json.dumps({k:round(c[k],3) for k in ("d3","dx","dy","dz")}) if c else "sem cota")
    await page.mouse.click(box[0]+sa["x"], box[1]+sa["y"]); await page.wait_for_timeout(100)
    await page.keyboard.press("Escape"); await page.wait_for_timeout(100)
    ok("Esc cancela o 1º ponto", await page.evaluate("__app.state.m1===null && __app.state.measure===true"))
    await page.keyboard.press("Escape"); await page.wait_for_timeout(100)
    ok("Esc sai do modo Medir", await page.evaluate("__app.state.measure===false"))
    # cota livre (sem Shift) entre dois pontos
    await page.click("#measure")
    await page.mouse.click(box[0]+sa["x"], box[1]+sa["y"]); await page.mouse.click(box[0]+sb["x"], box[1]+sb["y"]); await page.wait_for_timeout(300)
    await page.keyboard.press("Escape")
    await page.screenshot(path=os.path.join(OUT, "07_cotas.png"))
    # exportações CSV
    async with page.expect_download() as d1:
        await page.evaluate("document.querySelector('[data-tab=res]').click()"); await page.wait_for_timeout(100)
        await page.click("[data-csv='pontos']")
    dl = await d1.value; pth = await dl.path(); txt = open(pth, encoding="utf-8-sig").read()
    ok("export pontos.csv", txt.count("\n") >= 100 and txt.startswith("id;tipo"), f"{txt.count(chr(10))} linhas")
    await page.evaluate("document.querySelector('[data-tab=cot]').click()"); await page.wait_for_timeout(100)
    dls = []
    page.on("download", lambda d: dls.append(d))
    await page.click("#cCsv"); await page.wait_for_timeout(1200)
    names = [d.suggested_filename for d in dls]
    ok("export Cotas: pontos.csv + cotas.csv", "cotas.csv" in names and "pontos.csv" in names, str(names))
    # minimizar painel
    await page.click("#minbtn"); await page.wait_for_timeout(100)
    ok("minimizar painel", await page.evaluate("document.querySelector('#right').classList.contains('min')"))
    # busca com sugestões
    await page.fill("#q", "DRE-SS"); await page.wait_for_timeout(200)
    ok("busca com sugestões", await page.evaluate("document.querySelectorAll('#sugg [data-id]').length") > 0)
    ok(f"[{tag}] sem erro de console após interações", not errs, "; ".join(errs[:3]))
    # celular
    m = await br.new_context(viewport={"width":390,"height":844}, color_scheme="light", device_scale_factor=2, is_mobile=True, has_touch=True)
    mp = await m.new_page(); merr=[]; mp.on("pageerror", lambda e: merr.append(str(e))); await route(mp)
    await mp.goto(HTML); await mp.wait_for_timeout(2000)
    await mp.evaluate("__app.gotoId(__app.M.pontos.find(p=>p.amb==='LAVP').id)"); await mp.wait_for_timeout(900)
    sw = await mp.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    ok("celular: sem rolagem horizontal e sem erro", sw and not merr, str(merr[:2]))
    await mp.screenshot(path=os.path.join(OUT, "08_celular.png"))
    await br.close()

async def main():
    async with async_playwright() as pw:
        await run_theme(pw, "light", "claro")
        await run_theme(pw, "dark", "escuro")
    json.dump([dict(teste=a, ok=b, info=c) for a,b,c in results], open(os.path.join(HERE, "resultado_navegador.json"), "w"), ensure_ascii=False, indent=1)
    print(sum(1 for r in results if r[1]), "/", len(results), "ok")
asyncio.run(main())
