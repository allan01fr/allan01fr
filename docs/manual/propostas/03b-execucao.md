# 3b · Execução

**Para que serve**
Calcula a equipe, as horas (HH), o prazo e o custo da execução da obra, a partir dos itens de execução da opção. Quando o resultado está pronto, "Levar execução para o preço" manda a mão de obra e o material para a aba Preço.

**Campos e botões**

| Campo/botão | O que faz | Observação |
|---|---|---|
| Aplicar kit + Aplicar kit | Copia um kit de execução para os itens da opção | Os kits são provisórios (ver Cuidados) |
| Tabela de itens de execução (Descrição, Unid, Qtd, HH/unid, Função, Material (R$/unid), Base, Fase, Frente/kit) | Serviços de execução com horas por unidade | Linha sem descrição é ignorada. Pode incluir e remover linhas |
| Função | Perfil que executa (TC, ES, PL nos kits) | Nos kits: TC = mecânico de refrigeração, ES = ajudante, PL = encarregado |
| Fase que recebe a execução no preço | Fase ativa onde a mão de obra e o material caem | Só fases incluídas aparecem |
| Altura, Acesso, Ocupação, Turno | Fatores padrão que multiplicam as horas | Cada opção tem o seu valor (ver "Como o cálculo funciona") |
| Prazo-alvo (dias úteis) | Prazo que você quer cumprir | Padrão 20 |
| Horas/dia | Jornada de trabalho considerada | Padrão 8,0; de 1 a 24 |
| Eficiência | Fração do dia que a equipe produz de fato | Padrão 0,80; de 0,10 a 1,00 |
| Métricas: HH total, Mão de obra, Material, Prazo (dias úteis) | Resumo do cálculo | |
| Tabela de equipe e gráfico de frentes | Horas por função e por frente | |
| Curva ABC (gráfico e tabela) | Itens de maior custo, somando mão de obra e material | Aparece quando há custo |
| Levar execução para o preço | Grava os fornecimentos da execução na fase escolhida e ajusta o acompanhamento | Mensagem mostra quantos itens foram levados |

**Passo a passo**
1. Se houver um kit adequado, escolha-o em "Aplicar kit" e clique em "Aplicar kit". Confira a tabela depois.
2. Ajuste as linhas da tabela: descrição, quantidade, HH por unidade, função e material.
3. Em "Configuração", escolha a fase que recebe a execução e os quatro fatores padrão.
4. Informe prazo-alvo, horas/dia e eficiência.
5. Confira HH total, mão de obra, material e prazo nas métricas, a tabela de equipe e a curva ABC.
6. Clique em "Levar execução para o preço". Depois abra a aba Preço para conferir.

**Como o cálculo funciona**
- Fator = produto dos fatores escolhidos (altura, acesso, ocupação, turno). Cada opção usa os fatores escolhidos aqui; a tabela de itens não tem fator próprio.
- HH do item = quantidade × HH por unidade × fator × calibração (no kit, a calibração é 1,0).
- Pessoas por função = arredondar para cima de HH ÷ (horas/dia × prazo-alvo × eficiência). Se o prazo-alvo for 10 dias, esse é o número de pessoas de cada função.
- Dias úteis = cada frente, em sequência, leva o maior dos dias de suas funções, arredondado para cima de HH ÷ (horas/dia × pessoas × eficiência). Some as frentes. Se o arredondamento de cada frente fizer o total passar do prazo-alvo, a tela avisa.
- Dias corridos = arredondar para cima de dias úteis × 7 ÷ 5.
- Mão de obra = HH de cada função × custo-hora da função × encargos (padrão 1,0). O custo-hora vem dos parâmetros da empresa; sem ele, a tela usa valores de referência provisórios.
- Material = quantidade × material por unidade.
- Exemplo real: 10 × o kit "Instalação split 12.000 BTU/h (padrão)", com prazo-alvo de 10 dias, dá 6 dias úteis e 9 dias corridos, com equipe de 1 mecânico de refrigeração e 1 ajudante (HH de 32,5 e 9,5).
- Ao levar para o preço, o acompanhamento de obra da opção deixa de ser fixo e passa a ser "% sobre a execução", se ainda estiver no padrão. As horas dele são dimensionadas pela duração da obra: a duração em meses é o número de dias corridos ÷ 30, arredondado para cima. Obra de até um mês: um mês, uma visita a cada 5 dias úteis (mínimo de 2, início e entrega) e relatório final único. Obra maior: quatro visitas por mês.

**Cuidados e limitações**
- **Valores provisórios.** Os kits de execução trazem valores fictícios e marcados como "provisório" na base (HH, material e fonte). Ajuste com dados da empresa antes de usar em proposta.
- **Custo-hora provisório.** Enquanto o custo-hora de cada função não estiver nos parâmetros da empresa, a mão de obra usa valores de referência marcados como provisórios (por exemplo, encarregado, mecânico de refrigeração, ajudante). Não envie proposta com esse valor.
- "Levar execução para o preço" substitui a execução anterior: os fornecimentos de origem "execucao" são recriados. Se a lista estiver vazia ou houver erro no cálculo, nada é levado e a mensagem mostra 0 itens; leia o aviso no topo da aba.
- Depois de mudar a fase que recebe a execução, clique de novo em "Levar execução para o preço" para refazer os fornecimentos na fase nova.
- O acompanhamento só é trocado para "% sobre a execução" se ainda estiver no padrão; se você já configurou o acompanhamento, ele não muda.

**Histórico**

| Data | Mudança |
|---|---|
| 2026-11-22 | Versão inicial do manual |
