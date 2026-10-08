# -*- coding: utf-8 -*-
# Digitalização dos dutos da prancha "PLANTA BAIXA SUBSOLO COZINHA DUTOS EXAUSTÃO — AS BUILT PARA ADEQUAÇÕES"
# (Kaptek, Fase 2, 27/08/2026, esc. 1:35 — Anexo D do PA-COZINHA-003). Coordenadas em pt da folha (origem canto
# sup. esq.), eixo do duto obtido como linha média das duas linhas paralelas do vetor (camadas: laranja = exaustão,
# magenta/azul = insuflamento, cinza = ar exterior, vermelho = removido/refazer).
# Seção: W = largura medida no vetor (confere com o rótulo); H = o outro número do rótulo.
# Campos: id, sistema, rotulo, W, H, pontos [(x,y)...], status, nota
DUTOS = [
    # ---------------- Exaustão 3 (VM-COZ03): lavadoras + forno -> coletor do corredor norte -> prumada E-90x40
    dict(id="E3-01", sis="EXA", exaustor="VM-COZ03", rot="EC-30x40", W=0.30, H=0.40, pts=[(362.5, 702.0), (432.3, 702.0), (432.3, 352.4)],
         status="PENDENTE", nota="Trecho em vermelho tracejado: 'EC- duto de exaustão em chapa de aço preta removido / refazer' (legenda). Liga a coifa da lavadora ao coletor."),
    dict(id="E3-02", sis="EXA", exaustor="VM-COZ03", rot="EC-30x40", W=0.30, H=0.40, pts=[(432.3, 352.4), (432.3, 302.8), (1095.1, 302.8)], status="EXTRAÍDO",
         nota="Coletor no corredor norte (linhas laranja y=290,6 e 314,9 pt)."),
    dict(id="E3-03", sis="EXA", exaustor="VM-COZ03", rot="EC-50x40", W=0.50, H=0.40, pts=[(1095.1, 310.9), (1764.6, 310.9), (1764.6, 441.0)], status="EXTRAÍDO",
         nota="Coletor (y=290,6 e 331,1 pt) e descida em planta até o encontro com o EC-90x40."),
    dict(id="E3-04", sis="EXA", exaustor="VM-COZ03", rot="EC-90x40", W=0.90, H=0.40, pts=[(1780.8, 441.0), (1780.8, 753.4)], status="EXTRAÍDO",
         nota="Linhas x=1744,3 e 1817,2 pt; interrompidas onde cruzam o ar exterior e o insuflamento (passa por baixo)."),
    dict(id="E3-05", sis="EXA", exaustor="VM-COZ03", rot="EC-40x40", W=0.40, H=0.40, pts=[(2050.7, 416.7), (1817.2, 416.7)], status="EXTRAÍDO",
         nota="Ramal da coifa sobre os caldeirões (captor em x=2050,7–2083,1 pt)."),
    # ---------------- Exaustão 2 (VM-COZ02): coifa C (parede) -> coletor -> prumada E-60x50
    dict(id="E2-01", sis="EXA", exaustor="VM-COZ02", rot="EC-60x50", W=0.50, H=0.60, pts=[(1170.5, 416.7), (1660.8, 416.7)], status="EXTRAÍDO",
         nota="Coletor sobre a coifa de parede (y=396,4 e 437,0 pt); largura medida 0,50 m, altura adotada 0,60 m (rótulo EC-60x50)."),
    dict(id="E2-02", sis="EXA", exaustor="VM-COZ02", rot="EC-60x50", W=0.60, H=0.50, pts=[(1660.8, 416.7), (1660.8, 757.4)], status="EXTRAÍDO",
         nota="Linhas x=1636,5 e 1685,1 pt até a caixa da prumada (737,1–777,6 pt)."),
    # ---------------- Exaustão 1 (VM-COZ01): coifa A (ilha, fogões) -> prumada E-70x50
    dict(id="E1-01", sis="EXA", exaustor="VM-COZ01", rot="EC-50x30", W=0.50, H=0.30, pts=[(1230.7, 757.4), (1441.7, 757.4)], status="EXTRAÍDO",
         nota="Plenum/coletor sobre a coifa A (y=737,1 e 777,6 pt) até a caixa da prumada E-70x50 (x=1413,3–1470,0 pt)."),
    # ---------------- Exaustão geral E- (gelo / corredor) -> prumada E-85x50
    dict(id="EG-01", sis="EXG", exaustor="não identificado", rot="E-85x50", W=0.85, H=0.50, pts=[(1859.7, 757.4), (1859.7, 890.8)], status="EXTRAÍDO",
         nota="Duto E- (exaustão geral) x=1825,3–1894,1 pt; a jusante alarga em transição para o corredor sul."),
    dict(id="EG-02", sis="EXG", exaustor="não identificado", rot="E-20x15", W=0.20, H=0.15, pts=[(2218.4, 760.0), (2218.4, 1013.5), (1918.5, 1013.5), (1859.7, 890.8)], status="INFERIDO",
         nota="Grelhas do Gelo (E-20x15, x=2210,3–2226,5 pt) até o duto do corredor; o trecho do corredor e a transição até o E-85x50 foram simplificados."),
    # ---------------- Insuflamento (I-)
    dict(id="I-01", sis="INS", rot="I-50x40", W=0.50, H=0.40, pts=[(643.5, 528.9), (959.1, 528.9)], status="EXTRAÍDO", nota="Linhas magenta y=508,7 e 549,1 pt."),
    dict(id="I-02", sis="INS", rot="I-50x50", W=0.50, H=0.50, pts=[(959.1, 528.9), (1128.6, 528.9)], status="EXTRAÍDO", nota="Continuação em azul (mesma largura)."),
    dict(id="I-03", sis="INS", rot="I-30x50", W=0.30, H=0.50, pts=[(1128.6, 541.1), (1361.7, 541.1)], status="EXTRAÍDO", nota="Linhas azuis y=529,0 e 553,2 pt."),
    dict(id="I-04", sis="INS", rot="I-50x40", W=0.50, H=0.40, pts=[(643.5, 528.9), (643.5, 780.9)], status="EXTRAÍDO", nota="Linhas magenta x=623,2 e 663,8 pt."),
    dict(id="I-05", sis="INS", rot="I-25x40", W=0.25, H=0.40, pts=[(643.5, 780.9), (643.5, 890.5), (412.8, 890.5)], status="EXTRAÍDO", nota="Redução e ramal I-25x40 (y=880,3 e 900,6 pt) até a lavagem."),
    dict(id="I-06", sis="INS", rot="I-80x50", W=0.80, H=0.50, pts=[(1120.5, 549.1), (1120.5, 761.7)], status="EXTRAÍDO", nota="Linhas x=1088,1 e 1152,9 pt; termina em caixa com X (descida/prumada)."),
    dict(id="I-07", sis="INS", rot="I-65x50", W=0.65, H=0.50, pts=[(1572.1, 757.4), (1572.1, 818.1)], status="EXTRAÍDO", nota="Caixa com X 1545,8–1598,3 pt (prumada) e transição."),
    dict(id="I-08", sis="INS", rot="I-40x40", W=0.40, H=0.40, pts=[(1555.8, 818.1), (1555.8, 938.9)], status="EXTRAÍDO", nota="Linhas x=1539,6 e 1572,0 pt."),
    dict(id="I-09", sis="INS", rot="I-35x40", W=0.35, H=0.40, pts=[(1555.8, 938.9), (999.0, 938.9)], status="EXTRAÍDO", nota="Linhas y=924,7 e 953,1 pt."),
    dict(id="I-10", sis="INS", rot="I-55x40", W=0.55, H=0.40, pts=[(1714.8, 568.1), (1714.8, 793.9)], status="EXTRAÍDO", nota="Linhas x=1692,5 e 1737,0 pt."),
    dict(id="I-11", sis="INS", rot="I-40x40", W=0.40, H=0.40, pts=[(1714.8, 793.9), (1714.8, 842.5), (1572.1, 842.5)], status="EXTRAÍDO", nota="Redução e ramal (y=826,3 e 858,6 pt)."),
    dict(id="I-12", sis="INS", rot="I-35x30", W=0.35, H=0.30, pts=[(1714.8, 651.8), (2079.9, 651.8)], status="EXTRAÍDO", nota="Linhas y=637,6 e 666,0 pt."),
    dict(id="I-13", sis="INS", rot="I- (sem rótulo)", W=0.50, H=0.40, pts=[(1181.3, 761.7), (1181.3, 956.1)], status="INFERIDO",
         nota="Duto magenta x=1161,0–1201,5 pt sem rótulo próprio; altura 0,40 m adotada."),
    # ---------------- Ar exterior / compensação (AE-)
    dict(id="AE-01", sis="AEX", rot="AE-70x30", W=0.70, H=0.30, pts=[(971.2, 536.2), (1722.3, 536.2)], status="EXTRAÍDO",
         nota="Linhas cinza y≈500–572 pt (com flanges); largura do rótulo."),
    dict(id="AE-02", sis="AEX", rot="AE-40x30", W=0.40, H=0.30, pts=[(1722.3, 536.2), (1771.0, 536.2), (2095.3, 536.2)], status="EXTRAÍDO",
         nota="Transição 1722,3–1771,0 pt e duto y=520,1–552,4 pt."),
    dict(id="AE-03", sis="AEX", rot="AE-55x25", W=0.55, H=0.25, pts=[(1249.5, 536.2), (1249.5, 718.6)], status="EXTRAÍDO",
         nota="Descida de ar de compensação para a coifa A (x=1227,2–1271,8 pt)."),
    dict(id="AE-04", sis="AEX", rot="AE-55x25", W=0.55, H=0.25, pts=[(1375.9, 536.2), (1375.9, 719.4)], status="EXTRAÍDO",
         nota="Descida de ar de compensação para a coifa A (x=1353,6–1398,1 pt)."),
]
# Prumadas (caixas com X = duto vertical). x, y (centro), W x H, ligação
PRUMADAS = [
    dict(id="PR-E1", sis="EXA", exaustor="VM-COZ01", rot="E-70x50", W=0.70, H=0.50, x=1441.7, y=757.4, status="EXTRAÍDO",
         nota="Caixa 1413,3–1470,0 × 737,2–777,6 pt = 0,70 × 0,50 m, igual à seção da prumada da Exaustão 1 no fluxograma."),
    dict(id="PR-E2", sis="EXA", exaustor="VM-COZ02", rot="E-60x50", W=0.60, H=0.50, x=1660.8, y=757.4, status="EXTRAÍDO",
         nota="Caixa 1636,5–1685,1 × 737,1–777,6 pt = 0,60 × 0,50 m (fluxograma: E-60x50)."),
    dict(id="PR-E3", sis="EXA", exaustor="VM-COZ03", rot="E-90x40", W=0.90, H=0.40, x=1780.8, y=753.4, status="EXTRAÍDO",
         nota="Caixa 1744,3–1817,2 × 737,2–769,6 pt = 0,90 × 0,40 m (fluxograma: E-90x40)."),
    dict(id="PR-EG", sis="EXG", exaustor="não identificado", rot="E-85x50", W=0.85, H=0.50, x=1859.7, y=757.4, status="EXTRAÍDO",
         nota="Caixa 1825,3–1894,1 × 737,2–777,6 pt; exaustor não identificado nas pranchas disponíveis."),
    dict(id="PR-I1", sis="INS", exaustor="AC-COZ01", rot="I-80x50", W=0.80, H=0.50, x=1120.5, y=761.7, status="EXTRAÍDO",
         nota="Caixa com X 1088,1–1152,9 pt; associação ao AC-COZ01 INFERIDA (fluxograma: 2 unidades de insuflamento)."),
    dict(id="PR-I2", sis="INS", exaustor="AC-COZ02", rot="I-65x50", W=0.65, H=0.50, x=1572.1, y=757.4, status="EXTRAÍDO",
         nota="Caixa com X 1545,8–1598,3 pt; associação ao AC-COZ02 INFERIDA."),
    dict(id="PR-AE", sis="AEX", exaustor="VM-COZ05/06", rot="AE-100x40", W=1.00, H=0.40, x=971.2, y=536.2, status="INFERIDO",
         nota="Extremidade do AE-70x30 junto às setas SOBE/DESCE do corredor; descida do ar exterior (fluxograma: AE-100x40 de VM-COZ05/06) adotada neste ponto."),
]
# Captores / descidas para as coifas (caixas pequenas), em pt
CAPTORES = [
    dict(id="CP-A1", coifa="A", x=1255.0, y=800.4, W=0.50, H=0.30, sis="EXA", nota="Caixa 1234,7–1275,2 × 788,2–812,6 pt (EC-50x30)."),
    dict(id="CP-A2", coifa="A", x=1375.9, y=800.4, W=0.50, H=0.30, sis="EXA", nota="Caixa 1355,6–1396,1 × 788,2–812,6 pt (EC-50x30)."),
    dict(id="CP-C1", coifa="C", x=1196.9, y=412.6, W=0.30, H=0.25, sis="EXA", nota="Caixa azul com X 1186,7–1207,0 pt (4× E-30x25 no fluxograma)."),
    dict(id="CP-C2", coifa="C", x=1331.6, y=412.6, W=0.30, H=0.25, sis="EXA", nota="Caixa 1321,4–1341,7 pt."),
    dict(id="CP-C3", coifa="C", x=1466.3, y=412.6, W=0.30, H=0.25, sis="EXA", nota="Caixa 1456,1–1476,4 pt."),
    dict(id="CP-C4", coifa="C", x=1601.0, y=412.6, W=0.30, H=0.25, sis="EXA", nota="Caixa 1590,8–1611,1 pt."),
    dict(id="CP-D1", coifa="D", x=2066.9, y=416.7, W=0.40, H=0.40, sis="EXA", nota="Captor 2050,7–2083,1 pt na ponta do EC-40x40."),
    dict(id="CP-E1", coifa="E1", x=362.5, y=702.0, W=0.30, H=0.30, sis="EXA", nota="Caixa vermelha com X (trecho removido)."),
    dict(id="CP-AE1", coifa="A", x=1249.5, y=718.6, W=0.55, H=0.25, sis="AEX", nota="Chegada do ar de compensação na coifa A (caixa azul 1227,2–1271,8 pt)."),
    dict(id="CP-AE2", coifa="A", x=1375.9, y=719.4, W=0.55, H=0.25, sis="AEX", nota="Chegada do ar de compensação na coifa A (caixa azul 1353,6–1398,1 pt)."),
]
# Grelhas / difusores (quadrados vinho com X), em pt
DIFUSORES = [
    (767.6, 656.2, 0.60), (767.6, 816.5, 0.60), (1457.1, 656.1, 0.60), (1114.7, 886.9, 0.60), (1421.6, 886.9, 0.60),
    (1683.6, 886.9, 0.60), (2049.6, 583.4, 0.60), (2049.6, 913.5, 0.60), (1873.8, 588.4, 0.60), (435.2, 761.7, 0.47),
]
