# LEED e certificações no Brasil: síntese para a suíte HVAC-R

Pesquisa de 2026-11-08 feita por cinco subagentes em paralelo. Os relatórios completos estão
nesta pasta, com a fonte de cada fato e o grau de confirmação.

> **Limitação:** a rede da sessão bloqueou usgbc.org, gbci.org, arcskoru.com e ashrae.org. Os
> fatos vêm de trechos devolvidos pela busca, não dos PDFs oficiais. Cada relatório marca o que
> está confirmado, o que tem fonte única e o que não foi confirmado. Antes de usar um número em
> proposta, laudo ou cálculo de crédito, confira no documento oficial.

| Relatório | Assunto |
|---|---|
| [1_estrutura_leed_v5.md](1_estrutura_leed_v5.md) | Sistemas, LEED v5 × v4.1, níveis, transição, taxas |
| [2_creditos_hvacr.md](2_creditos_hvacr.md) | Créditos que dependem de HVAC-R e o cálculo que cada um exige |
| [3_om_existentes_arc.md](3_om_existentes_arc.md) | Edifícios existentes (O+M), plataforma Arc, M&V |
| [4_contexto_brasil.md](4_contexto_brasil.md) | GBC Brasil, PBE Edifica/INI-C, normas, clima, refrigerantes |
| [5_software_mercado.md](5_software_mercado.md) | Software de simulação, CFD, mercado, licenças |

## 1. O que vale hoje

- **LEED v5** foi lançado em abril de 2025 para BD+C, ID+C e O+M. Total de 110 pontos; níveis
  Certified 40, Silver 50, Gold 60 e Platinum 80. O Platinum passou a exigir mínimos de carbono.
- **v4/v4.1** aceitam novos registros até 30/06/2027. A partir de 01/07/2027 só existe o v5.
- **Tipologias** (escola, saúde, varejo, data center, hotel, armazém) viraram regras dentro dos
  créditos; ND, Residential e Cities seguem no v4/v4.1.
- **Taxas GBCI** (iguais às do v4.1): registro US$ 1.350 (membro) / US$ 1.700; certificação BD+C
  a partir de US$ 0,064/ft² (membro, mínimo US$ 3.200).
- **No Brasil:** 7º mercado fora dos EUA em 2025 (171 projetos). Escritórios e logística
  dominam, concentrados no Sudeste.

## 2. Onde HVAC-R pesa no LEED v5

| Tema | Pré-requisito / crédito | Cálculo que a suíte precisa fazer |
|---|---|---|
| Energia | EAp2 / EAc3 (até 10 pts) | Simulação 8760 pelo Apêndice G da ASHRAE 90.1 (2019 até 2027; 2022 depois) |
| Carbono | EAp1 | Projeção de 25 anos, incluindo vazamento de refrigerante, e plano de descarbonização com CAPEX |
| Carga de pico | EAc2 (5 pts) | Carga de pico de resfriamento e aquecimento **com ventilação**, por zona e sistema |
| Eletrificação | EAc1 (5 pts) | Fração do aquecimento atendida por bomba de calor |
| Refrigerantes | EAp5 (pré-requisito, novo) / EAc7 (2 pts) | Inventário (carga, GWP, tCO2e), alternativas para GWP > 700, teste de vazamento, GWP médio ponderado |
| Ventilação | EQp / EQc1 | ASHRAE 62.1-2022 (VRP), MERV 13, medição de ar externo; +15% ou +30% no crédito |
| Conforto | EQc2 | PMV/PPD pela ASHRAE 55-2023; CFD como evidência complementar |
| Medição e Cx | EAp3, EAp4, EAc5 | Plano de medição, consumo esperado por uso final, documentos de comissionamento |

**A NBR 16401 não substitui a ASHRAE 62.1 nem a 55** em nenhum caminho alternativo encontrado.
A suíte calcula as duas normas em paralelo.

## 3. Edifícios existentes (LEED O+M e Arc)

- 12 meses de dados de energia e água; a recertificação, a cada 3 anos, pede também os
  vazamentos de refrigerante.
- No Brasil, o caminho prático de energia é **redução de 8% ou mais sobre o histórico do
  próprio edifício** (o ENERGY STAR compara com a base dos EUA). É o produto de um analisador
  de energia com linha de base e M&V pelo IPMVP.
- O **plano de O+M** corresponde ao PMOC. O crédito de qualidade do ar pede 3 meses de
  monitoramento contínuo de CO2, PM2.5 e TVOC.
- O Arc tem API. Uma consultoria que atende vários clientes precisa de acordo de parceiro.

## 4. Contexto brasileiro

- **PBE Edifica / INI-C:** desde 11/2024 a etiqueta de projeto é feita por simulação contra uma
  edificação de referência nível D, na prática com EnergyPlus. Prédios federais precisam de
  nível A a partir de 2027 (Resolução CGIEE 4/2025).
- **Clima:** o LabEEE/UFSC recomenda os arquivos TMYx do climate.onebuilding.org.
- **Refrigerantes:** HCFC com corte de 97,5% em 2030 e eliminação em 2040; HFC com consumo
  congelado em 2024, redução de 10% em 2029 e cotas em tCO2e (Kigali).
- **Normas:** NBR 16401 revisada em 11/2024; a Parte 3 foi suspensa em 05/2025 e está em revisão.

## 5. Software e mercado

- O LEED não tem lista de software aprovado; o Apêndice G exige programa testado pela ASHRAE 140.
- **EnergyPlus/OpenStudio** atende LEED e INI-C, tem API Python (OpenStudio SDK) e o modelo de
  referência do Apêndice G vem do openstudio-standards (PNNL). DesignBuilder e TRACE 3D Plus usam
  o mesmo motor.
- **Licenças:** o nome EnergyPlus e a marca LEED não podem aparecer no nome do produto.
  Honeybee (AGPL), BESOS (GPL) e Pollination ficam fora do núcleo de uma suíte proprietária.
- **CFD** não é exigido por nenhum crédito confirmado do v5.
- **Honorários:** consultoria LEED no Brasil em torno de 0,5–1% da obra (fontes secundárias); não
  há dado público de modelagem energética e comissionamento no Brasil.

## 6. Consequências para a suíte

1. **Integrar o EnergyPlus/OpenStudio** como motor de energia anual da T4; construir o tradutor
   zonas/cargas → modelo, os relatórios e o pós-processamento. O mesmo motor atende LEED e INI-C.
2. **Inventário de refrigerantes** sobe de prioridade: pré-requisito no v5, base do EAp1 e
   recertificação O+M. Os ativos (T0) e as OS de campo (T2) produzem esses dados.
3. **Carga de pico com ventilação** (EAc2, 5 pts) reaproveita o módulo de carga térmica.
4. **Ventilação 62.1 + NBR 16401-3** e **PMV/PPD** entram como cálculos da T4.
5. **Analisador de energia** (linha de base + M&V) atende o LEED O+M e os estudos de retrofit.
6. **CFD (T6)** continua como ferramenta de projeto e conforto, não como requisito de certificação.
