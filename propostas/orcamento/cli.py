"""
Gera a planilha e as propostas DOCX a partir de um arquivo de proposta, sem interface.

    python -m orcamento.cli exemplos/hvac_consultoria_2d_3d_bim.json --xlsx --docx --saida saida/
"""

import argparse
import os
import sys

from . import catalogo as ct
from . import exportar_docx, exportar_viabilidade, exportar_xlsx, motor
from . import viabilidade as vb
from . import parametros as pm
from . import proposta as pp


def main(argv=None):
    ap = argparse.ArgumentParser(description="Propostas KAPTEK — gera XLSX e DOCX a partir do .json da proposta")
    ap.add_argument("proposta")
    ap.add_argument("--xlsx", action="store_true")
    ap.add_argument("--docx", action="store_true")
    ap.add_argument("--viabilidade", action="store_true", help="planilha do estudo de viabilidade (payback, VPL, TIR)")
    ap.add_argument("--saida", default=".")
    a = ap.parse_args(argv)

    cat = ct.carregar()
    erros = ct.validar(cat)
    if erros:
        print("Catálogo inválido:\n- " + "\n- ".join(erros), file=sys.stderr)
        return 2
    with open(a.proposta, encoding="utf-8") as f:
        p = pp.completar(pp.carregar_json(f.read()), cat, pm.carregar())
    res = motor.precificar(cat, p)
    os.makedirs(a.saida, exist_ok=True)

    for r in res["opcoes"]:
        print(f"{r['nome']}: {r['total_h']:.1f} h · {r['prazo_dias_corridos']} dias corridos · "
              f"fechado {exportar_docx.moeda(r['preco_fechado'])} · hora {exportar_docx.moeda(r['preco_hora'])} · "
              f"proposta ({r['modelo_preco']}) {exportar_docx.moeda(r['preco'])}")
    for av in res["avisos"]:
        print("AVISO:", av)

    if a.xlsx:
        nome = f"KAPTEK-orcamento-{exportar_docx.slug(p['cliente'].get('razao'))}-{exportar_docx.slug(p['numero'])}-rev{p.get('revisao', '00')}.xlsx"
        caminho = os.path.join(a.saida, nome)
        with open(caminho, "wb") as f:
            f.write(exportar_xlsx.gerar(cat, p, res))
        print("XLSX:", caminho)
    if a.viabilidade:
        if not p["viabilidade"]["alternativas"]:
            print("AVISO: a proposta não tem alternativas no estudo de viabilidade.")
        else:
            estudo = vb.calcular(p["viabilidade"], {r["id"]: r["preco"] for r in res["opcoes"]})
            for alt in estudo["alternativas"]:
                pb = f"{alt['payback']:.1f}" if alt["payback"] is not None else "> horizonte"
                print(f"  {alt['nome']}: CAPEX {exportar_docx.moeda(alt['capex'])} · economia {exportar_docx.moeda(alt['economia_ano1'])}/ano "
                      f"· payback {pb} anos · VPL {exportar_docx.moeda(alt['vpl'])} · {alt['classificacao']}")
            nome = f"KAPTEK-viabilidade-{exportar_docx.slug(p['cliente'].get('razao'))}-{exportar_docx.slug(p['numero'])}.xlsx"
            caminho = os.path.join(a.saida, nome)
            with open(caminho, "wb") as f:
                f.write(exportar_viabilidade.gerar(p, estudo))
            print("XLSX:", caminho)
    if a.docx:
        for conteudo, nome, pend in exportar_docx.gerar(cat, p, res):
            caminho = os.path.join(a.saida, nome)
            with open(caminho, "wb") as f:
                f.write(conteudo)
            print("DOCX:", caminho, f"(pendências: {', '.join(pend)})" if pend else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
