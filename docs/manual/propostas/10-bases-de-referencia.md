# 10 · Bases de referência

**Para que serve**
Guarda as tabelas de preço, os pisos das convenções coletivas, o CUB e os índices de reajuste que alimentam o orçamento. Cada valor fica gravado com fonte, código, data-base e UF, para você saber de onde veio. Nada vem pronto: você baixa a tabela oficial e importa.

**Abas internas**

| Aba | O que faz |
|---|---|
| Entidades | Lista as fontes conhecidas (EMOP, SCO-Rio, SINAPI e outras), a hierarquia do RJ e as bases já importadas |
| Importar | Carrega uma planilha ou PDF de uma entidade |
| Buscar itens | Procura um item nas bases importadas e monta a cesta de preços |
| Convenções e pisos → custo/h | Calcula o custo por hora a partir do piso da convenção |
| CUB | Escolhe um CUB importado ou informa um valor manual |
| ART | Tabela de honorários de ART, usada para salvar nos parâmetros da empresa |
| Índices | Baixa séries do Banco Central ou informa um número-índice de um mês |

**Campos e botões**

| Campo/botão | O que faz | Observação |
|---|---|---|
| O que importar | Escolhe o tipo: preços, pisos de convenção, CUB ou índice | Muda as colunas pedidas |
| Arquivo da entidade | Envia a planilha (XLSX, XLSM, CSV, TXT) ou o PDF | |
| Fontes em ordem de prioridade | Ordem em que a busca percorre as bases | Ex.: em obra do município do Rio, SCO-RIO primeiro |
| Buscar por código ou descrição | Texto da busca | |
| UF | Estado da busca | Vem da UF do cliente |
| Fontes | Restringe a busca a algumas bases | |
| Piso de referência | Convenção importada, Engenheiro (Lei 4.950-A) ou Informar | |
| Encargos sociais e benefícios | Entram no custo/h | Use os do SINAPI para a UF e os benefícios da convenção |
| Usar este CUB nesta proposta | Grava o CUB escolhido nos parâmetros | |
| Gravar (CUB manual) | Grava um CUB informado por você | |
| Índices | Escolhe os índices a baixar (INPC, IGP-M, IPCA, INCC-M) | Padrão: INPC e IGP-M |
| Baixar/atualizar do Banco Central | Baixa as séries mensais do BCB | Se falhar, importe o CSV |
| Índice e Mês (AAAA-MM) e Número-índice | Grava um número-índice de um mês | |

**Passo a passo**
1. Baixe a tabela oficial no site da entidade (planilha ou PDF).
2. Em Importar, escolha o tipo, envie o arquivo e confirme. A aba Entidades passa a listar a base.
3. Em Buscar itens, confirme a ordem das fontes para a UF da obra e procure o item.
4. Monte a cesta: escolha o critério (mediana, média ou menor) e compare as referências.
5. Para pisos, use Convenções e pisos → custo/h e confira o resultado.
6. Para CUB, escolha o importado e clique em "Usar este CUB nesta proposta".
7. Para reajuste de data-base, atualize os índices em Índices.

**Como o cálculo funciona**
- Busca: percorre as fontes na ordem da hierarquia. No RJ, a ordem padrão é EMOP, SCO-Rio, SINAPI e SICRO (Decreto Estadual 48.929/2024).
- Cesta: reúne as referências do mesmo item. O valor adotado é a mediana, a média ou o menor, conforme o critério escolhido. Valores fora de ±25% da mediana são marcados e deixam de contar. Com menos de 3 referências, o sistema avisa.
- Cotação não comparável: entra na lista, mas fica fora do cálculo da cesta, com o motivo registrado.
- Custo/h: (piso × (1 + adicionais) × (1 + encargos sociais) + benefícios) ÷ horas produtivas.
- Correção por índice: o valor da data-base vai para a data-alvo assim:

  **valor corrigido = valor × índice da data-alvo ÷ índice da data-base**

  Exemplo: um item de R$ 100,00 com índice 200 na data-base e 210 na data-alvo vale 100 × 210 ÷ 200 = R$ 105,00.

- Os índices vêm do Banco Central: INPC (série 188), IGP-M (189), IPCA (433) e INCC-M. Se a série não estiver disponível, o sistema mantém o histórico que já existe.

**Cuidados e limitações**
- Tabelas de referência em JSON (por exemplo, CEHOP-SE) podem trazer valores de exemplo marcados como provisórios. A tela mostra a coluna "Provisório"; confira esses valores com o documento oficial antes de usar em proposta.
- A série do INCC-M ainda precisa ser confirmada no Banco Central. Até lá, importe o INCC-M por CSV ou informe o número-índice mês a mês.
- Índice manual vale só para o mês informado. Para corrigir valores, a data-base e a data-alvo precisam ter índice gravado.
- Cotação de fornecedor é referência, não tabela oficial. Use-a na cesta com critério claro e registre a fonte.

**Histórico**

| Data | Mudança |
|---|---|
| 2026-11-22 | Versão inicial do manual |
