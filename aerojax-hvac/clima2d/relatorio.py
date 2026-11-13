"""Relatório técnico em HTML autocontido."""

import datetime as _dt
import os
from pathlib import Path

from .cargas import cargas_totais
from .criterios import conformidade
from .figuras import figura_resultados, png_base64

def relatorio_html(projeto, r, tabela_malha=None):
    """Relatório técnico autocontido (HTML com imagens embutidas)."""
    import matplotlib.pyplot as plt
    ind = r["indicadores"]
    cg = cargas_totais(projeto)
    conf = conformidade(r, projeto["criterios"])
    fig_r = figura_resultados(projeto, r)
    img_r = png_base64(fig_r)
    plt.close(fig_r)
    i = projeto["insuflamento"]
    c = projeto["condicao"]
    s = projeto["sala"]

    def tab(linhas, cab):
        h = "".join(f"<th>{x}</th>" for x in cab)
        corpo = "".join("<tr>" + "".join(f"<td>{x}</td>" for x in l) + "</tr>" for l in linhas)
        return f"<table><tr>{h}</tr>{corpo}</table>"

    parcelas = [(k, f"{v[0]:.0f}", f"{v[1]:.0f}") for k, v in cg["parcelas"].items()]
    parcelas.append(("<b>Total</b>", f"<b>{cg['sensivel']:.0f}</b>", f"<b>{cg['latente']:.0f}</b>"))
    conf_l = [(x["critério"], x["resultado"], x["limite"], "✔ atende" if x["atende"] else "✘ não atende",
               x["referência"]) for x in conf]
    malha_html = ""
    if tabela_malha:
        cab = list(tabela_malha[0].keys())
        malha_html = "<h2>Estudo de independência de malha</h2>" + tab(
            [[f"{v:.3f}" if isinstance(v, float) else v for v in l.values()] for l in tabela_malha], cab)

    return f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<title>Estudo de climatização - {projeto['nome']}</title>
<style>body{{font-family:Arial,sans-serif;max-width:1000px;margin:24px auto;padding:0 16px;color:#222}}
table{{border-collapse:collapse;margin:8px 0 16px}}td,th{{border:1px solid #bbb;padding:4px 8px;font-size:14px}}
th{{background:#eef}}h1{{font-size:24px}}h2{{font-size:18px;border-bottom:1px solid #ccc;margin-top:28px}}
.aviso{{background:#fff6e0;border-left:4px solid #e0a000;padding:8px 12px}}</style></head><body>
<h1>Estudo de distribuição de ar e conforto térmico</h1>
<p><b>Projeto:</b> {projeto['nome']}<br><b>Responsável:</b> {projeto.get('responsavel') or '-'}<br>
<b>Data:</b> {_dt.date.today().strftime('%d/%m/%Y')}</p>
<h2>1. Dados de entrada</h2>
{tab([("Dimensões do corte (L x H)", f"{s['largura']} x {s['altura']} m"), ("Profundidade", f"{s['profundidade']} m"),
      ("Condição de projeto", f"{c['T_alvo']} °C / {c['UR_alvo'] * 100:.0f} % UR"),
      ("Atividade / vestimenta", f"{c['met']} met / {c['clo']} clo"),
      ("Vazão de insuflamento", f"{i['vazao_m3h']:.0f} m³/h"),
      ("Temperatura de insuflamento", f"{i['temperatura']:.1f} °C ({i['ur_saida'] * 100:.0f} % UR)"),
      ("Ângulo do jato", f"{i['angulo_graus']:.0f}°")], ["Item", "Valor"])}
<h2>2. Cargas térmicas do ambiente [W]</h2>{tab(parcelas, ["Parcela", "Sensível", "Latente"])}
<h2>3. Verificação de conformidade (zona ocupada)</h2>{tab(conf_l, ["Critério", "Resultado", "Limite", "Situação", "Referência"])}
<h2>4. Resultados</h2>
{tab([("Temperatura média na zona ocupada", f"{ind['T_ocupada']:.2f} °C"),
      ("Umidade relativa média", f"{ind['UR_ocupada'] * 100:.1f} %"),
      ("Velocidade média / máxima", f"{ind['vel_media_ocupada']:.2f} / {ind['vel_max_ocupada']:.2f} m/s"),
      ("PMV médio (desvio)", f"{ind['PMV_medio']:+.2f} ({ind['PMV_desvio']:.2f})"),
      ("PPD médio", f"{ind['PPD_medio']:.1f} %"),
      ("Ar de retorno", f"{ind['T_retorno']:.2f} °C / {ind['UR_retorno'] * 100:.0f} % UR"),
      ("Eficácia de remoção de calor", f"{ind['eficacia_remocao_calor']:.2f}")], ["Indicador", "Valor"])}
<img src="data:image/png;base64,{img_r}" style="width:100%">
<h2>5. Controle de qualidade numérica</h2>
{tab([("Balanço de calor sensível (retirado x cargas)", f"{r['erro_balanco_sensivel'] * 100:+.1f} %"),
      ("Balanço de calor latente (retirado x cargas)", f"{r['erro_balanco_latente'] * 100:+.1f} %"),
      ("Malha", f"{r['malha'][0]} x {r['malha'][1]} células ({r['malha'][2] * 100:.1f} cm)"),
      ("Tempo simulado / média", f"{r['tempo_simulado'] / 60:.0f} min / {projeto['simulacao']['tempo_media_s'] / 60:.0f} min"),
      ("Viscosidade turbulenta efetiva", f"{projeto['simulacao']['nu_efetiva']:.1e} m²/s")], ["Verificação", "Valor"])}
<p>Balanços acima de ±5 % indicam que a simulação ainda não atingiu regime permanente
(aumente o tempo simulado) ou que a malha não resolve as aberturas.</p>
{malha_html}
<h2>6. Hipóteses e limitações</h2>
<div class="aviso"><ul>
<li>Modelo bidimensional (corte): o difusor é tratado como linear, ocupando toda a profundidade.
A vazão e os balanços de energia e umidade são preservados; o alcance de jatos de saídas
concentradas (splits) tende a ser subestimado.</li>
<li>Turbulência representada por viscosidade efetiva constante (parâmetro de calibração).</li>
<li>Temperatura radiante média igual à temperatura do ar local; paredes adiabáticas exceto
os fluxos de calor informados.</li>
<li>Estudo de caráter comparativo e de pré-projeto. Não substitui o cálculo de cargas conforme
ABNT NBR 16401-1 nem simulação 3D validada quando exigida.</li></ul></div>
<p style="font-size:12px;color:#777">Gerado por Clima2D (pacote clima2d).</p>
</body></html>"""


def gravar_relatorio(projeto, resultado, destino, tabela_malha=None):
    """Grava o relatório em UTF-8, de forma atômica, e devolve o caminho."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    html = relatorio_html(projeto, resultado, tabela_malha)
    temporario = destino.with_name(f".{destino.name}.{os.getpid()}.tmp")
    try:
        temporario.write_text(html, encoding="utf-8")
        os.replace(temporario, destino)
    finally:
        temporario.unlink(missing_ok=True)
    return destino
