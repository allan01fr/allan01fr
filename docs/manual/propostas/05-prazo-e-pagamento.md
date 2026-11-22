# 5 · Prazo e pagamento

**Para que serve**
Mostra o cronograma da proposta, fase a fase, em dias úteis e dias corridos, e define a forma de pagamento de cada fase de serviço de engenharia. Também confere se as parcelas somam 100%.

**Campos e botões**

| Campo/botão | O que faz | Observação |
|---|---|---|
| Gráfico de cronograma | Barras com as etapas no tempo, em dias úteis | Passe o mouse para ver horas e marcos |
| Tabela do cronograma | Etapa, início, horas, dias úteis, dias corridos e marco | Etapas de fases diferentes aparecem com "F1 ·", "F2 ·" |
| Forma de pagamento | Marcos e percentuais de cada fase | Fases de % da obra e de pacote têm a condição fixa, definida na aba Preço |
| Marco (texto da proposta) | Texto de cada parcela | Vai para o contrato e para a proposta como está escrito |
| % | Percentual da parcela | Soma precisa dar 100% |
| Linha nova na tabela de pagamento | Acrescenta uma parcela | Linhas sem marco são descartadas |
| Recalcular parcelas padrão | Volta a forma de pagamento sugerida pelo sistema | Desfaz o que foi digitado nessa fase |

**Passo a passo**
1. Confira o gráfico e a tabela do cronograma: as etapas estão na ordem certa e os prazos fazem sentido?
2. Veja o "Prazo total" embaixo do gráfico, em dias úteis e dias corridos.
3. Para cada fase, role até "Forma de pagamento" (ou "Pagamento — Fase N") e confira os marcos.
4. Ajuste o texto do marco e o percentual, se necessário. Para acrescentar uma parcela, use a última linha da tabela.
5. Confirme a mensagem verde "Parcelas somam 100%". Se aparecer em vermelho, corrija antes de exportar.
6. Se quiser voltar à sugestão do sistema, use "Recalcular parcelas padrão".

**Como o cronograma é calculado**
- Cada etapa tem as horas das atividades dela. Os dias úteis são as horas da etapa divididas pelo total de horas do dia da equipe (horas por dia × número de profissionais). Para etapas com equipe própria, usa-se a equipe da etapa.
- As etapas correm em sequência: a seguinte começa quando a anterior termina.
- Dias corridos = dias úteis × 7 ÷ 5, arredondado para cima.
- Se a proposta tem fornecimentos, entram duas etapas mínimas: suprimentos (prazo de fornecimento dos equipamentos) e obra (prazo de execução). Elas valem quando for maior que o cálculo pelas horas.
- Se não há serviço com horas, o cronograma depende só do prazo de execução. Informe-o na aba Fornecimentos.
- Etapa de obra de uma fase de % da obra dura os meses informados na aba Preço (21 dias úteis e 30 dias corridos por mês).

**Como o pagamento é sugerido**
- Parcela de sinal: o percentual de sinal dos parâmetros comerciais, na assinatura do instrumento contratual ou no aceite formal da proposta.
- Parcela intermediária: o restante do valor, proporcional às horas de campo (ou à execução, quando há obra ou fornecimento), arredondada para múltiplos de 5%.
- Saldo: o que sobra, na entrega do documento técnico, contra nota fiscal.
- Se a fase tem fornecimento, o valor dos fornecimentos pesa na parcela de execução.
- Se só há fornecimentos, a parcela intermediária fica na conclusão da execução e do comissionamento.

**Cuidados e limitações**
- Aviso "as parcelas de pagamento somam ..., não 100%": corrija os percentuais na tabela da fase. Sem isso a proposta não fica consistente.
- Fases de % da obra e de pacote de horas não têm tabela editável aqui: a condição sai da forma de cobrança configurada na aba Preço.
- Estimativa interna não tem forma de pagamento e não gera proposta.
- Os dias úteis são estimativas pela equipe e pela carga de horas. Confirme com o cronograma real da obra.
- Uma forma de pagamento digitada fica guardada na proposta. Use "Recalcular parcelas padrão" para voltar à sugestão do sistema.
- O prazo do cronograma aparece também na aba Preço, na linha de "Prazo (dias)" de cada fase.

**Histórico**

| Data | Mudança |
|---|---|
| 2026-11-22 | Versão inicial do manual |
