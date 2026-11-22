# 2 · Escopo

**Para que serve**
Monta os serviços da proposta, organizados em fases. Cada fase é precificada sozinha, pode ser contratada separadamente e tem a sua forma de cobrança. Aqui também se criam, duplicam e excluem as opções da proposta.

**Campos e botões**

| Campo/botão | O que faz | Observação |
|---|---|---|
| Nome da opção | Nome da opção que está aberta | Aparece na proposta |
| ➕ Nova opção | Cria uma opção nova com a primeira letra livre | |
| Duplicar com nível + ⧉ Duplicar | Copia a opção atual | Níveis: Duplicar igual, Duplicar em 2D, Duplicar em 3D, Duplicar em BIM |
| Modalidade | Proposta em fases ou Estimativa interna do valor global | A estimativa não gera proposta; serve de base para % da assessoria e CAPEX da viabilidade |
| Incluir módulo | Cria uma fase pronta com os serviços do módulo | Botões: Projeto, Acompanhamento de obra, Execução, Inspeção com laudo de conformidade, Avaliação de desempenho |
| Nome da fase | Nome da fase na proposta | Se a fase veio de um módulo, mostra "Módulo: ..." embaixo |
| Cobrança | Escopo fechado, Hora técnica, % da obra ou Pacote de horas | Os parâmetros de cada cobrança ficam na aba Preço |
| Incluir (chave) | Liga ou desliga a fase | Desligada, a fase sai do preço, do cronograma e da proposta, mas continua guardada. A última fase incluída não pode ser desligada |
| ⬆ (na fase) | Sobe a fase | A ordem das fases define a numeração (1, 2, 3...) |
| 🗑 (na fase) | Remove a fase | Os serviços dela vão para a primeira fase incluída |
| ➕ Nova fase | Cria uma fase vazia | |
| Disciplina, Tipo, Serviço | Filtros do catálogo para escolher o serviço | Mostra a descrição do serviço escolhido |
| Na fase | Fase que recebe o serviço novo | Aparece só quando há mais de uma fase |
| Adicionar à opção | Inclui o serviço escolhido na opção | O formulário do serviço abre logo abaixo |
| Campos do serviço | Dados que o catálogo pede (quantidades, tipos, opções) | Cada campo tem a sua unidade e, quando existe, uma ajuda ao passar o mouse |
| Nome na proposta | Nome alternativo do serviço | Vazio = nome do catálogo |
| Complexidade neste serviço | Troca a complexidade só deste serviço | Vazio = igual à proposta |
| Fator manual sobre as horas | Multiplica as horas deste serviço | De 0,1 a 5,0 |
| ⬆ / ⬇ / 🗑 Remover (do serviço) | Muda a ordem ou remove o serviço | |
| 🗑 Excluir a opção | Apaga a opção aberta | Só aparece quando há mais de uma opção |

**Passo a passo**
1. Escolha a modalidade. Para proposta de serviços de engenharia, use "Proposta em fases".
2. Para um pacote padrão, clique em um dos botões de "Incluir módulo". Cada clique cria uma fase própria. Depois ajuste nome, cobrança e a chave Incluir.
3. Em "Adicionar serviço do catálogo", filtre por disciplina e tipo, escolha o serviço, a fase (se houver mais de uma) e clique em "Adicionar à opção".
4. Abra o serviço na lista, confira a tabela de atividades e preencha os campos. Use "Ajustes deste serviço" só quando o serviço fugir do padrão.
5. Use ⬆ e ⬇ para ordenar os serviços dentro da fase.

**Como o cálculo funciona**
Cada serviço gera uma tabela de atividades, com quantidade, fator e horas por perfil. O total de horas do serviço aparece em negrito abaixo da tabela. Os fatores da aba 1 (complexidade, documentação, acesso, urgência) multiplicam essas horas, a menos que o serviço tenha complexidade própria. O "Fator manual" multiplica por último. Os custos diretos do serviço (quando existem) aparecem ao lado do total.

**Cuidados e limitações**
- Remover uma fase ou um serviço é imediato na tela: confira antes de clicar.
- Excluir a opção também apaga tudo o que está nela (serviços, fornecimentos e execução). Duplique antes se quiser guardar uma versão.
- Módulos não valem para a estimativa interna: nesse caso a tela mostra a lista de etapas da obra.
- Horas e nomes do catálogo vêm das tabelas de serviços; se um número não parecer seu, ajuste no formulário do serviço, não no catálogo.

**Histórico**

| Data | Mudança |
|---|---|
| 2026-11-22 | Versão inicial do manual |
