# LEED v5 BD+C: créditos que dependem de cálculos de HVAC-R e o que a suíte precisa calcular

**Projeto:** suíte de engenharia HVAC-R da KAPTEK (Rio de Janeiro)
**Data da pesquisa:** 08/11/2026
**Escopo:** LEED v5 BD+C (New Construction e Core & Shell), com as diferenças relevantes em relação ao v4.1

---

## 0. Limitações desta pesquisa (leia primeiro)

1. **Rede bloqueada.** Nesta sessão, `usgbc.org`, `ashrae.org`, `leeduser.buildinggreen.com`, `cagbc.org` e `gbcbrasil.org.br` estavam bloqueados pelo proxy, com erro 403 no CONNECT. Não deu para abrir nenhum PDF oficial. Tudo o que está aqui veio de trechos e resumos devolvidos pela ferramenta de busca (WebSearch), que leu essas páginas indiretamente. A cota de buscas da sessão acabou antes do fim do levantamento.
2. **Qual documento é o vigente.** A edição mais recente que encontrei é o PDF oficial *LEED v5 BD+C Rating System – July 2026 Edition*: https://www.usgbc.org/sites/default/files/2026-07/LEED%20v5%20BD+C%20Rating%20System_July%202026.pdf. Antes dela houve a edição de novembro de 2025 (https://www.usgbc.org/sites/default/files/2025-10/LEED%20v5%20BD+C%20Rating%20System_November%202025_clean.pdf) e o *Reference Guide* "Launch Edition" de abril de 2025 (cópia não oficial no Scribd: https://www.scribd.com/document/855773644/LEED-v5-BD-C-Reference-Guide-Launch-Edition). **Antes de codificar qualquer regra, baixe a edição de julho de 2026 e o Reference Guide atual.**
3. **Legenda de confiabilidade usada no texto:**
   - **[C]** confirmado por fonte primária (USGBC ou ASHRAE) ou por duas fontes secundárias concordantes, com a URL indicada.
   - **[S]** fonte secundária única (consultoria, fabricante ou LEEDuser).
   - **[M]** conhecimento prévio do texto das normas (ASHRAE 90.1/62.1/55, LEED v4), **não verificado on-line nesta sessão**.
   - **[?]** não confirmado ou com fontes em conflito.

---

## 1. Visão geral: o que mudou do v4.1 para o v5 em HVAC-R

| Tema | LEED v4.1 | LEED v5 BD+C |
|---|---|---|
| Norma de energia | ASHRAE 90.1-2016, Apêndice G | ASHRAE 90.1-2019 para projetos registrados até 31/12/2027; **90.1-2022** obrigatória a partir de 01/01/2028 [S] (Arlington County, mar/2026: https://www.arlingtonva.us/files/sharedassets/public/v/1/departments/documents/aire/20260324_arlington-county-leedv5-update-webinar.pdf ; https://www.buildingenclosureonline.com/blogs/14-the-be-blog-building-enclosure/post/94899-leed-v5-and-the-cost-impacts-of-ashrae-standard-901-2019) |
| Métrica do desempenho energético | Custo de energia **e** emissões de GHG (média das duas) [S] (https://www.usgbc.org/node/7487846) | **"Future source energy"** (energia primária futura), com fator elétrico site→source = **2,0** e BPFs da Tabela 4.2.1.1 substituídos [S] (LEEDuser NC-v5 EAp2: https://leeduser.buildinggreen.com/credit/NC-v5/EAp2 ; CI-v5 EAp2: https://leeduser.buildinggreen.com/credit/CI-v5/EAp2) |
| Pontos de eficiência | Optimize Energy Performance, até 18 pts | EAc3 Enhanced Energy Efficiency: **1–10 pts (NC)** e **1–7 pts (CS)** [C] (https://leeduser.buildinggreen.com/credit/NC-v5/EAc3 ; https://leeduser.buildinggreen.com/credit/CS-v5/EAc3) |
| Carbono operacional | não existia | **EAp1** Operational Carbon Projection & Decarbonization Plan, com projeção de 25 anos que inclui vazamento de refrigerante [S] |
| Cargas de pico | não existia | **EAc2 Reduce Peak Thermal Loads** (cálculo de pico de aquecimento e resfriamento incluindo ventilação) [S] |
| Eletrificação | não existia | **EAc1 Electrification**: 5 pts NC / 4 pts CS [S] |
| Refrigerante, pré-requisito | Proibido CFC | Proibido HCFC, **inventário** de refrigerantes, **avaliar alternativas quando GWP > 700**, teste de vazamento [S] |
| Refrigerante, crédito | 1 pt; fórmula LCGWP/LCODP ≤ 100 (IP) ou ≤ 13 (SI) | **2 pts**; GWP médio ponderado comparado a *benchmarks* por tipo de equipamento, detecção automática de vazamento etc. [S] |
| Ventilação | 62.1-2016 (v4.1); 62.1-2010 (v4) | **62.1-2022**, seções 5 e 6 (VRP ou IAQP), filtro **MERV 13 / ePM1 50%** no pré-requisito [S] |
| Conforto térmico | Crédito próprio (ASHRAE 55) | Opção dentro de **EQc2 Occupant Experience** (ASHRAE **55-2023**) [S] |

Calendário: segundo uma fonte secundária, desde 01/07/2026 só é possível registrar projetos no LEED v5 [S] (https://clearvue.business/leed-v5-explained-a-practical-guide-to-the-new-green-building-rating-system/). Isso precisa ser confirmado na USGBC [?].

---

## 2. Energia e Atmosfera (EA)

### 2.1 EAp1 – Operational Carbon Projection and Decarbonization Plan (pré-requisito)

- **Requisito.** Estimar o consumo anual de energia **no ponto de uso (site), separado por energético** (eletricidade, gás etc.) e enviá-lo à USGBC. A USGBC gera uma **projeção de 25 anos** a partir desse consumo, dos dados da rede elétrica e da localização do projeto. Em seguida a equipe elabora um **plano de descarbonização de 25 anos**, que o proprietário precisa atestar [S] (https://leeduser.buildinggreen.com/credit/NC-v5/EAp1 ; https://leeduser.buildinggreen.com/credit/CS-v5/EAp1).
- **O que entra no carbono operacional:** HVAC, iluminação, cargas de processo e tomadas, água e **vazamento de refrigerante** [S] (Trane Engineers Newsletter ADM-APN099: https://www.trane.com/content/dam/trane-commercial/global/north-america/en/document/engineers-newsletter/ADM-APN099-EN.pdf).
- **Caminho alternativo:** quem obtém 4 ou 5 pontos em EAc1 Electrification pode seguir esse caminho em vez da projeção [S] (LEEDuser CS-v5 EAp1).
- **Jurisdições com norma de desempenho baseada em carbono (BPS):** é preciso fazer uma projeção BAU sobreposta aos limites da norma local, com estimativa das multas [S] (https://www.swinter.com/leed-v5-decarbonization-requirements/). Não se aplica ao Rio de Janeiro, onde não existe BPS de carbono [M].
- **Relação com outros itens:** o crédito IPp3 / Carbon Assessment junta as projeções de 25 anos de carbono operacional (EAp1), de refrigerante (pré-requisito de refrigerante) e de carbono incorporado (MRp2) [S] (https://leeduser.buildinggreen.com/credit/NC-v5/IPp3).
- **O que a suíte precisa calcular:** consumo anual por energético (saída da simulação 8760), carga anual de refrigerante e vazamento anual em kg e tCO2e (cobrado no inventário do pré-requisito de refrigerante) e cenários de retrofit e eletrificação ao longo de 25 anos. Esse último é útil para o módulo de CAPEX/OPEX. O formato exato do envio à USGBC não foi confirmado: plataforma LEED Online ou Arc [?].

### 2.2 EAp2 – Minimum Energy Efficiency (pré-requisito)

- **Intenção:** atingir um nível mínimo de eficiência para reduzir os danos do consumo excessivo de energia e das emissões de GHG [S] (LEEDuser NC-v5 EAp2).
- **Norma de referência:**
  - ASHRAE 90.1-2019 para projetos registrados **antes de 01/01/2028**;
  - 90.1-2022 obrigatória depois dessa data [S] (Arlington 2026; LEEDuser).
  - O texto do v5 manda **substituir os BPFs da Tabela 4.2.1.1 da 90.1-2022** por BPFs derivados para a métrica de *future source energy*. Também permite documentar energia *site* ou *source* pelo **Apêndice Informativo I da 90.1-2022**, que trata de avaliar o Apêndice G com métricas diferentes de custo [S] (LEEDuser NC-v5 EAp2; ASHRAE: https://www.ashrae.org/file%20library/about/government%20affairs/advocacy%20toolkit/virtual%20packet/standard-90.1-2022-fact-sheet.pdf).
- **Opções:**
  - **Prescritiva:** cumprir a 90.1 seções 5 a 10 (envoltória, HVAC, SHW, potência, iluminação, outros), com seus requisitos obrigatórios e prescritivos. O Reference Guide do ID+C cita "Sections 5–11" [S] (https://www.scribd.com/document/855773520/LEED-v5-ID-C-Reference-Guide-Launch-Edition-1). A seção 11 da 90.1-2022 é a de *energy credits* adicionais [M].
  - **Desempenho:** Apêndice G (*Performance Rating Method*), demonstrando redução percentual de *future source energy* [S] (mesma fonte; https://docs.betterbuilding.io/support-and-training/other-support/faqs/leed/leed-minimum-energy-performance-v4.1-vs-v5.0).
- **Métricas:**
  - O Reference Guide (abr/2025) explica que *future source energy* prioriza eficiência. Explica também que **as métricas de GHG e de "code compliance" (PCI/custo) não se aplicam ao EAc3**, porque a redução de GHG já é premiada em EAc1 e EAc4 [S] (Scribd BD+C RG).
  - Isso indica que o **EAp2 ainda exige conformidade de código pelo Apêndice G (Performance Cost Index ≤ PCIt)** e, provavelmente, também verificação de GHG [?]. O webinar de Arlington lista **site energy, source energy, custo e carbono** como métricas do v5 [S].
  - **O percentual mínimo exato do EAp2 v5 não foi confirmado** [?]. Para comparação: no v4.1 o mínimo era 5% (NC). Uma atualização de março de 2024 do v4 subiu o mínimo para 10% sobre a 90.1-2010 [S] (https://www.buildings.com/articles/29033/usgbc-increases-leed-energy-performance-requirements).
- **Envoltória:** fontes mencionam uma "precondição de envoltória" e um *envelope performance factor* do Apêndice C da 90.1, em que o proposto não pode exceder o baseline [S] (CalBEM: https://calbem.ibpsa.us/?p=3524 ; Scribd RG).
- **Requisitos da simulação**, todos [M], da ASHRAE 90.1 seção G2.2. Valem igualmente para 90.1-2019 e 90.1-2022, mas a redação não foi verificada on-line:
  - Programa capaz de simular as **8.760 horas** do ano, com variação horária de ocupação, iluminação, cargas internas, *setpoints* e operação do HVAC, definidos separadamente para cada dia da semana e feriados.
  - Efeitos de massa térmica; **pelo menos 10 zonas térmicas**; curvas de carga parcial dos equipamentos; curvas de correção de capacidade e eficiência para aquecimento e resfriamento mecânicos; economizadores a ar e a água com controle integrado; características dos sistemas do baseline.
  - O programa deve ter sido **testado pela ASHRAE Standard 140**, com os resultados publicados pelo desenvolvedor. A edição exata da 140 referenciada em cada edição da 90.1 não foi confirmada [?].
  - Dados climáticos horários representativos do local (p. ex. TMY3, IWEC2 ou equivalente para o Rio).
  - **Horas de carga não atendida (G3.1.2.3):** no máximo **300 h** (de 8.760) no proposto e no baseline, e o proposto não pode exceder o baseline em **mais de 50 h**.
  - Rodar o baseline nas **4 orientações** (0°, 90°, 180°, 270°) e usar a média; tipo de sistema do baseline pela Tabela G3.1.1-3/-4; dimensionamento do baseline com sobredimensionamento de 15% no resfriamento e 25% no aquecimento.
  - Clima: o Rio de Janeiro deve cair na **zona 1A da ASHRAE 169** [M]. Isso define os BPFs e o sistema do baseline.
- **Pontuação:** pré-requisito, sem pontos.
- **Documentos de submissão:** relatório de entradas e saídas do modelo (proposto e baseline), relatórios de horas não atendidas, tarifas ou fatores de conversão, e o calculador oficial da USGBC. No v4/v4.1 era a planilha *Minimum Energy Performance Calculator*. **Não confirmei o nome nem o formato do calculador do v5** [?].

### 2.3 EAc3 – Enhanced Energy Efficiency (1–10 pts NC; 1–7 pts CS)

- **Pontos:** confirmados 1–10 (NC) e 1–7 (CS) [C] (LEEDuser NC-v5 EAc3 e CS-v5 EAc3). Para LEED **Platinum NC** são exigidos **8 pontos** neste crédito; para CS, 5 pontos [S] (https://orientation.montgomerycollege.edu/_documents/offices/facilities/md-cc-fpc/leedv5-preview-climate-solutions-now-presentation-may-9-2025.pdf ; https://www.3foldtraining.com/leed-v5-platinum-requirements/).
- **Use a mesma edição da 90.1 escolhida no EAp2** [S] (LEEDuser NC-v5 EAc3).
- **Opção prescritiva:**
  - *Path 1*, cargas reguladas: medidas prescritivas ligadas às seções da 90.1, inclusive a seção 11 da 90.1-2022.
  - *Path 2*, cargas de tomada e processo: pontos por número de categorias de equipamento eficiente. Exemplo encontrado: 2 categorias = 2 pts; ≥ 3 categorias = 3 pts.
  - Os dois *paths* podem ser somados até 10 pts [S] (https://docs.betterbuilding.io/support-and-training/other-support/faqs/leed/leed-v5-enhanced-energy-efficiency-ea-credit).
- **Opção por simulação:**
  - Apêndice G com métrica de **future source energy** (fator elétrico 2,0).
  - *Path 1*: apenas eficiência, sem renováveis. *Path 2*: inclui renováveis no local [S] (mesma fonte).
  - **Tabela de pontos não confirmada** [?]. Um slide de Arlington mostra degraus de **3% → 1 pt e 6% → 2 pts**. Uma fonte diz que 8 pts NC correspondem a ~24% de redução. Outra diz que 10 pts exigem ~30% (só eficiência) ou ~100% (com renováveis). As fontes divergem.
- **Saída necessária da suíte:** future source energy anual do proposto e do baseline (kWh ou kBtu), % de melhoria e pontos; quebra por uso final (aquecimento, resfriamento, ventiladores, bombas, SHW, iluminação, tomadas).
- **Diferença em relação ao v4.1:** o v4.1 tinha até 18 pts, a métrica era custo + GHG e o baseline era a 90.1-2016. O v4 usava a escala de 10,5% a 42% sobre a 90.1-2010 (https://s3.amazonaws.com/legacy.usgbc.org/usgbc/docs/Archive/General/Docs3198.pdf).

### 2.4 EAc2 – Reduce Peak Thermal Loads (5 pts NC/CS, conforme as fichas USGBC/CaGBC)

- **Pontos:** 5 pts NC e 5 pts CS segundo a ficha da USGBC (https://www.usgbc.org/sites/default/files/2025-05/LEED_LEED-v5-One-Pagers-Fact-Sheet_BD+C_v4_DL.pdf) e a da CaGBC (https://cagbc.org/wp-content/uploads/2025/04/LEED-v5-BDC-Fact-Sheet.pdf) [S]. Um trecho do Reference Guide menciona uma subescala de 1–3 pts por redução de pico movida pela envoltória: **10% → 1 pt; 20% → 2 pts** [S]/[?].
- **Requisitos encontrados:**
  - *Path 1*: limitar as cargas de pico abaixo de limites especificados.
  - **O cálculo de pico de aquecimento e de resfriamento deve incluir as cargas de ventilação.**
  - Caminho de *trade-off* de envoltória: o *envelope performance factor* do proposto deve ser ≤ ao do baseline (Apêndice C da 90.1) [S] (Scribd BD+C RG).
  - Estratégias citadas: estanqueidade e infiltração, ventilação balanceada com recuperação de energia, pontes térmicas, com possível exigência de simulação e de teste de campo [S] (https://verdicalgroup.com/how-leed-v5-is-reframing-energy-performance-paradigms/ ; https://vca-green.com/fundamental-shifts-in-leed-v5-energy-and-atmosphere-credits-that-every-project-team-should-know/).
  - **Os limites numéricos (W/m², Btu/h·ft² ou % sobre o baseline) não foram confirmados** [?].
- **Relevância para a suíte: muito alta.** É exatamente o módulo de carga térmica: pico de resfriamento (sensível + latente + ventilação) e pico de aquecimento, proposto contra baseline, com e sem ERV, mais o *envelope performance factor*.

### 2.5 EAc1 – Electrification (5 pts NC / 4 pts CS)

- Pontos confirmados no *scorecard* da edição de julho de 2026: "EAc1 · Electrification · 5 · 4" [S] (PDF USGBC jul/2026).
- Conteúdo, de fontes secundárias e não confirmado em detalhe [?]: sem combustão no local para aquecimento de ambiente e de água, com **bombas de calor**. Obter 4–5 pts aqui dispensa a projeção do EAp1 [S].
- **Cálculo da suíte:** fração da capacidade e da energia de aquecimento (ambiente + SHW) atendida eletricamente; dimensionamento de bomba de calor (COP sazonal com o clima do Rio); impacto no pico elétrico (que alimenta o EAc6).

### 2.6 EAc4 – Renewable Energy

- Pontos: 4 pts segundo o trecho do PDF de jul/2026 [S]/[?]. A ficha da CaGBC indica pontuação diferente para NC [?].
- **Cálculo da suíte:** consumo anual total (saída do 8760) como denominador e geração FV local horária (opcional). Para a suíte de HVAC-R, só fornecer o consumo.

### 2.7 EAp3 – Fundamental Commissioning e EAc5 – Enhanced Commissioning

- EAp3 é obrigatório. EAc5 vale 3 pts NC segundo o trecho do PDF de jul/2026 [S]/[?].
- Pelo v4.1 e pela prática ASHRAE [M]: processo conforme **ASHRAE Guideline 0** e **ASHRAE/IES Standard 202**, com OPR, BOD, plano de Cx, requisitos de Cx nas especificações, verificação de instalação, testes funcionais, relatório final e plano de O&M.
  - No v4.1 o comissionamento de envoltória (Guideline 0 + NIBS Guideline 3) era uma opção do crédito Enhanced.
  - O Enhanced v4.1 incluía *monitoring-based commissioning* (MBCx).
  - **Não confirmei a divisão exata do v5** (se a envoltória passou para o pré-requisito e quais opções restaram no EAc5) [?].
- **Cálculo da suíte:** nenhum cálculo normativo. Valor agregado: gerar o OPR/BOD a partir dos parâmetros de projeto e roteiros de testes funcionais (FPT) com valores esperados (vazões, ΔT, COP, setpoints). Para MBCx, fornecer regras de detecção de falhas sobre séries horárias de BMS.

### 2.8 EAp4 – Energy Metering and Reporting (pré-requisito)

- Nome confirmado [S] (Scribd BD+C RG).
- Pelo v4.1 [M]: medidores de nível de edifício para todos os energéticos, dados compartilhados com a USGBC por 5 anos; no v4.1 a submedição avançada era crédito separado. **O conteúdo exato do v5 não foi confirmado** (se exige submedição por uso final, como HVAC, de forma obrigatória) [?].
- **Cálculo da suíte:** plano de medição por uso final (lista de medidores, pontos de BMS), consumo esperado mensal e por uso final para comparar com o medido (baseline de M&V).

### 2.9 EAc6 – Grid Interactive / Demand Response

- **Não consegui confirmar o nome final, os requisitos nem a pontuação** [?]. No v4.1 o crédito Demand Response (até 2 pts) exigia capacidade de reduzir **≥ 10% da demanda de pico** projetada por ≥ 1 h, com programa de DR ou infraestrutura *DR-ready* [M].
- **Cálculo da suíte:** perfil horário de demanda elétrica do HVAC (saída 8760), potencial de *load shifting* (pré-resfriamento, termoacumulação, relaxamento de setpoint) e kW reduzível no pico.

---

## 3. Refrigerantes

### 3.1 Pré-requisito Fundamental Refrigerant Management (EAp5 no BD+C)

A numeração varia entre fontes: EAp5 no LEEDuser CS e EAp4 na ficha O+M.

- **Requisitos v5:**
  - **HCFC proibido** (no v4.1 a proibição era só de CFC).
  - **Inventário de todos os equipamentos com refrigerante**, com tipo, carga e GWP.
  - Para refrigerantes com **GWP > 700**, avaliar e listar alternativas com **GWP ≤ 700** durante o projeto.
  - **Teste de vazamento** (*leak check*) na instalação.
  - Opção de projeto sem refrigerante [S] (Trane APN099; ID+C Rating System nov/2025: https://www.usgbc.org/sites/default/files/2025-10/LEED%20v5%20ID+C%20Rating%20System_November%202025_clean.pdf ; https://archiroots.com/leed-v5/ ; https://salasobrien.com/news/leedv5/).
- O Reference Guide indica **taxa anual de vazamento padrão de 2%** (ou 1% para projetos que buscam a Opção 2 do crédito) para os cálculos de carbono do refrigerante [S] (Scribd BD+C RG). Um rascunho de 2024 usava 2,5% (https://www.usgbc.org/sites/default/files/2024-05/LEED-v5-summary-of-changes-LEED-v4-LEED-v41-BDC.pdf).
- **Não confirmado:** o procedimento exato do teste de vazamento no v5 (norma de referência, p. ex. ASHRAE 15 ou EN 378, pressão e duração) [?].

### 3.2 Crédito Enhanced Refrigerant Management (EAc7; 2 pts NC/CS)

- **Pontos:** 2 pts NC e 2 pts CS [C] (ficha USGBC mai/2025; PDF jul/2026).
- **Estrutura v5:** opções para "sem refrigerante", "baixo GWP" e um caminho para varejo (*retail*). Novidades: refrigerantes de **ultra-baixo GWP** e **minimização de vazamento** [S] (USGBC Summary of Changes 2024).
- **Cálculo v5 (abr/2025)** [S] (Scribd BD+C RG; LEEDuser NC-v5 EAc7):
  - Cada tipo de equipamento tem um **benchmark de GWP** (Tabela 1).
  - Calcula-se o **GWP médio ponderado pela carga**: Σ(GWP_i × carga_i) / Σ carga_i. Esse valor é comparado com o benchmark ponderado, Σ(benchmark_i × carga_i) / Σ carga_i.
  - **Benchmark ajustado:** o benchmark da Tabela 1 é multiplicado pela razão (carga por unidade de capacidade do equipamento comparável) / (carga por unidade de capacidade do equipamento do projeto). Esse ajuste premia baixa carga específica e só é permitido se nenhum dos dois equipamentos tiver GWP acima do benchmark da Tabela 1.
  - O exemplo do RG usa benchmark HVAC = 700. O LEEDuser NC-v5 cita benchmark de **1.400** para alguma categoria.
  - **Os valores completos da Tabela 1 não foram confirmados** [?]. Um rascunho do O+M (2024) citava 700 para VRF e 300 para sistemas com menos de 200 lb de carga (https://www.usgbc.org/sites/default/files/2024-04/LEED-v5-OM-Existing-Buildings-Public-Comment-1.pdf).
- **Detecção de vazamento:** especificar **sistema automático de detecção de vazamento** em ambientes fechados com equipamento cuja **carga total exceda 100 tCO2e** (carga [kg] × GWP / 1000) [S] (Scribd BD+C RG).
- **No O+M v5 (referência para retrofit e operação):** razão = Σ(GWP × massa vazada em 12 meses) / massa total de refrigerante instalada; **≤ 50 → 1 pt; ≤ 25 → 2 pts** [S] (https://www.usgbc.org/sites/default/files/2025-10/LEED%20v5%20O+M%20Rating%20System_November%202025_clean.pdf).

### 3.3 Fórmula do v4/v4.1 (Opção 2), mantida como referência e possivelmente útil para o ACP de varejo

Fontes [S] (LEEDuser CI-v4 EAc5: https://leeduser.buildinggreen.com/credit/CI-v4/EAc5 ; USGBC Guide BDC: https://www.usgbc.org/node/3156547 ; https://pdhonline.com/courses/m496/m496content.pdf):

```
LCGWP = [GWPr × (Lr × Life + Mr) × Rc] / Life
LCODP = [ODPr × (Lr × Life + Mr) × Rc] / Life
Critério: Σ (LCGWP + LCODP × 10^5) × Qunit / Qtotal ≤ 100 (IP)  ou ≤ 13 (SI)
```

| Variável | Significado | Valores padrão |
|---|---|---|
| GWPr, ODPr | Potencial de aquecimento global e de destruição de ozônio do refrigerante | — |
| Lr | Vazamento anual | 2% |
| Mr | Perda no fim de vida | 10% |
| Life | Vida útil do equipamento | Padrão por tipo de equipamento; 10 anos é o único valor confirmado [S]. Vidas por tipo, como 15 anos para unitários/split e 23 anos para chillers centrífugos ou parafuso, são [M]/[?] |
| Rc | Carga de refrigerante | 0,5–5,0 lb/ton AHRI (SI: 0,065–0,65 kg/kW AHRI ou Eurovent) |
| Qunit | Capacidade bruta de resfriamento do equipamento | Btu/h ou kW |
| Qtotal | Capacidade total de resfriamento do projeto | Btu/h ou kW |

- Opção 1 do v4/v4.1: sem refrigerante, ou refrigerantes com ODP = 0 e GWP < 50.
- Varejo (v4): cálculo separado para *downstream* e *upstream*, com média ponderada se um dos dois falhar.

---

## 4. Qualidade do Ambiente Interno (EQ)

### 4.1 EQp – Fundamental Air Quality (pré-requisito)

- **Junta** os antigos *Minimum IAQ Performance* e afins. Antes de escolher a estratégia de ventilação, exige **investigar a qualidade do ar externo local** [S] (https://bowman.com/news/leed-v5-mep-edition-indoor-environmental-quality).
- **Norma: ASHRAE 62.1-2022, seções 5 e 6** (o v4 usava 62.1-2010, seções 4–7) [C] (USGBC ID+C Summary of Changes: https://www.usgbc.org/sites/default/files/2025-04/LEED-IDC-v4-v5-Summary-of-Changes.pdf). Valem o **VRP** (*Ventilation Rate Procedure*) e o **IAQP** (*IAQ Procedure*) [S] (https://gpsair.com/leed-supports-the-iaqp).
- **Filtração:** **MERV 13 ou ISO 16890 ePM1 50%** nos sistemas que fornecem ar externo ou recirculado a espaços ocupados [S] (Kaiterra: https://learn.kaiterra.com/en/resources/indoor-air-quality-requirements-and-credits-in-well-v2-leed-v4-and-reset-air ; https://airscan.org/insights/green-building/air-quality-features-in-the-new-leed-v5-release-airscan/). O próprio texto da 62.1-2022 não exige MERV 13; a exigência vem do LEED.
- **Monitoramento:** **medidor de vazão de ar externo** nas tomadas com **> 1.000 cfm** (~472 L/s) [S] (https://epstengroup.com/leed-v5-is-here-what-building-owners-need-to-know/). No v4.1 a tolerância era ±10% da vazão mínima de projeto, com alarme em desvio de 15% [M].
- **Cálculo VRP da 62.1-2022** [M]:
  - Vazão na zona de respiração: **Vbz = Rp·Pz + Ra·Az**, com Rp e Ra da Tabela 6-1.
  - Vazão da zona: **Voz = Vbz / Ez**, com Ez da Tabela 6-4 conforme a distribuição de ar.
  - Sistemas de 100% de ar externo: Vot = ΣVoz.
  - Sistemas multizona recirculados: **Vou = D·ΣRp·Pz + ΣRa·Az** (D = diversidade de ocupação), **Ev** pela Tabela 6-5 ou pelo procedimento normativo do Apêndice A, e **Vot = Vou / Ev**.
  - Também: exaustões da Tabela 6-2; ar externo em modo de demanda (DCV); verificação de qualidade do ar externo (seção 4 / "Outdoor Air Quality").
- **Saída:** planilha zona a zona (Pz, Az, Rp, Ra, Vbz, Ez, Voz, Zpz, Ev, Vot por sistema), relatório da qualidade do ar externo e especificação de filtros.
- **Pontuação:** pré-requisito.

### 4.2 EQc1 – Enhanced Air Quality (1 pt NC pela ficha USGBC; uma fonte cita 1–2 pts [?])

- **Opções** [S] (Bowman; Airscan):
  - aumentar a vazão de ar externo em **≥ 15%** acima da 62.1-2022 (1 pt), ou **30%** (2 pts, segundo uma fonte; conflita com a ficha que indica 1 pt) [?];
  - ou projetar a QAI para limites de contaminantes mais baixos (por IAQP).
- O v5 **removeu** destas opções a ventilação natural projetada, as janelas operáveis, a filtração aprimorada, a contaminação cruzada e várias medidas de controle de fontes [S] (Bowman).
- **Cálculo:** repetir o VRP com fator 1,15 ou 1,30 sobre Vbz, aplicado à **vazão na zona de respiração**. Em sistemas multizona isso eleva **Vot** em mais que o percentual, porque Ev muda [S] (LEEDuser NC-v4.1 EQc1). Também o impacto energético do ar externo adicional, para retroalimentar o EAp2/EAc3, e a capacidade de serpentina e ERV.

### 4.3 EQc5 – Air Quality Testing and Monitoring (2 pts NC)

- 2 pts NC [S] (ficha USGBC mai/2025). Inclui **monitoramento contínuo** de QAI, até 1 pt [S] (https://learn.kaiterra.com/en/resources/leed-v4.1-vs.-leed-v5-the-shift-to-continuous-air-quality-monitoring). O **monitoramento de CO2** que estava no EQc1 do v4.1 foi para este crédito [S] (Bowman).
- Parâmetros e limites exatos (PM2.5, TVOC, CO2, CO, formaldeído), densidade de sensores e teste pré-ocupação **não foram confirmados** [?].
- **Cálculo da suíte:** localização e quantidade de sensores por zona e sistema; setpoints de DCV por CO2. Fórmula de equilíbrio de massa em regime permanente: **C_int = C_ext + N / (V̇oz por pessoa)**, com geração N de ~0,0052 L/s de CO2 por pessoa a 1,2 met [M].

### 4.4 EQc2 – Occupant Experience (até 7 pts NC)

- 7 pts no total [S] (https://projectific.com/blogs/leed-certification/leed-scorecard).
- **Opção "Thermal Environment":** 1 pt por projetar os espaços ocupados conforme a **ASHRAE 55-2023** (BD+C e ID+C) [S] (https://gbdmagazine.com/leed-v5/).
  - A 55-2023 traz o método PMV/PPD, o **método adaptativo** (espaços naturalmente condicionados), o método de velocidade elevada do ar (SET/CE) e um novo método de desconforto local por **gradiente vertical de temperatura cabeça-tornozelo** [C] (ASHRAE: https://www.ashrae.org/file%20library/about/government%20affairs/advocacy%20toolkit/virtual%20packet/standard-55-fact-sheet.pdf).
  - Faixa de conforto: tipicamente **PPD < 10% (−0,5 < PMV < +0,5)**; desconforto local por assimetria radiante, correntes de ar e temperatura de piso [M].
  - **Controle individual:** no v4/v4.1 o crédito *Thermal Comfort* exigia controle individual em ≥ 50% dos espaços individuais e controle em grupo nos espaços compartilhados [M]/[S] (https://www.firstgreen.co/leed-bdc-indoor-environmental-quality-credit-thermal-comfort/). **Não confirmei se o v5 mantém essa exigência** [?].
- **CFD como comprovação:** **não encontrei fonte da USGBC sobre CFD** [?]. A ASHRAE 55 exige documentar a conformidade de projeto com os parâmetros ambientais (temperatura do ar, temperatura radiante média, velocidade do ar, umidade) e os pessoais (met, clo) por zona representativa [M]. Ela não proíbe que essas grandezas venham de simulação. CFD é a forma mais robusta de obter velocidade do ar, gradiente vertical e assimetria por zona, sobretudo para o novo critério de gradiente vertical e para o método de velocidade elevada. **Recomendação:** tratar CFD como **evidência complementar** do cálculo PMV/PPD por zona (memória de cálculo da 55, no estilo da ferramenta CBE Thermal Comfort Tool) e não como substituto. Confirmar com a GBCI.
- **Opção "Sound Environment":** 1 pt. Plano acústico com zoneamento (ruidoso, silencioso, misto, circulação) [S] (https://leeduser.buildinggreen.com/forum/sound-environment-and-occupant-experience). Para referência, no v4 o crédito *Acoustic Performance* exigia **ruído de fundo do HVAC** pela **AHRI 885-2008** e pelo **ASHRAE Handbook (Applications, cap. "Noise and Vibration Control", Tabela 1, NC/RC)** [M]. **Não confirmei se o v5 mantém limites de NC/RC** [?].
- **Cálculo da suíte:** PMV/PPD por zona (ISO 7730 / ASHRAE 55) com dados de CFD ou de simulação horária; % de horas ocupadas dentro da faixa (útil, mas não necessariamente exigido) [?]; NC/RC no ambiente a partir da potência sonora dos equipamentos (AHRI 885).

### 4.5 EQc4 – Resilient Spaces

- Existe no BD+C NC e, segundo uma fonte, tem cinco opções [S] (Projectific). **Requisitos e pontos não confirmados** [?]. Pode incluir segurança térmica e sobrevivência passiva, com horas acima de limites de temperatura ou índice de calor sem energia, por simulação horária [?].

---

## 5. Caminhos alternativos de conformidade (ACPs) para projetos fora dos EUA e o Brasil

- **Energia:**
  - **NECB 2020** foi reconhecida como caminho alternativo no LEED v5 para o Canadá [S] (https://www.cagbc.org/news-resources/cagbc-news/necb-2020-recognized-as-alternative-path-in-leed-v5/).
  - Há caminho simplificado via **Passive House** no Canadá (https://www.cagbc.org/news-resources/cagbc-news/streamlined-path-to-leed-v5-with-passive-house-certification/).
  - Na Califórnia, a USGBC estuda equivalência com o **Title 24** [S] (CalBEM).
  - No v4 existia o ACP "alternative energy performance metric" (custo ou GHG, ou source energy) (https://www.usgbc.org/node/7487846).
  - **Não encontrei ACP brasileiro de energia** (p. ex. INI-C/PBE Edifica no lugar da 90.1) [?]. Para o Brasil, o caminho esperado é a própria 90.1 Apêndice G, com clima local (zona 1A) e os fatores e BPFs do v5 [M].
- **Ventilação e conforto:**
  - No LEED v4 havia ACPs internacionais que aceitavam **CEN EN 15251:2007 / EN 13779:2007** no lugar da 62.1 e **ISO 7730:2005 / EN 15251** no lugar da ASHRAE 55 (esses textos estavam inclusive na linguagem dos créditos) [M].
  - No v5, as normas europeias equivalentes seriam a **EN 16798-1** e a **ISO 7730**. **Não confirmei se o v5 as mantém** [?].
- **ABNT NBR 16401 (partes 1, 2 e 3):**
  - **Não encontrei nenhum ACP ou equivalência publicada pela USGBC ou pela GBC Brasil que aceite a NBR 16401-3 no lugar da ASHRAE 62.1, nem a NBR 16401-2 no lugar da ASHRAE 55** [?].
  - Avaliação técnica [M]: a **NBR 16401-3:2008** adota a mesma estrutura do VRP (Rp·Pz + Ra·Az, níveis 1–3, eficiência de distribuição), derivada da 62.1-2004/2007. Ela tende a ser aceita apenas com **demonstração de equivalência** caso a caso (*CIR/LEED Interpretation*), e mesmo assim o nível 1 dá vazões em geral iguais ou menores que a 62.1-2022. Não conte com isso.
  - A NBR 16401 continua **obrigatória localmente**. A Lei 13.589/2018 (PMOC) e a RE ANVISA 09/2003 são [M]. Portanto **a suíte deve calcular as duas normas** e reportar a mais exigente.
- **Recomendação:** consultar a página *LEED Interpretations / ACPs* no LEED Credit Library da USGBC e a GBC Brasil, e abrir *CIR* se for usar NBR 16401 ou EN 16798.

---

## 6. Tabela-resumo: crédito → cálculo que a suíte precisa fazer → entradas → saída

| Crédito (v5 BD+C) | Pts NC/CS | Cálculo que a suíte precisa fazer | Entradas | Saída / documento para submissão | Confiabilidade |
|---|---|---|---|---|---|
| **EAp1** Operational Carbon Projection & Decarbonization Plan | pré-req. | Consumo anual por energético; vazamento anual de refrigerante (kg e tCO2e); cenários de 25 anos de retrofit e eletrificação com CAPEX/OPEX | Saída do 8760 por energético; inventário de refrigerantes; fatores de rede (Brasil/SIN); cronograma de troca de equipamentos | Tabela de consumo anual por energético enviada à USGBC; plano de descarbonização de 25 anos atestado pelo proprietário | [S] |
| **EAp2** Minimum Energy Efficiency | pré-req. | Simulação 8760 pelo Apêndice G da 90.1-2019 ou 2022: proposto contra baseline (4 orientações), horas não atendidas ≤ 300 e ≤ baseline + 50, PCI/PCIt, future source energy (fator elétrico 2,0), GHG; ou checklist prescritivo das seções 5–10/11 | Geometria e zonas (≥ 10), envoltória (U, SHGC, infiltração), cargas internas e agendas, sistemas HVAC (curvas de carga parcial, COP/EER/IPLV, ventiladores W/cfm, bombas), SHW, iluminação, arquivo climático horário do Rio, tarifas, fatores site→source/GHG, zona climática 1A | Relatório de entradas e saídas do baseline e do proposto, uso final, horas não atendidas, % de melhoria; calculador oficial da USGBC (nome do v5 não confirmado); declaração de que o software foi testado pela ASHRAE 140 | Estrutura [S]; limiar [?]; regras do Apêndice G [M] |
| **EAc3** Enhanced Energy Efficiency | 1–10 / 1–7 | Mesmo modelo do EAp2: % de redução de future source energy (Path 1 sem FV; Path 2 com FV local); ou contagem prescritiva de medidas (cargas reguladas + plug/processo) | As do EAp2 + geração FV horária; lista de equipamentos eficientes | % de melhoria e pontos; tabela de medidas prescritivas | Pontos [C]; tabela de % [?] |
| **EAc2** Reduce Peak Thermal Loads | 5 / 5 | Carga de pico de resfriamento (sensível + latente) e de aquecimento **incluindo ventilação**, proposto contra baseline ou contra limite; efeito de ERV e da infiltração; *envelope performance factor* (Apêndice C da 90.1) | Envoltória, infiltração (teste de estanqueidade), vazão de ar externo (62.1), eficiência de recuperação, dados climáticos de projeto (ASHRAE 0,4%/1%/99,6%) | Memória de cálculo de cargas de pico por zona e sistema (W/m² ou Btu/h·ft²), % de redução, EPF proposto ≤ baseline | [S]; limites [?] |
| **EAc1** Electrification | 5 / 4 | Fração do aquecimento (ambiente + SHW) atendida por bomba de calor; dimensionamento de bomba de calor; impacto no pico elétrico | Cargas de aquecimento e SHW, catálogos de bombas de calor (COP por temperatura), clima | Planilha de equipamentos com combustão contra elétricos; % eletrificado | Pontos [S]; regras [?] |
| **EAc4** Renewable Energy | 4? | Denominador: consumo anual total (8760) | Saída do EAp2 | Consumo anual (kWh) para o cálculo do % renovável | [?] |
| **EAc6** Grid Interactive / DR | ? | Perfil horário de demanda do HVAC; kW reduzível no pico (pré-resfriamento, termoacumulação, setpoint) | Saída horária do 8760, sequências de controle, capacidade de TES | Curva de carga, estratégia de DR, % de redução do pico (v4.1: ≥ 10%) | [?] |
| **EAp3 / EAc5** Commissioning | pré-req. / 3? | Sem cálculo normativo; gerar OPR/BOD, plano de Cx, roteiros de FPT com valores esperados; regras de MBCx | Parâmetros de projeto (vazões, setpoints, capacidades, COP), pontos de BMS | OPR, BOD, plano de Cx, checklists, FPT, relatório de Cx, plano de MBCx | [M]/[?] |
| **EAp4** Energy Metering & Reporting | pré-req. | Plano de medição por energético e por uso final; consumo esperado mensal e por uso final (baseline de M&V) | Saída do 8760 por uso final, diagrama elétrico/térmico | Lista de medidores, compromisso de reporte, consumo esperado | [S] nome; conteúdo [?] |
| **EAp5** Fundamental Refrigerant Management | pré-req. | Inventário: carga (kg), GWP, tCO2e por equipamento; triagem GWP > 700 → alternativas ≤ 700; checagem de proibição de HCFC; registro do teste de vazamento | Lista de equipamentos (tipo, refrigerante, carga, capacidade); base de GWP (IPCC AR4/AR5, a confirmar qual) | Planilha de inventário de refrigerantes; análise de alternativas; relatório do teste de vazamento | [S] |
| **EAc7** Enhanced Refrigerant Management | 2 / 2 | GWP médio ponderado pela carga contra o benchmark ponderado (Tabela 1); benchmark ajustado por carga específica (kg/kW); verificação de detecção automática onde a carga > 100 tCO2e; opção de vazamento de 1%/ano. Referência v4.1: LCGWP/LCODP ≤ 100 (IP) / 13 (SI) | Refrigerante, carga, capacidade AHRI/Eurovent e GWP de cada equipamento; carga específica de equipamento comparável; volumes dos ambientes | Calculador de refrigerante (formato v5 não confirmado); lista de equipamentos com GWP e carga; especificação do detector de vazamento | Estrutura [S]; Tabela 1 [?] |
| **EQp** Fundamental Air Quality | pré-req. | VRP da 62.1-2022 (Vbz, Ez, Voz, D, Ev, Vot) ou IAQP; avaliação da qualidade do ar externo; seleção MERV 13/ePM1 50%; medição de ar externo onde a tomada > 1.000 cfm; em paralelo, NBR 16401-3 | Zonas: área, ocupação, tipo de espaço (Tabela 6-1), configuração de insuflamento e retorno (Ez), sistemas; dados de qualidade do ar externo (PM2.5, O3) | Planilha de ventilação por zona e sistema; especificação de filtros; especificação dos medidores de vazão de ar externo | 62.1-2022 [C]; demais [S] |
| **EQc1** Enhanced Air Quality | 1 (1–2?) | VRP com +15% (ou +30%) na zona de respiração; Vot resultante; impacto em energia, serpentina e ERV | As do EQp + fator de majoração | Planilha comparativa base contra majorada | [S]/[?] |
| **EQc5** Air Quality Testing & Monitoring | 2 | Plano de sensores (CO2, PM, TVOC…); setpoints de DCV por CO2 (equilíbrio de massa) | Zonas, ocupação, Voz | Plano de monitoramento; limites de alarme | [S]/[?] |
| **EQc2** Occupant Experience: Thermal Environment | 1 (de 7) | PMV/PPD por zona (ASHRAE 55-2023 / ISO 7730); método adaptativo onde aplicável; desconforto local (gradiente vertical, assimetria, correntes de ar) a partir de **CFD**; controle individual (a confirmar) | Temperatura do ar, temperatura radiante média, velocidade do ar, umidade (simulação, CFD), met, clo, agendas | Memória de cálculo da ASHRAE 55 por zona representativa; mapas CFD como evidência complementar | 55-2023 [S]/[C]; CFD [?] |
| **EQc2** Occupant Experience: Sound Environment | 1 (de 7) | Ruído de fundo do HVAC (NC/RC) a partir da potência sonora (AHRI 885), atenuação de dutos e ambiente | Potência sonora por banda dos equipamentos, rede de dutos, absorção do ambiente | Plano acústico por zona; NC/RC calculado (se o v5 exigir) | [S]/[?] |
| **EQc4** Resilient Spaces | ? | Possível: simulação de sobrevivência passiva e segurança térmica (horas acima de limite sem energia) | Modelo 8760 com HVAC desligado; clima extremo | Relatório de horas e temperaturas | [?] |

---

## 7. Prioridades para a suíte, em ordem de impacto em pontos

1. **Motor 8760 compatível com o Apêndice G**, testado pela ASHRAE 140 ou com exportação para EnergyPlus ou outro *engine* já validado. Ele alimenta EAp1, EAp2, EAc3 (até 10 pts), EAc1, EAc4, EAc6 e EAp4.
2. **Carga térmica de pico com ventilação** e *envelope performance factor*, para o EAc2 (5 pts).
3. **Inventário e calculador de refrigerantes** com base de GWP e tCO2e, para EAp5, EAc7 (2 pts) e EAp1. É barato de implementar e reaproveita o módulo de linhas frigoríficas, já que a carga de refrigerante depende do comprimento das linhas em VRF e split.
4. **Ventilação 62.1-2022 + NBR 16401-3** em paralelo, para EQp e EQc1.
5. **PMV/PPD por zona com CFD** como evidência da 55-2023, no EQc2.
6. **Geradores de documentos** de Cx, plano de medição e plano de descarbonização com CAPEX/OPEX.

## 8. Pontos abertos para confirmar no PDF oficial (edição de julho de 2026) e no Reference Guide

- Limiar percentual mínimo do EAp2 v5 e métricas exigidas (PCI, source, GHG).
- Tabela de pontos do EAc3 (Path 1 e Path 2).
- Limites numéricos do EAc2.
- Tabela 1 de benchmarks de GWP do EAc7 e base de GWP (AR4, AR5 ou AR6).
- Procedimento do teste de vazamento no EAp5.
- Requisitos e pontuação de EAc4, EAc5, EAc6 e EQc4.
- Se o v5 mantém o controle térmico individual e os limites de NC/RC.
- Nome e formato dos calculadores oficiais do v5.
- Existência de ACPs internacionais (EN 16798-1, ISO 7730) e de qualquer equivalência com a NBR 16401.
- Data de corte para registro no v4.1.

**Para destravar:** liberar `usgbc.org` e `leeduser.buildinggreen.com` no ambiente e repetir a coleta diretamente dos PDFs.
