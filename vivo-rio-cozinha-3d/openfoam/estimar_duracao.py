#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estimativa de duração do caso 3D completo (coifa A, estacionário) na máquina do usuário, a partir do que foi medido na nuvem.

  T = T_malha + N_iter * s_por_iter(células) + T_pós
  s_por_iter na nuvem: medido em 1…4 processos nas malhas grossa / média / produção (lei de potência nas células; a malha de produção é medida, não extrapolada).
  Passagem para o notebook: o solver em malha grande é limitado pela banda de memória, logo
      s_usuário = s_nuvem(4 proc.) * banda_nuvem(4) / banda_usuário(6) * k,   k ∈ [0,8; 1,25] (cache, compute, WSL2, aquecimento).
  Com --usuario bench_maquina.json (calibração rodada no notebook) o fator vem da medida e k cai para [0,9; 1,15].
  N_iter: a pluma quente oscila, então nas malhas finas os resíduos estacionam num patamar (na média: ~3e-4) e o critério usual de 1e-4 nunca é atingido.
      O critério prático adotado é patamar dos resíduos + janela de média (as grandezas pontuais oscilam; vale a média dos últimos passos).
      O patamar é medido na malha média; para malhas maiores adota-se N ∝ células^0,25 (hipótese de engenharia, não medida) com fator 0,7 a 1,5.
Uso: python3 estimar_duracao.py <pasta_medicoes> [--md saida.md] [--usuario bench_maquina.json | --bw-medido GB/s]"""
import argparse, json, math, os
import numpy as np

EXPOENTE_ITER = 0.25      # N_iter ∝ células^0,25 acima da malha média (hipótese de engenharia)
FATOR_ITER = (0.7, 1.5)   # faixa sobre o N_iter central
JANELA_MEDIA = 1000       # iterações de média depois do patamar

NOME = {"grossa": "grossa", "media": "média", "producao": "produção"}

def carregar(p, nome):
    f = os.path.join(p, nome); return json.load(open(f)) if os.path.exists(f) else None

def num(x, n=1):
    """pt-BR: vírgula decimal, ponto de milhar."""
    return f"{x:,.{n}f}".replace(",", "§").replace(".", ",").replace("§", ".")

def dur(h):
    if h < 1.5: return f"{num(h * 60, 0)} min"
    return f"{num(h, 1)} h"

def faixa_h(lo, hi):
    return f"{num(lo, 1)} a {num(hi, 1)} h" if lo >= 1.5 else f"{dur(lo)} a {dur(hi)}"

def patamar(h, bloco=250, fator=1.6):
    """Primeira iteração a partir da qual nenhum resíduo cai mais que `fator` em relação ao nível (mediana por bloco) medido nela.
    Devolve ({campo: iteração}, {campo: nível do patamar}, atingido): atingido=False se o início cai nos dois últimos blocos (o resíduo ainda cai, não há patamar visível)."""
    n = len(h["Ux"]); nb = n // bloco; por = {}; nivel = {}
    for c, r in h.items():
        med = np.array([np.nanmedian(r[i * bloco:(i + 1) * bloco]) for i in range(nb)])
        for i in range(nb):
            if med[i:].min() >= med[i] / fator: por[c] = i * bloco; nivel[c] = float(np.nanmedian(r[i * bloco:])); break
    return por, nivel, max(por.values()) < n - 2 * bloco

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("pasta"); ap.add_argument("--md", default=None); ap.add_argument("--json", default=None)
    ap.add_argument("--bw-usuario", default="26,32,36", help="banda de memória do notebook (GB/s) pior,típico,melhor com 6 processos: DDR4-2666 em dois canais")
    ap.add_argument("--bw-medido", type=float, default=None, help="banda de memória (GB/s) medida no notebook com bench_banda.py, linha dos 6 processos; troca a faixa --bw-usuario")
    ap.add_argument("--np-usuario", type=int, default=6); ap.add_argument("--usuario", default=None)
    ap.add_argument("--figura", default=None, help="PNG de figura_convergencia.py para referenciar no relatório (caminho relativo ao .md)"); a = ap.parse_args()
    solver = "compressivel"
    custo = {n: carregar(a.pasta, f"custo_{n}_{solver}.json") for n in ("grossa", "media", "producao")}
    banda = carregar(a.pasta, "banda_aqui.json")["GBs"]; conv = {n: carregar(a.pasta, f"convergencia_{n}_{solver}.json") for n in ("grossa", "media")}
    bw_lo, bw_mid, bw_hi = [float(x) for x in a.bw_usuario.split(",")] if a.bw_medido is None else (a.bw_medido,) * 3
    cel = {n: c["celulas"] for n, c in custo.items()}
    por_np = {n: {e["np"]: e for e in c["execucoes"]} for n, c in custo.items()}
    s4 = {n: por_np[n][4]["s_por_iter_mediana"] for n in custo}
    nn = sorted(cel, key=cel.get); X = np.log([cel[n] for n in nn]); Y = np.log([s4[n] for n in nn]); b_s, a_s = np.polyfit(X, Y, 1)
    s_aqui = lambda N: float(np.exp(a_s) * N ** b_s)
    # validação do modelo de custo: ajusta só com grossa e produção e prevê a média (que foi medida)
    bv = math.log(s4["producao"] / s4["grossa"]) / math.log(cel["producao"] / cel["grossa"]); pred = s4["grossa"] * (cel["media"] / cel["grossa"]) ** bv; erro_media = pred / s4["media"] - 1
    # iterações: patamar dos resíduos (grossa e média) e monitores físicos da média
    hist = {n: dict(np.load(f)) for n in ("grossa", "media") if os.path.exists(f := os.path.join(a.pasta, f"residuos_{n}_{solver}.npz"))}
    pat = {n: patamar(h) for n, h in hist.items()}
    mon = carregar(a.pasta, f"monitores_media_{solver}.json")
    n_media = math.ceil((max(pat["media"][0].values()) + JANELA_MEDIA) / 500) * 500 if "media" in pat else 3500
    def iters(N):
        mid = math.ceil(n_media * max(1.0, N / cel["media"]) ** EXPOENTE_ITER / 500) * 500
        return mid, mid * FATOR_ITER[0], mid * FATOR_ITER[1]
    mesh = custo["producao"]["malha_s"]; t_mesh_prod = mesh["blockMesh"] + mesh["snappyHexMesh"] + mesh["topoSet_createPatch"]
    bwa = banda["4"]
    if a.usuario and os.path.exists(a.usuario):
        u = json.load(open(a.usuario)); su = {e["np"]: e["s_por_iter_mediana"] for e in u["execucoes"] if e.get("s_por_iter_mediana")}
        k_ref = min(su, key=lambda x: abs(x - a.np_usuario)); fator = su[k_ref] / s4["media"]
        usr = lambda N: (0.9 * s_aqui(N) * fator, s_aqui(N) * fator, 1.15 * s_aqui(N) * fator)
        base_txt = f"calibrado com `bench_maquina.py` ({u.get('cpu', 'sua CPU')}, {num(su[k_ref], 2)} s/iteração na malha média com {k_ref} processos: fator {num(fator, 2)} sobre a nuvem)"
    else:
        fator = None; usr = lambda N: (0.8 * s_aqui(N) * bwa / bw_hi, s_aqui(N) * bwa / bw_mid, 1.25 * s_aqui(N) * bwa / bw_lo)
        base_txt = (f"extrapolado pela banda de memória medida no seu notebook ({num(a.bw_medido, 1)} GB/s com {a.np_usuario} processos, contra {num(bwa, 0)} GB/s na nuvem com 4); o solver ainda não foi medido na sua máquina" if a.bw_medido is not None else
                    f"extrapolado pela banda de memória ({num(bwa, 0)} GB/s na nuvem com 4 processos; {num(bw_lo, 0)} a {num(bw_hi, 0)} GB/s no notebook com {a.np_usuario}); ainda não foi medido na sua máquina")
    bm, am = np.polyfit(X, np.log([por_np[n][4]["pico_memoria_MB"] / 1024 for n in nn]), 1)
    mem_de = lambda N: next((por_np[n][4]["pico_memoria_MB"] / 1024 * 1.05 for n in cel if cel[n] == N), float(np.exp(am) * N ** bm) * 1.05)
    linhas = []
    for N, nome in ((cel["media"], "média"), (1_500_000, "intermediária"), (cel["producao"], "produção")):
        lo, mid, hi = usr(N); t_mesh = t_mesh_prod * N / cel["producao"] / 60; n_mid, n_lo, n_hi = iters(N)
        extra = lambda f: (t_mesh * f + 5) / 60             # geração da malha (pior caso: mais lenta no notebook) + pós-processamento
        linhas.append(dict(malha=nome, celulas=N, s_iter=(lo, mid, hi), mem_GB=mem_de(N), malha_min=t_mesh, iter=(n_lo, n_mid, n_hi),
                           h=(lo * n_lo / 3600 + extra(1.0), mid * n_mid / 3600 + extra(1.2), hi * n_hi / 3600 + extra(1.5)), h_por_mil=(lo / 3.6, mid / 3.6, hi / 3.6)))
    deriva = {n: conv[n]["s_por_iter_fim"] / conv[n]["s_por_iter_inicio"] - 1 for n in conv if conv[n] and conv[n].get("s_por_iter_inicio") and conv[n].get("s_por_iter_fim")}
    out = dict(modelo=dict(expoente_s_iter=float(b_s), base=base_txt, erro_validacao_media=float(erro_media), deriva_s_iter=deriva, expoente_iter=EXPOENTE_ITER, fator_iter=FATOR_ITER, janela_media=JANELA_MEDIA, iter_media=n_media),
               medidas={n: dict(celulas=cel[n], s4=s4[n], por_np={k: e["s_por_iter_mediana"] for k, e in por_np[n].items()}, mem_MB={k: e["pico_memoria_MB"] for k, e in por_np[n].items()}) for n in custo},
               patamar={n: dict(iteracao=max(p[0].values()), por_campo=p[0], nivel=p[1], atingido=bool(p[2])) for n, p in pat.items()}, monitores=mon,
               estimativas=linhas, banda_aqui=banda, malha_prod_s=t_mesh_prod)
    json.dump(out, open(a.json or os.path.join(a.pasta, "estimativa.json"), "w"), indent=1, default=float)
    # relatório
    m = []; P = m.append
    prod = linhas[-1]; med = linhas[0]; mid_l = linhas[1]
    P("# Quanto custa o caso 3D completo (coifa A, estacionário)\n")
    P("## Resumo\n")
    P(f"- Na sua máquina (Xeon E-2176M, 6 processos): malha média ({num(cel['media'] / 1e6, 2)} M células) **≈ {dur(med['h'][1])}**; intermediária (1,5 M) **≈ {dur(mid_l['h'][1])}**; "
      f"produção ({num(cel['producao'] / 1e6, 2)} M) **≈ {dur(prod['h'][1])}** ({faixa_h(prod['h'][0], prod['h'][2])}). Cada 1.000 iterações levam {num(prod['h_por_mil'][1], 1)} h na malha de produção.")
    P(f"- Base do tempo por iteração: {base_txt}.")
    P("- O caso não foi rodado até o fim. Mediu-se a malha, o custo por iteração e a memória nas três malhas, e o comportamento dos resíduos e de grandezas físicas até 3.500 iterações na malha média; o resto é extrapolação, com a faixa informada.")
    P("- **O número de iterações é a maior incerteza (fator 0,7 a 1,5).** A pluma quente oscila: na malha média os resíduos estacionam em torno de 3e-4 e o critério usual de 1e-4 não é atingido, de modo que o fim da simulação se decide pelo patamar dos resíduos e pela média de grandezas físicas, não por uma tolerância.")
    P("- Memória não é limite: o pico previsto para a malha de produção é de cerca de " + num(prod["mem_GB"], 1) + " GB, contra os 64 GB do notebook.\n")
    P("## O que foi medido na nuvem (Xeon 2,1 GHz, 4 núcleos, 15 GB; OpenFOAM ESI v1912)\n")
    P("| Malha | Células | 1 proc. | 2 proc. | 3 proc. | 4 proc. | Memória (4 proc.) |\n|---|---:|---:|---:|---:|---:|---:|")
    for n in nn:
        e = por_np[n]; P(f"| {NOME[n]} | {num(cel[n], 0)} | " + " | ".join(f"{num(e[k]['s_por_iter_mediana'], 2)} s" for k in (1, 2, 3, 4)) + f" | {num(e[4]['pico_memoria_MB'] / 1024, 1)} GB |")
    P(f"\nSegundos por iteração (mediana de 30 a 40 iterações). A geração da malha de produção (blockMesh + snappyHexMesh + patches) levou **{num(t_mesh_prod, 0)} s** com um processo e {num(mesh['snappy_pico_MB'] / 1024, 1)} GB. "
      f"O tempo por iteração cresce com as células elevadas a {num(b_s, 2)}.\n")
    P("## Quantas iterações: o que os resíduos e os monitores mostram\n")
    sci = lambda v: f"{v:.0e}".replace("e-0", "e-")
    for n in ("grossa", "media"):
        if n not in pat: continue
        por, nivel, atingido = pat[n]; N = len(hist[n]["Ux"]); pmax = max(por.values())
        niv = ", ".join(f"{c} {sci(nivel[c])}" for c in ("Ux", "h", "p_rgh") if c in nivel)
        if atingido: P(f"- Malha {NOME[n]} ({num(cel[n], 0)} células, {num(N, 0)} iterações rodadas): os resíduos estacionam a partir de ≈ {num(pmax, 0)} iterações, nos níveis {niv}.")
        else: P(f"- Malha {NOME[n]} ({num(cel[n], 0)} células, {num(N, 0)} iterações rodadas): os resíduos ainda caem devagar no fim da execução (≈ {niv}); não há patamar visível. Com o critério usual (1e-4) ela convergiu em {num(conv[n]['iter_convergencia_folgado'], 0)} iterações" +
                       (f" e com o rigoroso (1e-5), em {num(conv[n]['iter_convergencia_rigoroso'], 0)}." if conv[n].get("iter_convergencia_rigoroso") else "."))
    if a.figura: P(f"\n![Resíduos nas malhas grossa e média e grandezas físicas da malha média]({a.figura})\n")
    if deriva: P("- O custo por iteração é estável durante a execução: " + "; ".join(f"{NOME[n]}: {num(100 * d, 1).replace('-', '−')} % entre o começo e a segunda metade" for n, d in deriva.items()) + ".")
    if mon:
        ins = mon["instantes"]; ts = sorted(ins, key=int); T0 = 293.15
        P("\nGrandezas físicas na malha média a cada 500 iterações (T em K; U em m/s):\n")
        P("| Iteração | T média sob a coifa | \\|U\\| média sob a coifa | T média do ambiente | T na sonda (0,5 m sobre a ilha) | \\|U\\| na sonda |\n|---:|---:|---:|---:|---:|---:|")
        for t in ts: r = ins[t]; P(f"| {num(int(t), 0)} | {num(r['T_sob_coifa'], 2)} | {num(r['U_sob_coifa'], 2)} | {num(r['T_ambiente'], 2)} | {num(r['T_sonda'], 2)} | {num(r['U_sonda'], 2)} |")
        tail = [t for t in ts if int(t) >= 1000]
        def amp(k, exc=False):
            v = np.array([ins[t][k] - (T0 if exc else 0) for t in tail]); return 100 * (v.max() - v.min()) / 2 / abs(v.mean())
        P(f"\nDe 1.000 a 3.500 iterações, a variação (± metade da amplitude relativa) é de ±{num(amp('T_sob_coifa', True), 0)} % no excesso de temperatura sob a coifa e ±{num(amp('U_sob_coifa'), 0)} % na velocidade média sob a coifa, "
          f"mas de ±{num(amp('T_sonda', True), 0)} % e ±{num(amp('U_sonda'), 0)} % nos valores da sonda: a pluma pulsa e um valor pontual do último passo não representa o escoamento; vale a média de uma janela de iterações. "
          f"O excesso de temperatura médio do ambiente (uma fração de grau) ainda cai devagar.")
    P(f"\n**Critério adotado para o fim da simulação:** patamar dos resíduos + {num(JANELA_MEDIA, 0)} iterações para calcular a média das grandezas de interesse. Na malha média isso dá {num(n_media, 0)} iterações "
      f"({num(max(pat['media'][0].values()), 0) if 'media' in pat else '—'} até o patamar + {num(JANELA_MEDIA, 0)} de média, arredondado para cima). Para as malhas maiores, adotou-se N ∝ células^{num(EXPOENTE_ITER, 2)} "
      f"(hipótese de engenharia: com a malha grossa convergindo a 1e-5 e a média estacionando em 3e-4, as duas medidas não permitem ajustar o expoente), com faixa de ×{num(FATOR_ITER[0], 1)} a ×{num(FATOR_ITER[1], 1)}.\n")
    P("## Estimativa para o seu notebook (Xeon E-2176M, 6 processos, 64 GB)\n")
    P(f"Base: {base_txt}. Faixas = pior caso … melhor caso (combinam a incerteza do tempo por iteração com a do número de iterações); o valor central vem do modelo.\n")
    P("| Malha | Células | Memória | s/iteração | Iterações adotadas (faixa) | Duração | Faixa |\n|---|---:|---:|---|---|---|---|")
    for r in linhas:
        lo, mid, hi = r["s_iter"]; n_lo, n_mid, n_hi = r["iter"]
        P(f"| {r['malha']} | {num(r['celulas'], 0)} | {num(r['mem_GB'], 1)} GB | {num(lo, 1)} a {num(hi, 1)} ({num(mid, 1)}) | {num(n_mid, 0)} ({num(n_lo, 0)} a {num(n_hi, 0)}) | **{dur(r['h'][1])}** | {faixa_h(r['h'][0], r['h'][2])} |")
    P("\nA duração inclui a geração da malha e 5 minutos de pós-processamento. O notebook tem menos banda de memória que esta nuvem, e é ela que limita o solver em malha grande: por isso o tempo sobe mais do que a diferença de clock sugere.\n")
    P("## Quanto confiar\n")
    P(f"- **Custo por iteração na nuvem: alta confiança.** A malha de produção foi medida (não extrapolada) e o modelo de potência, ajustado só com a grossa e a de produção, prevê a média com erro de {num(100 * erro_media, 1)} % (previsto {num(pred, 2)} s, medido {num(s4['media'], 2)} s).")
    P(f"- **Passagem para o notebook: confiança média** enquanto não houver medida na sua máquina. A incerteza vem da banda de memória ({'medida, resta o efeito de cache e do WSL2' if a.bw_medido is not None else '26 a 36 GB/s é a faixa de um DDR4-2666 em dois canais, mais efeitos de cache e do WSL2'}); o tempo por iteração fica entre {num(100 * (prod['s_iter'][0] / prod['s_iter'][1] - 1), 0).replace('-', '−')} % e +{num(100 * (prod['s_iter'][2] / prod['s_iter'][1] - 1), 0)} % em torno do valor central. Rodar `bench_maquina.py` (cerca de 10 minutos) troca isso por medida e reduz a faixa para cerca de −10 % a +15 %.")
    P("- **Número de iterações: confiança média a baixa.** O patamar foi medido na malha média; para a de produção é extrapolação. Mudar as hipóteses do caso (carga térmica, reposição, abertura de equilíbrio) pode mudar o comportamento da pluma e o patamar.")
    P(f"- **Não estimado:** simulação transiente da fumaça (LES ou URANS). Como ordem de grandeza, 60 s físicos com passo de 0,01 s e duas correções por passo equivalem a cerca de 12 mil iterações do estacionário, ou seja, {num(12000 / prod['iter'][1], 1)} vezes as iterações adotadas para a malha de produção, sem contar o pós-processamento.\n")
    P("## Recomendação\n")
    P(f"1. Comece pela malha média ({dur(med['h'][1])} no notebook): ela já resolve a pluma e os captores e valida a configuração do caso antes de gastar uma noite.")
    P(f"2. Para o estudo de captura de verdade, use a malha intermediária (≈ 1,5 M células, {dur(mid_l['h'][1])}) ou a de produção ({dur(prod['h'][1])}, deixada rodando durante a noite), depois de confirmar as hipóteses de carga térmica e reposição.")
    P("3. Grave as grandezas de interesse (taxa de captura, temperatura na sonda) a cada iteração e pare quando a média móvel de 1.000 iterações variar menos que a tolerância que você aceitar; não pare pelo resíduo.")
    P("4. Rode antes a calibração: ela leva 10 minutos e substitui a extrapolação por medida.\n")
    P("## Como trocar a extrapolação por medida\n")
    P("Rode `python3 openfoam/bench_maquina.py --np 1,2,4,6` no notebook (≈ 10 min, gera a malha média e mede 30 iterações) e mande o resumo impresso: `estimar_duracao.py --usuario bench_maquina.json` recalcula a tabela com o seu tempo por iteração.\n")
    if a.md: open(a.md, "w", encoding="utf-8").write("\n".join(m))
    print("\n".join(m))

if __name__ == "__main__": main()
