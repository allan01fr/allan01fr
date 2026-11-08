# LEED O+M (v5 e v4.1), plataforma Arc e exigências HVAC-R para edifícios existentes

**Para:** KAPTEK (Rio de Janeiro). Desenho da suíte HVAC-R: retrofit, PMOC, análise de energia, CAPEX/OPEX.
**Data da pesquisa:** novembro de 2026.

---

## 0. Como esta pesquisa foi feita e qual a confiabilidade

- **Limitação técnica importante:** nesta sessão, o acesso direto (WebFetch) a `www.usgbc.org` e `arcskoru.com` foi **bloqueado pela rede do ambiente**, porque os domínios não estão na lista de permitidos. Por isso não li os PDFs inteiros. Todos os fatos abaixo vêm de **trechos indexados pela busca web (WebSearch) dentro dos próprios PDFs e páginas primárias** (usgbc.org, support.usgbc.org, arc.gbci.org, gbci.org, arcskoru.com, ashrae.org, evo-world.org, energystar.gov). A URL citada é a do documento primário de onde veio o trecho.
- Para ler as tabelas completas, por exemplo os limites de IAQ do v5 e o Apêndice II de EUI, é preciso liberar `www.usgbc.org` e `arcskoru.com` na rede da sessão e repetir a leitura dos PDFs.
- Legenda usada no texto:
  - **[CONFIRMADO]**: o trecho do documento primário diz isso explicitamente.
  - **[PARCIAL]**: confirmado em documento primário, mas em versão de rascunho/antiga, ou com detalhes faltando.
  - **[NÃO CONFIRMADO]**: não achei fonte primária, ou as fontes divergem.
  - **[CÁLCULO PRÓPRIO]**: soma ou inferência minha, não está na fonte.

---

## 1. LEED O+M para edifícios existentes

### 1.1 Visão geral e cronologia

| Item | Situação | Fonte |
|---|---|---|
| Edições do LEED v5 O+M: beta (set/2023), consulta pública 1 (abr/2024) e 2 (set/2024), edição de novembro/2025 e **edição de julho/2026** (a mais recente encontrada), com tabela de adendas de 31/07/2026 | [CONFIRMADO] | https://www.usgbc.org/sites/default/files/2026-07/LEED%20v5%20O+M%20Rating%20System_July%202026.pdf ; https://www.usgbc.org/sites/default/files/2025-10/LEED%20v5%20O+M%20Rating%20System_November%202025_clean.pdf ; https://www.usgbc.org/sites/default/files/2026-08/LEED%20v5%20O+M%20Addenda%20Table%20-%20only_07-31-2026.pdf |
| O registro de projetos LEED v5 O+M: Existing Buildings e a recertificação v5 **já são feitos no Arc** | [CONFIRMADO] | https://support.usgbc.org/hc/en-us/articles/25316160948755-LEED-v5 |
| A partir de **1º/07/2027**\*, o v5 passa a ser a única versão aceita para novos registros de BD+C, ID+C e O+M comerciais, com exceções limitadas (o asterisco está na própria fonte) | [CONFIRMADO] | https://support.usgbc.org/hc/en-us/articles/25316160948755-LEED-v5 |
| Período de desempenho (performance period) no v4.1 e no v5 O+M: **12 meses**, correspondentes ao ano anterior à submissão, salvo exceções previstas em créditos específicos | [CONFIRMADO] | https://www.usgbc.org/tools/leed-certification/commercial |
| Há créditos que exigem os 365 dias completos e outros que aceitam dados de um período menor, desde que dentro do período de relato | [CONFIRMADO] | https://support.usgbc.org/hc/en-us/articles/35196650547859-Arc-basics (FAQ de suporte USGBC) |
| O edifício precisa estar totalmente operacional e ocupado há pelo menos 1 ano (v4.1) | [PARCIAL]: aparece em material de treinamento USGBC | https://www.usgbc.org/education/sessions/introduction-leed-v41-existing-buildings-11633843 |

### 1.2 Níveis de certificação (v5 O+M)

- **Certified: 40–49 pontos. Silver: 50–59. Gold: 60–79. Platinum: 80 ou mais**, mais os "requisitos Platinum de O+M". [CONFIRMADO] https://www.usgbc.org/tools/leed-certification/commercial ; https://www.usgbc.org/sites/default/files/2025-10/LEED-v5-Recertification-Guidance.pdf
- Total possível: **110 pontos**. [CONFIRMADO] https://www.usgbc.org/sites/default/files/2025-05/LEED_LEED-v5-One-Pagers-Fact-Sheet_O+M_v4_DL.pdf
- **Requisitos extras para Platinum** [PARCIAL; o texto final completo não foi lido]:
  - ENERGY STAR score ≥ 80.
  - Baixas emissões operacionais, com meta de emissões diretas do ENERGY STAR NextGen por tipologia e zona climática.
  - Aquisição de energia renovável.
  - 2 pontos em GHG Emissions Reduction (Opção 2).
  - 5 pontos em Decarbonization and Efficiency Plans.

  Fontes: https://www.usgbc.org/sites/default/files/2026-01/Get%20ready%20for%20next%20version,%20and%20overview%20of%20LEEDv5_draft%20version.pdf ; https://www.usgbc.org/sites/default/files/2024-05/LEED-v5-summary-of-changes-LEED-v4-LEED-v41-OM.pdf ; https://www.usgbc.org/sites/default/files/2026-04/2026.3.17%20SDP%20Fact%20Sheet.pdf (fact sheet de 2026, que confirma a existência de "requisitos operacionais de descarbonização para Platinum" sem o texto completo)
- **Ponto em aberto para o Brasil:** o ENERGY STAR score para imóveis fora dos EUA/Canadá é calculado contra a população dos EUA (ver §3.1). **Não confirmei** como o USGBC trata o requisito "ES ≥ 80" do Platinum para projetos internacionais, nem se existe caminho alternativo.

### 1.3 Estrutura do LEED v5 O+M: categorias, pré-requisitos e créditos

Pontos por categoria segundo o fact sheet O+M v5 e a edição de nov/2025: **EA 34, WE 15, MR 13, EQ 26, LT 8**. [CONFIRMADO] https://www.usgbc.org/sites/default/files/2025-05/LEED_LEED-v5-One-Pagers-Fact-Sheet_O+M_v4_DL.pdf

Pela minha soma, o restante seria: SS 2, Project Priorities 10 e IP 2 (Operational Planning for Resilience 1 + Worker Safety and Training 1), totalizando 110. [CÁLCULO PRÓPRIO, a partir de trechos da edição nov/2025]

**Pré-requisitos (v5 O+M, edição nov/2025 e jul/2026)**

| Código | Pré-requisito | O que exige (resumo) | Status/Fonte |
|---|---|---|---|
| IPp | Climate Resilience Assessment | Avaliação de resiliência climática | [CONFIRMADO] Nov/2025 |
| IPp | Operations Assessment and Policy | Avaliações de vários elementos operacionais (novo no v5) | [CONFIRMADO o título; conteúdo detalhado NÃO LIDO]. Nov/2025 e https://www.usgbc.org/sites/default/files/2025-04/LEED-OM-v4-v5-Summary-of-Changes.pdf |
| IPp | Current Facilities Requirements and O+M Plan | Absorveu o antigo "Energy Efficiency Best Management Practices" do v4.1 (narrativa de sistemas e plano de manutenção preventiva) | [CONFIRMADO]. https://www.usgbc.org/sites/default/files/2024-05/LEED-v5-summary-of-changes-LEED-v4-LEED-v41-OM.pdf |
| EAp1 | Projeção de carbono operacional (nome muda entre edições; em 2026 aparece como "Operational Carbon Projection and Decarbonization Plan") | Projeção de carbono operacional e plano de descarbonização | [PARCIAL]. https://www.usgbc.org/sites/default/files/2026-01/Get%20ready%20for%20next%20version,%20and%20overview%20of%20LEEDv5_draft%20version.pdf |
| EAp2 | **Energy Monitoring and Reporting** | Medidores/submedidores permanentes para o consumo total, por fonte de energia. Medidores de inquilinos podem ser excluídos até 10% da área bruta. Relatar **dados mensais por fonte** dos 12 meses e, após a certificação, **continuar relatando anualmente os dados mensais** | [CONFIRMADO] Jul/2026 |
| EAp3 | **Minimum Energy Performance** | Opção 1: ENERGY STAR score ≥ 60 (Nov/2025), **obrigatória para tipologias elegíveis nos EUA e Canadá**. Opção 2: metas de **EUI de site ou de fonte** por tipologia e zona climática (Apêndice II, baseado na **ASHRAE 100-2024**). Opção 3: desempenho contra **linha de base histórica do próprio edifício**, com redução ≥ 8% em energia de site ou de fonte | [CONFIRMADO] Nov/2025 e Jul/2026. O limiar "60" pode ter mudado em Jul/2026 [NÃO CONFIRMADO] |
| EAp4 | **Fundamental Refrigerant Management** | Ver §3.4 | [CONFIRMADO] Nov/2025 |
| WEp1 | **Water Metering and Reporting** | Medição e relato mensal de água | [CONFIRMADO] Jul/2026; https://www.usgbc.org/sites/default/files/2025-04/LEED-OM-v41-v5-Summary-of-Changes.pdf |
| EQp | **Verification of Ventilation and Filtration** | Referência: ASHRAE 62.1-2022 | [CONFIRMADO] Nov/2025 |
| EQp | No Smoking | – | [CONFIRMADO] Nov/2025 |

**Créditos de maior interesse para HVAC-R e energia**

| Crédito | Pontos | Métrica / requisito | Fonte/Status |
|---|---|---|---|
| EAc1 GHG Emissions Reduction Performance | 1–12 | Redução percentual abaixo de metas de emissões de combustão local e de emissões totais do uso de energia. O caminho 3 (intensidade de combustão local) só vale para quem usou EAp3 Opção 2 | [CONFIRMADO] Jul/2026 e Nov/2025. A divisão de pontos entre componentes mudou entre edições |
| EAc2 Optimized Energy Performance | 2–12 | Caminho ENERGY STAR: 2 pts com score 69 até 12 pts com score 92. Outros caminhos pontuam por % de redução | [CONFIRMADO] Jul/2026. As tabelas dos caminhos não ES [NÃO LIDAS] |
| Decarbonization and Efficiency Plans | 4 (Jul/2026) | Auditoria energética (ASHRAE 211 nível 2 nos rascunhos) e/ou plano de descarbonização com plano de capital (CAPEX) | [PARCIAL]. Os pontos variaram entre 1–5 (beta) e 4 (Jul/2026) |
| Renewable Energy | 1–4 | Tiers 1–3, somáveis até 4 | [CONFIRMADO] |
| Enhanced Refrigerant Management Performance | 2 | Desempenho em vazamento/GWP. Detalhes não lidos | [PARCIAL] Fact sheet |
| Retrocomissionamento | 2 (rascunho 2024) | Processo concluído até 3 anos antes da submissão | [PARCIAL]. Não confirmei onde ficou na versão final |
| WEc1 Water Efficiency Performance | até 14 | Limiar de intensidade de uso de água (WUI) | [CONFIRMADO]. A fórmula exata não foi lida |
| WEc2 Advanced Water Metering | 1 | Medidores permanentes em ≥ 2 subsistemas de água | [CONFIRMADO] |
| MR Waste Reduction Performance | 12 | Geração e desvio de resíduos, excluindo resíduos de reforma. Prevenção conta como desvio | [CONFIRMADO] Jul/2026; summary of changes |
| MR Waste Reduction Strategies | 1 | – | [CONFIRMADO] |
| EQc1 Indoor Air Quality Performance | 10 | Ver §3.5 | [CONFIRMADO] |
| EQ Occupant Experience Performance | ? | Pontos por % de satisfação dos ocupantes (>60% até >90%) | [PARCIAL]. https://www.usgbc.org/sites/default/files/2025-04/LEED-OM-v4-v5-Summary-of-Changes.pdf |
| LTc1 Sustainable Transportation Performance | 1–6 | % de ocupantes que chegam por modos ativos/compartilhados (pesquisa dentro do período de 12 meses, requisitos de resposta no Apêndice III) ou Walk Score | [CONFIRMADO] Nov/2025 e Jul/2026 |

### 1.4 LEED v4.1 O+M (ainda válido até a migração)

- O v4.1 tem **5 pré-requisitos de desempenho**: transporte, água, energia, resíduos e IEQ. **90 dos 100 pontos** vêm de scores calculados com dados reais do edifício. [CONFIRMADO] https://www.usgbc.org/sites/default/files/2022-02/LEED%20v4%20v4.1%20crosswalk%20OM%20v2.pdf
- **Pontos máximos por categoria (scorecard Arc / v4.1):** Energia 33, Água 15, Resíduos 8, Transporte 14, Experiência Humana 20, Práticas Fundamentais (base) 10. Total: 100. [CONFIRMADO] https://support.usgbc.org/hc/en-us/articles/4423651977363-What-is-the-Arc-score-and-how-does-it-work ; https://arcskoru.com/sites/default/files/Arc%20Performance%20Scores%20Core%20Concepts.pdf
- **Faixas de pontos por crédito no beta v4.1:**
  - Energy Performance: 1–33 (o pré-requisito mínimo equivale a 6,5 pts).
  - Water: 1–15.
  - Waste: 3–8.
  - Transportation: 6–14.
  - IEQ/HE: 8–20.
  - **Score mínimo 40/100** em cada categoria na certificação inicial.

  [PARCIAL, beta 2018] https://www.usgbc.org/sites/default/files/LEED_v4_1_OM_beta_181114_redline.pdf
- **Outros pré-requisitos ligados a HVAC:**
  - Energy Efficiency Best Management Practices: narrativa dos sistemas mecânicos e elétricos e plano de manutenção preventiva.
  - Fundamental Refrigerant Management: proíbe CFC, salvo auditoria de inviabilidade ou plano de eliminação.
  - Minimum IAQ Performance: manutenção da ventilação conforme a Tabela 8.2 da ASHRAE 62.1-2016.

  [CONFIRMADO no crosswalk] https://www.usgbc.org/sites/default/files/2022-02/LEED%20v4%20v4.1%20crosswalk%20OM%20v2.pdf
- **Recertificação v4.1:** exige dados nas 5 categorias e no mínimo 40 pontos. O mínimo de 40 por categoria vale só na certificação inicial. As recertificações usam a versão vigente do Arc score. [CONFIRMADO] https://support.usgbc.org/hc/en-us/articles/4605861052691-Getting-started-with-your-recertification ; https://arc.gbci.org/arc-performance-score-updates-leed-v4-om-existing-buildings-performance-projects

### 1.5 Validade e recertificação

| Regra | Status/Fonte |
|---|---|
| Certificações **LEED v5 O+M e v4.1 expiram após 3 anos**. LEED v4 e anteriores: 5 anos | [CONFIRMADO] https://www.usgbc.org/sites/default/files/2025-10/LEED-v5-Recertification-Guidance.pdf ; https://support.usgbc.org/hc/en-us/articles/4605861052691-Getting-started-with-your-recertification |
| Recertificação v5: submeter no Arc os **últimos 12 meses de energia, água e vazamento de refrigerante**. Dados adicionais são opcionais e rendem pontos nos créditos de desempenho | [CONFIRMADO] Recertification Guidance (out/2025) |
| Entre recertificações: **inserir anualmente os dados de energia e água no Arc** | [CONFIRMADO] Idem |
| Recertificação v5 tem mínimo de 40 pontos. Projetos BD+C e O+M já certificados não pagam taxa de registro | [CONFIRMADO] Idem |
| Dados de recertificação devem ser de meses consecutivos, com lacunas razoáveis e justificáveis admitidas (regra citada para v4) | [PARCIAL] https://support.usgbc.org/hc/en-us/articles/4417273024275-Preparing-your-recertification-application |

---

## 2. Plataforma Arc (GBCI/Arc Skoru)

### 2.1 Como funciona o Performance Score (legado v4/v4.1)

- **Escala 0–100**, com 5 categorias dinâmicas (energia, água, resíduos, transporte, experiência humana) e 1 estática (práticas fundamentais, 10 pts). [CONFIRMADO] https://support.usgbc.org/hc/en-us/articles/4423651977363-What-is-the-Arc-score-and-how-does-it-work ; https://arcskoru.com/sites/default/files/Arc%20Performance%20Scores%20Core%20Concepts.pdf
- **Referência de comparação:** um conjunto global de edifícios certificados LEED. Score 100 significa desempenho melhor que todo o conjunto de referência. [CONFIRMADO] https://arcskoru.com/sites/default/files/Arc%20Performance%20Scores%20Core%20Concepts.pdf ; https://arc.gbci.org/introducing-arc-improvement-score
- **Janela móvel:** o score usa os **últimos 365 dias** e o Arc recalcula diariamente. [CONFIRMADO] https://www.gbci.org/metrics-motion-exploring-energy-arc ; https://support.usgbc.org/hc/en-us/articles/4423651977363-What-is-the-Arc-score-and-how-does-it-work
- **Energia:**
  - 50% do score vem das **emissões de GEE** e 50% da **energia primária (fonte)**. [CONFIRMADO] https://arc.gbci.org/ghg-emissions-are-central-arc-performance-score-learn-how-they-are-estimated ; https://www.gbci.org/metrics-motion-exploring-energy-arc
  - O GEE é estimado aplicando a intensidade média anual de emissões ao consumo mensal. O Arc não calcula GEE de materiais, água ou resíduos. [CONFIRMADO] mesma fonte
  - Conversão site→fonte com **três conjuntos de fatores: EUA, Canadá e "todos os outros locais"**. O valor exato para o Brasil [NÃO CONFIRMADO]; aparece um multiplicador 2,8 para eletricidade da rede sem país associado. https://www.gbci.org/metrics-motion-exploring-energy-arc ; https://www.usgbc.org/sites/default/files/2024-06/Guidance%20for%20Entering%20Renewable%20Energy%20in%20Arc_6.7.2024.pdf
  - Fatores de emissão padrão: eGRID (EUA) ou IEA. **Fatores personalizados podem substituir os padrões** quando o suprimento local difere. [PARCIAL, artigo de 2019] https://arc.gbci.org/ghg-emissions-are-central-arc-performance-score-learn-how-they-are-estimated
  - A suíte deve poder exportar o fator do SIN (MCTI) para justificar um fator personalizado [recomendação, não requisito].
- **Água:** consumo por ocupante e por área, comparado com edifícios LEED de alto desempenho. [PARCIAL] https://www.usgbc.org/sites/default/files/LEED_v4_1_OM_beta_181114_redline.pdf
- **Resíduos:** score 0–100 convertido para até 8 pts. Usa a geração média diária e o desvio por ocupante, mais o resultado de uma auditoria anual de resíduos. A geração pesa mais que o desvio. [PARCIAL] https://www.gbci.org/metrics-motion-exploring-waste-arc ; beta v4.1
- **Transporte:** pesquisa com ocupantes (modo e distância), convertida em CO2e por viagem de ida por ocupante. Se a pesquisa tiver mais de 365 dias, o score de transporte vai a **zero**. [CONFIRMADO] https://support.usgbc.org/hc/en-us/articles/4423532407571-About-Arc ; https://arcskoru.com/sites/default/files/Arc%20Transport%20Score%201_%20Relationships_R2.pdf
- **Experiência humana (v4.1):**
  - Pesos: **50% satisfação** (escala 1–10, média e variância), **25% CO2** (referência 1.000 ppm) e **25% TVOC** (referência 500 µg/m³). Pesquisa pelo menos 1 vez a cada 12 meses. Mínimo 40.
  - [PARCIAL: beta 2018 e guia Arc Schools 2022] https://www.usgbc.org/sites/default/files/LEED_v4_1_OM_beta_181114_clean.pdf ; https://www.usgbc.org/sites/default/files/2022-10/Arc+Schools%20Getting%20Started%20Guide_Sept2022.pdf ; https://www.gbci.org/metrics-motion-exploring-human-experience-arc
  - Não confirmei se esses pesos continuam atuais.
- **Ocupação:** o padrão é a ocupação do último dia do período. Na COVID-19 foi permitida a ocupação ponderada no tempo. [CONFIRMADO] https://arc.gbci.org/managing-occupancy-arc-leed-certification-during-covid-19 ; https://www.usgbc.org/sites/default/files/2020-12/LEED-OM-COVID-19-Submittal-Guidance.pdf
- **Improvement Score:** compara a intensidade (por exemplo, energia de fonte por área) com um período de linha de base do próprio edifício. É conceitualmente análogo a M&V. [CONFIRMADO] https://arc.gbci.org/introducing-arc-improvement-score
- **Outros benchmarks no Arc:** ENERGY STAR (EUA), CRREM (caminhos de descarbonização para alguns países) e ASHRAE 100. [CONFIRMADO] https://arc.gbci.org/arc-supports-building-performance-standards
- **Arc e v5:** o v5 O+M não usa o "Performance Score" 0–100. Usa créditos com métricas próprias (ES score, EUI, % de redução, % de satisfação etc.), mas **a submissão e o relato contínuo acontecem no Arc**. [CONFIRMADO o registro no Arc; como o Arc calcula/exibe os créditos v5 está NÃO CONFIRMADO] https://support.usgbc.org/hc/en-us/articles/25316160948755-LEED-v5

### 2.2 Dados exigidos, formato e frequência

- **Medidores ("Meters & Surveys"):** cada medidor tem tipo (eletricidade da rede, gás, renovável no local ou fora, água potável/reúso etc.) e unidade. [CONFIRMADO] https://support.usgbc.org/hc/en-us/articles/4425290998675-Arc-and-data-input ; https://www.usgbc.org/sites/default/files/LEEDv5Resources/LEED-v5-Water-Meter-Guide_2026.pdf (Guia de medidores de água do v5, 2026)
- **Formato da leitura:** série temporal com **data/hora de início, data/hora de fim e leitura**. Para energia e água, a leitura é o **consumo total no período**, e não a leitura acumulada do medidor. Em contas mensais, início e fim são o ciclo de faturamento. [CONFIRMADO] https://arcskoru.com/sites/default/files/Arc%20Platform%20-%20Integration%20Guide%20(May%2028%202020).pdf ; https://www.usgbc.org/sites/default/files/2022-10/Arc+Schools%20Getting%20Started%20Guide_Sept2022.pdf
- **Cobertura:** 12 meses consecutivos de consumo total do edifício. Renováveis e energia fora do local entram com valores mensais positivos alinhados às contas. [CONFIRMADO] https://www.usgbc.org/sites/default/files/2024-06/Guidance%20for%20Entering%20Renewable%20Energy%20in%20Arc_6.7.2024.pdf ; https://www.usgbc.org/sites/default/files/leed-om-transit.pdf
- **Frequência:** não achei cadência obrigatória de envio (mensal ou por conta). O mínimo prático é: 12 meses para certificar, atualização anual entre recertificações (v5) e, para o score Arc ser contínuo, alimentação recorrente. [NÃO CONFIRMADO como regra formal]
- **Vias de entrada de dados:**
  1. Digitação manual ("Add Row").
  2. **Planilha-modelo** (template Excel) por medidor, depois upload.
  3. **Sincronização com o ENERGY STAR Portfolio Manager:** compartilhar a propriedade com a conta USGBC, informar o LEED/Arc ID em "Standard IDs". Os dados aparecem em 24–48 h. Limitações: renovável fora do local não sincroniza e "Green Power" chega como "Purchased from Grid".
  4. **API Arc**, diretamente ou via parceiro.

  [CONFIRMADO] https://support.usgbc.org/hc/en-us/articles/4425290998675-Arc-and-data-input ; https://arcskoru.com/sites/default/files/060921_Arc-NewProperty.pdf ; https://www.usgbc.org/sites/default/files/2024-06/Guidance%20for%20Entering%20Renewable%20Energy%20in%20Arc_6.7.2024.pdf
- **Pesquisas** de ocupantes (transporte e satisfação) são feitas por link do próprio Arc. Resíduos entram como pesos gerados e desviados. IAQ entra por medidores de CO2/TVOC/PM, também disponíveis via API para parceiros, como mostra o guia Re-Entry. [PARCIAL] https://arc.gbci.org/sites/default/files/Arc%20Guide%20to%20Re%20Entry%20v1.2.pdf

### 2.3 API do Arc (integração ERP/CMMS → Arc)

- **Existe API pública documentada** no "Arc Integration Guide" (rev. 29/11/2023). [CONFIRMADO] https://arc.gbci.org/sites/default/files/legal/Arc-Platform_Integration-Guide_Nov-2023.pdf (versão de 2020: https://arcskoru.com/sites/default/files/Arc%20Platform%20-%20Integration%20Guide%20(May%2028%202020).pdf)
- **Acesso:**
  - Conta de desenvolvedor em **developer.usgbc.org**, com assinatura das "Arc data dev APIs" para chaves e testes, mais uma conta de usuário para a troca real de dados.
  - Existe ambiente de desenvolvimento com projetos de teste.
  - Quem atende **vários clientes** (caso de uma consultoria como a KAPTEK) precisa **contatar o Arc e assinar um acordo comercial** de segurança, privacidade e preferências do usuário.
  - Quem desenvolve para um único cliente pode começar sem esse acordo.
  - O checklist de 2020 inclui conta de teste, QA e virada para produção.

  [CONFIRMADO] mesmas fontes.
- **Fluxo:** autenticar o usuário → listar projetos acessíveis → listar medidores do projeto (distinguidos por "Type ID") → por medidor, **ler leituras ou enviar leituras**. Escopo: edifícios (inclusive espaços/CI), cidades, comunidades e transporte. [CONFIRMADO] Integration Guide 2023
- **Não confirmei:** tipo de OAuth, cabeçalho de chave (por exemplo `Ocp-Apim-Subscription-Key`), nomes de endpoints, limites de taxa, envio de dados de refrigerante (vazamento/GWP) por API, envio de resíduos e pesquisas por API. **Isso precisa ser verificado no portal developer.usgbc.org.** [NÃO CONFIRMADO]
- **Parceiros de integração já listados:** ENERGY STAR Portfolio Manager, Arbnco, Commutifi (transporte), Measurabl, QLEAR (IAQ), Schneider Electric, Skanska, B-line. [CONFIRMADO, lista de 2020–2023] https://arc.gbci.org/arc-integrations-four-new-partnerships-make-it-faster-and-easier-manage-performance-and-achieve-leed ; https://arc.gbci.org/qlear
- **Rota alternativa de menor risco:** a suíte publica no **Portfolio Manager**, que tem Web Services documentados (https://portfoliomanager.energystar.gov/pdf/reference/Introduction_to_Exchanging_Data_en_US.pdf), e o PM sincroniza com o Arc. Desvantagem: as limitações de renovável/green power descritas acima e uma camada a mais.

---

## 3. Exigências de O+M ligadas a HVAC-R

### 3.1 Benchmark de energia: ENERGY STAR Portfolio Manager e equivalentes no Brasil

- **ENERGY STAR fora dos EUA/Canadá:** não existe score desenvolvido para outros países. Por padrão, o imóvel é comparado à população dos EUA. A **certificação ENERGY STAR** só vale para EUA e Canadá. Tipologias sem score ainda recebem EUI, GEE, EUI normalizada pelo clima e comparação com a mediana nacional (CBECS). [CONFIRMADO] https://portfoliomanager.energystar.gov/pdf/reference/ENERGY%20STAR%20Score.pdf ; https://www.energystar.gov/buildings/benchmark/understand-metrics/how-score-calculated
- **Implicação para o LEED v5 no Brasil:** a EAp3 Opção 1 (ES score) só é **obrigatória** para tipologias elegíveis nos EUA e Canadá. No Brasil, as alternativas práticas são a **Opção 2** (metas de EUI da ASHRAE 100-2024 por zona climática, Apêndice II) e a **Opção 3** (linha de base histórica com redução ≥ 8%). [CONFIRMADO o texto da opção; a aplicabilidade de ES a projetos brasileiros como "opção voluntária" NÃO CONFIRMADA]
- **Equivalente brasileiro:** a plataforma **DEO – Desempenho Energético Operacional** do CBCS (desde 2013) faz benchmarking de agências bancárias, escritórios corporativos e prédios públicos administrativos, com indicador em kWh/m²·ano. Exemplo de prédios públicos: 121 kWh/m²·ano (típico) e 112 kWh/m²·ano (boa prática). [PARCIAL] https://www.gov.br/mma/pt-br/assuntos/mudanca-do-clima/mitigacao/repositorio/projeto-3e/publicacoes/relatorio-tecnico-de-desenvolvimento-benchmarking.pdf
  - **Não confirmei** se o USGBC aceita o DEO como benchmark equivalente em algum crédito.
  - Também não verifiquei se o PBE Edifica (INI-C) tem rota de etiquetagem de edifícios existentes utilizável para isso.

### 3.2 Auditoria energética: ASHRAE Standard 211

- O padrão define procedimentos, escopo comum, rigor mínimo de análise e requisitos mínimos de relatório para os **níveis 1, 2 e 3**. [CONFIRMADO] https://www.ashrae.org/technical-resources/bookstore/standards-180-and-211 ; https://www.ashrae.org/File%20Library/Technical%20Resources/Bookstore/previews_2016437_pre.pdf
  - **Nível 1:** avaliação preliminar (walk-through). Análise de contas e inspeção do local, medidas de custo zero ou baixo e visão geral de oportunidades de capital.
  - **Nível 2:** levantamento e análise de engenharia. Análise detalhada de custos, usos e características, decomposição dos usos finais e medidas com análise financeira.
  - **Nível 3:** análise detalhada de modificações intensivas em capital, com monitoramento, coleta de dados e engenharia aprofundada.
  - [PARCIAL]: as definições curtas vêm de FAQ da ASHRAE e de fonte secundária. O texto normativo é pago. https://resourcecenter.ashrae.org/technical-resources/technical-faqs
- **Adendo "a" à 211-2018 (RA2023), out/2024:** amplia o propósito para incluir **avaliações de descarbonização**. [CONFIRMADO] https://www.ashrae.org/file%20library/technical%20resources/standards%20and%20guidelines/standards%20addenda/211_2018_ra2023_a_20241030.pdf
- **Ligação com o LEED v5:** os rascunhos pediam auditoria **ASHRAE 211 nível 2** (ou equivalente) para 1 ponto. Na versão final, a auditoria fica dentro do crédito **Decarbonization and Efficiency Plans**, que também pede plano de descarbonização com plano de capital. [PARCIAL] https://www.usgbc.org/sites/default/files/2024-04/LEED-v5-OM-Existing-Buildings-Public-Comment-1.pdf ; https://www.usgbc.org/sites/default/files/2024-05/LEED-v5-summary-of-changes-LEED-v4-LEED-v41-OM.pdf

### 3.3 Retrocomissionamento, manutenção e monitoramento contínuo

- **LEED v5 (rascunho 2024):** retrocomissionamento vale 2 pts e deve estar concluído até **3 anos antes** da submissão. O plano de comissionamento de edifício existente foi absorvido pelas fases de engajamento, planejamento e avaliação do RCx. [PARCIAL] https://www.usgbc.org/sites/default/files/2024-04/LEED-v5-OM-Existing-Buildings-Public-Comment-1.pdf ; https://www.usgbc.org/sites/default/files/2025-04/LEED-OM-v4-v5-Summary-of-Changes.pdf
- **Normas ASHRAE de referência:**
  - **Standard 180-2018:** inspeção e manutenção de HVAC comercial. É a base natural para o PMOC.
  - **Guideline 0.2-2015:** comissionamento de sistemas existentes.
  - **Standard 230-2022:** requisitos mínimos de comissionamento de edifícios existentes.
  - **Standard 202-2024:** comissionamento de edifícios novos.
  - [CONFIRMADO; edições a verificar] https://www.ashrae.org/File%20Library/About/Government%20Affairs/Advocacy%20Toolkit/ASHRAE-Standards-Summary.pdf ; https://www.ashrae.org/technical-resources/standards-and-guidelines/titles-purposes-and-scopes
- **Comissionamento baseado em monitoramento:** não achei norma ASHRAE específica. O Handbook descreve o monitoramento como tendências via BAS ou data loggers, analisadas depois, cobrindo operação normal, partida, parada e fins de semana. [PARCIAL] https://handbook.ashrae.org/Handbooks/A19/SI/a19_ch44/a19_ch44_si.aspx
- **Ligação com a EAp2 do v5:** submedição permanente por fonte e relato mensal contínuo. É a base para o monitoramento contínuo de energia. [CONFIRMADO]
- **No v4.1:** o pré-requisito Energy Efficiency Best Management Practices pede narrativa de sistemas e **plano de manutenção preventiva**. No v5 isso migrou para "Current Facilities Requirements and O+M Plan". Um **PMOC bem estruturado é a matéria-prima direta desse pré-requisito**. [CONFIRMADO]
- **Brasil:** a **Lei 13.589/2018** exige PMOC em edifícios de uso público e coletivo climatizados. Seu art. 3º, parágrafo único, remete os padrões de qualidade do ar a norma técnica. [CONFIRMADO] https://planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13589.htm

### 3.4 Gestão de refrigerantes em operação

- **LEED v5 EAp4 Fundamental Refrigerant Management** [CONFIRMADO, Nov/2025]:
  1. **Inventário** de todo equipamento com refrigerante: tipo, **GWP**, **carga** de cada um e **GWP total**.
  2. **Inspeção visual** de vazamentos e recarga dos equipamentos com vazamento.
  3. **Rastreio de recargas/compras** por tipo e massa durante 12 meses, com relato do **GWP total vazado** (kg × GWP).
  4. Conformidade com **EPA Section 608**, **F-Gas (UE)** ou **regras nacionais/locais equivalentes**.
  5. **Rastreio do descarte** adequado de equipamentos removidos.

  Mudança em relação ao v4.1: removeram as metas fixas de taxa de vazamento e entrou o rastreio de GWP vazado. https://www.usgbc.org/sites/default/files/2025-10/LEED%20v5%20O+M%20Rating%20System_November%202025_clean.pdf ; https://www.usgbc.org/sites/default/files/2025-04/LEED-OM-v41-v5-Summary-of-Changes.pdf
- **Enhanced Refrigerant Management Performance:** 2 pts. Critério não lido. [PARCIAL]
- **Recertificação v5:** exige **dados de vazamento de refrigerante** dos últimos 12 meses **no Arc**. [CONFIRMADO] Recertification Guidance
- **v4.1:** proíbe CFC, salvo auditoria de inviabilidade ou plano de eliminação. [CONFIRMADO]
- **Brasil, o "equivalente nacional" para a EAp4:**
  - **IN Ibama nº 20/2022** define a cota-país de importação de HCFC no Programa Brasileiro de Eliminação dos HCFCs (PBH) e revogou a IN 4/2018.
  - A IN 5/2018 dispensava o CTF para compra por prestadores de serviço e consumidores finais.
  - O programa HFC (Kigali) estava em fase inicial de planejamento.
  - [PARCIAL; conferir no DOU] https://www.legisweb.com.br/legislacao/?id=439834 ; https://www.gov.br/ibama/pt-br/acesso-a-informacao/analise-de-impacto-regulatorio-air/relatorios-de-analise-de-impacto-regulatorio-air/arquivos/20230424_SEI_Ibama_13862362_Nota_Tecnica_55_Corem_CGQua_Diqua_AIR_HCFC.pdf
  - **Não confirmei** se há no Brasil exigência legal de registro de vazamentos comparável à EPA 608. Na prática, o PMOC e as ordens de serviço viram a evidência.

### 3.5 Qualidade do ar interno (CO2, PM2.5, TVOC)

- **LEED v5 EQc1 Indoor Air Quality Performance (10 pts)** [PARCIAL]:
  - Opção 1, **monitoramento contínuo** por no mínimo **3 meses** de **CO2, PM2.5 e TVOC**. Métrica: **percentil 95 para CO2**, **médias diárias para PM2.5 e TVOC**. Pontos por cumprir limiares de cada parâmetro.
  - Opção de **teste pontual**. Pela adenda de jul/2026: medição de **4 horas**, com **pico de CO** e **média de O3, PM2.5, PM10 e NO2**.
  - **Os valores-limite numéricos não foram lidos [NÃO CONFIRMADO].**
  - Fontes: https://www.usgbc.org/sites/default/files/2025-04/LEED-OM-v41-v5-Summary-of-Changes.pdf ; https://www.usgbc.org/sites/default/files/2024-04/LEED-v5-OM-Existing-Buildings-Public-Comment-1.pdf ; https://www.usgbc.org/sites/default/files/2026-08/LEED%20v5%20O+M%20Addenda%20Table%20-%20only_07-31-2026.pdf
  - O USGBC publica também um "v5 O+M Indoor Air Quality Monitoring Questionnaire" (não lido).
- **Pré-requisito v5:** Verification of Ventilation and Filtration (ASHRAE 62.1-2022). [CONFIRMADO]
- **v4.1/Arc:** CO2 com referência de 1.000 ppm e TVOC com 500 µg/m³ entram em 50% do score de Experiência Humana. [PARCIAL, ver §2.1]
- **Brasil:**
  - A **ABNT NBR 17037** (Qualidade do ar interior em ambientes não residenciais climatizados artificialmente: padrões referenciais) substitui a referência da RE 09/2003 da ANVISA, citada a partir de 25/07/2024.
  - O limite de **CO2 passa a ser relativo: externo + 700 ppm**.
  - Avalia PM10 e PM2.5 com laboratórios acreditados pela ISO/IEC 17025.
  - [PARCIAL: fonte ABRAVA + secundária] https://abrava.com.br/wp-content/uploads/2024/08/Comunicado-de-Alteracoes-na-legislacao-brasileira-sobre-qualidade-do-ar-interno-Confira.pdf
  - Os limites de PM2.5 da NBR 17037 e o seu status de obrigatoriedade [NÃO CONFIRMADOS].
  - **Oportunidade:** o mesmo conjunto de sensores e laudos serve ao PMOC/NBR 17037 e ao EQc1 do LEED. A suíte deve calcular as duas métricas (por exemplo, CO2 relativo ao externo e percentil 95) a partir da mesma série.

---

## 4. Relação com o "analisador de energia" (contas, medições, linha de base, M&V/IPMVP) e com os planos de manutenção

### 4.1 IPMVP (EVO)

- **Equação comum às quatro opções:** Economia = (Energia da linha de base − Energia do período de relato) ± Ajustes de rotina ± Ajustes não rotineiros. [CONFIRMADO] https://evo-world.org/br/general/1897-x-ipmvp-core-concepts-statutory-review-copy-1/file ; https://evo-world.org/images/corporate_documents/NRE-NRA_White_Paper_Final_2701.pdf
- **Opções:**
  - **A:** isolamento da medida, com parâmetros-chave medidos e outros estimados.
  - **B:** isolamento da medida, com todos os parâmetros medidos.
  - **C:** edifício inteiro, pelo medidor da concessionária.
  - **D:** simulação calibrada.

  A opção C ou D é preferida quando a economia é apurada no nível da instalação. [CONFIRMADO] mesmas fontes
- **Ajustes de rotina** (por exemplo, clima: graus-dia de resfriamento e ocupação) e **ajustes não rotineiros** (mudanças nos "fatores estáticos", como área, uso e horário). [CONFIRMADO] https://evo-world.org/images/corporate_documents/NRE-NRA_White_Paper_Final_2701.pdf
- **Edição vigente:** Core Concepts 2022, com revisão estatutária em curso. [PARCIAL] https://evo-world.org/images/EVO_PROGRAMS_2022_EN_v02.pdf

### 4.2 Como o analisador alimenta O+M/Arc

| Função do analisador | Requisito LEED/Arc atendido |
|---|---|
| Ingestão de faturas (energia por fonte, água) em séries de período início/fim | EAp2, WEp1, medidores Arc (formato início/fim/consumo) |
| Linha de base de 12 meses, EUI de site e de fonte, normalização climática (regressão por CDD, Opção C) | EAp3 Opção 2 (EUI contra ASHRAE 100) e **Opção 3 (linha de base histórica, ≥ 8% de redução)**, EAc2 (% de redução), Arc Improvement Score |
| Conversão para GEE (fator do SIN/MCTI e combustíveis) e energia primária | EAc1, Platinum, energia Arc (50% GEE + 50% fonte), fator personalizado no Arc |
| M&V das medidas de retrofit (IPMVP A/B para chillers e VFDs, C para o edifício) | Evidência de redução para EAc1/EAc2, plano de descarbonização e business case de CAPEX/OPEX |
| Auditoria ASHRAE 211 nível 2/3 com medidas e análise financeira | Decarbonization and Efficiency Plans (auditoria e plano de capital) |
| Submedição e monitoramento contínuo (BMS/IoT) com detecção de desvios | EAp2, retrocomissionamento/MBCx, Advanced Water Metering |

### 4.3 Como o plano de manutenção (PMOC/CMMS) alimenta O+M/Arc

| Função do PMOC/CMMS | Requisito LEED/Arc atendido |
|---|---|
| Inventário de ativos HVAC-R (equipamento, refrigerante, carga, GWP) | EAp4 (inventário e GWP total), Enhanced Refrigerant Mgmt |
| Ordens de serviço com inspeção de vazamento, recarga (kg por tipo) e descarte | EAp4 (12 meses de recargas, GWP vazado, descarte) e dados de vazamento no Arc para a recertificação |
| Narrativa de sistemas e plano de manutenção preventiva (ASHRAE 180 ≈ PMOC) | Current Facilities Requirements and O+M Plan (v5); EE BMP (v4.1) |
| Verificação de ventilação e filtros (vazões, troca de filtros, MERV) | EQp Verification of Ventilation and Filtration |
| Laudos de QAI (NBR 17037) e sensores contínuos | EQc1 IAQ Performance; HE do Arc (v4.1) |
| Registro de RCx (achados, correções, data de conclusão ≤ 3 anos) | Crédito de retrocomissionamento |

---

## 5. Principais incertezas (o que verificar quando usgbc.org e arcskoru.com estiverem acessíveis)

1. Limiares numéricos do EQc1 (CO2, PM2.5, TVOC) no texto final ou nas adendas de jul/2026.
2. Valores do Apêndice II (metas de EUI da ASHRAE 100-2024) para a zona climática do Rio de Janeiro e para as tipologias da KAPTEK. Também como a zona climática é atribuída fora dos EUA.
3. Como o requisito Platinum "ES ≥ 80" se aplica a projetos fora dos EUA/Canadá.
4. Limiar exato da EAp3 Opção 1 na edição de jul/2026 (60 em nov/2025).
5. Critérios do Enhanced Refrigerant Management Performance e do Occupant Experience Performance. Posição final do retrocomissionamento no v5.
6. Especificação técnica da API Arc: autenticação, endpoints, limites e se aceita refrigerante, resíduos e pesquisas. Também custos e condições do acordo de parceiro.
7. Fatores site→fonte e de emissão que o Arc usa por padrão para o Brasil.
8. Pesos atuais do Arc Performance Score (os números 33/15/8/14/20/10 vêm de material de 2020–2024).
9. Limites de PM2.5 e status de obrigatoriedade da NBR 17037. Normas do Ibama sobre HFC posteriores a 2023.
10. Métricas de cálculo exatas do WEc1 (WUI) e do MR Waste Reduction Performance no v5.

---

## 6. Dados e cálculos que a suíte precisa produzir para O+M/Arc

**Cadastro e contexto do edifício**
1. Área bruta (m² e ft²), tipologia (mapeada para os tipos do ENERGY STAR/ASHRAE 100), zona climática, horário de operação e **ocupação** (no último dia do período e ponderada no tempo).
2. Cadastro de **medidores** por fonte (rede, gás, diesel, solar local, renovável fora do local, água potável/reúso/subsistemas), com tipo/unidade compatíveis com o Arc e o Portfolio Manager, e a fração de área coberta (exclusão de inquilinos ≤ 10%).

**Energia (analisador)**
3. Séries de consumo por medidor no formato **início, fim e consumo do período**, mensais, com 12 meses consecutivos e detecção e justificativa de lacunas.
4. **EUI de site e de fonte** (kWh/m²·ano e kBtu/ft²·ano) com os multiplicadores site→fonte usados pelo Arc e pela ASHRAE 100. Comparação com as metas do Apêndice II (EAp3 Opção 2) e com o DEO/CBCS.
5. **Linha de base histórica** de 12 meses, com regressão climática (CDD/HDD, ocupação) e % de redução de site e fonte (EAp3 Opção 3 ≥ 8%; EAc2).
6. **Emissões de GEE** (tCO2e/ano e kgCO2e/m²) separadas em **combustão local** e **energia comprada**, com fator do SIN e fatores de combustível documentados. Intensidade por ocupante e por área (EAc1; Arc).
7. Score ENERGY STAR (via Portfolio Manager) quando aplicável, ou indicação de "não elegível".
8. **M&V IPMVP** por medida (Opções A/B/C/D): linha de base, ajustes de rotina e não rotineiros, economia em kWh, R$ e tCO2e, e incerteza.
9. Relatório de **auditoria ASHRAE 211** (nível 1/2/3): usos finais, medidas, custos, payback/VPL e **plano de descarbonização com plano de capital** (para o crédito Decarbonization and Efficiency Plans e os estudos de CAPEX/OPEX).
10. Monitoramento contínuo: tendências de submedidores e BMS, detecção de desvios e registro de achados e correções de **retrocomissionamento** com data.

**Refrigerantes (PMOC/CMMS)**
11. **Inventário de refrigerantes:** equipamento, tipo de fluido, **carga (kg)**, **GWP** (com fonte, por exemplo AR4/AR5/AR6) e **GWP total** do edifício (kgCO2e).
12. Registro de inspeções de vazamento, **recargas e compras por tipo e massa** em 12 meses, **GWP vazado total** e taxa de vazamento por equipamento e global.
13. Registro de **descarte e recolhimento** de equipamentos e fluidos, com evidência de conformidade nacional (Ibama/CTF quando aplicável).

**Água e resíduos**
14. Consumo mensal de água por medidor e subsistema e **intensidade de uso de água** (por m² e por ocupante).
15. Massa de resíduos gerada e desviada (por fluxo), **geração por ocupante e taxa de desvio**, mais o resultado da auditoria anual de resíduos.

**Qualidade do ar e experiência humana**
16. Séries contínuas de **CO2, PM2.5 e TVOC** (≥ 3 meses) por zona, com **percentil 95 de CO2**, **médias diárias de PM2.5 e TVOC**, CO2 relativo ao externo (NBR 17037: externo + 700 ppm) e % do tempo dentro dos limites.
17. Resultados de testes pontuais (4 h: pico de CO; médias de O3, PM2.5, PM10, NO2) e laudos NBR 17037 de laboratório acreditado.
18. Evidência de **verificação de ventilação e filtração** (vazões de ar externo × ASHRAE 62.1-2022, classe e troca de filtros).
19. Pesquisas de ocupantes: **% de satisfação** (v5) e média e variância na escala 1–10 (Arc v4.1). **Pesquisa de transporte**: % de modos ativos e compartilhados (v5) e CO2e por viagem (Arc), sempre com menos de 365 dias.

**Documentos de O+M**
20. **Narrativa de sistemas e plano de manutenção preventiva** (derivado do PMOC, alinhado à ASHRAE 180) para o "Current Facilities Requirements and O+M Plan", além de insumos para "Operations Assessment and Policy".

**Integração e governança**
21. Exportação para o **Arc**: API, que exige conta em developer.usgbc.org e acordo de parceiro para atender vários clientes, ou planilha-modelo. Alternativamente, exportação para o **Portfolio Manager** via Web Services, com sincronização ao Arc.
22. **Calendário de conformidade:** 12 meses de dados para a certificação; atualização **anual** de energia e água (v5) entre ciclos; **recertificação a cada 3 anos** com 12 meses de energia, água e vazamento de refrigerante; validade da pesquisa de ocupantes de 365 dias; retrocomissionamento com no máximo 3 anos.
23. Trilha de auditoria: origem de cada dado (fatura, medidor, OS), fatores de conversão e de emissão usados, versão do Arc score e da edição do LEED.
