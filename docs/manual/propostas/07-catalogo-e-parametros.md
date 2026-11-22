# 7 · Catálogo e parâmetros

**Para que serve**
Guarda os serviços que aparecem nas propostas (horas por atividade, campos do formulário, custos diretos) e os valores padrão da empresa (custo e taxa de venda por hora, margem, overhead). Também traz a calculadora de BDI pela fórmula do TCU.

**Campos e botões — Serviços do catálogo**

| Campo/botão | O que faz | Observação |
|---|---|---|
| Serviço | Escolhe o serviço a editar | Mostra disciplina · nome |
| Nome / Tipo / Descrição | Identificação do serviço | Tipo vem da lista do catálogo |
| Formulário (campos) | Tabela só de leitura com os campos do serviço | Use os ids nas expressões de driver |
| Atividades e produtividade | Tabela editável das atividades | Ver "Como o cálculo funciona" |
| Custos diretos | Itens de custo com quantidade por expressão, valor unitário e unidade | Linhas em branco são ignoradas |
| Edição avançada (JSON) | Edita o serviço inteiro em JSON | Use só se souber o formato; "Aplicar JSON" valida antes |
| Salvar catálogo | Grava o catálogo em disco | Desabilitado enquanto houver erros |
| Novo id para duplicar / Duplicar serviço | Cria uma cópia com outro id | O nome recebe "(cópia)" |
| Excluir serviço | Remove o serviço do catálogo | Indisponível se o serviço está na proposta aberta |
| Recarregar catálogo do disco | Descarta edições não salvas | Pede cuidado: a ação não tem volta |

**Campos e botões — Parâmetros da empresa**

| Campo/botão | O que faz | Observação |
|---|---|---|
| Tabela de perfis (Custo/h, Taxa de venda/h) | Valor padrão por perfil técnico | Em R$ por hora |
| Calculadora de custo-hora | Calcula o custo/h a partir da folha | Ver fórmula abaixo |
| Aplicar custo/h ao perfil | Grava o custo calculado no perfil escolhido | Vale só depois de salvar |
| Margem-alvo padrão (%) | Margem de referência | Valor provisório, confirmar com o Allan |
| Overhead padrão (%) | Rateio de custos fixos | |
| % sobre obra padrão | Percentual padrão sobre a obra | |
| Salvar parâmetros da empresa | Grava em `dados/parametros.json` | |
| Aplicar à proposta aberta | Copia os parâmetros para a proposta que está na tela | Não altera outras propostas |

**Calculadora de BDI (fórmula TCU)**

| Campo | Valor padrão na tela | Observação |
|---|---|---|
| Administração central (%) | 4,0 | Provisório; confirmar |
| Seguro + garantia (%) | 0,8 | Provisório; confirmar |
| Risco (%) | 1,0 | Provisório; confirmar |
| Despesas financeiras (%) | 1,0 | Provisório; confirmar |
| Lucro (%) | 7,0 | Provisório; confirmar |
| Impostos (%) | 8,65 | Provisório; confirme com o regime tributário |
| BDI | Calculado | Mostrado em % com vírgula |
| Usar este BDI em | Escolhe a categoria de fornecimento | Grava em "BDI de fornecimento" dos parâmetros |

**Passo a passo — editar um serviço**
1. Escolha o serviço em "Serviço".
2. Ajuste nome, tipo e descrição.
3. Na tabela de atividades, altere horas (fixo e unidade por perfil), fatores ou calibração. Para incluir, use a última linha em branco.
4. Confira a lista de custos diretos.
5. Clique em "Salvar catálogo". Se aparecer "Catálogo com problemas", corrija a lista de erros antes de salvar.

**Passo a passo — atualizar custo/h**
1. Preencha salário ou pró-labore, encargos (%), benefícios (R$/mês) e horas produtivas por mês.
2. Confira o "Custo/h" calculado.
3. Escolha o perfil em "Aplicar ao perfil" e clique em "Aplicar custo/h ao perfil".
4. Clique em "Salvar parâmetros da empresa".

**Passo a passo — calcular BDI**
1. Preencha as seis taxas com os valores da proposta.
2. Leia o BDI mostrado.
3. Se aparecer aviso de faixa, revise as taxas antes de usar.
4. Para usar o BDI num tipo de fornecimento, escolha o tipo e clique em "Usar este BDI em: ...". Depois clique em "Aplicar à proposta aberta" na aba de parâmetros.

**Como o cálculo funciona**
- Horas de cada atividade: (fixo + unidade × quantidade^b) × fatores × calibração. O expoente b (entre 0,05 e 1,5) controla o crescimento com a quantidade.
- Custo/h da calculadora: (salário × (1 + encargos) + benefícios) ÷ horas produtivas por mês.
- BDI pela fórmula do TCU: BDI = [(1 + AC + S + R + G) × (1 + DF) × (1 + L)] ÷ (1 − I) − 1, em que AC é administração central, S seguro e garantia, R risco, G garantia (opcional), DF despesas financeiras, L lucro e I impostos. Impostos precisam ser menores que 100%.

**Cuidados e limitações**
- Alterações no catálogo valem para propostas novas e para as abertas depois de recalcular; propostas já emitidas não mudam sozinhas.
- Antes de salvar o catálogo, uma cópia da versão anterior fica guardada em `dados/catalogo.bak.json`.
- Parâmetros da empresa valem como padrão; a proposta guarda a sua própria cópia até você clicar em "Aplicar à proposta aberta".
- Os percentuais de BDI e a margem na tela são valores de exemplo, marcados como provisórios, até o Allan confirmar.
- A calculadora de BDI não grava nada sozinha; só altera os parâmetros quando você clica no botão de uso.

**Histórico**

| Data | Mudança |
|---|---|
| 2026-11-22 | Versão inicial do manual |
