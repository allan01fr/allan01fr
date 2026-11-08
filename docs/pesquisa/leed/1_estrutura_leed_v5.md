# Estrutura atual do LEED (situação em novembro de 2026)

Relatório de pesquisa preparado para a KAPTEK (Rio de Janeiro), para avaliar como uma suíte de engenharia HVAC-R pode apoiar projetos LEED. Data de referência: 08/11/2026.

---

## 0. Nota metodológica (leia antes)

- **Acesso às fontes primárias:** nesta sessão, a busca na web funcionou, mas o download direto de páginas de `www.usgbc.org` e `www.gbci.org` foi **bloqueado pela rede da sessão** (DNS não resolvido). Os fatos abaixo vêm de **trechos de documentos primários do USGBC/GBCI indexados pelo buscador** (PDFs dos sistemas de avaliação, páginas de prazos e de taxas, central de suporte) e, quando indicado, de fontes secundárias. Em nenhum caso foi possível ler o documento inteiro. Para validar números críticos (pontos por crédito, taxas), libere `usgbc.org` e `gbci.org` na rede da sessão e repita a leitura direta.
- **Legenda de confiabilidade:**
  - **[P]**: fonte primária (USGBC/GBCI/CaGBC), confirmada por trecho.
  - **[S]**: fonte secundária (consultoria, imprensa técnica).
  - **[?]**: não confirmado, conflitante ou possivelmente desatualizado.
- Os PDFs do LEED v5 tiveram várias edições: lançamento (abr/2025), nov/2025, fev/2026 e **jul/2026, a mais recente encontrada**. Os pontos por crédito **variam entre as edições**. Use sempre a edição vigente.

---

## 1. Sistemas de avaliação e tipologias

### 1.1 Visão geral (o que existe hoje)

| Sistema | Versões abertas a novos registros (nov/2026) | Plataforma | Observações |
|---|---|---|---|
| **BD+C** (Building Design and Construction) | v5; v4 e v4.1 até 30/06/2027 | v5: Arc. v4/v4.1: LEED Online | A v5 é obrigatória para novos registros comerciais a partir de 01/07/2027 [P] |
| **ID+C** (Interior Design and Construction) | v5; v4 e v4.1 até 30/06/2027 | Idem | Idem [P] |
| **O+M** (Operations and Maintenance) | v5; v4.1 até 30/06/2027 (inclui recertificação) | Idem | Recertificação v5 em ciclos de 3 anos [P] |
| **ND** (Neighborhood Development) | v4 (Plan / Built Project) | LEED Online | Não aparece na tabela de encerramento de prazos. Não há v5 ND confirmada [?] |
| **Residential / Homes** | v4.1 Residential (Single Family, Multifamily, Multifamily Core and Shell); v4 Homes | LEED Online | **Não há v5 residencial dedicada.** Multifamiliar com 4 ou mais pavimentos acima do solo pode usar a v5 BD+C [P] |
| **Cities and Communities** | v4.1 (Plan and Design; Existing) | Arc | **LEED v5 for Cities** foi a consulta pública em nov/2025 (rascunho com 110 pontos) [P] |
| **LEED Zero** (Carbon, Energy, Water, Waste) | Aberto a qualquer projeto já certificado LEED | Arc | Os prazos de encerramento da v4/v4.1 não se aplicam [P] |

Fontes:
- Prazos e sistemas: https://www.usgbc.org/tools/leed-certification/deadlines [P]
- v4.1 (residencial e cidades): https://www.usgbc.org/leed/v41 [P]
- Residencial: https://www.usgbc.org/leed/rating-systems/residential [P]
- Guia de seleção do sistema: https://www.usgbc.org/leed-tools/rating-system-selection-guidance [P]
- ND: https://www.usgbc.org/tools/leed-certification/neighborhood [P]
- Cities v5 (rascunho): https://www.usgbc.org/sites/default/files/2025-10/LEED-v5-Cities-Rating-System-Draft-1_0.pdf e https://www.usgbc.org/sites/default/files/2025-10/LEED-v5-for-Cities-Public-Comment-Guide.pdf [P]
- Cities v4.1: https://www.usgbc.org/articles/leed-v41-launches-cities-and-communities [P]

### 1.2 Tipologias por sistema: v4/v4.1 × v5

| Sistema | v4 / v4.1 ("adaptações" = sistemas separados) | **v5** (tipologias consolidadas) |
|---|---|---|
| BD+C | New Construction; Core and Shell; Schools; Retail; Healthcare; Data Centers; Hospitality; Warehouses and Distribution Centers. A v4 também tinha Homes/Multifamily Lowrise e Midrise [?, de memória, não reconfirmado] | **New Construction** e **Core and Shell** apenas. Escolas, varejo, saúde, data centers, armazéns, hotelaria e residencial são tratados **dentro** dos pré-requisitos e créditos, por regras específicas de tipologia. Essas regras se aplicam quando a tipologia ocupa 60% ou mais da área bruta. |
| ID+C | Commercial Interiors; Retail; Hospitality | **Commercial Interiors** |
| O+M | v4.1: Existing Buildings; Existing Interiors. A v4 tinha várias adaptações (Retail, Schools, Hospitality, Data Centers, Warehouses, Multifamily) [?, de memória] | **Existing Buildings** (com caminhos específicos por tipologia e pelo ENERGY STAR) |

Detalhes da v5 relevantes para HVAC:
- **Data centers:** os caminhos prescritivos de EAp2 (Minimum Energy Efficiency) e EAc (Enhanced Energy Efficiency) foram feitos para data centers, inclusive colocation. O Core and Shell é recomendado quando mais de 40% da área estiver incompleta na certificação [P/S].
- **Armazéns:** o crédito *Sensitive Project Location* tem pontos para data centers, armazéns e centros de distribuição. Projetos com 60% ou mais da área em armazém/distribuição têm 20% de desconto na taxa de certificação [P].
- **Escolas:** há um crédito ou opção específica para escolas no BD+C. **Saúde:** há exclusões específicas, como pacientes na contagem de ocupantes [P].

Fontes:
- https://www.usgbc.org/tools/leed-certification/deadlines (lista das tipologias v4.1) [P]
- Suporte v5: https://support.usgbc.org/hc/en-us/articles/25316160948755-LEED-v5 [P]
- Data centers: https://support.usgbc.org/hc/en-us/articles/12154267763987-Applying-LEED-to-data-center-projects [P]
- Armazéns: https://support.usgbc.org/hc/en-us/articles/12089652865683-Applying-LEED-to-warehouse-and-distribution-center-projects [P]
- Hotelaria: https://support.usgbc.org/hc/en-us/articles/12127181820435-Applying-LEED-to-hospitality-and-venue-projects [P]
- Varejo: https://support.usgbc.org/hc/en-us/articles/12158168044819-Applying-LEED-to-retail-projects [P]
- CaGBC, tipologias na v5 (regra dos 60%): https://www.cagbc.org/news-resources/cagbc-news/healthcare-schools-and-other-unique-project-types-in-leed-v5/ [P, conselho nacional]
- BD+C v5, ed. fev/2026: https://www.usgbc.org/sites/default/files/2026-03/LEED%20v5%20BD+C%20Rating%20System_February%202026.pdf [P]

---

## 2. LEED v5

### 2.1 Cronologia

| Data | Evento | Fonte |
|---|---|---|
| abr/2024 a 2025 | Consultas públicas, com a 1ª em abr/2024 | https://www.usgbc.org/articles/us-green-building-council-releases-leed-v5-public-comment ; https://www.usgbc.org/sites/default/files/2024-04/LEED-Exploring-LEED-v5.pdf [P] |
| **28/03/2025** | Ratificação pelos membros do USGBC | https://support.usgbc.org/hc/en-us/articles/25316160948755-LEED-v5 [P] |
| **abr/2025** (anúncio em 28/04/2025) | Lançamento da v5 para BD+C, ID+C e O+M e abertura do registro no Arc | https://www.usgbc.org/articles/us-green-building-council-launches-new-more-comprehensive-leed-rating-system-sustainable [P]; https://www.architecturalrecord.com/articles/17514-us-green-building-council-announces-launch-of-leed-v5 [S] |
| 19/08/2025 | Primeiros projetos certificados na v5, em O+M (12 milhões de ft², 9 países) | https://cmmonline.com/news/first-projects-achieve-leed-v5-certification [S] |
| **03/11/2025** | Certificação v5 aberta no Arc para todos os sistemas comerciais: créditos, upload e revisão | https://www.usgbc.org/articles/usgbc-opens-leed-v5-project-certification-unveils-new-tools-and-resources-world-s-most [P]; https://facilityexecutive.com/usgbc-opens-leed-v5-project-certification [S] |
| nov/2025 | Consulta pública do LEED v5 for Cities | link na seção 1.1 [P] |
| fev/2026 | Abertura do registro para os **exames beta** LEED v5 (GA e AP), não para projetos | https://www.gbci.org/leed-v5-beta-exams-launch-2026 [P] |
| jul/2026 | Edição de julho de 2026 do sistema BD+C v5, com correções do guia em 31/07/2026 | https://www.usgbc.org/sites/default/files/2026-07/LEED%20v5%20BD+C%20Rating%20System_July%202026.pdf [P] |
| **01/07/2027** | A v5 passa a ser a **única** versão para novos registros comerciais (BD+C, ID+C, O+M), com "exceções limitadas" | https://www.usgbc.org/tools/leed-certification/deadlines [P] |

[?] Uma fonte relata que uma loja em Curitiba recebeu Platinum v5 em out/2024. Isso é incompatível com a cronologia oficial e foi desconsiderado.

### 2.2 Situação em novembro de 2026

- A v5 está **em plena operação** para BD+C (NC e CS), ID+C (CI) e O+M (EB). O registro e a documentação são feitos **exclusivamente no Arc** [P]. Há **pré-certificação** para BD+C NC e CS [P] (https://support.usgbc.org/hc/en-us/articles/25316160948755-LEED-v5).
- As **taxas da v5 são iguais às da v4/v4.1** [S] (https://clearvue.business/leed-v5-explained-a-practical-guide-to-the-new-green-building-rating-system/).
- Ainda não existem v5 para ND, Residential (exceto multifamiliar com 4+ pavimentos via BD+C) e Cities (em consulta).
- Mais créditos de *Project Priorities* estavam previstos para 2026 [S].

### 2.3 Áreas de impacto e conceitos transversais

- Três **áreas de impacto**: **Decarbonization**, **Quality of Life** e **Ecological Conservation and Restoration**. Todo crédito e pré-requisito é vinculado a pelo menos uma delas. Equidade e resiliência são conceitos transversais definidos pelo Steering Committee [P] (https://www.usgbc.org/sites/default/files/2025-04/LEED-BDC-v4-v5-Summary-of-Changes.pdf).
- **Cerca de 50% dos pontos** estão ligados à descarbonização, segundo a cobertura do lançamento [S] (https://www.esgtoday.com/usgbc-launches-new-sustainable-buildings-leed-rating-system/). [?] Não encontrei a divisão oficial de pontos por área de impacto.

### 2.4 Categorias e pontuação: BD+C v5 (New Construction / Core and Shell)

Fonte principal: fact sheet do USGBC (mai/2025), https://www.usgbc.org/sites/default/files/2025-05/LEED_LEED-v5-One-Pagers-Fact-Sheet_BD+C_v4_DL.pdf [P], com conferências na ed. jul/2026 (link na seção 2.1). **[?] Os pontos de alguns créditos mudaram entre as edições.**

| Categoria | Pontos NC | Pontos CS | Pré-requisitos (obrigatórios) |
|---|---|---|---|
| Integrative Process, Planning and Assessments (IP) | 1 | 1 | **Climate Resilience Assessment**; **Human Impact Assessment** |
| Location and Transportation (LT) | 15 | 15 | — |
| Sustainable Sites (SS) | 11 | 11 | Minimized Site Disturbance |
| Water Efficiency (WE) | 9 | 8 | Water Metering and Reporting (inferido; [?]) |
| **Energy and Atmosphere (EA)** | **33** | 27 | **Operational Carbon Projection and Decarbonization Plan**; **Minimum Energy Efficiency**; Fundamental Commissioning; Energy Metering and Reporting; **Fundamental Refrigerant Management** |
| Materials and Resources (MR) | 18 | 18 [?] | Planning for Zero Waste Operations; **Quantify and Assess Embodied Carbon** |
| Indoor Environmental Quality (EQ) | 13 | 13 [?] | Construction Management; Fundamental Air Quality; No Smoking or Vehicle Idling |
| Project Priorities (PR: inovação, prioridade regional, créditos-piloto e créditos adaptados por tipologia) | 10 | 10 | — |
| **Total** | **110** | **110** | |

Créditos de EA no BD+C NC (fact sheet 2025; entre parênteses, NC/CS na ed. jul/2026 quando difere):
- **Electrification**: 5 (5/4)
- **Reduce Peak Thermal Loads**: 5. É um crédito novo, focado na envolvente e na redução da demanda de pico de aquecimento e resfriamento. Veio de um crédito-piloto da v4 e permite equipamentos de HVAC menores.
- **Enhanced Energy Efficiency**: 10 (10/7). Substitui o *Optimize Energy Performance*, que tinha 18 pontos na v4.
- **Renewable Energy**: 5 (5/4)
- **Enhanced Commissioning**: 4
- **Grid Interactive**: 2. Absorveu parte do Advanced Energy Metering e incluiu armazenamento.
- **Enhanced Refrigerant Management**: 2. Prevê fluido de GWP ultrabaixo e minimização de vazamentos.

Fontes: https://www.usgbc.org/sites/default/files/2025-04/LEED-BDC-v4-v5-Summary-of-Changes.pdf [P]; https://www.usgbc.org/sites/default/files/2025-05/LEED_LEED-v5-One-Pagers-Fact-Sheet_Decarbonization.pdf [P].

Outros créditos citados (NC):
- **LT:** Sensitive Land Protection 1; Equitable Development 2; Compact and Connected Development 6; Transportation Demand Management 4; Electric Vehicles 2.
- **SS:** Biodiverse Habitat 2; Accessible Outdoor Space 1; Enhanced Resilient Site Design 2; Rainwater Management 3 [?]; Heat Island Reduction 2.
- **WE:** Water Metering and Leak Detection 1; Enhanced Water Efficiency 8.
- **MR:** Building and Materials Reuse 3; **Reduce Embodied Carbon 6**; Building Product Selection 5; C&D Waste Diversion 2.
- **EQ:** Enhanced Air Quality 1; **Occupant Experience 7**, que inclui conforto térmico pela **ASHRAE 55-2023**; Accessibility and Inclusion; **Resilient Spaces**; **Air Quality Testing and Monitoring** [?: 2 pts no BD+C segundo fonte secundária, 4 pts no ID+C].

Fontes:
- https://leeduser.buildinggreen.com/credit/NC-v5/EQc2 [S]
- https://learn.kaiterra.com/en/resources/comparison-of-indoor-air-quality-in-leed-v5-and-leed-v4.1-certification [S]
- https://www.cagbc.org/wp-content/uploads/2025/04/LEED-v5-BDC-Fact-Sheet.pdf [P]

**Base normativa de energia (BD+C/ID+C):** ASHRAE 90.1-2019 ou 90.1-2022 à escolha para projetos registrados **antes de 01/01/2028**. A partir dessa data, apenas a 90.1-2022 (Option 2) [S, a confirmar]. O caminho de desempenho, por simulação, passa a usar **energia-fonte futura** (fator elétrico site-to-source igual a 2,0, refletindo a descarbonização da rede) e emissões, e **não mais custo**. [?] Uma fonte ainda menciona custo, o que precisa ser verificado no guia de referência. A NECB 2020 é aceita como alternativa no Canadá. No **EAp1**, o USGBC fornece uma **projeção de carbono de 25 anos** (operação, refrigerantes e carbono incorporado). A equipe faz a análise de projeto, a estimativa de energia e o plano de descarbonização. Quem obtém 4 a 5 pontos em Electrification fica isento do plano.

Fontes:
- https://docs.betterbuilding.io/support-and-training/other-support/faqs/leed/leed-minimum-energy-performance-v4.1-vs-v5.0 [S]
- https://www.cagbc.org/news-resources/cagbc-news/necb-2020-recognized-as-alternative-path-in-leed-v5/ [P]
- https://www.cagbc.org/news-resources/cagbc-news/what-new-prerequisites-under-leed-v5-mean-for-projects/ [P]
- https://leeduser.buildinggreen.com/blog/finally-clear-zero-emissions-standard-and-leed-v5-board [S]

### 2.5 ID+C v5 (Commercial Interiors) e O+M v5 (Existing Buildings): parcial

| Categoria | ID+C (CI) | O+M (EB) |
|---|---|---|
| IP | ? | 2 (inferido da soma) [?] |
| LT | ? | 8 |
| SS | n/a | 2 |
| WE | ? | 15 |
| EA | ? (cerca de 38 segundo fonte secundária) [?] | **34** |
| MR | 26 | 13 |
| EQ | 18 | 26 (soma EQc1 a EQc8) |
| PR | 10 [?] | 10 [?] |
| Total | 110 | 110 |

O+M v5 em detalhe:
- **EAp Minimum Energy Performance** tem três opções: ENERGY STAR **≥ 60** (era 75 na v4), metas de EUI ou melhoria em relação à linha de base histórica. Imóveis elegíveis ao ENERGY STAR nos EUA e no Canadá são obrigados a usá-lo. **No Brasil, pode-se usar o ENERGY STAR ou a EUI.**
- **Optimized Energy Performance** vale 2 a 12 pontos (ENERGY STAR de 69 a 92).
- **GHG Emissions Reduction** vale até 12 pontos. **Decarbonization and Efficiency Plans** vale 1 a 5 pontos, com plano de capital de 5 anos que reduza no mínimo 5% das emissões diretas e 5% da energia.
- O **pré-requisito de refrigerantes** passa a exigir política de gestão e rastreamento do GWP dos vazamentos.

Fontes:
- ID+C: https://www.usgbc.org/sites/default/files/2025-05/LEED_LEED-v5-One-Pagers-Fact-Sheet_ID+C_v4_DL.pdf ; https://www.usgbc.org/sites/default/files/2025-10/LEED%20v5%20ID+C%20Rating%20System_November%202025_clean.pdf [P]
- O+M: https://www.usgbc.org/sites/default/files/2025-05/LEED_LEED-v5-One-Pagers-Fact-Sheet_O+M_v4_DL.pdf ; https://www.usgbc.org/sites/default/files/2025-10/LEED%20v5%20O+M%20Rating%20System_November%202025_clean.pdf ; https://www.usgbc.org/sites/default/files/2025-04/LEED-OM-v41-v5-Summary-of-Changes.pdf [P]

### 2.6 Níveis de certificação

| Nível | Pontos | Exigência adicional na v5 |
|---|---|---|
| Certified | 40–49 | — |
| Silver | 50–59 | — |
| Gold | 60–79 | — (nenhuma exigência extra encontrada) |
| **Platinum** | **80+** | **Mínimos de carbono obrigatórios.** **BD+C NC:** Electrification 5 pts; Enhanced Energy Efficiency ≥ 8 pts; renovável equivalente a 100% da energia aplicável; redução de 20% do carbono incorporado (MR Reduce Embodied Carbon) [S, a confirmar na ed. jul/2026]. **O+M:** ENERGY STAR ≥ 80, meta *NextGen* de emissões diretas, compra de renovável e pontos mínimos em GHG Reduction e Decarbonization Plans [P]. **LEED Zero Carbon (O+M):** ENERGY STAR ≥ 85 [P]. |

Fontes:
- https://www.usgbc.org/tools/leed-certification/commercial [P]
- https://www.usgbc.org/sites/default/files/2025-10/LEED-v5-Recertification-Guidance.pdf [P]
- https://www.usgbc.org/sites/default/files/2025-02/GB24_B13_slides.pdf [P]
- https://www.3foldtraining.com/leed-v5-platinum-requirements/ [S]
- https://www.aia.org/aia-architect/article/what-you-should-know-about-leed-version-5 [S]

Na prática, um projeto Platinum v5 de edifício novo **não pode ter queima de combustível fóssil no local**, exceto em emergências [S].

### 2.7 Principais diferenças entre v4/v4.1 e v5

| Tema | v4 / v4.1 | v5 |
|---|---|---|
| **Descarbonização operacional** | Optimize Energy Performance, até 18 pts, com métrica de custo (v4) ou custo e GHG (v4.1) | Pontos divididos entre Electrification, Reduce Peak Thermal Loads, Enhanced Energy Efficiency (energia-fonte futura e GHG), Renewable Energy e Grid Interactive. Novo pré-requisito **Operational Carbon Projection and Decarbonization Plan**. Cerca de 50% dos pontos ligados a carbono. |
| **Carbono incorporado** | Crédito de LCA, opcional | **Pré-requisito** de quantificação do GWP (A1–A3: estrutura, envoltória e pavimentos externos; 3 *hot spots*) e crédito de redução de até 6 pts. 20% de redução obrigatório para Platinum. |
| **Refrigerantes** | Pré-requisito focado na eliminação de CFC; crédito de impacto (LCGWP + LCODP) | Pré-requisito com **inventário, GWP máximo e teste de vazamento** (permite edificações sem refrigerante). Crédito Enhanced (2 pts) para GWP ultrabaixo e vazamento mínimo. No O+M, política de gestão e rastreio do GWP vazado. A projeção de 25 anos inclui refrigerantes. |
| **Resiliência** | Créditos-piloto | Pré-requisito **Climate Resilience Assessment**, créditos Enhanced Resilient Site Design e **Resilient Spaces** (EQ) |
| **Equidade / impacto humano** | Créditos-piloto de equidade social | Pré-requisito **Human Impact Assessment** (comunidade, força de trabalho e cadeia de suprimentos), Equitable Development (LT) e Accessibility and Inclusion (EQ) |
| **Qualidade de vida / IEQ** | Thermal Comfort, IAQ Assessment, Daylight e Views separados | Créditos consolidados em **Occupant Experience** (térmico pela ASHRAE 55-2023, iluminação, acústica e vistas), Enhanced Air Quality e Air Quality Testing and Monitoring (monitoramento contínuo) |
| **Platinum** | Apenas 80+ pontos | 80+ pontos **e** mínimos obrigatórios de carbono |
| **Tipologias** | Adaptações como sistemas separados | NC/CS/CI/EB, com regras por tipologia dentro dos créditos (≥ 60% da área) |
| **Plataforma** | LEED Online | **Arc** |
| **Validade O+M** | v4: 5 anos; v4.1: 3 anos | 3 anos |

Fontes:
- https://www.usgbc.org/sites/default/files/2025-04/LEED-BDC-v4-v5-Summary-of-Changes.pdf [P]
- https://www.usgbc.org/sites/default/files/2024-05/LEED-v5-summary-of-changes-LEED-v4-LEED-v41-BDC.pdf [P]
- https://www.usgbc.org/sites/default/files/2025-04/LEED-OM-v41-v5-Summary-of-Changes.pdf [P]
- https://www.usgbc.org/sites/default/files/2026-02/LEED%20V5%20Materials%20as%20Climate%20System%20Article%20Course-V1.pdf [P]

---

## 3. Situação da v4 e da v4.1 e regras de transição

| Item | Data | Fonte |
|---|---|---|
| Encerramento de **novos registros** v4/v4.1 (BD+C, ID+C, O+M e O+M Recertification; inclui o Transit Stations Pilot) | **30/06/2027**, prorrogado. O plano original era o fim do 1º trimestre de 2026 e depois 30/06/2026. | https://www.usgbc.org/tools/leed-certification/deadlines ; https://www.usgbc.org/articles/reminder-upcoming-leed-registration-close-dates [P]; https://www.greenengineer.com/news/usgbc-extends-leed-v4-and-v4-1-commercial-registration-close-date-to-june-30-2027 [S] |
| **Sunset** (prazo final para certificar projetos registrados) | **30/06/2033** | idem [P]. [?] A UL cita 30/06/2032 em material anterior à prorrogação. |
| Projetos de volume ou protótipo na v4/v4.1 | [?] **Conflito:** a página de prazos indica 30/06/2030; o FAQ da v5 indica 30/06/2029 | https://www.usgbc.org/tools/leed-certification/deadlines ; https://support.usgbc.org/hc/en-us/articles/25316160948755-LEED-v5 |
| Campus / master site já registrados | Podem acrescentar projetos até 30/06/2027 [S] | https://www.ul.com/insights/what-know-about-leed-v5 |
| Multifamiliar residencial | A v4 BD+C NC fecha em 30/06/2027. Multifamiliar com 4+ pavimentos pode ir para a v5 BD+C; com 3 ou menos, segue na v4/v4.1 Residential | https://www.usgbc.org/leed/rating-systems/residential [P] |
| LEED Zero | Sem prazo de encerramento: aberto a qualquer projeto já certificado | https://www.usgbc.org/tools/leed-certification/deadlines [P] |
| Revisões | O GBCI aceita submissões (preliminar ou de projeto) até a data de sunset | idem [P] |
| ND v4, Residential v4.1 e Cities v4.1 | [?] Datas de encerramento não encontradas: não aparecem na tabela de prazos | — |

**Regra prática:** em nov/2026, um projeto comercial novo no Brasil **ainda pode escolher** entre v4.1 e v5 até 30/06/2027. A partir de 01/07/2027 só existe a v5. Atenção: algumas fontes secundárias ainda citam 30/06/2026 ou 01/07/2026, mas essas datas foram **superadas** pela prorrogação.

---

## 4. Processo e custos de certificação

### 4.1 Etapas

| Etapa | Descrição | Fonte |
|---|---|---|
| 1. Registro | Na v5, pelo **Arc**; na v4/v4.1, pelo **LEED Online**. A taxa de registro é fixa e paga no registro, com cartão, boleto/cheque (exceto Europa) ou "Pay later", que gera fatura. | https://support.usgbc.org/hc/en-us/articles/40666784248339-Working-on-LEED-v5-projects-in-Arc [P] |
| 2. (Opcional) Pré-certificação | BD+C NC/CS (v5) e O+M v4.1. Pagamento à parte. | https://www.usgbc.org/tools/leed-certification/commercial [P] |
| 3. Submissão e taxa de certificação | **Revisão combinada**, com tudo ao final, ou **revisão dividida** (*split*, apenas BD+C e ID+C): créditos de projeto (*design*) ao fim do projeto e créditos de obra (*construction*) ao fim da obra. Cada crédito tem direito a duas rodadas de revisão. | https://www.usgbc.org/tools/leed-certification/commercial ; https://certificationwiki.gbci.org/images/7/70/LEED_Certification_Manual_2024_Edition.pdf [P] |
| 4. Revisão preliminar do GBCI | Meta de **20 a 25 dias úteis**. A equipe aceita o resultado ou responde em até cerca de 25 dias úteis. Há revisão expressa mediante taxa extra. | idem [P] |
| 5. Revisão final e resultado | Certificação com selo e placa. **Revisão suplementar (apelação): US$ 700 por crédito**, valor único desde **27/03/2026**, sem desconto para membros. | https://www.gbci.org/most-leed-supplemental-reviews-appeals-now-have-one-flat-fee [P] |
| 6. Dados pós-ocupação | Compromisso de compartilhar dados de energia e água do edifício inteiro por 5 anos | https://www.usgbc.org/tools/leed-certification/commercial [P] |
| 7. **Recertificação** | Na v5, **via O+M v5**. A certificação **expira 3 anos** após a aceitação (v4.1 também é 3 anos; v4 é 5 anos). Exige os últimos 12 meses de energia, água e **vazamento de refrigerante** no Arc, com mínimo de 40 pontos. Projetos já certificados ganham **5 pontos** em Project Priorities. **Registro da recertificação é gratuito.** | https://www.usgbc.org/sites/default/files/2025-10/LEED-v5-Recertification-Guidance.pdf ; https://support.usgbc.org/hc/en-us/articles/4605861052691-Getting-started-with-your-recertification [P] |

**Arc:** o Arc dá uma nota de 0 a 100 em cinco categorias (Energy, Water, Waste, Transportation, Human Experience), sobre um período de 365 dias consecutivos. Na v5, o Arc é a plataforma de registro, documentação e certificação.
- https://support.usgbc.org/hc/en-us/articles/4423651977363-What-is-the-Arc-score-and-how-does-it-work [P]
- https://support.usgbc.org/hc/en-us/articles/4423532407571-About-Arc [P]
- https://www.usgbc.org/articles/leed-v5-expands-new-arc-certification-tools-and-resources-users [P]

### 4.2 Taxas GBCI (USD; tabela vigente segundo a página oficial)

"Membro" significa membro USGBC nos níveis **Silver, Gold ou Platinum**. Membros organizacionais pagam o preço de não membro. A v5 tem as mesmas taxas da v4.1.

**Registro (BD+C, ID+C, O+M):**

| | Membro | Não membro |
|---|---|---|
| Registro | **US$ 1.350** | **US$ 1.700** |

**Certificação BD+C (revisão padrão):**

| Área bruta (ft²) | Membro | Não membro |
|---|---|---|
| < 250.000 | US$ 0,064/ft² (mín. US$ 3.200) | US$ 0,076/ft² (mín. US$ 3.825) |
| 250.000–499.999 | US$ 0,062/ft² (≈ US$ 16.000) | US$ 0,074/ft² (≈ US$ 19.000) |
| 500.000–749.999 | US$ 0,056/ft² (≈ US$ 31.000) | US$ 0,067/ft² (≈ US$ 37.000) |
| ≥ 750.000 | Sob consulta | Sob consulta |

[?] Um trecho também menciona uma "taxa fixa por edifício" de US$ 4.500 (membro) e US$ 5.600 (não membro). **Não consegui confirmar a que se refere**, possivelmente campus/grupo ou pré-certificação. Verificar.

**Certificação O+M v4.1/v5 (< 250.000 ft²):** membro US$ 0,026/ft² (mín. US$ 1.275); não membro US$ 0,030/ft² (mín. US$ 1.500).

**ID+C:** [?] Tabela não localizada nos trechos. A estrutura deve ser análoga à do BD+C.

**Outros:**
- Desconto de 20% para projetos com 60% ou mais da área em armazém/distribuição.
- Revisão expressa com taxa adicional.
- Taxas não reembolsáveis e intransferíveis.
- Aplica-se a tabela vigente na data da fatura.
- Último reajuste geral de cerca de 12% em 01/05/2023 [S].

Conversão aproximada para o Brasil: 1 m² = 10,764 ft². Um edifício de 10.000 m² (107.640 ft²), com membro, paga cerca de 107.640 × 0,064 ≈ **US$ 6.900** de certificação, mais US$ 1.350 de registro. Não membro: cerca de **US$ 8.180 + 1.700**. Cálculo ilustrativo: **não inclui** consultoria, comissionamento, modelagem energética ou ensaios, que normalmente custam muito mais do que as taxas do GBCI.

Fontes:
- https://www.usgbc.org/tools/leed-certification/fees [P]
- https://new.usgbc.org/cert-guide/fees [P]
- https://www.gbci.org/most-leed-supplemental-reviews-appeals-now-have-one-flat-fee [P]
- https://bee-inc.com/2023/03/24/leed-registration-and-certification-prices-increase/ [S]
- https://clearvue.business/leed-v5-explained-a-practical-guide-to-the-new-green-building-rating-system/ [S] (paridade v5 = v4.1)

---

## 5. Pontos de interesse imediato para a suíte KAPTEK (ligação com o mapeamento)

Esta seção não fazia parte do escopo de pesquisa e serve só como orientação. Créditos e pré-requisitos da v5 em que uma suíte de carga térmica, simulação 8760, CFD e CAPEX/OPEX entra diretamente:

| Módulo da suíte | Créditos/pré-requisitos v5 |
|---|---|
| Simulação 8760 (energia, emissões, energia-fonte) | EAp Minimum Energy Efficiency; EAc Enhanced Energy Efficiency (até 10 pts); EAp Operational Carbon Projection (estimativa de energia anual que alimenta a projeção de 25 anos); O+M: Optimized Energy Performance (EUI) e GHG Emissions Reduction |
| Carga térmica de pico / envoltória | **EAc Reduce Peak Thermal Loads** (5 pts, novo, recompensa equipamento de HVAC menor) |
| Eletrificação (bombas de calor, VRF, chillers) | EAc Electrification (5 pts; obrigatório para Platinum NC) |
| Gestão de refrigerantes (inventário, GWP, vazamento) | EAp Fundamental Refrigerant Management; EAc Enhanced Refrigerant Management; dados de vazamento na recertificação O+M |
| Flexibilidade de rede / termoacumulação | EAc Grid Interactive |
| CFD / conforto e qualidade do ar | EQc Occupant Experience (ASHRAE 55-2023); Enhanced Air Quality; Air Quality Testing and Monitoring; Resilient Spaces |
| CAPEX/OPEX de retrofit | O+M: Decarbonization and Efficiency Plans (plano de capital de 5 anos); BD+C: plano de descarbonização (EAp1) |
| Resiliência climática | IPp Climate Resilience Assessment (cargas sob climas futuros) |

---

## 6. Incertezas e pendências (resumo)

1. **Acesso direto bloqueado** a usgbc.org e gbci.org nesta sessão. Todos os números vêm de trechos indexados. Revalidar com acesso liberado.
2. **Pontos por crédito na v5:** há diferenças entre as edições de 2025, fev/2026 e jul/2026. Os totais por categoria do ID+C e do O+M estão incompletos.
3. **Requisitos exatos de Platinum no BD+C:** EEE ≥ 8, 100% renovável e −20% de carbono incorporado vêm de fontes secundárias e de slides do USGBC. Confirmar na ed. jul/2026.
4. **ASHRAE 90.1-2019 × 2022** (corte em 01/01/2028) e a métrica exata do EAc Enhanced Energy Efficiency (energia-fonte e GHG × custo) foram confirmados só por fontes secundárias.
5. **Volume/protótipo v4/v4.1:** 30/06/2029 × 30/06/2030, conflito entre páginas do USGBC.
6. **"Exceções limitadas"** após 01/07/2027: não detalhadas.
7. **Taxa ID+C**, pré-certificação e o valor fixo de US$ 4.500/5.600 por edifício não foram esclarecidos.
8. **ND, Residential e Cities:** datas de encerramento da v4/v4.1 e calendário da v5 (Cities v5 ainda em consulta pública em nov/2025) não confirmados.
9. A lista completa de tipologias da v4 (O+M e Homes) foi citada de memória. Marcada com [?].
