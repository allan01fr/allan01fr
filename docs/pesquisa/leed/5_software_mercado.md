# 5 — Software, mercado e riscos para uma suíte HVAC-R orientada a LEED (KAPTEK)

Data da pesquisa: 8 nov. 2026. Pesquisa feita só na web, sem tocar em repositórios.

## Convenções e limites desta pesquisa

- **[FATO]**: afirmação com URL citada. Quando a fonte é secundária (fórum, blog de fornecedor, site de preparação para prova), isso vem indicado.
- **[NÃO CONFIRMADO]**: procurei e não achei fonte, ou as fontes se contradizem.
- **[ESTIMATIVA KAPTEK]**: conta ou opinião minha. Não é dado de mercado.
- **Limites técnicos da sessão.** Vários domínios estavam bloqueados para leitura direta: usgbc.org, leeduser.buildinggreen.com, bigladdersoftware.com, designbuilder.co.uk, pnnl.github.io, onebuilding.org, es.senac.br, sienge.com.br, ugreen.com.br e pncp.gov.br. Por isso, parte dos fatos vem de trechos de buscadores, não da página inteira. A cota de buscas web também acabou antes do fim, e ficaram sem busca três pontos: (a) recursos de PMV/PPD do SimScale, (b) a carteira de serviços das consultorias brasileiras, (c) horas típicas de um modelo do Apêndice G. Antes de citar qualquer número a cliente, confira nas páginas oficiais.

---

## 1. Software de simulação energética para o Apêndice G da ASHRAE 90.1 e para o LEED

### 1.1 O que o LEED e o Apêndice G exigem do software

- **[FATO]** O LEED não mantém uma lista própria de software aprovado. Quem define o requisito é a ASHRAE 90.1, Apêndice G, seção G2 ("Simulation General Requirements"): o programa de simulação precisa ter sido testado pela ASHRAE Standard 140. Fonte: resumo do BEMcyclopedia, https://bemcyclopedia.com/wiki/ASHRAE_Standard_90.1. O rascunho de adenda à 90.1-2022 cita a 140 ("tested according to ASHRAE Standard 140, except Sections 7 and 8"): https://osr.ashrae.org/Online-Comment-Database/ShowDoc2/Table/DocumentAttachments/FileName/4410-90.1-2022at%20PPR1%20Draft.pdf/download/false
- **[FATO]** A adenda "b" da ASHRAE 140-2020, aprovada em 31/01/2023, criou critérios de aceitação (faixas de resultado) que normas como a 90.1 podem exigir: https://www.ashrae.org/file%20library/technical%20resources/standards%20and%20guidelines/standards%20addenda/140_2020_b_20230131.pdf. A edição 140-2023 traz faixas quantificadas de aceitação: https://www.ashrae.org/technical-resources/bookstore/ashrae-building-energy-simulation-and-performance-modeling-resources
- **[FATO] LEED v5.** Foi lançado em 28/04/2025 (https://aecom.com/blog/?p=19504; https://www.mannpublications.com/mannreport/2025/04/28/u-s-green-building-council-launches-new-leed-rating-system/). Cerca de metade dos pontos está ligada a descarbonização (https://www.bdcnetwork.com/sustainability/news/55288412/usgbc-launches-leed-version-5).
  - O pré-requisito de eficiência mínima usa a 90.1-2022 com o Apêndice G. Projetos podem documentar pela 90.1-2019 como alternativa. Os BPFs da Tabela 4.2.1.1 são substituídos por fatores de "future source energy". Fonte: LEEDuser NC-v5 EAp2 (via trecho de busca), https://leeduser.buildinggreen.com/credit/NC-v5/EAp2
  - O pré-requisito EAp1 (Operational Carbon Projection) usa os dados anuais de energia do modelo para o USGBC projetar o carbono de 25 anos (https://leeduser.buildinggreen.com/credit/NC-v5/EAp1; https://www.swinter.com/leed-v5-decarbonization-requirements/).
  - O crédito EAc3 (Enhanced Energy Efficiency) usa a mesma versão da 90.1 do EAp2 e o método de cálculo excepcional (G2.5) para cargas de tomada e de processo (https://leeduser.buildinggreen.com/credit/NC-v5/EAc3).
- **[FATO]** O USGBC publicou mais de 20 calculadoras do LEED v5 na Resource Library (https://www.cagbc.org/news-resources/cagbc-news/leed-v5-expands-new-arc-certification-tools-and-resources-for-users). No LEED v4.1, o caminho de desempenho usa a planilha oficial "Minimum Energy Performance Calculator", atualizada no "2024 Energy Update" para projetos registrados a partir de 01/03/2024 (https://ghtltd.com/leed-v4-energy-update/; https://www.cagbc.org/news-resources/cagbc-news/leed-v4-4-1-july-2024-addenda-new-energy-performance-calculators-and-more/).
- **[NÃO CONFIRMADO]** Datas de encerramento do registro LEED v4/v4.1. As fontes se contradizem: 31/03/2026, 30/06/2026 ou 30/06/2027 (https://www.ul.com/insights/what-know-about-leed-v5; https://urbanistas-web.pages.dev/insights-leed-v5.html). Para projeto novo em nov./2026, presuma LEED v5 e confirme no USGBC.
- **[FATO, histórico]** No LEED 2009, projetos no Brasil com nível "A" no PBE Edifica (envoltória, iluminação e AVAC) cumpriam o pré-requisito de energia por um ACP regional (https://leeduser.buildinggreen.com/credit/Retail-NC-v2009/EAp2). **[NÃO CONFIRMADO]** se existe ACP equivalente com PBE Edifica/INI-C no v4.1 ou no v5.

### 1.2 Comparação dos programas

| Programa | Licença / custo | Usado no Apêndice G / LEED? | API ou biblioteca Python | Relatório no formato LEED |
|---|---|---|---|---|
| **EnergyPlus** (DOE; desenvolvido pelo NREL, renomeado em 01/12/2025 para National Laboratory of the Rockies) | Gratuito. Licença estilo BSD-3 com cláusula própria sobre o nome (detalhe na seção 4). Versão atual 26.2.0, de 30/09/2026 (https://github.com/NREL/EnergyPlus/releases; licença: https://github.com/NREL/EnergyPlus/blob/develop/LICENSE.txt; renomeação: https://www.energy.gov/eere/articles/energy-department-renames-nrel-national-lab-rockies) | Sim. É o motor de DesignBuilder, OpenStudio e TRACE 3D Plus. Tem recursos próprios para o Apêndice G, como a rotação automática nas 4 orientações do baseline (https://bigladdersoftware.com/epx/docs/25-1/using-energyplus-for-compliance/features-related-to-appendix-g-and-leed.html, via trecho de busca). Há relatórios de validação pela ASHRAE 140 (https://simulationresearch.lbl.gov/dirpubs/valid_ep.html). **[NÃO CONFIRMADO]** resultado publicado da 140-2023 para a versão 26.x | **eppy** 0.6.7, MIT, 26/08/2026 (https://pypi.org/project/eppy/). **geomeppy** 0.12.2, MIT, 13/03/2026 (PyPI JSON). **BESOS** 2.2.3, GPLv3, 31/05/2024, suporta só E+ 8.8–9.3+, ou seja, está desatualizado (https://pypi.org/project/besos/). API Python embutida (pyenergyplus): **[NÃO CONFIRMADO nesta pesquisa]**, mas consta da documentação desde a v9.3 (conhecimento prévio) | Sim. Gera o relatório "LEED Summary" com boa parte dos valores pedidos pelos formulários LEED (mesma fonte bigladder) |
| **OpenStudio SDK + openstudio-standards** | Gratuito, BSD-3. SDK 3.11.0 no PyPI, de 15/01/2026 (https://pypi.org/project/openstudio/). Duas versões por ano (https://github.com/NREL/OpenStudio/releases/tag/v3.6.0) | Sim, porque o motor é o EnergyPlus. A medida PNNL "Create ASHRAE 90.1-2019 PRM Model" gera o baseline do Apêndice G 2019 (OpenStudio 3.7.0; https://bcl.nrel.gov/content/a984a630-2a41-45fd-80ec-6454777bf253). A medida antiga "Create Baseline Building" é do OS 2.0, para 90.1 até 2013 (https://bcl.nrel.gov/content/4de56e21-b6cd-45d9-8466-862507d228b2) | SDK com bindings Python oficiais desde a 3.2.0 (`pip install openstudio`). O openstudio-standards é uma **gem Ruby** (https://github.com/NREL/openstudio-standards); do Python, roda-se pela CLI do OpenStudio. **[NÃO CONFIRMADO]** suporte ao PRM da 90.1-2022 no openstudio-standards | Não tem relatório LEED pronto. O fluxo PNNL traduz os modelos para RPD (ASHRAE 229) (https://pnnl.github.io/BEM-for-PRM/get_start/usecase_workflows/compliance_check, via trecho de busca) |
| **eQUEST / DOE-2.2** | Gratuito. Versão 3.64 (https://doe2.com/eQUEST). O download do DOE-2.2 exige termo de licença | Historicamente muito usado no LEED. Pacotes de teste ASHRAE 140 estão no site (https://doe2.com/DOE2/). **[NÃO CONFIRMADO]** adequação atual à 90.1-2019/2022; motor e interface sem evolução relevante | Não tem API Python oficial. Na prática, edição de arquivos INP por texto **[ESTIMATIVA]** | Não automatiza o relatório LEED atual **[NÃO CONFIRMADO]** |
| **Carrier HAP v6.x** | Comercial, chave de licença renovada todo ano (guia de terceiros: https://manuals.plus/carrier/v6-2-hourly-analysis-program-software-manual). **Preço não encontrado** | Sim. HAP 6.1 testado pela ASHRAE 140-2017 (qualificação DOE/179D, https://www.energy.gov/sites/default/files/2025-05/bto-hap61-1054-qs-052225.pdf). A v6.2 acrescentou análise do Apêndice G (https://hvacinsider.com/carrier-releases-hap-v6-a-major-upgrade-to-hvac-system-design-software/) | Não tem API pública **[NÃO CONFIRMADO]** | Sim. Gera um "LEED v4.0 Summary report" (mesma fonte). **[NÃO CONFIRMADO]** relatório para v4.1 ou v5 |
| **Trane TRACE 3D Plus** | SaaS com renovação anual; preço só sob cotação. O formulário de pedido (sem data) indica taxa anual de 29% do preço de lista e licenças Enterprise/Limited Enterprise (https://www.trane.com/content/dam/Trane/Commercial/global/products-systems/design-analysis-tools/analysis-tools/CDS_software_order_formV2.pdf) | Sim. Motor EnergyPlus com conhecimento Trane embutido (https://elibrary.tranetechnologies.com/public/commercial-hvac/Literature/Sales/CDS-SLB019-EN_02022021.pdf). Resultados ASHRAE 140-2020 publicados (https://www.jp.trane.com/content/dam/Trane/Commercial/software/trace-3d-plus/ASHRAE_Std140_6_10_289_compressed.pdf) | Não tem API pública **[NÃO CONFIRMADO]** | Tem um "Standards Wizard" para LEED e 90.1 (https://elibrary.tranetechnologies.com/public/commercial-hvac/Literature/Sales/CDS-SLC002-EN_06022025.pdf) |
| **IES VE** (VE-Navigator para 90.1) | Comercial, assinatura anual com renovação automática; preço sob consulta (https://www.iesweb.com/faq/Purchases.html; https://www.iesve.com/software/virtual-environment/packs) | Sim. O Navigator automatiza o PRM do Apêndice G e o ECB; a versão 2016 serve ao LEED v4.1 (https://www.iesve.com/software/virtual-environment/applications/nav-ashrae901; https://www.iesve.com/discoveries/view/20614/ashrae-901-2016). Motor próprio (ApacheSim) | API Python **[NÃO CONFIRMADO nesta pesquisa]**; sei por conhecimento prévio que o VE tem scripting Python | Sim. Gera relatórios de saída automáticos para LEED PRM e ECB (mesma fonte) |
| **DesignBuilder** | Comercial. "Engineering Plus" (EnergyPlus + 90.1/LEED + otimização), usuário único: US$ 3.050 por 1 ano, US$ 5.500 por 2 anos, US$ 7.800 por 3 anos (https://designbuilder.co.uk/engineering-plus, via trecho de busca; página sem data) | Sim. Motor EnergyPlus (v2025.1 usa E+ 23.1). Suporta o Apêndice G 2019 e as calculadoras LEED v4/v4.1 (https://designbuilder.co.uk/software/what-s-new-in-2025-1; https://support.designbuilder.co.uk/support/solutions/articles/103000411904-leed-mepc-versions-supported-in-designbuilder-v2025-1). Resultados ASHRAE 140-2023 da v7.3 (https://static.designbuilder.co.uk/download/validation). Em jul./2026 consultava usuários sobre a "90.1 Appendix G 2025" (https://onebuilding.org/archive-part2/bldg-sim-onebuilding.org/2026-July/005278.html) | Scripting **[NÃO CONFIRMADO]** | Sim. Preenche as calculadoras LEED (MEPC) v4/v4.1. **[NÃO CONFIRMADO]** suporte ao v5 |
| *Extra:* **Ladybug Tools / Pollination** | honeybee-energy 1.128.0, **AGPL-3.0** (PyPI, 06/11/2026). Receita "appendix-g-performance" 0.3.7, **PolyForm Shield 1.0.0**, que proíbe uso concorrente (PyPI JSON) | Gera baseline do Apêndice G 2016+ e calcula o PCI para 2016, 2019 e 2022, mais os pontos de "Optimize Energy Performance" do LEED v4 (https://pypi.org/project/pollination-appendix-g-performance/) | Python nativo | `appendix_g_summary.json` e `leed_summary.json` |

### 1.3 O EnergyPlus/OpenStudio pode ser o motor de uma suíte própria?

**Sim, e é o caminho usado por DesignBuilder, TRACE 3D Plus e OpenStudio.** Ver as fontes da tabela acima. O que isso exige:

1. **ASHRAE 140.** **[ESTIMATIVA/interpretação]** Se o EnergyPlus for usado sem modificar o código, a suíte pode se apoiar nos resultados de validação do próprio EnergyPlus e declarar no relatório "EnergyPlus version X". DesignBuilder e TRACE ainda assim publicam testes 140 próprios (ver links acima), o que reforça a credibilidade. Recomendo rodar a suíte BESTEST/140 na sua própria cadeia (pré-processador KAPTEK → OpenStudio → E+) e guardar o relatório. Os arquivos de apoio da 140 estão em https://data.ashrae.org/standard140/AccompanyingSection11.html. **[NÃO CONFIRMADO]** se algum revisor GBCI já pediu teste 140 de um "wrapper".
2. **Geração automática do baseline do Apêndice G.** Não reescrever as regras do zero. Usar o openstudio-standards / PNNL PRM (`Standard.build("90.1-PRM-2019")`, com a classe Translator gerando RPD), pela CLI do OpenStudio. Fonte: guia de compliance check do BEM-for-PRM (link na tabela).
   - **Lacuna:** o LEED v5 usa por padrão a 90.1-2022. A versão 2022 do PRM no openstudio-standards não foi confirmada. Pode ser preciso implementar as diferenças de 2019 para 2022 (por exemplo, o "envelope backstop", https://www.energycodes.gov/sites/default/files/2023-11/TSD_Facilitate_Adoption_ASHRAE_90-1_20231113.pdf) ou usar a opção 2019 que o LEED v5 permite.
   - Também é preciso montar a cadeia de tarifas e fatores de conversão e a rotação nas 4 orientações (o E+ já faz a rotação).
3. **Verificação de regras (ASHRAE 229 / RCT).**
   - **[FATO]** O RCT da PNNL é MIT, versão 0.5.0 de 01/02/2026 no PyPI. Cobre a 90.1-2019 Apêndice G e tem extra opcional `[ashrae9012022]`. Entrada: arquivos RPD (JSON) do usuário, do proposto e do baseline (https://pypi.org/project/ruleset-checking-tool/; https://github.com/pnnl/ruleset-checking-tool).
   - **[FATO]** A ASHRAE 229P ainda era rascunho: segunda revisão pública em out./2025 (https://osr.ashrae.org/Online-Comment-Database/ShowDoc2/Table/DocumentAttachments/FileName/4708-Std229P_2nd_PPR_Draft_V3_chair_approved.pdf/download/false; https://www.energy.gov/cmei/buildings/ashrae-standard-229p-development). **[NÃO CONFIRMADO]** publicação final em 2026.
   - **[FATO, fonte secundária]** Há relato de erro (KeyError) no passo RPD → rct229 (https://unmethours.com/questions/101739/revisions/). Conte com ferramenta ainda imatura.
4. **Relatórios LEED.** Gerar as tabelas que alimentam as calculadoras oficiais do USGBC: consumo por uso final, custos, PCI, PCI_t e dados anuais para o EAp1. Não clonar o formulário (ver riscos na seção 4).
5. **Exceções do G2.5 e documentação.** O EAc3 do v5 exige o método de cálculo excepcional para cargas de tomada e de processo (LEEDuser NC-v5 EAc3). Isso é trabalho de engenharia caso a caso; automatizar só os modelos de memorial.

---

## 2. CFD para conforto térmico e qualidade do ar no LEED

### 2.1 O LEED aceita CFD?

O LEED não exige CFD em nenhum crédito que eu tenha conseguido confirmar. Mas CFD é a evidência usada na prática em três situações:

- **Ventilação natural (LEED v4 / v4.1).** **[FATO]** No crédito Enhanced IAQ Strategies, a opção E para modo misto ("natural ventilation room-by-room calculations") pede seguir a CIBSE AM10, Seção 4, Design Calculations (https://leeduser.buildinggreen.com/credit/NC-v4/EQc1). O LEED 2009 pedia "macroscopic, multizone, analytic model" (mesma família de páginas).
  - **[FATO, fórum]** Praticantes relatam que projetos BD+C com ventilação natural costumam comprovar "com CIBSE ou modelagem CFD" (https://leeduser.buildinggreen.com/node/52553; https://leeduser.buildinggreen.com/node/52637).
  - **[FATO]** A ASHRAE 62.1-2022, Seção 6.4.2 (sistema de ventilação natural "engenheirado"), exige quantificar as vazões pelos caminhos de ar considerando pressões de vento e de empuxo térmico (https://www.ashrae.org/file%20library/technical%20resources/research/research%20project%20bidding/1918-trp.pdf). Na prática isso costuma ser feito com CFD ou com modelo multizona.
  - **[FATO]** Para a América Latina existiu um ACP, o "Verification Protocol for Engineered Natural Ventilation Systems in Equatorial Climates", com revisão de projeto pela ACAIRE, da Colômbia (LEED 2009; https://leeduser.buildinggreen.com/credit/CI-2009/IEQc2). **[NÃO CONFIRMADO]** se ele vale no v4.1 ou no v5.
- **LEED v5.** **[FATO, fonte secundária]** O crédito EQc1 Enhanced Air Quality foi reorganizado e **perdeu a opção de ventilação natural engenheirada**. O foco passou a ser vazão de ar externo 15% ou 30% acima da 62.1-2022 (https://bowman.com/news/leed-v5-mep-edition-indoor-environmental-quality; https://leeduser.buildinggreen.com/credit/CI-v5/EQc1). No v5, a demanda de CFD "por crédito" tende a cair (**[ESTIMATIVA]**).
- **Conforto térmico.** **[FATO]**
  - No v4.1 a referência é a ASHRAE 55-2017, com a 55-2020 permitida. A documentação aceita inclui gráfico psicrométrico, PMV/PPD e a CBE Thermal Comfort Tool (https://www.leeduser.buildinggreen.com/taxonomy/term/5445; https://leeduser.buildinggreen.com/node/54340).
  - Para velocidade do ar elevada, um revisor do LEED 2009 exigiu o "Computer Model Method" (SET) para risco de corrente de ar (https://leeduser.buildinggreen.com/node/31502, fórum).
  - No v5, a conformidade com a ASHRAE 55-2023 é uma opção de 1 ponto dentro do EQc2 Occupant Experience (https://leeduser.buildinggreen.com/credit/NC-v5/EQc2).
  - **[NÃO CONFIRMADO]** se o GBCI aceita mapa de PMV/PPD por CFD como documentação primária. A leitura mais segura é usar CFD como suporte (campo de velocidade e temperatura) e a ASHRAE 55 (PMV/SET/adaptativo) como critério de conformidade.
- **Outros usos (inferência):** atrios, saúde (idade do ar para a ASHRAE 170; https://www.iesve.com/software/cfd-airflow) e créditos de Inovação. **[ESTIMATIVA]**

### 2.2 Ferramentas de CFD usadas

| Ferramenta | Licença / custo | Observações |
|---|---|---|
| **IES VE MicroFlo** | Módulo do IES VE, preço sob consulta | Calcula PMV/PPD por célula, idade média do ar e eficácia de troca de ar. É acoplado ao ApacheSim e ao MacroFlo (vazões nas aberturas), e serve para ventilação natural e modo misto (https://www.iesve.com/software/virtual-environment/applications/microflo; FAQ: https://www.iesve.com/support/ve/knowledgebase_faq/faq/can-i-set-the-maximum-air-velocity-in-an-occupied-zone-to-control-the-comfort-index/1545; forum: https://forums.iesve.com/viewtopic.php?p=2626) |
| **SimScale** | Nuvem. Planos Professional e Enterprise só sob cotação; plano Community gratuito (https://simscale.com/pricing/). Valores de terceiros (US$ 125/mês) **[NÃO CONFIRMADO]** | "Pedestrian Wind Comfort" é assinatura à parte e trata de conforto externo, não interno (mesma fonte). **[NÃO CONFIRMADO]** PMV/PPD interno nativo (a cota de busca acabou) |
| **Ansys Fluent** (Airpak) | Sem preço público (https://www.g2.com/products/ansys-fluent/pricing). Valores anedóticos: cerca de US$ 25 mil perpétua mais 18–20% ao ano de manutenção **[NÃO CONFIRMADO]** (https://www.thepricer.org/ansys-cost/) | Padrão de mercado em consultoria. Situação do Airpak **[NÃO CONFIRMADO]** |
| **OpenFOAM** | Código aberto. GPL (**[conhecimento prévio, não verificado aqui]**) | Bastante usado na academia, inclusive no Brasil, para ventilação natural com o método "Elevated Air Speed" da ASHRAE (https://amcaonline.org.ar/ojs3/index.php/mc/article/download/38/39/79; https://publicacoes.softaliza.com.br/cilamce2023/article/view/5103) e para ADPI em AVAC (https://www.preprints.org/manuscript/202410.2385) |
| **DesignBuilder CFD** | Incluído em alguns pacotes **[NÃO CONFIRMADO]** | — |

**Implicação para a KAPTEK [ESTIMATIVA]:** o CFD 2D em JAX serve para triagem rápida (cortes, jatos de difusores, estratificação). Ventilação natural e conforto em ambientes reais pedem 3D com malha do edifício, condições de vento e validação. É aí que o custo de construir é alto e o valor diferencial é baixo.

---

## 3. Mercado de serviços LEED: Brasil e EUA

### 3.1 Serviços que as consultorias vendem (Brasil)

**[FATO]** O escopo típico de consultorias brasileiras (ENE Consultores e outras) e de editais inclui:
- diagnóstico LEED e scorecard;
- consultoria de projeto e de obra;
- simulação computacional de eficiência energética (pré-requisito);
- comissionamento básico (pré-requisito) e avançado (opcional);
- gestão documental junto ao USGBC.

Fontes: https://eneconsultores.com/servicos/certificacao-leed/ e o edital Senac-ES, Concorrência 011/2026, que contratou consultoria LEED Platinum com simulação e comissionamento básico e avançado para Serra e Cariacica, com peso de 80% para a consultoria LEED e 20% para o comissionamento (https://es.senac.br/licitacoes; https://es.senac.br/admin/data/dynamic/documentolicitatorio/1068/downloads/f07568f02d2f7e8e81ade5a589d73888.pdf). A empresa considerada apta foi a **VG Petinelli** (mesma página). **[NÃO CONFIRMADO]** valor global.

**[FATO]** No edital Senac-ES, a simulação energética se divide em relatórios preliminar, intermediário e final, cada um com workshop, e cita o EnergyPlus (https://es.senac.br/admin/data/dynamic/documentolicitatorio/1014/downloads/958dc76c608abbb28600e83057c4f078.pdf, via trecho de busca).

Tamanho do mercado:
- **[FATO, fonte secundária]** O Brasil ficou em 9º no ranking USGBC de 2024, por área, com 125 projetos certificados.
- **[NÃO CONFIRMADO]** 7º lugar em 2025, com 171 projetos e 2,93 milhões de m² (post no LinkedIn, https://br.linkedin.com/in/camilaanfilo).
- As alegações de "4º lugar" são de 2015–2017.

### 3.2 Honorários: o que há de dado público

| Serviço | Brasil (dado de mercado) | EUA (dado de mercado) |
|---|---|---|
| **Consultoria LEED (gestão da certificação)** | 0,5–1% do valor da obra, segundo a Sienge, blog de fornecedor (https://sienge.com.br/blog/o-que-e-certificacao-leed/, via trecho). Edital Senac citando guia Ugreen: "usual o valor de até USD 30.000 (≈ R$ 175.000)" (https://es.senac.br/admin/data/dynamic/documentolicitatorio/443/downloads/e5d86abe33d1acf87469e52800b8f1ab.pdf, via trecho) | US$ 5.000–50.000+ por projeto, a US$ 50–200/h (agregadores de baixa confiabilidade: https://everbluetraining.com/the-costs-of-leed-certification/; https://latestcost.com/leed-certification-cost-u-s-buyers/). Cushman & Wakefield (2021): US$ 31–42 mil para certificar escritório de 500.000 ft² (https://globest.com/2021/09/13/they-cost-more-to-build-but-leed-certified-assets-command-much-higher-prices) |
| **Modelagem energética (Apêndice G)** | **Nenhum dado público encontrado** | Dados antigos (2010–2012), de fórum: US$ 0,10–0,20/ft²; US$ 10–15 mil para 100.000 ft²; cerca de 40 h para um prédio médio, a cerca de US$ 100/h; documentação no LEED Online cobrada à parte (https://onebuilding.org/archive/bldg-sim-onebuilding.org/2011-May/041854.html; https://energy-models.com/leed-and-energy-modeling; https://unmethours.com/question/2/how-much-does-it-cost-to-create-a-model). **Baixa confiabilidade** |
| **Comissionamento (CxA)** | **Nenhum dado público em R$/m² encontrado** | Meta-análise LBNL (Mills, 2009): mediana de **US$ 1,16/ft²**, cerca de **0,4% do custo da obra** em construção nova, em dólares de 2009 (https://cx.lbl.gov/2009-assessment.html; https://eta-publications.lbl.gov/bibcite/reference/30498). Fórum: US$ 0,35–0,75/ft² (https://leeduser.buildinggreen.com/node/50627) |
| **M&V** | Nenhum dado encontrado | Nenhum dado encontrado nesta pesquisa |
| **Taxas GBCI** | — | Registro: US$ 1.350 (membro) / US$ 1.700 (não membro). Certificação BD+C em torno de US$ 0,064/ft² **[NÃO CONFIRMADO]**. Recurso: US$ 700 por crédito desde 27/03/2026 **[conflita com outra fonte que dá US$ 500]** (https://archiroots.com/leed-certified-buildings). Reajuste de cerca de 12% em 01/05/2023 (https://blog.zeroconsulting.com/en/changes-in-leed-registration-and-certification-fees) |
| **Sobrecusto da obra** | 3–7% (CBIC, https://cbic.org.br/certificacao-para-sustentabilidade-atrai-as-empresas/). Estudo de caso UFMG: +1,84% (https://repositorio.ufmg.br/handle/1843/31234) | — |
| **Custo-hora de referência** | GOINFRA, jun./2025: "Engenheiro/Profissional Sênior" de R$ 85,64 a 153,48 por hora. Não está claro o que cada coluna representa (https://goias.gov.br/goinfra/wp-content/uploads/sites/77/tabela-de-composicao/87/arquivos/). Tabelas de honorários: ABENC-MT (https://www.crea-mt.org.br/portal/wp-content/uploads/2021/07/A-TABELA-DE-HONORARIOS-BASICOS-PROFISSIONAIS-DA-ABENC.pdf) e convenção coletiva SEESP×SINAENCO 2025-26 (https://seesp.org.br/site/images/Acordos_2025/CCT-SP-SEESPxSINAENCO_2025-2026.pdf) | — |

### 3.3 [ESTIMATIVA KAPTEK] Faixas de referência para precificar (não são dados de mercado)

Premissas: câmbio de R$ 5,40/US$ e inflação americana de 2009 a 2026 de cerca de 1,5×. Ambas são suposições não verificadas. Custo de serviço no Brasil entre 40% e 60% do nível americano, também suposição.

- **Modelagem do Apêndice G (proposto + baseline × 4 orientações + documentação):** de 150 a 400 h, conforme a complexidade. Edifício comercial de 10.000 m²: **R$ 40–100 mil**, ou cerca de **R$ 4–10/m²**. Conta: US$ 0,15–0,30/ft² atualizado ≈ US$ 1,6–3,2/m² ≈ R$ 9–17/m² no nível EUA; vezes 0,4–0,6.
- **Comissionamento fundamental + avançado:** Mills atualizado dá cerca de US$ 1,75/ft² ≈ US$ 19/m² ≈ R$ 100/m² no nível EUA. No Brasil, **R$ 30–60/m²**, ou **0,3–0,5% da obra**. Em obra de R$ 30 milhões: R$ 90–150 mil.
- **Consultoria LEED (gestão):** 0,5–1% da obra (dado Sienge). Em obra de 10.000 m² a cerca de R$ 3.000/m² (suposição), dá **R$ 150–300 mil**. Bate com o "até US$ 30 mil (≈ R$ 175 mil)" citado no edital Senac.
- Valide essas faixas com 2 ou 3 cotações reais, ou com atas no PNCP buscando "LEED" e "comissionamento".

---

## 4. Riscos

### 4.1 Marca e licenciamento

- **Marca LEED/USGBC [FATO].**
  - As diretrizes do USGBC proíbem usar as marcas para sugerir parceria ou endosso. Também listam como uso restrito colocar a marca em nome de organização, produto, domínio ou logo. O logo do programa LEED é de uso exclusivo do USGBC/GBCI e depende de permissão escrita do departamento de marketing (https://usgbc.gitbook.io/brand-identity-systems/usgbc-brand-identity-system/general-brand-guidelines; https://usgbc.gitbook.io/brand-identity-systems/gbci-products/leed/leed-program-logo).
  - As diretrizes canadenses exigem acordo escrito para produtos de terceiros (https://www.cagbc.org/wp-content/uploads/2025/05/LEED-trademark-policy-and-brand-guidelines_EN_2025-05.pdf).
  - **Ação:** não usar "LEED" no nome do produto ou módulo. Usar descrições como "apoio à documentação de créditos LEED®", com aviso de marca registrada.
- **Calculadoras e formulários oficiais [ESTIMATIVA/risco].** Não replicar nem redistribuir as planilhas USGBC dentro da suíte. Gerar os dados de entrada e orientar o preenchimento da planilha oficial, que muda com as adendas: há adendas de nov./2025 (https://www.cagbc.org/news-resources/cagbc-news/leed-addenda-update-november-2025).
- **EnergyPlus [FATO].** A licença exige chamar o software de "EnergyPlus version X" e proíbe usar "EnergyPlus", "E+" ou "e+" em nome de empresa, produto ou publicidade sem consentimento do DOE. Também proíbe usar os nomes do DOE ou dos laboratórios para endossar (https://github.com/NREL/EnergyPlus/blob/develop/LICENSE.txt).
- **Licenças "contaminantes" [FATO].**
  - honeybee-energy é **AGPL-3.0**: um SaaS com código modificado teria de abrir o código.
  - A receita Pollination Appendix G é **PolyForm Shield**: proíbe produto concorrente.
  - BESOS é **GPLv3**.
  - OpenFOAM é GPL (conhecimento prévio).
  - Opções seguras para uma suíte proprietária: OpenStudio (BSD-3), eppy e geomeppy (MIT), RCT (MIT) e EnergyPlus (estilo BSD).
- **ASHRAE.** O texto das normas (90.1, 140, 229P) é protegido por copyright. Implementar as regras é permitido, mas não se pode reproduzir tabelas e texto na interface ou nos relatórios **[ESTIMATIVA]**.

### 4.2 Credenciais

| Papel | Exigência no LEED | Custo e manutenção |
|---|---|---|
| **LEED AP BD+C** | Não é obrigatório. Ter um LEED AP na equipe historicamente vale 1 ponto em Inovação (conhecimento prévio, **[NÃO CONFIRMADO]** no v5) | Prova: US$ 250 (membro) / US$ 350, ou combo GA + AP de US$ 400 / 550 **[NÃO CONFIRMADO, sites de preparação]** (https://open-exam-prep.com/study-guides/leed-ap-bdc/introduction/exam-facts). Manutenção: 30 horas de CE a cada 2 anos, sendo 6 específicas LEED (**[FATO]** https://usgbc.gitbook.io/credential-maintenance-program-cmp-guide). Versão da prova (v4.1 ou v5) **[NÃO CONFIRMADO]** |
| **CxA** | **[FATO, v4/v4.1]** Experiência em pelo menos 2 projetos de escopo similar, do projeto até 10 meses de ocupação. Pode ser empregado do proprietário, consultor independente ou funcionário de empresa de projeto ou obra que não faça parte da equipe. Em projetos com menos de 20.000 ft² (1.860 m²), pode ser membro qualificado da equipe (https://cxplanner.com/commissioning-101/leed-v4; https://leeduser.buildinggreen.com/node/64500). LEED não exige certificação formal (ACG, BCxA etc.) **[ESTIMATIVA, conforme o texto]**. Requisitos do v5 **[NÃO CONFIRMADO]** | — |
| **Modelador (ASHRAE BEMP)** | Não é exigido pelo LEED **[ESTIMATIVA, nenhuma fonte encontrada que exija]**. É diferencial de credibilidade | Prova: US$ 495 (membro) / US$ 745. Renovação a cada 3 anos (https://www.bdcnetwork.com/home/article/55259960/a-new-certification-validates-decarbonization-expertise; https://www.ashrae.org/education-certification/certification/bemp-building-energy-modeling-professional-certification) |
| **Brasil** | ART no CREA para simulação, projeto e comissionamento **[conhecimento prévio, não pesquisado]** | — |

### 4.3 Riscos técnicos e de mercado

- **Transição para o v5 e para a 90.1-2022.** Se o PRM 2022 não estiver no openstudio-standards, a KAPTEK terá de implementar ou validar as diferenças, ou documentar pela opção 2019 que o v5 permite.
- **Concorrência.** DesignBuilder custa cerca de US$ 3 mil por ano e já entrega 90.1 + LEED. O diferencial da suíte precisa ser integração (carga RTS → modelo energético → orçamento → Cx), não o motor.
- **Aceitação pelo revisor.** O revisor GBCI recebe o modelo e os relatórios. Uma ferramenta própria sem histórico pode atrair pedidos de esclarecimento. Mitigação: rodar o RCT/229, guardar a validação BESTEST e anexar os arquivos IDF/OSM.

---

## 5. Recomendação: construir × integrar, por capacidade

| # | Capacidade | Decisão | Justificativa |
|---|---|---|---|
| 1 | Motor de simulação energética anual | **INTEGRAR** EnergyPlus (26.x) via OpenStudio SDK Python (BSD-3) | Exigência da ASHRAE 140, motor aceito no mercado, licença permissiva. Construir um motor próprio não tem retorno |
| 2 | Tradutor da modelagem KAPTEK (zonas, cargas RTS, sistemas) para OpenStudio/IDF | **CONSTRUIR** | É o diferencial: reaproveita os dados do python-hvac. Use eppy/geomeppy (MIT) ou a API do OpenStudio; evite honeybee (AGPL) no núcleo |
| 3 | Baseline automático do Apêndice G | **INTEGRAR** openstudio-standards / PNNL PRM 2019 pela CLI. **CONSTRUIR** só a camada de orquestração, as exceções e o delta 2019→2022 se faltar | As regras são extensas e mantidas por laboratório federal. Reescrever seria caro e arriscado |
| 4 | Verificação de regras (QA do modelo) | **INTEGRAR** RCT PNNL (MIT) com exportação RPD | Antecipa a ASHRAE 229 e reduz idas e voltas com o revisor. Tratar como ferramenta beta |
| 5 | Relatórios e pacote de documentação LEED (PCI, usos finais, dados do EAp1, memoriais G2.5) | **CONSTRUIR**, com nome neutro, alimentando as calculadoras oficiais | Valor direto para o cliente. Não replicar nem distribuir planilhas USGBC e não usar "LEED" no nome do produto |
| 6 | Carga térmica (RTS) | **MANTER** (já existe). Acrescentar comparação com o dimensionamento do EnergyPlus | — |
| 7 | CFD 2D em JAX | **MANTER** como triagem e P&D | Rápido e próprio, mas não substitui 3D em entregável |
| 8 | CFD 3D de entregável (ventilação natural, átrios, velocidade de ar elevada) | **INTEGRAR**: OpenFOAM como processo externo, sem linkar, para evitar a GPL; ou SimScale/IES por projeto | Demanda pontual, e o LEED v5 tirou a opção de ventilação natural engenheirada do EQc1. Construir 3D validado é caro |
| 9 | Pós-processamento de conforto (PMV/PPD, SET, adaptativo ASHRAE 55-2023) | **CONSTRUIR** em cima de biblioteca aberta. Candidata: pythermalcomfort, licença **[NÃO CONFIRMADO]** | Barato de fazer e útil para o EQc2 do v5 e para laudos |
| 10 | Gestão de comissionamento (OPR/BOD, checklists, FPT, registro de pendências, relatório do CxA) | **CONSTRUIR** (em português, ligado ao orçamento) | Há SaaS americanos (CxPlanner, Bluerithm), mas não achei oferta em PT-BR (**[NÃO CONFIRMADO]**). O comissionamento é cerca de 20% do valor no edital Senac e serviço recorrente |
| 11 | M&V e calibração (ASHRAE Guideline 14: CV(RMSE)/NMBE; IPMVP) | **CONSTRUIR** módulo leve sobre o motor integrado | Métricas simples; reaproveita o modelo do LEED |
| 12 | Orçamento de serviços LEED | **CONSTRUIR**: estender o motor atual com parâmetros de área, créditos e opções (modelagem, comissionamento fundamental e avançado, M&V) | Calibrar com as faixas da seção 3.3 e com cotações reais |
| 13 | Ferramenta comercial de referência | **COMPRAR** 1 licença (DesignBuilder Engineering Plus, cerca de US$ 3.050/ano, ou IES VE) durante 12–18 meses | Benchmark e QA da suíte e entregas enquanto o pipeline próprio amadurece **[ESTIMATIVA]** |
| 14 | Credenciais | **INVESTIR**: pelo menos 1 LEED AP BD+C, 1 profissional com experiência de CxA (2 projetos) e, a médio prazo, 1 BEMP | A ferramenta não substitui a credencial na proposta |

### Principais incertezas que pedem verificação antes de decidir
1. Suporte ao PRM 90.1-2022 no openstudio-standards e no RCT (o extra `ashrae9012022` existe; a maturidade não foi verificada).
2. Texto oficial do LEED v5 BD+C (EAp2, EAc3, EQc2) e as calculadoras v5. Li só trechos do LEEDuser.
3. Preços de HAP, IES VE, TRACE 3D Plus e SimScale: todos sob cotação.
4. Honorários brasileiros por serviço: não há dado público consolidado. Os números da seção 3.3 são estimativa minha.
5. Datas de fim de registro do v4/v4.1 e se existe ACP brasileiro (PBE Edifica/INI-C) no v5.
