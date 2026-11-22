# 9 · Viabilidade

**Para que serve**
Compara alternativas de intervenção (por exemplo, troca de equipamentos, retrofit ou geração fotovoltaica) com o sistema atual. Mostra quando as contas empatam, em quanto tempo o investimento se paga e se a troca compensa, com VPL, TIR e custo de ciclo de vida (LCC). Gera uma planilha de cálculo e um relatório para o cliente.

**Campos e botões**

| Campo/botão | O que faz | Observação |
|---|---|---|
| Título do estudo | Nome que aparece nos documentos | |
| Linha de base | Escolhe como descrever o sistema atual: pela capacidade ou pelo consumo medido | "Pela capacidade" usa TR; "Pelo consumo anual medido" usa kWh |
| Capacidade (TR), kW/TR medido, Horas de operação/ano, Fator de carga médio | Dados para estimar o consumo atual | Aparecem só no modo "Pela capacidade" |
| Consumo anual (kWh) | Consumo real do sistema atual | Aparece só no modo "consumo medido" |
| kW/TR de projeto | Consumo previsto pelo projeto original | 0 = não comparar |
| Tarifa média (R$/kWh) | Custo da energia | Use a fatura do cliente ou a tarifa homologada pela ANEEL, com tributos |
| Manutenção atual (R$/ano) | Custo anual de manutenção do sistema atual | |
| Paliativos / manutenção de emergência (R$) | Custos comuns a todas as alternativas | Entram no LCC, não no fluxo incremental |
| TMA (% a.a.) | Taxa mínima de atratividade, usada para descontar | Base do payback e do VPL |
| Horizonte (anos) | Período de análise | De 1 a 30 |
| Reajuste da energia / da manutenção (% a.a.) | Crescimento anual desses custos | |
| Tabela de alternativas | Uma linha por alternativa | Veja as colunas abaixo |
| CAPEX (R$) | Investimento da alternativa | Ignorado quando a linha usa "CAPEX = preço da opção" |
| CAPEX = preço da opção | Usa o preço de uma opção desta proposta como investimento | "—" = usar o CAPEX informado |
| Extra sobre a opção (R$) | Valor somado ao preço da opção | Ex.: obra civil à parte |
| Redução de consumo (%) | Quanto a alternativa reduz o consumo atual | |
| Geração FV (kWh/ano) | Energia gerada no local, descontada do consumo | |
| Manutenção (R$/ano) | Manutenção da alternativa | Vazio = igual à atual |
| Gerar planilha do estudo (.xlsx) | Monta a planilha com as contas em fórmulas | Botão "Baixar estudo de viabilidade" aparece depois |
| Gerar relatório para o cliente | Monta o relatório em DOCX | Botão "Relatório para o cliente (DOCX)" aparece depois |
| Gerar PDF do relatório | Converte o DOCX em PDF | Só aparece se o LibreOffice estiver instalado |

**Resultados na tela**
- Consumo atual, consumo previsto no projeto original e custo anual da perda de desempenho.
- Tabela com, para cada alternativa: economia no ano 1, breakeven, payback, VPL, TIR, classificação, origem do CAPEX, economia mínima (VPL = 0), LCC e consumo em relação ao projeto.
- Gráfico do fluxo acumulado: a curva cruza o zero no breakeven.
- Sensibilidade do VPL para variações da economia (de -30% a +30%), do CAPEX (de -20% a +20%) e da tarifa (de -20% a +20%).

**Passo a passo**
1. Escolha a linha de base e preencha os dados do sistema atual (capacidade ou consumo).
2. Informe a tarifa, a manutenção atual e, se houver, os paliativos.
3. Ajuste TMA, horizonte e reajustes.
4. Na tabela de alternativas, dê um nome a cada uma e escolha o CAPEX: informado ou vinculado a uma opção da proposta, com extra se houver.
5. Preencha a redução de consumo, a geração FV e a manutenção de cada alternativa.
6. Confira a tabela de resultados e a sensibilidade.
7. Gere a planilha ou o relatório para o cliente.

**Como o cálculo funciona**
- Consumo atual: no modo TR, TR × kW/TR medido × horas × fator de carga. No modo consumo, o kWh informado.
- Economia no ano t: a economia de energia e a de manutenção, reajustadas pelos percentuais de cada ano.
- Ano 0 é o investimento (CAPEX), negativo.
- Breakeven: ano em que a economia acumulada, sem desconto, iguala o CAPEX.
- Payback: ano em que a economia acumulada, descontada pela TMA, iguala o CAPEX.
- VPL: valor presente da economia menos o CAPEX. Positivo = a alternativa rende mais que a TMA.
- TIR: taxa que zera o VPL. Não aparece quando não há retorno.
- LCC: custo total ao longo do horizonte (paliativos, energia, manutenção e investimento, em valor presente). Menor LCC = menor custo para o cliente.
- Classificação: "Quick win" (breakeven em até 2 anos), "Viável" (VPL positivo), "Inviável financeiramente" (VPL negativo) ou "Sem economia".

**Relatório para o cliente**
- Quando uma alternativa não tem investimento informado, ela aparece como "Investimento não informado" e fica fora da conclusão.
- A conclusão é gerada pelos números. Se nenhuma alternativa tiver VPL positivo, o texto diz isso.

**Cuidados e limitações**
- Os resultados dependem das premissas. Revise tarifa, TMA e reajustes com o cliente.
- O CAPEX vinculado a uma opção usa o preço dessa opção na proposta. Se a opção mudar, o estudo muda junto.
- O VPL pode ficar negativo com economia 30% menor que a prevista. A conclusão aponta essas alternativas.
- Paliativos entram só no LCC; não alteram a economia incremental de cada alternativa.
- Confira a tarifa com a fatura real: tributos e bandeiras mudam o valor do kWh.

**Histórico**

| Data | Mudança |
|---|---|
| 2026-11-22 | Versão inicial do manual |
