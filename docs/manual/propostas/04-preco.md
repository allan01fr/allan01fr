# 4 · Preço

**Para que serve**
Mostra quanto a proposta custa, como o preço se forma em cada fase e como cada fase é cobrada (escopo fechado, hora técnica, % da obra ou pacote de horas). Também planeja as ARTs e compara as opções da proposta.

**Campos e botões**

| Campo/botão | O que faz | Observação |
|---|---|---|
| Preço total | Soma da parcela fixa e da parcela estimada | Valor global da proposta |
| Parcela fixa | Parte do preço com valor certo | Depende da forma de cobrança de cada fase |
| Parcela estimada | Parte que depende de medição ou de horas | Hora técnica e % sobre as medições da obra |
| Margem efetiva | Margem real da proposta depois de impostos e custos | Negativa quando a cobrança não cobre o custo |
| Tabela por fase | Uma linha por fase, com Nº, Fase, Cobrança, Preço, Fixo, Estimado, Margem, Horas e Prazo | Margem é a margem efetiva da fase. Fixo e Estimado somem quando nenhuma fase tem parcela estimada; Módulo aparece só quando difere do nome da fase; Custo não aparece na tabela (a Margem mostra a relação com o custo). A linha "Total" soma tudo |
| Detalhar a fase | Escolhe a fase para ver a formação do preço e as horas | Mostra a cadeia de custos e o que é próprio da cobrança |
| Planejar ARTs automaticamente | Liga o plano de ARTs da opção | Regras provisórias: confirmar com o CREA-RJ |
| ARTs previstas | Lista das ARTs que o orçamento exige, com taxa e se entra no preço | Aparece quando há plano de ARTs |
| Cobrança de cada fase | Uma caixa por fase, com a forma de cobrança e seus campos | Aberta sozinha nas fases de % da obra e de pacote |
| Comparativo das opções | Indicadores e gráfico lado a lado | Aparece quando a proposta tem mais de uma opção |
| Parâmetros comerciais da proposta | Margem, impostos, overhead, contingência, BDI e deslocamento | Cópia dos parâmetros da empresa: mudar aqui não altera outras propostas |

**Passo a passo**
1. Confira no topo as quatro métricas: Preço total, Parcela fixa, Parcela estimada e Margem efetiva.
2. Na tabela por fase, veja se alguma fase tem margem baixa ou preço zero.
3. Use "Detalhar a fase" para conferir a formação do preço e as horas por perfil de uma fase.
4. Em "Cobrança de cada fase", escolha a forma de cobrança de cada fase e preencha os campos dela.
5. Se a fase é de obra, informe a base do % (valor da obra ou execução) e a duração em meses.
6. Ligue "Planejar ARTs automaticamente" se quiser que a proposta inclua as ARTs, e confira a caixa "ARTs previstas".
7. Veja o "Comparativo das opções" quando houver mais de uma opção.

**Como o preço é formado**
Em palavras simples, o preço de uma fase é montado em etapas:

1. **Mão de obra:** horas de cada atividade × custo por hora de cada perfil.
2. **Overhead:** custos fixos da empresa rateados. Pode ser por percentual da mão de obra ou por hora faturável.
3. **Custos diretos:** o que a fase gasta fora do próprio trabalho, como deslocamento acima do raio isento e a taxa de ART.
4. **Custo da fase** = mão de obra + overhead + custos diretos.
5. **Contingência:** percentual sobre o custo da fase, definido pelo risco do escopo (Baixo, Médio ou Alto). Aparece na tabela "Formação do preço" como "Contingência (…%)".
6. **Margem e impostos:** o preço dos serviços é o custo mais a contingência, dividido por (1 − impostos − margem-alvo). Assim, depois de pagar os impostos, sobra a margem desejada.
7. **Fornecimentos:** materiais e equipamentos entram pelo custo com o BDI da categoria (parâmetros comerciais), somados ao preço da fase.

A **margem efetiva** é o que sobra de honorários depois de impostos, descontado o custo dos serviços, dividido pelos honorários. Se der negativa, a cobrança não cobre o custo.

**Formas de cobrança de uma fase**

- **Escopo fechado:** preço pela cadeia de custos acima. Valor certo.
- **Hora técnica:** horas × taxa de venda de cada perfil, faturadas pelo apontamento. O valor é estimado e tem teto.
- **% da obra:** percentual sobre o valor global da obra. Campos: "% sobre a obra", "Forma" e, na forma "Parcela fixa + % das medições", a "Parcela fixa — mobilização e planejamento (R$)". Formas:
  - "% sobre cada medição": o percentual incide sobre cada medição aprovada.
  - "Fixo pelo valor global (faturado nas medições)": valor fixo = % × base, pago conforme as medições.
  - "Parcela fixa + % das medições": parcela fixa na mobilização mais o percentual sobre cada medição.
  - A base é o "Valor global da obra" (campo "Base"). As opções são "Estimativa interna", "Valor informado", "Custo dos fornecimentos da fase" e "Valor da execução desta opção". Esta última usa o total de fornecimentos e execução da opção (ou só o preço das fases de execução, na parte "Preço total das fases de execução").
  - "Duração da obra (meses; 0 = prazo pelas horas)" e "Curva das medições" (Curva S ou Linear) definem como o valor se distribui no tempo.
- **Pacote de horas:** um número de horas vendido com taxa fixa. Formas:
  - "Mensal (h/mês × meses)": horas por mês e número de meses. Em "Horas por mês", zero usa as horas dos serviços da fase.
  - "Total sob demanda": horas do pacote, validade em meses e número de parcelas.
  - "Estimado pelas horas da obra": horas = dias úteis da obra × "Horas de acompanhamento por dia útil" + "Horas fixas (mobilização e relatório)". Os dias úteis vêm do plano de execução, se houver; senão, do campo de dias da obra.
  - A taxa do pacote é a taxa média de venda do mix de perfis, com o "Desconto sobre a taxa de venda (%)" aplicado. "Acréscimo na hora excedente (%)" define a hora que passar do pacote.
- **Taxa de desempenho:** opcional e variável. Fica fora do preço. Mostra o potencial de bônus num cenário simulado, limitado a um teto.

**Cuidados e limitações**
- Aviso "% da obra rende ... abaixo do mínimo para cobrir as horas": o percentual não paga as horas da fase. O aviso mostra o mínimo e a porcentagem que seria preciso. Ajuste o % ou use "Estimado pelas horas da obra" ou "Parcela fixa + % das medições".
- Aviso "a cobrança ... não cobre o custo": a margem efetiva da fase é negativa. Revise a forma de cobrança ou os valores.
- Aviso "fase sem ART no preço": fase só de fornecimentos. Confirme se a execução exige ART própria.
- Aviso "% da obra sem base": informe o valor da obra ou vincule uma estimativa interna.
- As ARTs previstas seguem regras provisórias. Confirme com o CREA-RJ antes de usar em proposta.
- A taxa de cada ART sai da faixa do valor base (tabela de faixas) ou de um valor fixo, conforme os parâmetros da empresa. Confira a tabela vigente.
- A margem-alvo, a contingência, o overhead e o BDI vêm dos parâmetros desta proposta. Confira se refletem a sua prática antes de enviar.
- Uma fase desligada fica fora do preço e de todos os cálculos.

**Histórico**

| Data | Mudança |
|---|---|
| 2026-11-22 | Versão inicial do manual |
| 2026-11-22 | Tabela por fase cabe na tela; coluna Margem visível (P-10) |
