# 3 · Fornecimentos e subcontratações

**Para que serve**
Lista o que entra na proposta como compra ou terceirização: equipamentos, materiais, mão de obra de execução e subcontratos (instalação mecânica, elétrica, isolamento, automação...). Também registra o prazo de fornecimento dos equipamentos e o prazo de execução da obra.

**Campos e botões**

| Campo/botão | O que faz | Observação |
|---|---|---|
| Tabela de itens (Descrição, Categoria, Unid, Qtd, Custo unitário (R$), Fonte, Código, Data-base (AAAA-MM)) | Itens do fornecimento | Linhas podem ser incluídas e removidas; linha sem descrição é ignorada |
| Categoria | Material, Equipamento, Mão de obra de execução ou Subcontrato | Cada categoria recebe o seu BDI (aba Preço, parâmetros) |
| Fase | Fase que recebe o item | Só aparece com mais de uma fase. Fase desligada aparece com "(desligada)" |
| Prazo de fornecimento dos equipamentos — lead time (dias úteis) | Prazo de compra e entrega | Vira a etapa "Suprimentos" do cronograma, quando há equipamentos ou materiais |
| Prazo de execução da obra/instalação (dias úteis) | Duração da instalação | Usado no cronograma quando há fornecimentos |
| Pesquisa de preços (cesta) por item | Junta várias referências para um mesmo item | Só aparece quando há itens |
| Item | Escolhe o item da cesta | Mostra quantas referências ele tem |
| Tabela de referências (Fonte / fornecedor, Código, Data-base, Valor unitário (R$)) | Cotações e preços de bases | Pode incluir linhas à vontade |
| Critério | Mediana, Média ou Menor valor | Vem do parâmetro da empresa |
| Atualizar pelo índice | Corrige os valores por um índice de custo | "Não atualizar" mantém os valores como estão |
| Data-alvo (AAAA-MM) | Mês para o qual os valores são corrigidos | Começa com o mês da data da proposta |
| Aplicar o valor adotado ao item | Grava o valor da cesta no custo unitário | Troca a fonte do item por "Cesta de preços (...)" |

**Passo a passo**
1. Na tabela, inclua uma linha por item. Preencha descrição, categoria, unidade e quantidade.
2. Informe o custo unitário quando já tiver cotação. Se não tiver, use a aba 10 (Bases de referência) para buscar preços.
3. Em "Fase", escolha a fase que vai pagar o item (só em propostas com mais de uma fase).
4. Preencha o prazo de fornecimento e o prazo de execução em dias úteis.
5. Para itens com mais de uma fonte, abra "Pesquisa de preços (cesta) por item", escolha o item, preencha as referências (recomendado no mínimo 3), confira a faixa e clique em "Aplicar o valor adotado ao item".

**Como o cálculo funciona**
Na pesquisa de preços, a cesta junta as referências do item e calcula a mediana. O valor adotado é o critério escolhido (mediana, média ou menor valor) entre as referências que ficam dentro da faixa de desvio em torno da mediana; as demais aparecem como "fora da faixa". Quando há índice escolhido, cada referência é corrigida da sua data-base até a data-alvo. O custo do fornecimento entra no preço da fase com o BDI da sua categoria.

**Cuidados e limitações**
- Os fornecimentos gerados pela aba 3b (origem "execucao") são recriados quando você clica em "Levar execução para o preço". Não edite esses itens à mão; ajuste a execução na aba 3b.
- Itens sem fonte ou data-base dificultam a conferência. Preencha sempre que houver cotação.
- Confira a data-alvo da cesta: um índice aplicado a uma data muito distante pode distorcer o valor.

**Histórico**

| Data | Mudança |
|---|---|
| 2026-11-22 | Versão inicial do manual |
