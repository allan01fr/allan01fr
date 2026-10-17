# Testes dos utilitários de pós-processamento e estimativa em openfoam/ (puro Python: não precisam do OpenFOAM).
#   leitura de campos do OpenFOAM (ascii, binário, uniforme), instante no cabeçalho do .vtu,
#   busca da célula que contém cada ponto numa malha com níveis de refino diferentes (inclui célula grossa com nós pendurados),
#   formatação pt-BR da estimativa e leitura da calibração do usuário.
import json, os, struct, sys, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "openfoam"))
from scipy.spatial import cKDTree
import quadros, ler_vtu, estimar_duracao

res = []
def ok(nome, cond, info=""):
    res.append(bool(cond)); print(("OK  " if cond else "FALHA ") + nome, info)

CAB = "FoamFile\n{\n    version     2.0;\n    format      %s;\n    arch        \"LSB;label=32;scalar=64\";\n    class       volScalarField;\n    object      T;\n}\n\ndimensions      [0 0 0 0 0 0 0];\n\n"
tmp = tempfile.mkdtemp()
def escreve(nome, dados):
    p = os.path.join(tmp, nome); open(p, "wb").write(dados); return p

# ---- campos do OpenFOAM
v = np.array([0.0, 0.25, 1.0, 1e-6, 0.5])
asc = (CAB % "ascii") + "internalField   nonuniform List<scalar> \n5\n(\n" + "\n".join(repr(float(x)) for x in v) + "\n)\n;\n\nboundaryField\n{\n}\n"
ok("campo ascii (nonuniform)", np.allclose(quadros.campo_escalar(escreve("T_asc", asc.encode()), 5), v))
binario = (CAB % "binary").encode() + b"internalField   nonuniform List<scalar> \n5\n(" + struct.pack("<5d", *v) + b")\n;\n\nboundaryField\n{\n}\n"
ok("campo binário de 64 bits (nonuniform)", np.allclose(quadros.campo_escalar(escreve("T_bin", binario), 5), v))
uni = ((CAB % "ascii") + "internalField   uniform 0;\n\nboundaryField\n{\n}\n").encode()
ok("campo uniforme expande para o nº de células", np.array_equal(quadros.campo_escalar(escreve("T_uni", uni), 4), np.zeros(4)))
try: quadros.campo_escalar(escreve("T_ruim", binario), 7); falhou = False
except SystemExit: falhou = True
ok("nº de valores diferente do nº de células é erro", falhou)

# ---- instante no cabeçalho do .vtu
vtu = escreve("a.vtu", b"<?xml version='1.0'?>\n<!-- case='fumaca' region='region0' time='12.5' index='250' -->\n<VTKFile>")
ok("instante lido do comentário do .vtu (e não do índice do passo)", ler_vtu.tempo(vtu) == 12.5)

# ---- célula que contém o ponto: malha com uma célula grossa (0,2) ao lado de 8 finas (0,1) e um buraco (sólido)
LO, HI = [], []
LO.append([0, 0, 0]); HI.append([0.2, 0.2, 0.2])                      # grossa, ocupa [0,0.2]^3
for i in range(2):
    for j in range(2):
        for k in range(2):
            if (i, j, k) == (1, 1, 1): continue                        # buraco: sólido em [0.3,0.4]^3
            LO.append([0.2 + 0.1 * i, 0.1 * j, 0.1 * k]); HI.append([0.3 + 0.1 * i, 0.1 * (j + 1), 0.1 * (k + 1)])
LO, HI = np.array(LO, float), np.array(HI, float); C = (LO + HI) / 2; meia = (HI - LO) / 2; arv = cKDTree(C)
P = np.array([[0.01, 0.01, 0.01], [0.19, 0.19, 0.19], [0.25, 0.05, 0.05], [0.35, 0.15, 0.15], [0.35, 0.15, 0.05], [0.9, 0.9, 0.9]])
ach = quadros.celula_que_contem(P, arv, C, meia, ks=(2, 4, 8))
ok("ponto na célula grossa (mesmo longe do centro, com k pequeno)", ach[0] == 0 and ach[1] == 0, str(ach[:2]))
ok("ponto em célula fina", ach[2] >= 1 and (LO[ach[2]] <= P[2]).all() and (P[2] <= HI[ach[2]]).all())
ok("buraco e fora do domínio são sólidos (-1)", ach[3] == -1 and ach[5] == -1, str(ach))
ok("ponto na célula fina vizinha do buraco", ach[4] >= 1 and (LO[ach[4]] <= P[4]).all() and (P[4] <= HI[ach[4]]).all())
# a média dos vértices de uma célula com nós pendurados fica deslocada; o centro da caixa não
vert = np.vstack([LO[0], HI[0], [0.2, 0.0, 0.0], [0.2, 0.2, 0.0], [0.2, 0.0, 0.2], [0.2, 0.2, 0.2], [0.2, 0.1, 0.0], [0.2, 0.1, 0.2], [0.2, 0.0, 0.1], [0.2, 0.2, 0.1], [0.2, 0.1, 0.1]])
ok("centro da caixa ≠ média dos vértices em célula com nós pendurados (por isso quadros.py usa a caixa)", np.allclose((LO[0] + HI[0]) / 2, 0.1) and abs(vert.mean(0)[0] - 0.1) > 0.01, f"{vert.mean(0)[0]:.3f}")

# ---- formatação e estimativa
ok("número em pt-BR: milhar com ponto e decimal com vírgula", estimar_duracao.num(1234567.891, 1) == "1.234.567,9" and estimar_duracao.num(0.5, 2) == "0,50")
ok("duração: minutos abaixo de 1,5 h, horas acima", estimar_duracao.dur(0.5) == "30 min" and estimar_duracao.dur(8.04) == "8,0 h")

# ---- patamar dos resíduos: cai 3 décadas em 1000 iterações e estaciona; ou cai sempre (sem patamar)
rng = np.random.default_rng(1)
def historia(n, cai_ate, piso, campos=("Ux", "Uy", "Uz", "h", "p_rgh", "k", "epsilon")):
    it = np.arange(n); base = np.where(it < cai_ate, 10 ** (-3 * it / cai_ate), 1e-3) * (piso / 1e-3) if piso else 10 ** (-4 * it / n)
    return {c: base * 10 ** rng.normal(0, 0.05, n) for c in campos}
por, nivel, atingido = estimar_duracao.patamar(historia(3000, 1000, 1e-3))
ok("patamar detectado onde o resíduo para de cair (≈ 1.000 iterações)", atingido and 750 <= max(por.values()) <= 1500, f"{max(por.values())}")
ok("nível do patamar recuperado (1e-3)", all(0.7e-3 < v < 1.4e-3 for v in nivel.values()))
por2, _, atingido2 = estimar_duracao.patamar(historia(3000, 0, None))
ok("resíduo que cai sempre não tem patamar (atingido = falso)", not atingido2)

# ---- estimativa com medições sintéticas: custo ∝ N^1,2; a calibração do usuário escala o tempo por iteração
med = os.path.join(tmp, "med"); os.makedirs(med)
def custo(nome, N, s4):
    exe = [dict(np=k, s_por_iter_mediana=s4 * 4 / k, pico_memoria_MB=N / 1e6 * 1800) for k in (1, 2, 3, 4)]
    d = dict(celulas=N, execucoes=exe)
    if nome == "producao": d["malha_s"] = dict(blockMesh=0.4, snappyHexMesh=170.0, topoSet_createPatch=10.0, snappy_pico_MB=3800.0)
    json.dump(d, open(os.path.join(med, f"custo_{nome}_compressivel.json"), "w"))
for nome, N in (("grossa", 120_000), ("media", 720_000), ("producao", 3_100_000)): custo(nome, N, 0.1 * (N / 120_000) ** 1.2)
json.dump({"GBs": {"1": 16.0, "2": 32.0, "3": 48.0, "4": 65.0}}, open(os.path.join(med, "banda_aqui.json"), "w"))
for nome, N, f, r in (("grossa", 120_000, 2000, 4000), ("media", 720_000, 3000, None)):
    json.dump(dict(iter_convergencia_folgado=f, iter_convergencia_rigoroso=r, s_por_iter_inicio=0.1, s_por_iter_fim=0.1), open(os.path.join(med, f"convergencia_{nome}_compressivel.json"), "w"))
np.savez(os.path.join(med, "residuos_grossa_compressivel.npz"), **historia(4000, 3000, 1e-5)); np.savez(os.path.join(med, "residuos_media_compressivel.npz"), **historia(3500, 1000, 3e-4))
md1 = os.path.join(tmp, "e1.md"); md2 = os.path.join(tmp, "e2.md")
saved = sys.argv; sys.argv = ["x", med, "--md", md1, "--json", os.path.join(tmp, "e1.json")]
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()): estimar_duracao.main()
e1 = json.load(open(os.path.join(tmp, "e1.json")))
ok("modelo de custo recupera o expoente 1,2 dos dados sintéticos", abs(e1["modelo"]["expoente_s_iter"] - 1.2) < 0.01, f"{e1['modelo']['expoente_s_iter']:.3f}")
ok("validação cruzada (prever a malha média sem usá-la) dá erro < 1 % em dados exatos", abs(e1["modelo"]["erro_validacao_media"]) < 0.01)
ok("iterações da malha média = patamar + 1.000, arredondado para 500", e1["modelo"]["iter_media"] == int(np.ceil((e1["patamar"]["media"]["iteracao"] + 1000) / 500) * 500) and 2000 <= e1["modelo"]["iter_media"] <= 3000, str(e1["modelo"]["iter_media"]))
est = {r["malha"]: r for r in e1["estimativas"]}
ok("iterações crescem com as células (N ∝ células^0,25 acima da média) e a faixa é 0,7× a 1,5×", est["produção"]["iter"][1] > est["média"]["iter"][1] and abs(est["produção"]["iter"][0] / est["produção"]["iter"][1] - 0.7) < 1e-9 and abs(est["produção"]["iter"][2] / est["produção"]["iter"][1] - 1.5) < 1e-9)
ok("duração = malha + iterações × s/iteração + pós (conferida à mão para a média)", abs(est["média"]["h"][1] - (est["média"]["s_iter"][1] * est["média"]["iter"][1] / 3600 + (est["média"]["malha_min"] * 1.2 + 5) / 60)) < 1e-9)
usuario = os.path.join(tmp, "u.json")
json.dump(dict(cpu="CPU de teste", execucoes=[dict(np=k, s_por_iter_mediana=json.load(open(os.path.join(med, "custo_media_compressivel.json")))["execucoes"][3]["s_por_iter_mediana"] * 2.0) for k in (1, 2, 4, 6)]), open(usuario, "w"))
sys.argv = ["x", med, "--md", md2, "--json", os.path.join(tmp, "e2.json"), "--usuario", usuario]
with contextlib.redirect_stdout(io.StringIO()): estimar_duracao.main()
sys.argv = saved; e2 = json.load(open(os.path.join(tmp, "e2.json")))
r_media = e2["estimativas"][0]["s_iter"][1] / (e1["medidas"]["media"]["s4"])
ok("calibração do usuário: tempo por iteração da malha média = o medido (fator 2 sobre a nuvem)", abs(r_media - 2.0) < 1e-6, f"{r_media:.3f}")
txt = open(md2, encoding="utf-8").read()
ok("relatório calibrado cita a CPU informada e usa vírgula decimal", "CPU de teste" in txt and "," in txt and ".5 h" not in txt)

print(sum(res), "/", len(res), "ok"); sys.exit(0 if all(res) else 1)
