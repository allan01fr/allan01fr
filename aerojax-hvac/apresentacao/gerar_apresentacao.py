"""
Gera a apresentação "As ferramentas por trás do Clima2D" no formato Excalidraw.

Cada slide é um frame de 1600 x 900. As cores seguem as camadas da arquitetura:
    vermelho = interface | amarelo = projeto e arquivos | verde = física (nossos módulos)
    azul = motor numérico | roxo = gráficos e tabelas | cinza = qualidade e bastidores

Este script só monta o "esqueleto" (formato de entrada do convertToExcalidrawElements);
o arquivo .excalidraw final é produzido pelo próprio Excalidraw (convertToExcalidrawElements),
que mede os textos e liga as setas às caixas.
"""

import json
import os

L, A, GAP = 1600, 900, 160          # tamanho do slide e espaço entre slides

COR = {
    "interface": ("#e03131", "#ffc9c9"),
    "projeto": ("#f08c00", "#ffec99"),
    "fisica": ("#2f9e44", "#b2f2bb"),
    "motor": ("#1971c2", "#a5d8ff"),
    "graficos": ("#6741d9", "#d0bfff"),
    "qualidade": ("#495057", "#e9ecef"),
    "neutro": ("#1e1e1e", "#ffffff"),
    "codigo": ("#343a40", "#f1f3f5"),
    "alerta": ("#e8590c", "#ffe8cc"),
}
TITULO, CORPO, CODIGO = 5, 6, 3      # Excalifont, Nunito, Cascadia

slides = []


class Slide:
    def __init__(self, nome):
        self.k = len(slides)
        self.nome = nome
        self.ox = self.k * (L + GAP)
        self.els = []
        self.n = 0
        self.geo = {}
        slides.append(self)

    def _id(self, p):
        self.n += 1
        return f"s{self.k}_{p}{self.n}"

    # ---------------------------------------------------------------- primitivas
    def texto(self, x, y, txt, fs=24, ff=CORPO, cor="#1e1e1e", align="left"):
        i = self._id("t")
        self.els.append({"type": "text", "id": i, "x": self.ox + x, "y": y, "text": txt, "fontSize": fs,
                         "fontFamily": ff, "strokeColor": cor, "textAlign": align})
        return i

    def caixa(self, x, y, w, h, txt="", cat="neutro", fs=24, ff=CORPO, align="center", valign="middle",
              forma="rectangle", traco="solid", tcor=None, espessura=2):
        i = self._id("b")
        stroke, bg = COR[cat]
        e = {"type": forma, "id": i, "x": self.ox + x, "y": y, "width": w, "height": h,
             "strokeColor": stroke, "backgroundColor": bg, "fillStyle": "solid", "strokeWidth": espessura,
             "strokeStyle": traco, "roughness": 1}
        if forma == "rectangle":
            e["roundness"] = {"type": 3}
        self.geo[i] = (self.ox + x, y, w, h, forma)
        if txt and align == "center":
            e["label"] = {"text": txt, "fontSize": fs, "fontFamily": ff, "textAlign": align,
                          "verticalAlign": valign, "strokeColor": tcor or "#1e1e1e"}
        self.els.append(e)
        if txt and align != "center":
            # Texto alinhado à esquerda: elemento próprio com margem interna, agrupado com a caixa
            grupo = self._id("g")
            e["groupIds"] = [grupo]
            altura_linha = {TITULO: 1.25, CORPO: 1.35, CODIGO: 1.2}[ff]
            th = (txt.count("\n") + 1) * fs * altura_linha
            ty = y + 26 if valign == "top" else y + (h - th) / 2
            t = self.texto(x + 30, ty, txt, fs=fs, ff=ff, cor=tcor or "#1e1e1e")
            self.els[-1]["groupIds"] = [grupo]
        return i

    def _borda(self, caixa, alvo):
        """Ponto na borda da caixa na direção do ponto alvo (retângulo ou elipse)."""
        x, y, w, h, forma = caixa
        cx, cy = x + w / 2, y + h / 2
        dx, dy = alvo[0] - cx, alvo[1] - cy
        if dx == 0 and dy == 0:
            return cx, cy
        if forma == "ellipse":
            t = 1.0 / ((dx / (w / 2)) ** 2 + (dy / (h / 2)) ** 2) ** 0.5
        else:
            tx = (w / 2) / abs(dx) if dx else float("inf")
            ty = (h / 2) / abs(dy) if dy else float("inf")
            t = min(tx, ty)
        return cx + dx * t, cy + dy * t

    def seta(self, de, para, txt=None, cor="#1e1e1e", traco="solid", fs=18, espessura=2, folga=10):
        i = self._id("a")
        a, b = self.geo[de], self.geo[para]
        ca = (a[0] + a[2] / 2, a[1] + a[3] / 2)
        cb = (b[0] + b[2] / 2, b[1] + b[3] / 2)
        x0, y0 = self._borda(a, cb)
        x1, y1 = self._borda(b, ca)
        L_ = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 or 1.0
        ux, uy = (x1 - x0) / L_, (y1 - y0) / L_
        x0, y0, x1, y1 = x0 + ux * folga, y0 + uy * folga, x1 - ux * folga, y1 - uy * folga
        dx, dy = x1 - x0, y1 - y0
        e = {"type": "arrow", "id": i, "x": x0, "y": y0, "width": abs(dx), "height": abs(dy),
             "points": [[0, 0], [dx, dy]], "start": {"id": de}, "end": {"id": para},
             "strokeColor": cor, "strokeStyle": traco, "strokeWidth": espessura, "endArrowhead": "arrow"}
        if txt:
            e["label"] = {"text": txt, "fontSize": fs, "fontFamily": CORPO, "strokeColor": cor}
        self.els.append(e)
        return i

    def seta_livre(self, x, y, dx, dy, cor="#1e1e1e", traco="solid", espessura=2):
        i = self._id("a")
        self.els.append({"type": "arrow", "id": i, "x": self.ox + x, "y": y, "width": abs(dx), "height": abs(dy),
                         "points": [[0, 0], [dx, dy]], "strokeColor": cor, "strokeStyle": traco,
                         "strokeWidth": espessura, "endArrowhead": "arrow"})
        return i

    def codigo(self, x, y, w, h, txt, fs=20):
        return self.caixa(x, y, w, h, txt, "codigo", fs=fs, ff=CODIGO, align="left", valign="middle")

    # ---------------------------------------------------------------- padrões de slide
    def cabecalho(self, titulo, subtitulo=None, cat=None):
        if cat:
            stroke, bg = COR[cat]
            self.caixa(60, 58, 14, 64, cat=cat)
        self.texto(96 if cat else 60, 50, titulo, fs=52, ff=TITULO)
        if subtitulo:
            self.texto(96 if cat else 60, 128, subtitulo, fs=26, cor="#495057")
        self.texto(L - 70, A - 50, f"{self.k + 1}", fs=20, cor="#868e96", align="right")

    def onde(self, x, y, w, h, txt, cat):
        """Quadro 'Onde usamos no Clima2D'."""
        return self.caixa(x, y, w, h, "📍 Onde usamos no Clima2D\n\n" + txt, cat, fs=22, align="left", valign="top",
                          traco="dashed")

    def esqueleto(self):
        quadro = {"type": "frame", "id": f"frame{self.k}", "name": f"{self.k + 1:02d} · {self.nome}",
                  "x": self.ox, "y": 0, "width": L, "height": A,
                  "children": [e["id"] for e in self.els]}
        return [quadro] + self.els


# =============================================================================
# 1. Capa
s = Slide("Capa")
s.texto(80, 150, "As ferramentas\npor trás do\nClima2D", fs=76, ff=TITULO)
s.texto(84, 450, "Um mapa para aprender, ferramenta por ferramenta,\no que faz cada peça do estudo de climatização.", fs=30, cor="#495057")
s.texto(84, 590, "Cada cor é uma camada:", fs=24, cor="#495057")
leg = [("interface", "Interface"), ("projeto", "Projeto e arquivos"), ("fisica", "Física"),
       ("motor", "Motor numérico"), ("graficos", "Gráficos e tabelas"), ("qualidade", "Qualidade")]
for j, (c, t) in enumerate(leg):
    s.caixa(84 + (j % 3) * 230, 640 + (j // 3) * 70, 210, 52, t, c, fs=20)
camadas = [("interface", "Interface — Streamlit"), ("projeto", "Projeto e arquivos — ezdxf · JSON"),
           ("fisica", "Física — sala2d · psicrometria · conforto"), ("motor", "Motor numérico — JAX · NumPy"),
           ("qualidade", "Linguagem — Python")]
for j, (c, t) in enumerate(camadas):
    s.caixa(930 + j * 18, 150 + j * 128, 600 - j * 36, 104, t, c, fs=24)
s.texto(L - 70, A - 50, "1", fs=20, cor="#868e96", align="right")

# =============================================================================
# 2. Arquitetura
s = Slide("Como as peças se conectam")
s.cabecalho("Como as peças se conectam", "Do clique na tela até o relatório: quem chama quem")
voce = s.caixa(60, 380, 170, 90, "👷 Você", "neutro", fs=26)
app = s.caixa(330, 250, 260, 110, "Interface\napp.py (Streamlit)", "interface")
dxf = s.caixa(330, 520, 260, 110, "Planta / corte DXF\n(AutoCAD)", "neutro")
imp = s.caixa(660, 520, 260, 110, "importar_dxf.py\n(ezdxf)", "projeto")
proj = s.caixa(660, 250, 260, 110, "projeto.py\ncargas · validação", "projeto")
cfd = s.caixa(990, 250, 260, 110, "sala2d.py\nsimulação CFD", "fisica")
psi_ = s.caixa(930, 470, 190, 80, "psicrometria.py", "fisica", fs=20)
conf = s.caixa(1140, 470, 170, 80, "conforto.py", "fisica", fs=20)
motor = s.caixa(60, 720, 1500, 90, "Motor numérico: JAX + NumPy  (tudo acima roda sobre ele)", "motor")
fig = s.caixa(1330, 160, 230, 90, "Figuras\n(Matplotlib)", "graficos", fs=22)
csv = s.caixa(1330, 290, 230, 90, "Tabelas / CSV\n(pandas)", "graficos", fs=22)
rel = s.caixa(1330, 420, 230, 90, "Relatório\nHTML", "graficos", fs=22)
s.seta(voce, app, "clica")
s.seta(voce, dxf, "desenha")
s.seta(dxf, imp)
s.seta(imp, proj)
s.seta(app, proj)
s.seta(proj, cfd, "simula")
s.seta(cfd, psi_)
s.seta(cfd, conf)
s.seta(cfd, fig)
s.seta(cfd, csv)
s.seta(cfd, rel)

# =============================================================================
# 3. Python
s = Slide("Python e o ambiente")
s.cabecalho("Python: a linguagem que une tudo", "E três peças que fazem o programa rodar igual em qualquer computador", "qualidade")
cards = [("🐍 Python", "A linguagem.\nTodo o Clima2D é escrito nela."),
         ("📦 pip", "A \"loja\" de bibliotecas.\nBaixa NumPy, JAX, Streamlit..."),
         ("🗃️ venv (.venv)", "Uma caixa isolada com as\nversões certas, só deste projeto."),
         ("📝 requirements.txt", "A lista de compras:\nquais bibliotecas instalar.")]
for j, (t, d) in enumerate(cards):
    s.caixa(60 + j * 380, 210, 350, 210, f"{t}\n\n{d}", "qualidade", fs=23)
s.texto(60, 470, "O que o iniciar.bat faz por você:", fs=28, ff=TITULO)
passos = ["cria a .venv\n(1ª vez)", "pip install\n-r requirements.txt", "streamlit run\napp\\app.py", "navegador abre\nlocalhost:8501"]
ids = [s.caixa(60 + j * 300, 530, 250, 100, t, "qualidade", fs=21) for j, t in enumerate(passos)]
for a, b in zip(ids, ids[1:]):
    s.seta(a, b)
s.codigo(60, 680, 720, 150, "python -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt")
s.caixa(830, 680, 710, 150, "💡 Analogia: a .venv é como uma maleta de ferramentas\nsó deste serviço. Atualizar algo em outro projeto\nnão estraga este.", "alerta", fs=22, align="left")

# =============================================================================
# 4. NumPy
s = Slide("NumPy")
s.cabecalho("NumPy: contas com a tabela inteira de uma vez", "A base de quase toda a ciência em Python", "motor")
s.texto(60, 200, "A sala vira uma grade de números:", fs=26, ff=TITULO)
valores = [[25.8, 25.9, 26.1, 26.3], [24.6, 24.4, 24.5, 24.9], [23.1, 22.6, 22.8, 23.4], [21.9, 21.5, 21.7, 22.2]]
fundo = {21: "#a5d8ff", 22: "#a5d8ff", 23: "#d0ebff", 24: "#fff3bf", 25: "#ffc9c9", 26: "#ffa8a8"}
for li, linha in enumerate(valores):
    for co, v in enumerate(linha):
        i = s._id("g")
        s.els.append({"type": "rectangle", "id": i, "x": s.ox + 60 + co * 120, "y": 260 + li * 80, "width": 120,
                      "height": 80, "strokeColor": "#868e96", "backgroundColor": fundo[int(v)], "fillStyle": "solid",
                      "strokeWidth": 1, "roughness": 0,
                      "label": {"text": f"{v:.1f}", "fontSize": 24, "fontFamily": CORPO, "strokeColor": "#1e1e1e"}})
s.texto(60, 590, "T[i, j] = temperatura da célula (i, j)\nna simulação real: 50 × 28 = 1.400 células", fs=22, cor="#495057")
s.codigo(640, 220, 900, 200, "import numpy as np\nT = np.full((50, 28), 24.0)  # sala inteira a 24 °C\nT[:, 0] -= 2                 # piso 2 °C mais frio\nmedia = T.mean()             # uma linha, sem laço", fs=21)
s.caixa(640, 450, 900, 140, "⚡ Por que importa: o Excel calcula célula por célula; o NumPy\nopera a grade inteira de uma vez, em código compilado —\ndezenas a centenas de vezes mais rápido que um laço em Python.", "motor", fs=22, align="left")
s.onde(640, 620, 900, 200, "• guardar os campos de temperatura, umidade e velocidade\n• calcular médias na zona ocupada\n• exportar o CSV e alimentar as figuras", "motor")

# =============================================================================
# 5. JAX
s = Slide("JAX")
s.cabecalho("JAX: o NumPy com superpoderes", "Biblioteca do Google para computação científica e aprendizado de máquina", "motor")
poderes = [("jnp", "Mesma sintaxe do NumPy:\njnp.mean, jnp.exp...", "todo o código físico"),
           ("jax.jit", "Compila a função: vira código\nde máquina otimizado", "a simulação compila uma vez\ne roda milhares de passos"),
           ("jax.grad", "Derivada EXATA de qualquer\nfunção escrita em JAX", "sensibilidades (ex. 02)\notimização (ex. 04)"),
           ("jax.lax.scan", "Laço no tempo que pode ser\ncompilado e derivado", "os ~40 mil passos\nde tempo da CFD")]
for j, (t, d, u) in enumerate(poderes):
    s.caixa(60 + j * 380, 200, 350, 200, f"{t}\n\n{d}", "motor", fs=23)
    s.caixa(60 + j * 380, 420, 350, 100, "📍 " + u, "motor", fs=19, traco="dashed")
s.codigo(60, 570, 860, 170, "import jax\nf = lambda t: psi.umidade_relativa(t, 0.010)\njax.grad(f)(24.0)   # → -0.032\n# a UR cai 3,2 % por °C de aquecimento", fs=21)
s.caixa(960, 570, 580, 260, "⚠️ Duas regras que mais dão erro\n\n1. Arrays não mudam no lugar:\n    x = x.at[i].set(v)   (e não x[i] = v)\n\n2. Dentro do jit, sem \"if\" em valores:\n    use jnp.where(condição, a, b)", "alerta", fs=21, align="left", valign="top")

# =============================================================================
# 6. Gradiente através da simulação
s = Slide("Gradiente através da CFD")
s.cabecalho("Como o jax.grad atravessa a simulação inteira", "A ideia que permitiu otimizar vazão, ângulo e setpoint automaticamente", "motor")
p = s.caixa(60, 300, 230, 130, "Parâmetros\nvazão · ângulo\nsetpoint", "projeto", fs=22)
p1 = s.caixa(370, 310, 180, 110, "passo 1", "fisica")
p2 = s.caixa(620, 310, 180, 110, "passo 2", "fisica")
pd = s.caixa(870, 310, 110, 110, "...", "neutro", fs=36)
pn = s.caixa(1050, 310, 180, 110, "passo\n40 000", "fisica")
j_ = s.caixa(1310, 300, 230, 130, "Nota do projeto J\n(PMV², corrente\nde ar, energia)", "alerta", fs=21)
for a, b in [(p, p1), (p1, p2), (p2, pd), (pd, pn), (pn, j_)]:
    s.seta(a, b, cor="#2f9e44", espessura=3)
s.texto(370, 250, "IDA: simula a sala normalmente →", fs=24, cor="#2f9e44")
s.seta_livre(1420, 460, 0, 70, cor="#e03131", traco="dashed", espessura=3)
s.seta_livre(1420, 530, -1270, 0, cor="#e03131", traco="dashed", espessura=3)
s.seta_livre(150, 530, 0, -80, cor="#e03131", traco="dashed", espessura=3)
s.texto(420, 545, "← VOLTA (jax.grad): quanto J muda se eu mexer em cada parâmetro", fs=24, cor="#e03131")
s.caixa(60, 640, 470, 190, "💰 Custo\n≈ 3 simulações, seja para\n3 ou para 300 parâmetros", "motor", fs=23)
s.caixa(565, 640, 470, 190, "🧠 Memória\njax.checkpoint guarda só alguns\nestados e recalcula o resto", "motor", fs=23)
s.caixa(1070, 640, 470, 190, "🆚 Diferenças finitas\n2 simulações POR parâmetro\n(300 parâmetros = 600 simulações)", "qualidade", fs=23)

# =============================================================================
# 7. AeroJAX
s = Slide("AeroJAX")
s.cabecalho("AeroJAX: de onde veio a ideia", "Simulador 2D de aerodinâmica em JAX (Arno Meijer, licença LGPL v3)", "motor")
s.caixa(60, 210, 700, 460, "✅ O que aproveitamos (a arquitetura)\n\n• passo de tempo como função pura em JAX\n• estado da simulação como \"PyTree\"\n• laço no tempo com jax.lax.scan\n• simulação inteira diferenciável (jax.grad)\n• método da projeção de pressão\n• obstáculos por penalização de Brinkman", "fisica", fs=24, align="left", valign="top")
s.caixa(840, 210, 700, 460, "🛠️ O que precisou ser novo (climatização)\n\n• sala fechada, aberturas em qualquer parede\n• empuxo térmico: ar frio desce, quente sobe\n• transporte de umidade\n• cargas: pessoas, equipamentos, fachada\n• conforto: PMV, PPD, corrente de ar\n• interface, DXF e relatório", "projeto", fs=24, align="left", valign="top")
s.caixa(60, 710, 1480, 110, "ℹ️ O AeroJAX foi feito para escoamento externo (perfis NACA, cilindros). Ele foi estudado e rodado sem\nalterações — nada foi enviado ao repositório dele. O Clima2D reaproveita o jeito de construir, não o código.", "qualidade", fs=22, align="left")

# =============================================================================
# 8. Passo de tempo CFD
s = Slide("Um passo de CFD")
s.cabecalho("Por dentro de um passo de tempo (sala2d.py)", "Repetido ~40 mil vezes, cada um avançando 0,03–0,04 s", "fisica")
etapas = [("1 · Advecção", "o ar carrega calor e umidade\n(esquema TVD van Leer)", 600, 190),
          ("2 · Difusão + empuxo", "mistura turbulenta; ar frio\ndesce (Boussinesq)", 1040, 380),
          ("3 · Fontes", "pessoas, equipamentos,\nfachada, iluminação", 860, 620),
          ("4 · Projeção de pressão", "garante que não some nem\nsurge ar (Poisson por DCT)", 340, 620),
          ("5 · Contornos", "insuflamento, retorno,\nparedes sem escorregamento", 160, 380)]
ids = [s.caixa(x, y, 400, 150, f"{t}\n{d}", "fisica", fs=21) for t, d, x, y in etapas]
for a, b in zip(ids, ids[1:] + ids[:1]):
    s.seta(a, b, cor="#2f9e44", espessura=3)
s.caixa(620, 420, 360, 120, "🔁 próximo\npasso de tempo", "neutro", fs=24, forma="ellipse")
s.caixa(1180, 120, 380, 150, "Malha MAC: velocidades nas\nfaces das células; T, W e p\nno centro", "motor", fs=19, traco="dashed")

# =============================================================================
# 9. Psicrometria e conforto
s = Slide("Psicrometria e conforto")
s.cabecalho("Física do ar úmido e do conforto", "Módulos escritos para o Clima2D, todos diferenciáveis com JAX", "fisica")
s.caixa(60, 200, 720, 470, "💧 psicrometria.py  (ASHRAE Fundamentals)\n\n• pressão de saturação (Hyland-Wexler)\n• umidade absoluta ↔ relativa\n• ponto de orvalho, bulbo úmido, entalpia\n• mistura de ar externo + retorno\n• serpentina: ADP e fator de bypass\n• estado de insuflamento pelas cargas", "fisica", fs=24, align="left", valign="top")
s.caixa(820, 200, 720, 470, "🧍 conforto.py  (ISO 7730 / NBR 16401-2)\n\n• PMV: voto médio estimado\n   (-3 muito frio · 0 neutro · +3 muito quente)\n• PPD: % de pessoas insatisfeitas\n• DR: risco de corrente de ar\n   (\"vento gelado\" na pele)", "fisica", fs=24, align="left", valign="top")
s.caixa(60, 710, 1480, 110, "✔️ Validados contra: tabelas da ASHRAE · tabela D.1 da ISO 7730 · biblioteca de referência\npythermalcomfort · balanço de energia e umidade da própria simulação", "qualidade", fs=22, align="left")

# =============================================================================
# 10. Streamlit
s = Slide("Streamlit")
s.cabecalho("Streamlit: interface web escrita só em Python", "Sem HTML nem JavaScript: cada linha de Python vira um elemento na tela", "interface")
c1 = s.caixa(110, 230, 320, 120, "Você mexe num campo\nou clica num botão", "interface", fs=22)
c2 = s.caixa(560, 230, 320, 120, "app.py roda inteiro\nde cima a baixo", "interface", fs=22)
c3 = s.caixa(335, 450, 320, 120, "a tela é redesenhada\ncom os novos valores", "interface", fs=22)
s.seta(c1, c2)
s.seta(c2, c3)
s.seta(c3, c1)
s.texto(130, 610, "A ideia central: o script\ninteiro roda a cada interação.", fs=26, ff=TITULO)
s.codigo(980, 200, 560, 230, "vazao = st.number_input(\n    \"Vazão [m³/h]\", value=600)\nif st.button(\"▶ Simular\"):\n    r = simular_projeto(P)\nst.metric(\"PMV\", r[\"PMV\"])", fs=20)
s.caixa(980, 460, 560, 170, "🧠 st.session_state\nmemória que sobrevive às\nreexecuções: o projeto fica aqui", "interface", fs=22)
s.caixa(980, 660, 560, 170, "🔒 Roda no SEU computador\nlocalhost:8501 — nada vai\npara a internet", "qualidade", fs=22)

# =============================================================================
# 11. ezdxf
s = Slide("ezdxf")
s.cabecalho("ezdxf: lendo o desenho do AutoCAD", "DXF é um formato aberto de CAD; o ezdxf lê e escreve sem precisar do AutoCAD", "projeto")
etapas = ["Arquivo .dxf\nplanta ou corte", "Separa por layer\nAMBIENTE, INSUFLAMENTO,\nRETORNO, PESSOA...", "Caixa de cada\nentidade (bbox)",
          "Unidades\nmm / cm → m", "Corte 2D\nprojeta no eixo\nx ou y", "Tabelas do\nprojeto"]
ids = [s.caixa(40 + j * 260, 260, 225, 170, t, "projeto", fs=20) for j, t in enumerate(etapas)]
for a, b in zip(ids, ids[1:]):
    s.seta(a, b)
s.caixa(60, 500, 700, 320, "🗂️ Por que layers?\n\nO programa não \"entende\" o desenho como\numa pessoa. A convenção de layers diz o\nque cada linha é: o contorno do ambiente,\num difusor, uma pessoa, uma mesa.", "projeto", fs=22, align="left", valign="top")
s.onde(820, 500, 720, 320, "• importar_dxf.py: importar_corte e\n   importar_planta\n• a planta não tem alturas: pé-direito e\n   alturas dos difusores vêm da interface\n• gerar_exemplos cria os DXF de exemplo", "projeto")

# =============================================================================
# 12. Matplotlib e pandas
s = Slide("Matplotlib e pandas")
s.cabecalho("Matplotlib e pandas: números viram figura e tabela", "As duas bibliotecas mais usadas para mostrar resultados em Python", "graficos")
s.caixa(60, 200, 720, 380, "📈 Matplotlib — figuras\n\n• imshow: mapa de cores (temperatura, PMV...)\n• streamplot: linhas do escoamento do ar\n• contour: contorno da zona ocupada\n• savefig: PNG para o relatório e o manual", "graficos", fs=23, align="left", valign="top")
s.caixa(820, 200, 720, 380, "🧮 pandas — tabelas\n\n• DataFrame = uma planilha dentro do Python\n• tabelas editáveis da interface\n   (aberturas, fontes, obstáculos)\n• exporta CSV com \";\" e \",\" decimal,\n   pronto para o Excel em português", "graficos", fs=23, align="left", valign="top")
s.codigo(60, 620, 720, 200, "fig, ax = plt.subplots()\nax.imshow(T.T, origin=\"lower\", cmap=\"coolwarm\")\nax.streamplot(x, y, u, v)\nfig.savefig(\"sala.png\")", fs=20)
s.codigo(820, 620, 720, 200, "df = pd.DataFrame({\"x\": x, \"T\": T})\ndf.to_csv(\"campos.csv\", sep=\";\",\n          decimal=\",\")", fs=20)

# =============================================================================
# 13. pytest
s = Slide("pytest e validação")
s.cabecalho("pytest: como saber que o cálculo está certo", "Teste = uma afirmação verificável sobre o código", "qualidade")
niveis = [("Integração: importar DXF, projeto JSON, validação", 520, "qualidade"),
          ("Numérica: divergência nula · gradiente = diferenças finitas", 760, "motor"),
          ("Conservação: energia e umidade fecham em regime (±2 %)", 1000, "fisica"),
          ("Propriedades: tabelas ASHRAE e ISO 7730", 1240, "projeto")]
for j, (t, w, c) in enumerate(niveis):
    s.caixa(60 + (1240 - w) / 2, 200 + j * 115, w, 95, t, c, fs=22)
s.codigo(60, 690, 660, 140, "python -m pytest testes -q\n........................  23 passed", fs=22)
s.caixa(760, 690, 780, 140, "⚠️ Se você mudar o código e algum teste falhar,\no resultado das simulações não é mais confiável.", "alerta", fs=23, align="left")

# =============================================================================
# 14. Git e GitHub
s = Slide("Git e GitHub")
s.cabecalho("Git e GitHub: histórico e revisão", "Cada mudança fica registrada e só entra no principal com a sua aprovação", "qualidade")
g1 = s.caixa(60, 260, 260, 120, "Arquivos\nalterados", "neutro", fs=23)
g2 = s.caixa(420, 260, 260, 120, "Histórico local\n(commits)", "qualidade", fs=23)
g3 = s.caixa(780, 260, 330, 120, "GitHub: branch\nclaude/funny-planck-2g41pw", "qualidade", fs=20)
g4 = s.caixa(1250, 260, 290, 120, "main\n(só se você aceitar)", "fisica", fs=22)
s.seta(g1, g2, "commit")
s.seta(g2, g3, "push")
s.seta(g3, g4, "Pull Request #1\n+ merge")
glos = [("commit", "foto do projeto num\nmomento, com descrição"), ("branch", "linha de trabalho\nseparada da principal"),
        ("push", "envia os commits\npara o GitHub"), ("pull request", "pedido de revisão\nantes de juntar")]
for j, (t, d) in enumerate(glos):
    s.caixa(60 + j * 380, 450, 350, 160, f"{t}\n{d}", "qualidade", fs=21)
s.caixa(60, 660, 1480, 120, "🔒 AeroJAX original: apenas clonado para leitura. Nenhum commit foi enviado a ele.\nTudo foi para o SEU repositório allan01fr/allan01fr, num branch separado.", "fisica", fs=23, align="left")

# =============================================================================
# 15. Bastidores
s = Slide("Ferramentas de bastidor")
s.cabecalho("Ferramentas usadas para construir e conferir", "Não fazem parte do Clima2D, mas ajudaram a garantir que ele funciona", "qualidade")
bast = [("🤖 Playwright", "Navegador automático.\nAbriu a interface, clicou nos\nbotões, rodou a simulação e\ntirou as capturas do manual."),
        ("🌡️ pythermalcomfort", "Biblioteca de referência em\nconforto térmico. Usada só\npara conferir o nosso PMV."),
        ("✏️ Excalidraw + esbuild", "Esta apresentação: os slides\nsão gerados por um script e\nconvertidos pelo próprio\nExcalidraw."),
        ("💻 Claude Code", "Ambiente onde o código foi\nescrito, testado e enviado\npara o GitHub.")]
for j, (t, d) in enumerate(bast):
    s.caixa(60 + j * 380, 220, 350, 330, f"{t}\n\n{d}", "qualidade", fs=21, valign="top")
s.caixa(60, 600, 1480, 200, "🔍 Regra usada em todo o trabalho: nenhum número foi aceito sem conferência independente —\ntabela de norma, outra biblioteca, lei de conservação ou uma simulação mais longa.\nFoi assim que dois erros foram achados e corrigidos (otimização curta demais e NaN no gradiente).", "alerta", fs=22, align="left")

# =============================================================================
# 16. Trilha de estudo
s = Slide("Por onde começar")
s.cabecalho("Por onde começar a estudar", "Uma trilha de ~8 semanas, 1 a 2 horas por dia")
trilha = [("1", "Python básico", "1-2 sem", "qualidade"), ("2", "NumPy", "1 sem", "motor"),
          ("3", "Matplotlib +\npandas", "1 sem", "graficos"), ("4", "JAX: jit,\ngrad, scan", "1 sem", "motor"),
          ("5", "Psicrometria e\nconforto no código", "1 sem", "fisica"), ("6", "CFD: ler\nsala2d.py", "2 sem", "fisica"),
          ("7", "Streamlit: mudar\na interface", "1 sem", "interface")]
ids = []
for j, (n, t, d, c) in enumerate(trilha):
    y = 230 if j % 2 == 0 else 400
    ids.append(s.caixa(50 + j * 215, y, 190, 140, f"{n}. {t}\n({d})", c, fs=20))
for a, b in zip(ids, ids[1:]):
    s.seta(a, b, traco="dashed")
s.caixa(60, 600, 1480, 200, "📚 Material\n\n• Python: docs.python.org/pt-br/3/tutorial      • NumPy: numpy.org/doc      • JAX: jax.readthedocs.io (\"JAX 101\")\n• Streamlit: docs.streamlit.io      • ezdxf: ezdxf.mozman.at      • Matplotlib: matplotlib.org\n• CFD: Ferziger & Perić, Computational Methods for Fluid Dynamics      • No repositório: README.md, módulos 0 a 5", "neutro", fs=20, align="left", valign="top")


def esqueleto_completo():
    tudo = []
    for sl in slides:
        tudo += sl.esqueleto()
    return tudo


if __name__ == "__main__":
    destino = os.path.join(os.path.dirname(__file__), "esqueleto.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(esqueleto_completo(), f, ensure_ascii=False)
    print(f"{len(slides)} slides -> {destino}")
