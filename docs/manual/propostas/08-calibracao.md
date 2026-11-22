# 8 · Calibração

**Para que serve**
Compara as horas estimadas pelo sistema com as horas realmente gastas nos projetos encerrados e sugere um fator de ajuste para cada atividade. Assim, as próximas propostas refletem a sua experiência de campo.

**Campos e botões**

| Campo/botão | O que faz | Observação |
|---|---|---|
| Tabela de horas (Serviço, Atividade, Estimado (h), Realizado (h)) | Lista as atividades da proposta aberta | Só a coluna Realizado (h) é editável |
| Registrar horas realizadas de '...' | Salva o registro do projeto no histórico | Só com a proposta aberta e horas preenchidas |
| Histórico: N registro(s) | Quantos projetos já foram registrados | |
| Tabela de fatores sugeridos | Fator sugerido por atividade e quantidade de amostras | Fator = mediana de realizado ÷ estimado |
| Mínimo de amostras para aplicar | Número mínimo de registros para uma atividade ser ajustada | Padrão 2 |
| Aplicar fatores sugeridos ao catálogo e salvar | Grava os fatores no catálogo e salva | Só atividades com amostras suficientes |

**Passo a passo — registrar um projeto encerrado**
1. Abra a proposta do projeto que terminou.
2. Vá até a aba 8 · Calibração.
3. Na coluna "Realizado (h)", digite as horas reais de cada atividade. Deixe em branco o que não foi executado ou não foi medido.
4. Clique em "Registrar horas realizadas de ...".
5. Confira a mensagem de confirmação com o número de atividades salvas.

**Passo a passo — aplicar os fatores**
1. Confira a tabela de fatores sugeridos e o número de amostras de cada atividade.
2. Ajuste "Mínimo de amostras para aplicar" se quiser ser mais ou menos exigente.
3. Clique em "Aplicar fatores sugeridos ao catálogo e salvar".
4. Confira a mensagem "N atividade(s) calibradas e catálogo salvo".

**Como o cálculo funciona**
- Para cada atividade, o sistema divide as horas realizadas pelas estimadas em cada projeto registrado e usa a mediana dessas razões. A mediana evita que um projeto muito fora do padrão distorça o resultado.
- Uma atividade só é ajustada quando tem pelo menos o número mínimo de amostras definido no campo.
- O fator aplicado vai para o campo de calibração da atividade no catálogo; as horas das próximas propostas passam a usá-lo como multiplicador.

**Cuidados e limitações**
- Registre só projetos encerrados. Horas parciais distorcem a mediana.
- Registre a proposta certa: o sistema usa a proposta aberta na tela. Se você estiver numa revisão diferente, confira antes.
- Aplicar os fatores altera o catálogo e as propostas futuras. Propostas já emitidas não mudam; gere uma nova versão para usar o fator.
- O histórico de registros é guardado em `dados/historico.json`. Mantenha uma cópia de segurança junto com o catálogo.
- Com poucos projetos, a sugestão é pouco confiável. Use o mínimo de 2 amostras como piso e revise à mão as atividades com fator muito alto ou muito baixo.
- Não há desfazer para "Aplicar fatores". Para voltar atrás, restaure `dados/catalogo.bak.json` (versão anterior ao último salvamento).

**Histórico**

| Data | Mudança |
|---|---|
| 2026-11-22 | Versão inicial do manual |
