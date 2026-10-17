# Cálculo 1D da rede de dutos — cozinha de banquetes (subsolo)

Vazão, velocidade e perda de carga de cada duto do modelo (`saida/modelo.json`), com Darcy-Weisbach e coeficientes K de singularidades. É um cálculo de verificação de projeto, não de fabricação: tudo que o desenho não traz está listado em **Premissas** e marcado INFERIDO. Arquivos: `calculo_dutos.csv` (por duto), `calculo_ventiladores.csv` (por ventilador), `calculo_dutos.json` (para o visualizador).

## Exaustão: pressão que cada ventilador precisa vencer

Cenário 1 = vazão das coifas da prancha de 2006; cenário 2 = vazão de placa do ventilador (coifas proporcionalmente ajustadas). Pressão total = maior caminho coifa→ventilador (atrito, singularidades e perda de coifa com filtros) + descarga até a cobertura. Faixa = caso baixo – alto.

| Ventilador | Placa (m³/h) | Coifas (m³/h) | Placa/coifas | Veloc. na prumada, cenário 1 / 2 (m/s) | Pressão, cenário 1 (Pa) | Pressão, cenário 2 (Pa) | Caminho crítico |
|---|---:|---:|---:|---:|---|---|---|
| VM-COZ01 | 15.200 | 13.247 | 1,15 | 10,5 / 12,1 | **625** (352–1.156) | **782** (437–1.458) | D-EXA-SS-016 |
| VM-COZ02 | 15.200 | 10.189 | 1,49 | 9,4 / 14,1 | **304** (185–526) | **520** (311–924) | D-EXA-SS-020 |
| VM-COZ03 | 9.600 | 10.575 | 0,91 | 8,2 / 7,4 | **304** (194–510) | **273** (174–455) | D-EXA-SS-022 |

Os ventiladores não têm curva nem pressão de placa no modelo; falta confrontar esses números com o catálogo (GTS 560-9 etc.).

## Achados

1. **Coletor da coifa A (D-EXA-SS-011, EC-50x30) estrangula a Exaustão 1.** Como desenhado, o trecho final leva as duas descidas somadas: 13.247 m³/h a 24,5 m/s (cenário 1) e 28,1 m/s (placa); a vazão máxima a 12,5 m/s nessa seção seria 6.750 m³/h. As duas descidas EC-50x30 já ficam em 12,3 m/s. Só esse trecho responde por cerca de 306 Pa dos 625 Pa requeridos; com a seção da prumada (0,70 × 0,50) a pressão cairia para 318 Pa. O rótulo EC-50x30 pode referir-se só aos captores: **medir o coletor em campo**.
2. **Exaustão 2: a prumada E-60x50 passa de 12,5 m/s se o ventilador entregar a vazão de placa.** Com 15.200 m³/h: 14,1 m/s; com a vazão da coifa C da prancha de 2006 (10.189 m³/h): 9,4 m/s. Os 13,28 m/s e 17,15 m/s do relatório (DIV-013) correspondem a 14.342 e 18.522 m³/h nessa seção. Vazão máxima a 12,5 m/s: 13.500 m³/h.
3. **Exaustão 3: as coifas somam 10.575 m³/h e o ventilador GTS 560-9 entrega 9.600 m³/h** (91 % da soma, antes de considerar a curva). A coifa B não tem ligação desenhada e a E2 depende do ramal removido (DIV-009).
4. **Dutos de exaustão acima de 12,5 m/s no cenário 1:** D-EXA-SS-011 (EC-50x30, 24,5 m/s). **No cenário 2 (placa), mais 10 trechos**, a 14,1 m/s: SS-009, SS-010, SS-013, SH-002, SS-015, SS-016, SS-017, SS-018, SS-019, SS-020 (toda a Exaustão 2 e as descidas da coifa A, que sobem 1,15x e 1,49x quando o ventilador entrega a vazão de placa).
5. **Balanço de ar.** Exaustão das coifas 34.010 m³/h (placa dos três ventiladores: 40.000); insuflamento 18.000 + ar exterior 13.000 = 31.000 m³/h. Reposição/exaustão: 91 % (coifas) ou 78 % (placa). Não inclui a exaustão geral (exaustor não identificado, DIV-011) nem infiltração.
6. **Ar exterior: o AE-70x30 (D-AEX-SS-001) leva 13.000 m³/h a 17,2 m/s** se os dois ventiladores (VM-COZ05/06, AE-100x40 a 9,0 m/s na prumada) alimentarem só essa rede; a 9 m/s essa seção comporta 6.804 m³/h. Ou parte do ar exterior segue por outra rede fora do recorte, ou a seção está subdimensionada (a associação da prumada AE a esta rede é INFERIDA). Insuflamento/ar exterior acima de 10 m/s (referência usual): D-INS-SS-005 (I-25x40, 12,5 m/s); D-INS-SS-013 (I-40x40, 10,4 m/s); D-INS-SS-014 (I-35x30, 11,9 m/s); D-AEX-SS-001 (AE-70x30, 17,2 m/s); D-AEX-SS-002 (AE-40x30, 10,0 m/s); D-AEX-SS-003 (AE-40x30, 10,0 m/s).

## Insuflamento e ar exterior (perda só nos dutos, sem difusor, filtro nem serpentina)

| Rede | Vazão (m³/h) | Pressão nos dutos, base (Pa) (baixo–alto) | Maior velocidade | Caminho crítico |
|---|---:|---|---|---|
| Insuflamento — AC-COZ01 | 9.000 | 183 (103–345) | 12,5 m/s (D-INS-SS-005) | DIF-02 |
| Insuflamento — AC-COZ02 | 9.000 | 188 (105–354) | 11,9 m/s (D-INS-SS-014) | DIF-09 |
| Ar exterior (igual por terminal) — VM-COZ05 + VM-COZ06 | 13.000 | 337 (188–636) | 17,2 m/s (D-AEX-SS-001) | D-AEX-SS-007 |
| Ar exterior (tudo nas descidas da coifa A) — VM-COZ05 + VM-COZ06 | 13.000 | 382 (214–716) | 17,2 m/s (D-AEX-SS-001) | D-AEX-SS-007 |

As derivações para os difusores não estão desenhadas: cada difusor foi ligado ao duto de insuflamento mais próximo (distâncias em `calculo_dutos.json`/abaixo). A vazão nos ramais depende dessa hipótese; a do tronco (prumada) não.

Difusores mais distantes do duto de ligação adotado: DIF-08 → D-INS-SS-014 (3,2 m), DIF-03 → D-INS-SS-003 (1,8 m), DIF-10 → D-INS-SS-006 (1,6 m).

## Vazão específica das coifas (consistência da prancha de 2006)

| Coifa | Vazão (m³/h) | Área em planta (m²) | m³/h por m² | Velocidade de face (m/s) |
|---|---:|---:|---:|---:|
| COIFA-A | 13.247 | 5,81 | 2.280 | 0,63 |
| COIFA-C | 10.189 | 6,98 | 1.459 | 0,41 |
| COIFA-B | 2.462 | 1,69 | 1.459 | 0,41 |
| COIFA-D | 5.713 | 3,92 | 1.459 | 0,41 |
| COIFA-E1 | 1.200 | 0,81 | 1.481 | 0,41 |
| COIFA-E2 | 1.200 | 0,81 | 1.481 | 0,41 |

B, C, D e E seguem a mesma regra (≈ 0,41 m/s sobre a área em planta); a coifa A (ilha) usa ≈ 0,63 m/s.

## Premissas e parâmetros

- Vazão de cada coifa = valor do texto da prancha de 2006 (m³/min), dividida igualmente entre os captores desenhados.
- Coifas E1 e E2 (20 m³/min cada) saem pelo mesmo captor CP-E1 (ramal removido, a refazer); só um captor foi desenhado.
- Coifa B (forno elétrico) não tem ligação desenhada: derivação adotada no coletor da Exaustão 3 mais próximo da coifa; a perda do ramal próprio não é contada.
- Insuflamento: vazão de cada ventilador dividida igualmente entre os difusores ligados à sua rede; cada difusor liga ao duto de insuflamento mais próximo (a ligação não está desenhada). Pontas com 'tampa' ficam sem vazão.
- Ar exterior: vazão dividida igualmente entre as duas descidas da coifa A e a ponta que segue fora do recorte (AE-02).
- Singularidades (cotovelos, tês, transições) deduzidas da geometria; construção real (raio, aletas) não consta no desenho: K varia de 0,5x a 2x entre os casos baixo/alto.
- Perda da coifa com filtros adotada em 125 Pa (80–200 Pa); curva e pressão do ventilador não constam do modelo, então a pressão requerida não é comparada com a de placa.
- Insuflamento e ar exterior: perda só nos dutos (sem difusor, filtro, serpentina nem registro).
- Ar a 20 °C: ρ = 1,20 kg/m³, μ = 1,81·10⁻⁵ Pa·s. Atrito: Darcy-Weisbach com Colebrook e diâmetro hidráulico; rugosidade 0,09 / 0,15 / 0,30 mm (baixo/base/alto).
- K base: cotovelo 90° 0,6, derivação 0,8, passante 0,1, redução 0,1, saída livre 1,0; multiplicadores 0,5× / 1× / 2× nos casos baixo / base / alto. Perda da coifa com filtros: 80 / 125 / 200 Pa.
- Critérios: 12,5 m/s é o limite citado no relatório PA-COZINHA-003 (DIV-013). Os 7,5 m/s de piso na exaustão foram **adotados e precisam ser confirmados na NBR 14518 vigente**; os 10 m/s para insuflamento são só referência usual.
- Alturas, shafts e descargas seguem as premissas P12–P13 do modelo (traçado acima do térreo INFERIDO, sem cotovelos).
