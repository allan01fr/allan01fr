# T1 Comercial: plano de implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para executar este plano tarefa por tarefa. Os passos usam caixas de seleção (`- [ ]`) para acompanhamento.

**Objetivo:** fazer pela web o projeto comercial completo, nesta ordem: proposta (motor `orcamento`), HH de execução, equipe e prazo, preço de obra, honorário pelo método ABRAVA/DNPC com os ajustes da empresa, situação da proposta, contrato, documentos PDF e painel comercial.

**Arquitetura:** o cálculo novo entra no pacote `propostas/orcamento` como módulos puros e testados. São quatro arquivos: `execucao.py`, `honorario_abrava.py`, `ajustes_honorario.py` e `erros.py`. O motor de preço ganha uma cobrança `valor` (valor definido), para que o honorário ABRAVA ajustado entre no mesmo motor de preço. O módulo `suite/backend/app/modulos/comercial` segue `rotas.py → esquemas.py → servico.py → repositorio.py → modelos.py`. Ele só monta as entradas, chama o motor, grava e congela cada proposta gerada numa revisão imutável (regra 7). As telas ficam em `suite/frontend/src/paginas/comercial`.

**Tecnologias:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 síncrono, Alembic, PostgreSQL 16, WeasyPrint + Jinja2 (PDF), num2words (valor por extenso), openpyxl e python-docx (já usados pelo motor), React 19 + TypeScript + Vite, Vitest + Testing Library, Playwright.

**Especificação:** `docs/superpowers/specs/2026-11-08-suite-hvacr-design.md`, seções 3, 4, 5 (linha `comercial`) e 6 (T1, versão atualizada). Requisitos detalhados: `requisitos_video_hvac_office.md`, recebido do coordenador, com proposta, projeto, documentos e painel. Ele é só referência de funcionalidade: não se copiam marca, textos nem telas. A T0 está em `docs/superpowers/plans/2026-11-08-t0-fundacao.md`, e os nomes deste plano seguem os dela.

## Restrições globais

- Python `>=3.12,<3.13` na suíte, conforme a T0. O pacote `orcamento` declara `>=3.12`. `cd propostas && python3 -m pytest -q testes` precisa passar ao fim de toda tarefa (hoje são 155 testes).
- O motor não é copiado para `suite/`. Ele é instalado em modo editável (`pip install -e propostas`), porque os módulos acham `dados/` e `modelos/` pelo caminho do pacote.
- IDs são UUID v4. Toda tabela nova usa o mixin `ComEmpresa`, com `empresa_id` não nulo. Os repositórios herdam `RepositorioBase` e partem de `self.consulta()`. É proibido `select(`, `text(`, `.query(` ou `sessao.get` em `repositorio.py`, e o teste de arquitetura da T0 falha se aparecerem.
- O serviço recebe `(sessao, ctx: Contexto, ...)` e devolve esquemas `*Saida`, nunca objetos ORM. Entradas herdam `EsquemaEntrada`. Listagens devolvem `Pagina[T]` e recebem `ParametrosLista`.
- Só o comercial grava nas suas tabelas. Para ler o cadastro e a empresa, ele usa `cadastro/servico.py` e as funções do núcleo listadas abaixo. Ele nunca importa `modelos` ou `repositorio` de outro módulo.
- Toda rota usa `Depends(exigir("comercial.<permissão>"))`. As permissões entram em `PERMISSOES` de `app/nucleo/perfis.py` (Tarefa 9). A rota não tem parâmetro de caminho que não seja id de recurso, porque o teste de isolamento da T0 exige 404 em toda rota com parâmetro.
- Erros: as classes da T0 (`NaoEncontrado`, `Conflito`, `EntradaInvalida`, `RegraNegocio`) ou `ErroDominio(codigo, mensagem, status, detalhes)` quando o código é específico do comercial. Os códigos estão em cada tarefa. Mensagens em português.
- Toda escrita grava `registrar_auditoria(sessao, ctx.empresa_id, ctx.usuario_id, acao, entidade, entidade_id)`, com estas ações: `criar`, `alterar`, `remover`, `gerar_proposta`, `gerar_contrato`, `recusar`, `entregar`, `desfazer_entrega`.
- Unidades na API e no banco: `m2`, `m`, `un`, `kW` (regra 5). R$/TR só existe dentro do conjunto privado de parâmetros ABRAVA e da conta do motor `honorario_abrava`. A API não recebe nem devolve TR como grandeza de projeto; ela devolve `tr_estimada` só como passo do memorial do método.
- Regra 7: cada proposta gerada vira revisão com `versao_motor = orcamento.__version__`, `entradas`, `resultado`, `normas` e `emitida_em`. Revisão não se altera.
- Regra 9: os parâmetros do método ABRAVA/DNPC são dados privados por empresa, com fonte, edição e seção/tabela. Nenhum valor oficial entra no repositório. Os testes usam valores marcados `# FICTÍCIO`, e o caso oficial fica como teste pendente (`pytest.mark.skip` com o motivo).
- Os ajustes da empresa ficam fora do método e são rotulados como tal em toda saída (API, tela e PDF): fator do nível do RT, adicional, desconto, custos extras, adicional por planilha, valor final manual e referencial de licitação.
- As observações internas do projeto nunca entram em revisão, exportação ou PDF.
- Toda tarefa que muda rota ou esquema regenera os tipos do front-end com `cd suite/backend && python -m app.exportar_openapi > ../frontend/openapi.json && cd ../frontend && npm run tipos`. Sem isso, `testes/test_openapi.py` da T0 falha.
- Datas: "hoje" vem de `orcamento.parametros.hoje()` (horário de Brasília). Serviços que dependem da data recebem `hoje: date`, e as rotas chamam `hoje()` importado em `comercial/rotas.py`, para que os testes possam fazer monkeypatch.
- Qualidade: `ruff check` e `ruff format --check` (line-length 100), ESLint, um assunto por arquivo, legível por um júnior, o mesmo fluxo para o mesmo tipo de trabalho.

### Permissões do comercial (acrescentadas a `PERMISSOES`)

| Permissão | Perfis | Uso |
|---|---|---|
| `comercial.ler` | admin, engenharia, comercial, financeiro | todos os `GET` (propostas, revisões, contratos, catálogo, tabelas, configuração, modelos, documentos) |
| `comercial.editar_proposta` | admin, comercial | criar e editar projeto e itens, gerar proposta, gerar contrato, recusar, entregar, desfazer |
| `comercial.calcular` | admin, comercial, engenharia | `POST /propostas/{proposta_id}/calculo` |
| `comercial.tabelas` | admin, engenharia | funções, produtividade, parâmetros ABRAVA |
| `comercial.configurar` | admin | configuração comercial (ajustes da empresa, salário mínimo, validade, faixas do painel) |
| `comercial.modelos_documento` | admin, comercial | modelos de documento por seção |
| `comercial.painel` | admin, comercial, financeiro | `GET /painel` |
| `comercial.recibo` | admin, comercial, financeiro | `POST /contratos/{contrato_id}/recibo` |

O perfil `campo` não acessa o comercial.

## Interfaces consumidas da T0 (nomes do plano da T0)

Back-end, em `suite/backend/app/`:

| Interface | Uso na T1 |
|---|---|
| `nucleo/banco.py`: `Base`, mixin `ComEmpresa` (`id: UUID`, `empresa_id: UUID` FK não nula, `criado_em`, `atualizado_em`), `obter_sessao()` | modelos e rotas |
| `nucleo/contexto.py`: `Contexto(usuario_id: UUID, empresa_id: UUID, perfis: frozenset[Perfil])` | todo serviço |
| `nucleo/repositorio.py`: `RepositorioBase[M]` (`modelo`, `__init__(sessao, empresa_id)`, `consulta()`, `obter(id_)`, `obter_ou_erro(id_, mensagem)`, `listar(consulta, limite, deslocamento) -> (itens, total)`, `adicionar(obj)`) | repositórios |
| `nucleo/esquemas.py`: `Pagina[T]`, `EsquemaEntrada`, `ParametrosLista` | esquemas e listagens |
| `nucleo/perfis.py`: `Perfil`, `PERMISSOES`, `exigir(permissao) -> Callable[..., Contexto]` | rotas; a T1 acrescenta as permissões acima |
| `nucleo/erros.py`: `ErroDominio(codigo, mensagem, status, detalhes=None)`, `NaoEncontrado(mensagem)`, `Conflito(mensagem, detalhes=None)`, `EntradaInvalida(mensagem, detalhes=None)`, `RegraNegocio(mensagem)` | serviço |
| `nucleo/auditoria.py`: `registrar_auditoria(sessao, empresa_id, usuario_id, acao, entidade, entidade_id, dados=None)` | escritas |
| `nucleo/configuracao_empresa.py`: `obter_empresa(sessao, ctx) -> EmpresaSaida` (`razao_social`, `cnpj_cpf`, `endereco`, `cidade`, `uf`, `cep`, `telefone`, `email`, `comarca_foro`, `logomarca_arquivo_id`, `responsaveis: list[ResponsavelSaida(id, nome, titulo, conselho, registro, assinatura_arquivo_id)]`) | PDFs e RT da proposta |
| `nucleo/arquivos.py`: `obter_arquivo(sessao, empresa_id, arquivo_id)` (confere a empresa); `obter_armazenamento().ler(f"{empresa_id}/{arquivo_id}")` (convenção de chave da T0) | logo e assinatura nos PDFs |
| `modulos/cadastro/servico.py`: `obter_cliente(sessao, ctx, cliente_id) -> ClienteSaida` (`nome`, `tipo_pessoa`, `cnpj_cpf`, `representante_nome`, `representante_cpf`, `email`, `telefone`); `obter_obra(sessao, ctx, obra_id) -> ObraSaida` (`cliente_id`, `nome`, `endereco`, `cidade`, `uf`, `cep`); ambos lançam `NaoEncontrado` para outra empresa | projeto e contrato |
| `app/main.py` `criar_app()`; `app/registro.py` `importar_modelos()` | a T1 inclui o roteador e os modelos |
| `app/exportar_openapi.py`, `testes/test_openapi.py` | tipos do front-end |
| Testes: `conftest.py` (`sessao`, `cliente_http`, `armazenamento`); `fabricas.py` (`nova_empresa`, `novo_usuario`, `entrar`, `SENHA_TESTE`); `isolamento/mundo.py` (`Mundo.ids_a`, `corpos`, `Caso`); `isolamento/test_isolamento.py` (`CRIACOES_SEM_REFERENCIA`); `isolamento/test_perfis_rotas.py` (cobre toda rota com `exigir`) | a T1 acrescenta ids, corpos e criações |
| `pyproject.toml` do back-end; `infra/backend.Dockerfile`; `.github/workflows/suite.yml` (job `backend`: `pip install -e ".[dev]"`) | Tarefas 1 e 17 |

Front-end, em `suite/frontend/src/`:

| Interface | Uso |
|---|---|
| `api/cliente.ts`: `api<T>(metodo, caminho, corpo?)`, `ErroApi {status, codigo, mensagem, detalhes}`, `camposDoErro(e)` | cliente do comercial; a T1 acrescenta `baixar` |
| `api/esquema.ts` (gerado) e `api/tipos.ts` (apelidos dos esquemas) | tipos |
| `sessao/ContextoSessao.tsx`: `useSessao().pode(permissao)` | botões por permissão |
| `App.tsx` (rotas), `componentes/Menu.tsx`, `componentes/CampoTexto.tsx`, `componentes/TabelaErros.tsx`, `util/numeros.ts` (`lerDecimal`) | telas |
| `e2e/cadastro.spec.ts` (`entrar`, `sair`); usuários de demonstração `<perfil>@demo-a.local` com `SUITE_SEMENTE_SENHA` | ponta a ponta |

## Caso de referência (obra), conferido à mão

Este caso é usado pelos testes das Tarefas 2, 3, 4, 12, 13, 14 e 27. Usa horas por dia = 8 e eficiência = 0,8.

Fatores padrão de execução (`FATORES_PADRAO`, valores iniciais da empresa, a confirmar pela engenharia):

| Fator | Opções → multiplicador |
|---|---|
| altura | `ate_3m` 1,00 · `de_3_a_6m` 1,15 · `acima_6m` 1,30 |
| acesso | `livre` 1,00 · `restrito` 1,15 · `confinado` 1,30 |
| ocupacao | `desocupado` 1,00 · `ocupado` 1,20 |
| turno | `diurno` 1,00 · `noturno` 1,25 |

Funções (custo-hora com encargos = salário-hora × (1 + encargos)): `encarregado` 40,00 × 1,8 = **72,00**; `mecanico_refrigeracao` 30,00 × 1,8 = **54,00**; `ajudante` 15,00 × 1,8 = **27,00**.

Produtividade (hh por unidade; fonte "caso de referência T1"):

| item (unidade) | encarregado | mecânico | ajudante |
|---|---|---|---|
| `duto_m2` (m2) | 0,05 | 0,40 | 0,40 |
| `linha_frigorifica_m` (m) | 0,02 | 0,30 | 0,30 |
| `evaporadora_un` (un) | 0,50 | 4,00 | 4,00 |

Itens:

| # | frente | item | qtd | altura | acesso | ocupação | turno | fator | material R$/un (categoria) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Térreo | duto_m2 | 100 | de_3_a_6m | livre | ocupado | diurno | 1,15 × 1,20 = 1,38 | 120,00 (material) |
| 2 | Térreo | linha_frigorifica_m | 50 | ate_3m | livre | ocupado | noturno | 1,20 × 1,25 = 1,50 | 85,00 (material) |
| 3 | Cobertura | evaporadora_un | 4 | ate_3m | restrito | desocupado | diurno | 1,15 | 3 500,00 (equipamento) |

HH = quantidade × hh/unidade × fator × calibração (calibração = 1):

| | encarregado | mecânico | ajudante |
|---|---|---|---|
| item 1 | 100 × 0,05 × 1,38 = 6,90 | 100 × 0,40 × 1,38 = 55,20 | 55,20 |
| item 2 | 50 × 0,02 × 1,50 = 1,50 | 50 × 0,30 × 1,50 = 22,50 | 22,50 |
| item 3 | 4 × 0,50 × 1,15 = 2,30 | 4 × 4,00 × 1,15 = 18,40 | 18,40 |
| **total** | **10,70** | **96,10** | **96,10** (soma 202,90) |
| frente Térreo | 8,40 | 77,70 | 77,70 |
| frente Cobertura | 2,30 | 18,40 | 18,40 |

- **Modo prazo** (prazo-alvo 10 dias úteis). Capacidade por pessoa = 8 × 10 × 0,8 = 64 h. Pessoas: encarregado ⌈10,7/64⌉ = 1; mecânico ⌈96,1/64 = 1,50⌉ = 2; ajudante = 2.
- **Cronograma com equipe (1, 2, 2)**. As frentes correm em sequência, e cada frente leva o maior valor, entre as funções, de ⌈HH ÷ (8 × pessoas × 0,8)⌉.
  - Térreo: encarregado ⌈8,4/6,4⌉ = 2; mecânico ⌈77,7/12,8 = 6,07⌉ = 7. A frente leva **7 dias** (dias 1–7).
  - Cobertura: encarregado ⌈2,3/6,4⌉ = 1; mecânico ⌈18,4/12,8 = 1,44⌉ = 2. A frente leva **2 dias** (dias 8–9).
  - Prazo = **9 dias úteis**, sem aviso (9 ≤ 10). Dias corridos = ⌈9 × 7/5⌉ = **13**.
- **Modo equipe fixa** (1, 3, 3): Térreo ⌈77,7/19,2 = 4,05⌉ = 5; Cobertura ⌈18,4/19,2⌉ = 1. Prazo = **6 dias úteis**.
- **Preço** (BDI de `dados/parametros.json`: `mo_execucao` 0,22, `material` e `equipamento` 0,14):
  - MO = 10,7 × 72 + 96,1 × 54 + 96,1 × 27 = **8 554,50**, que × 1,22 dá **10 436,49**.
  - Materiais e equipamentos = 12 000 + 4 250 + 14 000 = **30 250,00**, que × 1,14 dá **34 485,00**.
  - A proposta tem a opção A com a fase F1 de escopo fechado, sem serviços de engenharia. Preço = **44 921,49**. O motor dá a etapa `obra` com 9 dias úteis e 13 corridos e o pagamento padrão 30% + 70%, ou seja, **13 476,45 + 31 445,04**. Isso foi conferido rodando `motor.precificar`.

## Caso do método ABRAVA/DNPC com valores FICTÍCIOS (conferido à mão)

As tabelas oficiais (Rev. 01/2014) ainda não estão disponíveis. Todos os números abaixo são inventados para teste e ficam marcados `# FICTÍCIO`.

Parâmetros FICTÍCIOS:
- Tipos de ambiente (peso): `escritorio` 1,0; `auditorio` 1,2; `cpd` 1,5. Fator de repetição 0,5. Pesos de ventilação: `exaustao` 0,3; `cozinha` 0,8.
- Densidade de carga 0,05 TR/m². FS (fator de margem de seleção) 1,1.
- Custo por TR (região "RJ"): `expansao_direta` 4 000; `vrf` 6 000; `agua_gelada` 8 000.
- Curva de percentual por custo base: (0; 8%), (100 000; 6%), (500 000; 4%), com interpolação linear e valor da ponta fora da faixa.
- Fator de escopo: `planilha_orcamento` 0,4; `nova_em_existente` 1,1; `nova_em_novo` 1,0; `retrofit` 1,2. Sem outros fatores do método.
- Piso de 3 salários mínimos. O salário mínimo FICTÍCIO é 1 500, o que dá piso de 4 500.

Fórmulas, isoladas em `honorario_abrava.py`. A forma exata é conferida quando o PDF chegar:
- área corrigida = Σ climatizados [área × peso do tipo × (1 + (repetições − 1) × fator de repetição)] + Σ ventilados [área × peso da ventilação]
- TR estimada = área corrigida × densidade × FS
- custo base = TR × custo por TR do tipo de instalação
- P = curva(custo base)
- honorário do método = máx(custo base × P × fator de escopo × Π outros fatores, piso)

Caso 1: VRF, instalação nova em edifício novo. Auditório 160 m² (1×), CPD 48 m² (2×), banheiro 32 m² com exaustão.
- Área corrigida = 160 × 1,2 + 48 × 1,5 × (1 + 1 × 0,5) + 32 × 0,3 = 192 + 108 + 9,6 = **309,6 m²**.
- TR = 309,6 × 0,05 × 1,1 = **17,028**. Custo base = 17,028 × 6 000 = **102 168,00**.
- P = 0,06 + (2 168/400 000) × (−0,02) = **0,0598916**.
- Honorário do método = 102 168 × 0,0598916 × 1,0 = **6 119,00** (6 119,0049888).

Caso 2: o mesmo, com água gelada e retrofit. Custo base = **136 224,00**; P = **0,0581888**; honorário = 136 224 × 0,0581888 × 1,2 = **9 512,05**.

Caso 3 (piso): escritório de 20 m², expansão direta, nova em edifício novo. Custo base = 20 × 0,05 × 1,1 × 4 000 = **4 400,00**; P = 0,07912; bruto = **348,13**. O piso de **4 500,00** vale, com aviso.

Ajustes da empresa sobre o caso 1. Os fatores de nível (júnior 0,70, pleno 1,00, sênior 1,40, expert 1,80), o adicional por planilha de 10% e o fator de licitação 0,85 são padrões da empresa vindos dos requisitos, não da ABRAVA. Nível sênior, inclui planilha, adicional de 5%, desconto de 3% e custos extras de 800 (deslocamento) + 450 (hospedagem):

| Passo | Conta | Subtotal |
|---|---|---|
| honorário do método | — | 6 119,00 |
| nível do RT (sênior) | × 1,40 | 8 566,61 |
| planilha quantitativa e orçamento | × 1,10 | 9 423,27 |
| adicional | × 1,05 | 9 894,43 |
| desconto | × 0,97 | 9 597,60 |
| custos extras | + 1 250,00 | **10 847,60** = calculado |
| referencial de licitação | calculado × 0,85 | **9 220,46** |
| valor final manual = 9 000,00 | diferença | **−1 847,60** |

## Preços de referência dos exemplos (motor atual, conferidos com `python -m orcamento.cli`)

| arquivo | opção → preço |
|---|---|
| `hvac_consultoria_2d_3d_bim.json` | A 55 672,13 · B 96 243,17 · C 140 048,50 |
| `hvac_retrofit_fases.json` | A 138 637,75 · B 125 937,62 · E 1 163 417,61 (estimativa interna) |
| `nr13_inspecao.json` | A 29 069,38 |
| `spci_projeto.json` | A 21 622,49 · B 32 069,63 |

## Foco de revisão

1. **Arredondamento de pessoas e dias com ponto flutuante.** Quando HH ÷ capacidade dá inteiro (64 h para capacidade de 64 h), o resultado é 1 pessoa, não 2. Regra: `math.ceil(round(x, 9))`. O teste fica na Tarefa 3.
2. **Equipe fixa sem uma função que tem HH, ou item sem produtividade na empresa** (mas com produtividade em outra empresa). O sistema responde 422 `equipe_incompleta` ou `item_sem_produtividade`, com o nome em `detalhes`. Não pode haver divisão por zero nem uso da tabela alheia. Os testes ficam nas Tarefas 3 e 12.
3. **Ajuste manual e licitação.** O valor final manual não altera o "calculado" nem o referencial de licitação. Apagar o valor manual volta ao calculado, e os documentos usam sempre o final. Um desconto de 100% ou mais, ou um valor manual ≤ 0, responde 422. O teste fica na Tarefa 7.
4. **Revisão antiga, proposta vencida e dados mudados depois da geração.** Gerar contrato a partir de uma revisão que não é a última responde 409 `revisao_desatualizada`. Gerar contrato de proposta vencida responde 409 `proposta_vencida`. Mudar produtividade, parâmetros ABRAVA ou catálogo depois da geração não muda a revisão nem os seus documentos. Os testes ficam nas Tarefas 13, 14 e 15.
5. **JSON antigo do app Streamlit** (sem `fases`, com `modelo_preco`). Importado pela API, ele dá o mesmo preço da CLI. Serviço inexistente no catálogo responde 422 `documento_invalido`, sem erro 500. Os testes ficam nas Tarefas 11 e 12.

---

### Tarefa 1: pacote `orcamento` instalável

**Arquivos:**
- Criar: `propostas/pyproject.toml`
- Modificar: `propostas/orcamento/__init__.py` (`__version__`), `propostas/README.md` (seção "Como pacote")
- Modificar: `suite/backend/pyproject.toml` (dependência `kaptek-orcamento>=1.0`), `suite/infra/backend.Dockerfile` e `suite/infra/docker-compose.yml` (contexto de build na raiz do repositório, `COPY propostas /src/propostas`, `pip install -e /src/propostas` antes de `pip install .`), `.github/workflows/suite.yml` (job `backend`: `pip install -e ../../propostas` antes de `pip install -e ".[dev]"`)
- Teste: `propostas/testes/test_pacote.py`

**Interfaces:**
- Produz: `orcamento.__version__ = "1.0.0"`; a distribuição `kaptek-orcamento` com o pacote `orcamento`, sem `app/` nem `testes/`.

- [ ] **Passo 1: escrever os testes que falham**

```python
# propostas/testes/test_pacote.py
import subprocess, venv
import orcamento
from conftest import RAIZ

def test_versao_do_motor():
    assert orcamento.__version__ == "1.0.0"

def test_instalacao_editavel_funciona_fora_da_pasta(tmp_path):
    destino = tmp_path / "venv"
    venv.EnvBuilder(system_site_packages=True, with_pip=True).create(destino)
    py = str(destino / "bin" / "python")
    subprocess.run([py, "-m", "pip", "install", "-q", "--no-deps", "--no-build-isolation", "-e", RAIZ], check=True)
    codigo = ("import os, orcamento, orcamento.catalogo as c, orcamento.exportar_docx as d;"
              "assert os.path.exists(c.CAMINHO_PADRAO) and os.path.exists(d.TEMPLATE);"
              "print(orcamento.__version__)")
    saida = subprocess.run([py, "-c", codigo], cwd=tmp_path, capture_output=True, text=True, check=True)
    assert saida.stdout.strip() == "1.0.0"
```

- [ ] **Passo 2: rodar e ver falhar.** Rode `cd propostas && python3 -m pytest -q testes/test_pacote.py`. Resultado esperado: FAIL com `AttributeError: ... '__version__'`.
- [ ] **Passo 3: criar `pyproject.toml` e `__version__`.** Use setuptools `>=68` com estes valores:
  - `name = "kaptek-orcamento"`, `requires-python = ">=3.12"`
  - `dynamic = ["version"]` com `[tool.setuptools.dynamic] version = {attr = "orcamento.__version__"}`
  - `[tool.setuptools] packages = ["orcamento"]`
  - `dependencies = ["openpyxl>=3.1,<4", "python-docx>=1.1,<2"]`
  - extra `referencias = ["pdfplumber>=0.11,<0.12"]`

  Não altere `requirements.txt` nem `app/requirements.txt`, porque `test_requisitos_da_nuvem_acompanham_os_locais` compara os dois. O README explica que a instalação é só editável.
- [ ] **Passo 4: rodar e ver passar.**
  - `cd propostas && python3 -m pytest -q testes`: resultado esperado `157 passed`.
  - `docker compose -f suite/infra/docker-compose.yml build api`: termina sem erro.
- [ ] **Passo 5: commit.** Mensagem: `build(orcamento): instalável como pacote kaptek-orcamento (modo editável)`.

### Tarefa 2: HH de execução (`orcamento/execucao.py`)

**Arquivos:**
- Criar: `propostas/orcamento/erros.py`, `propostas/orcamento/execucao.py`
- Teste: `propostas/testes/test_execucao.py`

**Interfaces:**
- Produz (`erros.py`): `class ErroEntrada(ValueError)` com `__init__(self, codigo: str, mensagem: str, detalhes: dict | None = None)` e os atributos `codigo`, `mensagem`, `detalhes`.
- Produz (`execucao.py`):
  - `FUNCOES_PADRAO = {"encarregado": "Encarregado", "mecanico_refrigeracao": "Mecânico de refrigeração", "ajudante": "Ajudante", "soldador": "Soldador", "eletricista": "Eletricista", "tecnico_tab": "Técnico de TAB"}`
  - `UNIDADES_ITEM = ("m2", "m", "un", "kW")`
  - `ITENS_SUGERIDOS = {"duto_m2": "m2", "linha_frigorifica_m": "m", "evaporadora_un": "un", "condensadora_un": "un", "capacidade_kw": "kW", "ponto_eletrico_un": "un", "difusor_un": "un"}`
  - `FATORES_PADRAO`: a tabela do caso de referência, com as chaves `altura`, `acesso`, `ocupacao`, `turno`.
  - `config_padrao(fase: str = "F1") -> dict` devolve `{"fase": fase, "modo": "prazo", "prazo_alvo_dias": 20, "equipe": {}, "horas_dia": 8.0, "eficiencia": 0.8, "fatores": deepcopy(FATORES_PADRAO)}`.
  - Item (dict): `{"id": str, "frente": str, "item": str, "unidade": str, "descricao": str, "quantidade": float, "altura": str, "acesso": str, "ocupacao": str, "turno": str, "custo_material_unit": float, "categoria_material": "material"|"equipamento"}`.
  - Produtividade (dict): `{"item": str, "funcao": str, "hh_por_unidade": float, "fator_calibracao": float, "fonte": str}`.
  - `fator_item(fatores: dict, item: dict) -> tuple[float, dict[str, float]]`.
  - `hh_execucao(itens, produtividade, fatores) -> dict`. Devolve `{"linhas": [{"item_id", "frente", "item", "funcao", "quantidade", "hh_por_unidade", "fator", "fator_calibracao", "hh_base", "hh"}], "hh_funcao", "hh_funcao_base", "hh_frente_funcao": {frente: {funcao: hh}}, "frentes": [na ordem da primeira aparição], "total_hh"}`. Fórmulas: `hh_base = quantidade × hh_por_unidade × Π fatores`, `hh = hh_base × fator_calibracao`.
  - Erros (`ErroEntrada`): `item_sem_produtividade` (detalhes `{"item"}`), `quantidade_negativa` (`{"item_id"}`), `fator_desconhecido` (`{"fator", "valor"}`).

- [ ] **Passo 1: escrever os testes que falham.** No topo do arquivo, as constantes `PRODUTIVIDADE_REF` e `ITENS_REF` do caso de referência.

```python
def test_fator_item_multiplica_os_quatro_fatores():
    fator, det = ex.fator_item(ex.FATORES_PADRAO, ITENS_REF[0])
    assert fator == pytest.approx(1.38)
    assert det == {"altura": 1.15, "acesso": 1.0, "ocupacao": 1.2, "turno": 1.0}

def test_hh_do_caso_de_referencia():
    r = ex.hh_execucao(ITENS_REF, PRODUTIVIDADE_REF, ex.FATORES_PADRAO)
    assert r["hh_funcao"] == pytest.approx({"encarregado": 10.7, "mecanico_refrigeracao": 96.1, "ajudante": 96.1})
    assert r["total_hh"] == pytest.approx(202.9) and r["frentes"] == ["Térreo", "Cobertura"]
    assert r["hh_frente_funcao"]["Térreo"] == pytest.approx({"encarregado": 8.4, "mecanico_refrigeracao": 77.7, "ajudante": 77.7})
    assert len(r["linhas"]) == 9

def test_calibracao_multiplica_hh_mas_nao_o_base():
    prod = [{**p, "fator_calibracao": 1.1} if p["funcao"] == "ajudante" else p for p in PRODUTIVIDADE_REF]
    r = ex.hh_execucao(ITENS_REF, prod, ex.FATORES_PADRAO)
    assert (r["hh_funcao"]["ajudante"], r["hh_funcao_base"]["ajudante"]) == pytest.approx((105.71, 96.1))

@pytest.mark.parametrize("alteracao, codigo", [({"item": "inexistente"}, "item_sem_produtividade"),
                                               ({"quantidade": -1}, "quantidade_negativa"),
                                               ({"altura": "no_teto"}, "fator_desconhecido")])
def test_entradas_invalidas(alteracao, codigo):
    with pytest.raises(ErroEntrada) as e:
        ex.hh_execucao([{**ITENS_REF[0], **alteracao}], PRODUTIVIDADE_REF, ex.FATORES_PADRAO)
    assert e.value.codigo == codigo
```

- [ ] **Passo 2: rodar e ver falhar.** Rode `cd propostas && python3 -m pytest -q testes/test_execucao.py`. Resultado esperado: FAIL com `ModuleNotFoundError`.
- [ ] **Passo 3: implementar `erros.py` e `execucao.py`.** A docstring traz as fórmulas e aponta o caso de referência.
- [ ] **Passo 4: rodar e ver passar.** Depois rode `python3 -m pytest -q testes`.
- [ ] **Passo 5: commit.** Mensagem: `feat(orcamento): HH de execução por função com fatores e calibração`.

### Tarefa 3: equipe, prazo e cronograma por frentes

**Arquivos:**
- Modificar: `propostas/orcamento/execucao.py`
- Teste: `propostas/testes/test_execucao.py`

**Interfaces:**
- Consome: `hh_execucao`.
- Produz:
  - `dimensionar_equipe(hh_funcao: dict[str, float], horas_dia: float, prazo_dias: int, eficiencia: float) -> dict[str, int]`: `n = ceil(round(HH ÷ (horas_dia × prazo_dias × eficiencia), 9))` quando HH > 0, e 0 quando HH = 0.
  - `cronograma_frentes(hh_frente_funcao, frentes, equipe, horas_dia, eficiencia) -> list[dict]`. Cada elemento é `{"frente", "dias_uteis", "inicio", "fim", "dias_funcao"}`. Os dias de cada função são `ceil(round(HH ÷ (horas_dia × pessoas × eficiencia), 9))`, e a frente leva o máximo. As frentes correm em sequência a partir do dia 1. Uma função com HH > 0 e 0 pessoas lança `ErroEntrada("equipe_incompleta", ..., {"funcao": f})`.
  - `planejar_execucao(itens, produtividade, config) -> dict`: devolve o resultado de `hh_execucao` mais `{"modo", "equipe", "cronograma", "prazo_dias_uteis", "prazo_dias_corridos", "avisos"}`.
    - Modo `"prazo"`: equipe por `dimensionar_equipe` com `prazo_alvo_dias`. Modo `"equipe"`: `config["equipe"]`.
    - Dias corridos = `ceil(dias_uteis × 7 / 5)`.
    - No modo prazo, se o prazo calculado passar do alvo, entra o aviso `f"O cronograma por frentes dá {n} dias úteis, acima do prazo-alvo de {alvo}, pelo arredondamento de cada frente."`.
    - Valida `horas_dia > 0`, `0 < eficiencia <= 1`, `prazo_alvo_dias >= 1` e equipe inteira `>= 0`. Fora disso, `ErroEntrada("parametro_invalido", ..., {"campo": nome})`.
    - Sem itens: HH 0, equipe `{}`, cronograma `[]`, prazo 0.

- [ ] **Passo 1: escrever os testes que falham**

```python
def test_equipe_no_modo_prazo_do_caso_de_referencia():
    p = ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, {**ex.config_padrao(), "prazo_alvo_dias": 10})
    assert p["equipe"] == {"encarregado": 1, "mecanico_refrigeracao": 2, "ajudante": 2}
    assert [(c["frente"], c["dias_uteis"], c["inicio"], c["fim"]) for c in p["cronograma"]] == [("Térreo", 7, 1, 7), ("Cobertura", 2, 8, 9)]
    assert (p["prazo_dias_uteis"], p["prazo_dias_corridos"], p["avisos"]) == (9, 13, [])

def test_prazo_ao_contrario_com_equipe_fixa():
    cfg = {**ex.config_padrao(), "modo": "equipe", "equipe": {"encarregado": 1, "mecanico_refrigeracao": 3, "ajudante": 3}}
    p = ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, cfg)
    assert [c["dias_uteis"] for c in p["cronograma"]] == [5, 1] and p["prazo_dias_uteis"] == 6

def test_divisao_exata_nao_soma_uma_pessoa():
    assert ex.dimensionar_equipe({"ajudante": 64.0, "soldador": 0.0}, 8, 10, 0.8) == {"ajudante": 1, "soldador": 0}

def test_equipe_fixa_sem_funcao_com_hh():
    cfg = {**ex.config_padrao(), "modo": "equipe", "equipe": {"encarregado": 1, "mecanico_refrigeracao": 3}}
    with pytest.raises(ErroEntrada) as e:
        ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, cfg)
    assert (e.value.codigo, e.value.detalhes) == ("equipe_incompleta", {"funcao": "ajudante"})

def test_aviso_quando_arredondamento_por_frente_passa_do_alvo():
    # alvo 8: capacidade 51,2 h → equipe (1, 2, 2) → prazo 9 > 8
    p = ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, {**ex.config_padrao(), "prazo_alvo_dias": 8})
    assert p["prazo_dias_uteis"] == 9 and "acima do prazo-alvo de 8" in p["avisos"][0]

@pytest.mark.parametrize("campo, valor", [("eficiencia", 0), ("eficiencia", 1.2), ("horas_dia", 0), ("prazo_alvo_dias", 0)])
def test_parametros_invalidos(campo, valor):
    with pytest.raises(ErroEntrada) as e:
        ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, {**ex.config_padrao(), campo: valor})
    assert (e.value.codigo, e.value.detalhes) == ("parametro_invalido", {"campo": campo})
```

- [ ] **Passo 2: rodar e ver falhar.** Resultado esperado: FAIL com `AttributeError: ... planejar_execucao`.
- [ ] **Passo 3: implementar as três funções.**
- [ ] **Passo 4: rodar e ver passar.** Depois rode `python3 -m pytest -q testes`.
- [ ] **Passo 5: commit.** Mensagem: `feat(orcamento): equipe, prazo e cronograma por frentes`.

### Tarefa 4: preço de obra no mesmo motor

**Arquivos:**
- Modificar: `propostas/orcamento/execucao.py`
- Teste: `propostas/testes/test_execucao.py`

**Interfaces:**
- Consome: `planejar_execucao`; `proposta.novo_fornecimento`; `motor.precificar`.
- Produz:
  - `fornecimentos_execucao(plano, itens, funcoes: dict[str, dict], fase: str) -> list[dict]`, com `funcoes` na forma `{codigo: {"nome", "custo_hora"}}`.
    - Para cada função com HH > 0, um fornecimento `novo_fornecimento(descricao=f"Mão de obra de execução — {nome}", categoria="mo_execucao", unid="h", qtd=HH, custo_unit=custo_hora, fonte="HH de execução", fase=fase)`.
    - Para cada item com `custo_material_unit > 0`, um fornecimento `novo_fornecimento(descricao=item["descricao"] or item["item"], categoria=item["categoria_material"], unid=item["unidade"], qtd=quantidade, custo_unit=custo_material_unit, fonte="item de execução", fase=fase)`.
    - Função com HH > 0 ausente de `funcoes` ou com `custo_hora <= 0` lança `ErroEntrada("funcao_sem_custo", ..., {"funcao": f})`.
  - `precificar_com_execucao(cat, proposta, itens_por_opcao: dict[str, list[dict]], produtividade, funcoes) -> dict`. Devolve `{"proposta", "orcamento", "execucao": {opcao_id: plano}}`.
    - Trabalha numa cópia profunda da proposta.
    - Para cada opção com itens, usa `opcao.get("execucao") or config_padrao(primeira fase)`, planeja, acrescenta os fornecimentos, define `opcao["prazo_execucao_dias"] = plano["prazo_dias_uteis"]` e chama `motor.precificar`.
    - Fase de execução inexistente: `ErroEntrada("fase_inexistente", ..., {"opcao", "fase"})`.
    - Em `orcamento["avisos"]`, tira só estes dois textos do motor, e só nas opções e fases com execução: `f"{nome_opcao}: nenhum serviço com horas — adicione serviços na aba Escopo."` e `f"{nome_opcao} / {nome_fase}: fase sem serviços."`. Os avisos do plano entram com o prefixo `f"{nome_opcao}: "`.

- [ ] **Passo 1: escrever os testes que falham**

```python
FUNCOES_REF = {"encarregado": {"nome": "Encarregado", "custo_hora": 72.0},
               "mecanico_refrigeracao": {"nome": "Mecânico de refrigeração", "custo_hora": 54.0},
               "ajudante": {"nome": "Ajudante", "custo_hora": 27.0}}

def _proposta_obra(cat, params):
    p = pp.completar(pp.padrao(params), cat, params)
    p["opcoes"][0]["execucao"] = {**ex.config_padrao("F1"), "prazo_alvo_dias": 10}
    return p

def test_preco_de_obra_do_caso_de_referencia(cat, params):
    p = _proposta_obra(cat, params)
    r = ex.precificar_com_execucao(cat, p, {"A": ITENS_REF}, PRODUTIVIDADE_REF, FUNCOES_REF)
    o = r["orcamento"]["opcoes"][0]
    mo = [f for f in o["fornecimentos"] if f["categoria"] == "mo_execucao"]
    assert (sum(f["custo"] for f in mo), sum(f["preco"] for f in mo)) == pytest.approx((8554.50, 10436.49))
    assert o["preco"] == pytest.approx(44921.49) and (o["prazo_dias_uteis"], o["prazo_dias_corridos"]) == (9, 13)
    assert r["orcamento"]["avisos"] == [] and p["opcoes"][0]["fornecimentos"] == []   # original intacta

def test_sem_itens_da_o_mesmo_preco_do_motor(cat, params):
    for caminho in EXEMPLOS:
        p = abrir_exemplo(caminho, cat, params)
        esperado = [o["preco"] for o in motor.precificar(cat, p)["opcoes"]]
        assert [o["preco"] for o in ex.precificar_com_execucao(cat, p, {}, [], {})["orcamento"]["opcoes"]] == pytest.approx(esperado)

def test_funcao_sem_custo_hora(cat, params):   # custo_hora do ajudante = 0
    with pytest.raises(ErroEntrada) as e:
        ex.precificar_com_execucao(cat, _proposta_obra(cat, params), {"A": ITENS_REF}, PRODUTIVIDADE_REF,
                                   {**FUNCOES_REF, "ajudante": {"nome": "Ajudante", "custo_hora": 0.0}})
    assert e.value.codigo == "funcao_sem_custo"
```

- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.** Depois rode `python3 -m pytest -q testes`.
- [ ] **Passo 5: commit.** Mensagem: `feat(orcamento): preço de obra (HH × custo-hora + materiais + BDI) no motor`.

### Tarefa 5: cobrança "valor definido" no motor de preço

O honorário ABRAVA ajustado precisa ser o preço de uma fase no mesmo motor, com XLSX e DOCX coerentes. Esta tarefa acrescenta uma cobrança. Ela não muda as quatro cobranças existentes.

**Arquivos:**
- Modificar: `propostas/orcamento/proposta.py` (`COBRANCAS` acrescenta `"valor"`; `nova_fase` acrescenta `"valor_definido": {"valor": 0.0, "origem": "", "prazo_dias": 0}`), `propostas/orcamento/motor.py`, `propostas/orcamento/exportar_xlsx.py`, `propostas/orcamento/exportar_docx.py`, `propostas/app/app.py` (dicionário `COBRANCAS` acrescenta `"valor": "Valor definido"`)
- Teste: `propostas/testes/test_valor_definido.py`

**Interfaces:**
- Produz:
  - `motor.ROTULO_COBRANCA["valor"] = "valor definido"`.
  - Em `precificar_fase`, para `cob == "valor"`: `honorarios = valor_definido.valor`; `preco = preco_fixo = honorarios + preco_fornec`; `preco_estimado = 0`. O custo e o preço dos serviços (`preco_servicos`) continuam calculados pelas horas, para a comparação. O pagamento usa `fase["pagamento"]` ou `pagamento_padrao`. Com `prazo_dias > 0`, o cronograma da fase é uma etapa única `{"etapa": "projeto", "rotulo": f"{nome da fase} — prazo definido", "marco": "Entrega do projeto", "campo": False, "horas": total_h, "dias_uteis": prazo_dias, "dias_corridos": ceil(prazo_dias × 7/5)}`. Sem prazo, o cronograma é o normal pelas horas.
  - Nos avisos, a condição de "nenhum serviço com horas" passa a ignorar opções com fase `pacote` ou `valor`.
  - XLSX: na aba da opção, nova linha de entrada `("vd", "Valor definido (honorário adotado)", MOEDA, True, "Entrada")`, preenchida com `valor_definido.valor`. Nas fórmulas `honorarios` e `p_fixo`, novo ramo `IF(cob="valor", vd [+ preco_forn no p_fixo], ...)`. O texto da linha `cob` passa a `"Cobrança (fechado | hora | percentual | pacote | valor)"`.
  - DOCX: `valor` usa as mesmas linhas de `fechado` em `_linhas_fase`, e o rótulo vem de `ROTULO_COBRANCA`.

- [ ] **Passo 1: escrever os testes que falham.** A fixture monta a proposta padrão com F1 `valor` (valor 10 000, prazo 30 dias), o serviço `hvac.projeto` em F1, um fornecimento `material` de 1 000 na F1 e uma F2 `fechado` com `hvac.tab`.

```python
def test_preco_da_fase_e_o_valor_definido(cat, params, proposta_valor):
    r = motor.precificar(cat, proposta_valor)["opcoes"][0]
    f1 = r["fases"][0]
    assert f1["preco"] == pytest.approx(10_000 + 1_000 * 1.14) and f1["preco_estimado"] == 0
    assert f1["preco_servicos"] > 0                       # HH continua calculado para comparar
    assert [(e["dias_uteis"], e["dias_corridos"]) for e in f1["cronograma"]] == [(30, 42)]
    assert sum(m["pct"] for m in f1["pagamento"]) == pytest.approx(1.0)

def test_fases_existentes_nao_mudam(cat, params):   # os 4 exemplos dão os mesmos preços da tabela de referência
    ...

@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice não instalado")
def test_xlsx_recalculado_com_valor_definido(cat, params, proposta_valor, tmp_path):
    ...   # mesmo roteiro de test_xlsx_recalculado_com_todas_as_cobrancas: sem erros de fórmula e
          # "PREÇO DA FASE", "Preço — parcela fixa", "Custo da fase" de F1 e F2 iguais ao motor (abs=0,01)

def test_docx_com_valor_definido(cat, params, proposta_valor):
    ...   # exportar_docx.gerar não levanta exceção e o texto tem "R$ 11.140,00"
```

- [ ] **Passo 2: rodar e ver falhar.** Rode `cd propostas && python3 -m pytest -q testes/test_valor_definido.py`.
- [ ] **Passo 3: implementar nos quatro arquivos.**
- [ ] **Passo 4: rodar e ver passar.** Rode `python3 -m pytest -q testes`. Todos passam, inclusive os testes com LibreOffice, que está instalado neste ambiente.
- [ ] **Passo 5: commit.** Mensagem: `feat(orcamento): cobrança por valor definido (motor, XLSX, DOCX)`.

### Tarefa 6: honorário de projeto pelo método ABRAVA/DNPC (`orcamento/honorario_abrava.py`)

**Arquivos:**
- Criar: `propostas/orcamento/honorario_abrava.py`
- Teste: `propostas/testes/test_honorario_abrava.py`

**Interfaces:**
- Consome: `ErroEntrada`.
- Produz:
  - `TIPOS_INSTALACAO = ("expansao_direta", "vrf", "agua_gelada")`
  - `ESCOPOS = ("planilha_orcamento", "nova_em_existente", "nova_em_novo", "retrofit")`
  - `TIPOS_VENTILACAO = ("insuflacao_exaustao", "exaustao", "insuflacao", "cozinha", "estacionamento")`
  - Parâmetros (privados por empresa): `{"tipos_ambiente": {codigo: {"rotulo", "edificacao", "peso"}}, "fator_repeticao", "peso_ventilacao": {tipo: float}, "densidade_tr_m2", "fs", "regiao", "custo_tr": {tipo_instalacao: R$/TR}, "curva_percentual": [{"custo_base", "pct"}], "fator_escopo": {escopo: float}, "fatores_metodo": {nome: float}, "piso_salarios_minimos": float | None, "fonte", "edicao", "secao_tabela", "edicao_superada": bool}`
  - Projeto (dict): `{"tipo_instalacao", "escopo", "climatizados": [{"tipo", "area_m2", "repeticoes"}], "ventilados": [{"tipo", "area_m2"}]}`
  - `area_corrigida(parametros, climatizados, ventilados) -> tuple[float, list[dict]]`. O detalhe de cada ambiente é `{"origem": "climatizado"|"ventilado", "tipo", "area_m2", "repeticoes", "peso", "area_corrigida"}`.
  - `percentual_curva(curva, custo_base) -> float`: interpolação linear, ponta fora da faixa.
  - `calcular_abrava(parametros, projeto, salario_minimo: float | None) -> dict`. Devolve `{"area_corrigida", "detalhe_areas", "tr_estimada", "custo_tr", "fs", "custo_base", "pct", "fator_escopo", "fatores_metodo", "honorario_bruto", "piso", "honorario_metodo", "avisos", "fonte", "edicao", "secao_tabela"}`, com as fórmulas da seção "Caso do método ABRAVA".
  - O piso só existe com `piso_salarios_minimos` e `salario_minimo`. Quando ele vale, entra o aviso `"Honorário pelo piso de {n} salários mínimos."`. Com `edicao_superada`, entra o aviso `"Parâmetros ABRAVA/DNPC de edição superada ({edicao}): confira a tabela vigente."`.
  - Erros (`ErroEntrada`): `sem_ambientes` (nenhum climatizado), `ambiente_desconhecido` (`{"tipo"}`), `ventilacao_desconhecida` (`{"tipo"}`), `area_invalida` (área ≤ 0), `repeticoes_invalida` (< 1 ou não inteiro), `parametro_abrava_ausente` (`{"campo", "valor"}`: tipo de instalação ou escopo sem valor), `curva_vazia`.
  - `comparar_com_hh(preco_hh: float, honorario_final: float) -> dict`. Devolve `{"preco_hh", "honorario_final", "diferenca": final − hh, "razao": final ÷ hh ou None}`.

- [ ] **Passo 1: escrever os testes que falham.** No topo, `PARAMS_FICTICIOS` com os valores da seção "Caso do método ABRAVA" (comentário `# FICTÍCIO`).

```python
AUDITORIO_CPD_BANHEIRO = {"climatizados": [{"tipo": "auditorio", "area_m2": 160, "repeticoes": 1},
                                           {"tipo": "cpd", "area_m2": 48, "repeticoes": 2}],
                          "ventilados": [{"tipo": "exaustao", "area_m2": 32}]}

def test_area_corrigida():
    a, det = ha.area_corrigida(PARAMS_FICTICIOS, AUDITORIO_CPD_BANHEIRO["climatizados"], AUDITORIO_CPD_BANHEIRO["ventilados"])
    assert a == pytest.approx(309.6) and [d["area_corrigida"] for d in det] == pytest.approx([192, 108, 9.6])

@pytest.mark.parametrize("tipo, escopo, custo_base, pct, honorario", [
    ("vrf", "nova_em_novo", 102_168.00, 0.0598916, 6_119.0049888),
    ("agua_gelada", "retrofit", 136_224.00, 0.0581888, 9_512.0533094),
])
def test_honorario_pelo_metodo(tipo, escopo, custo_base, pct, honorario):
    r = ha.calcular_abrava(PARAMS_FICTICIOS, {**AUDITORIO_CPD_BANHEIRO, "tipo_instalacao": tipo, "escopo": escopo}, 1500.0)
    assert (r["custo_base"], r["pct"], r["honorario_metodo"]) == pytest.approx((custo_base, pct, honorario))
    assert r["tr_estimada"] == pytest.approx(17.028)

def test_piso_em_salarios_minimos():
    proj = {"tipo_instalacao": "expansao_direta", "escopo": "nova_em_novo", "ventilados": [],
            "climatizados": [{"tipo": "escritorio", "area_m2": 20, "repeticoes": 1}]}
    r = ha.calcular_abrava(PARAMS_FICTICIOS, proj, 1500.0)
    assert (r["custo_base"], r["honorario_bruto"], r["honorario_metodo"]) == pytest.approx((4400, 348.128, 4500))
    assert "piso de 3 salários mínimos" in r["avisos"][0]

def test_comparar_com_hh():
    assert ha.comparar_com_hh(8_000, 10_000) == pytest.approx({"preco_hh": 8000, "honorario_final": 10000, "diferenca": 2000, "razao": 1.25})

# os erros: um teste parametrizado por código (ambiente "garagem", repeticoes 0, área 0, escopo sem fator,
# sem climatizados, curva vazia) e um teste do aviso de edição superada.

@pytest.mark.skip(reason="Aguardando o PDF oficial 'Metodologia para Avaliação dos Honorários de Projetos de HVAC' "
                         "(ABRAVA/DNPC, Rev. 01/2014): preencher PARAMS_OFICIAIS (fora do repositório) e conferir o "
                         "exemplo de referência (área corrigida 302 m²) antes de habilitar.")
def test_caso_oficial_abrava():
    ...
```

- [ ] **Passo 2: rodar e ver falhar.** Rode `cd propostas && python3 -m pytest -q testes/test_honorario_abrava.py`.
- [ ] **Passo 3: implementar.** A docstring diz que a forma das fórmulas é provisória e só vale depois de conferida no documento oficial, e que nenhum valor de tabela fica no código.
- [ ] **Passo 4: rodar e ver passar.** Resultado esperado: o caso oficial aparece como `skipped` com o motivo. Depois rode `python3 -m pytest -q testes`.
- [ ] **Passo 5: commit.** Mensagem: `feat(orcamento): honorário pelo método ABRAVA/DNPC com parâmetros externos`.

### Tarefa 7: ajustes da empresa e aplicação na proposta

**Arquivos:**
- Criar: `propostas/orcamento/ajustes_honorario.py`
- Modificar: `propostas/orcamento/honorario_abrava.py` (acrescentar `aplicar_na_proposta`)
- Teste: `propostas/testes/test_ajustes_honorario.py`

**Interfaces:**
- Produz (`ajustes_honorario.py`):
  - `NIVEIS_RT = ("junior", "pleno", "senior", "expert")`
  - `AJUSTES_PADRAO = {"fator_nivel_rt": {"junior": 0.70, "pleno": 1.00, "senior": 1.40, "expert": 1.80}, "nivel_rt_padrao": "pleno", "adicional_planilha_pct": 0.10, "fator_licitacao": 0.85}`. O comentário diz: "padrões da empresa (requisitos do usuário), não da ABRAVA".
  - Ajustes do projeto (dict): `{"nivel_rt": str | None, "inclui_planilha": bool, "adicional_planilha_pct": float | None, "adicional_pct": float, "desconto_pct": float, "custos_extras": [{"descricao", "valor"}], "valor_final_manual": float | None}`. `None` usa o padrão da empresa.
  - `aplicar_ajustes(honorario_metodo: float, ajustes_empresa: dict, ajustes_projeto: dict) -> dict`. Devolve `{"honorario_metodo", "linhas": [{"rotulo", "operacao": "×"|"+", "valor", "subtotal"}], "honorario_calculado", "valor_final_manual", "honorario_final", "diferenca_manual", "referencial_licitacao", "nivel_rt", "fator_rt"}`.
    - A ordem e os rótulos são fixos: `"Ajuste da empresa — nível do RT ({nivel})"` (×), `"Ajuste da empresa — planilha quantitativa e orçamento"` (×, só com `inclui_planilha`), `"Ajuste da empresa — adicional"` (×(1+a), só se a > 0), `"Ajuste da empresa — desconto"` (×(1−d), só se d > 0) e uma linha `"Ajuste da empresa — {descricao}"` (+) por custo extra.
    - `honorario_final = valor_final_manual or honorario_calculado`; `diferenca_manual = final − calculado` (0 sem manual).
    - `referencial_licitacao = honorario_calculado × fator_licitacao`, sempre sobre o calculado.
    - Erros (`ErroEntrada`): `nivel_rt_desconhecido`, `desconto_invalido` (fora de [0, 1)), `percentual_invalido` (adicional < 0), `custo_extra_invalido` (< 0), `valor_manual_invalido` (≤ 0).
- Produz (`honorario_abrava.py`): `aplicar_na_proposta(proposta: dict, parametros: dict | None, ajustes_empresa: dict, salario_minimo: float | None) -> tuple[dict, dict[str, dict]]`.
  - Devolve uma cópia da proposta e `{opcao_id: {"abrava", "ajustes", "fase", "adotado"}}` para cada opção com `opcao["projeto_abrava"]["ativo"]`.
  - O `projeto_abrava` da opção é `{"ativo", "fase", "adotar", "tipo_instalacao", "escopo", "climatizados", "ventilados", "prazo_dias", "ajustes"}`.
  - Com `adotar`, a fase indicada passa a `cobranca = "valor"` com `valor_definido = {"valor": honorario_final, "origem": "Método ABRAVA/DNPC com ajustes da empresa", "prazo_dias": prazo_dias}`.
  - Com projeto ativo e `parametros is None`: `ErroEntrada("sem_parametros_abrava", ...)`. Fase inexistente: `ErroEntrada("fase_inexistente", ...)`.

- [ ] **Passo 1: escrever os testes que falham**

```python
AJ = {"nivel_rt": "senior", "inclui_planilha": True, "adicional_planilha_pct": None, "adicional_pct": 0.05,
      "desconto_pct": 0.03, "custos_extras": [{"descricao": "deslocamento", "valor": 800}, {"descricao": "hospedagem", "valor": 450}],
      "valor_final_manual": None}

def test_ajustes_do_caso_1():
    r = aj.aplicar_ajustes(6119.0049888, aj.AJUSTES_PADRAO, AJ)
    assert [l["subtotal"] for l in r["linhas"]] == pytest.approx([8566.60698, 9423.26768, 9894.43107, 9597.59813, 10397.59813, 10847.59813])
    assert (r["honorario_calculado"], r["honorario_final"], r["referencial_licitacao"]) == pytest.approx((10847.598, 10847.598, 9220.458), abs=0.01)
    assert all(l["rotulo"].startswith("Ajuste da empresa — ") for l in r["linhas"])

def test_valor_manual_nao_muda_calculado_nem_licitacao():
    r = aj.aplicar_ajustes(6119.0049888, aj.AJUSTES_PADRAO, {**AJ, "valor_final_manual": 9000})
    assert (r["honorario_final"], r["diferenca_manual"], r["referencial_licitacao"]) == pytest.approx((9000, -1847.598, 9220.458), abs=0.01)

def test_nivel_do_rt_usa_padrao_da_empresa_quando_ausente():   # nivel_rt None → "pleno", fator 1,0
    ...

@pytest.mark.parametrize("campo, valor, codigo", [("desconto_pct", 1.0, "desconto_invalido"), ("nivel_rt", "mestre", "nivel_rt_desconhecido"),
                                                  ("valor_final_manual", 0, "valor_manual_invalido")])
def test_ajustes_invalidos(campo, valor, codigo): ...

def test_aplicar_na_proposta_adota_o_valor(cat, params):
    # proposta padrão; opção A com projeto_abrava do caso 1 (vrf, nova_em_novo, AJ), fase "F1", adotar=True, prazo_dias 30
    p2, info = ha.aplicar_na_proposta(p, PARAMS_FICTICIOS, aj.AJUSTES_PADRAO, 1500.0)
    f1 = p2["opcoes"][0]["fases"][0]
    assert f1["cobranca"] == "valor" and f1["valor_definido"]["valor"] == pytest.approx(10847.598, abs=0.01)
    assert motor.precificar(cat, p2)["opcoes"][0]["preco"] == pytest.approx(10847.598, abs=0.01)
    assert p["opcoes"][0]["fases"][0]["cobranca"] == "fechado"        # original intacta

def test_sem_parametros_abrava(): ...   # código sem_parametros_abrava
```

  Os subtotais esperados da primeira lista: × 1,4 = 8 566,61; × 1,1 = 9 423,27; × 1,05 = 9 894,43; × 0,97 = 9 597,60; + 800 = 10 397,60; + 450 = 10 847,60.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.** Depois rode `python3 -m pytest -q testes`.
- [ ] **Passo 5: commit.** Mensagem: `feat(orcamento): ajustes da empresa sobre o honorário ABRAVA e adoção na proposta`.

### Tarefa 8: modelos, migração e repositórios do comercial

**Arquivos:**
- Criar: `suite/backend/app/modulos/comercial/__init__.py`, `modelos.py`, `repositorio.py`
- Criar: `suite/backend/migracoes/versions/0101_comercial.py` (`alembic revision --autogenerate -m comercial --rev-id 0101`, `down_revision` = cabeça da T0)
- Modificar: `suite/backend/app/registro.py` (`importar_modelos` importa `app.modulos.comercial.modelos`)
- Teste: `suite/backend/testes/modulos/comercial/__init__.py`, `conftest.py`, `test_repositorio.py`

**Interfaces:**
- Produz os modelos, todos com `ComEmpresa` (FK em UUID):

| Modelo (tabela) | Colunas | Restrições |
|---|---|---|
| `Funcao` (`funcao`) | `codigo` str(40), `nome` str(80), `salario_hora` Numeric(10,2), `encargos` Numeric(6,4), `ativo` bool | único (`empresa_id`, `codigo`); propriedade `custo_hora = salario_hora × (1 + encargos)` |
| `Produtividade` (`produtividade`) | `item` str(60), `unidade` str(4) (CHECK em `UNIDADES_ITEM`), `funcao_id` FK, `hh_por_unidade` Numeric(10,4) ≥ 0, `fator_calibracao` Numeric(6,3) padrão 1, `fonte` str(200) | único (`empresa_id`, `item`, `funcao_id`) |
| `ParametroAbrava` (`parametro_abrava`) | `nome`, `fonte`, `edicao`, `secao_tabela`, `regiao` str, `edicao_superada` bool, `dados` JSONB (o dict da Tarefa 6), `vigente` bool | índice único parcial (`empresa_id`) onde `vigente` |
| `ConfiguracaoComercial` (`configuracao_comercial`) | `ajustes` JSONB (forma de `AJUSTES_PADRAO`), `salario_minimo` Numeric(10,2) nulo, `validade_padrao_dias` int padrão 15, `dias_alerta_validade` int padrão 7, `faixas_valor` JSONB padrão `[5000, 20000, 50000]` | único (`empresa_id`) |
| `SecaoDocumento` (`secao_documento`) | `documento` str(10) (CHECK em proposta/contrato/recibo), `chave` str(60), `titulo` str(120), `texto` Text, `ordem` int, `padrao` bool | único (`empresa_id`, `documento`, `chave`) |
| `Proposta` (`proposta`) | `numero` str(40), `cliente_id` UUID, `obra_id` UUID, `responsavel_id` UUID nulo, `situacao` str(10) (CHECK em rascunho/enviada/aprovada/recusada/entregue), `documento` JSONB, `observacoes_internas` Text padrão "", `valor_referencia` Numeric(14,2) nulo, `data_envio` date nulo, `validade_dias` int, `historico` JSONB padrão `[]` | único (`empresa_id`, `numero`) |
| `ItemExecucao` (`item_execucao`) | `proposta_id` FK, `opcao_id` str(2), `ordem` int, `frente` str(80), `item` str(60), `descricao` str(200), `quantidade` Numeric(14,3), `altura`, `acesso`, `ocupacao`, `turno` str(20), `custo_material_unit` Numeric(14,2) padrão 0, `categoria_material` str(12) padrão "material" | |
| `PropostaRevisao` (`proposta_revisao`) | `proposta_id` FK, `numero` int, `entradas` JSONB, `resultado` JSONB, `versao_motor` str(20), `normas` JSONB, `emitida_em` timestamptz, `emitida_por` UUID | único (`proposta_id`, `numero`) |
| `Contrato` (`contrato`) | `numero` str(40), `proposta_id` FK único, `revisao_id` FK, `opcao_id` str(2), `cliente_id`, `obra_id`, `responsavel_id` UUID nulo, `valor_total`, `valor_fixo`, `valor_estimado` Numeric(14,2), `prazo_dias_uteis`, `prazo_dias_corridos` int, `data_inicio`, `previsao_entrega` date, `condicoes_pagamento`, `hh_previsto_funcao`, `hh_previsto_funcao_base` JSONB, `tipo_instalacao` str(20) nulo, `area_m2` Numeric(12,2) nulo, `situacao` str(10) padrão "vigente" | único (`empresa_id`, `numero`) |

- Produz os repositórios, todos `RepositorioBase[...]` partindo de `self.consulta()`:
  - `FuncaoRepositorio.por_codigo(codigo) -> Funcao | None`
  - `ProdutividadeRepositorio.dos_itens(itens: set[str]) -> list[Produtividade]` e `da_funcao(funcao_id) -> list[Produtividade]`
  - `ParametroAbravaRepositorio.vigente() -> ParametroAbrava | None`
  - `ConfiguracaoRepositorio.unica() -> ConfiguracaoComercial | None`
  - `SecaoDocumentoRepositorio.do_documento(documento) -> list[SecaoDocumento]`, ordenada por `ordem`
  - `PropostaRepositorio.filtrar(situacao, obra_id) -> Select` e `proximo_numero(ano) -> str` (`f"PC-{n:03d}/{ano}"`, com n = propostas da empresa com esse sufixo + 1)
  - `ItemExecucaoRepositorio.da_proposta(proposta_id) -> list`
  - `RevisaoRepositorio.ultima(proposta_id)` e `RevisaoRepositorio.da_proposta(proposta_id)`, sem método de alterar
  - `ContratoRepositorio.da_proposta(proposta_id)` e `ContratoRepositorio.filtrar(situacao) -> Select`
- Produz as fixtures em `testes/modulos/comercial/conftest.py`:
  - `empresa_teste`; `ctx_admin` (`Contexto`)
  - `api_como(perfil) -> TestClient`, que cria o usuário e chama `entrar`, como no cadastro; `api_admin`, `api_comercial`, `api_eng`
  - `obra_teste -> (cliente_id, obra_id)`, criados por `cadastro.servico.criar_cliente` e `criar_obra`
  - `outra_empresa -> (Empresa, Contexto)`

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_tabelas_do_comercial_existem`: confere o conjunto dos 9 nomes com `inspect`.
  - `test_repositorio_nao_ve_outra_empresa`: uma `Funcao` "ajudante" na empresa A; `por_codigo` na B dá `None`; na A, `custo_hora == Decimal("27.00")` para 15 × 1,8.
  - `test_numero_sequencial_por_empresa`: A gera "PC-001/2026" e "PC-002/2026"; B gera "PC-001/2026".
  - `test_produtividade_unica_por_item_e_funcao`: a segunda linha igual dá `IntegrityError`.
- [ ] **Passo 2: rodar e ver falhar.** Rode `cd suite/backend && pytest testes/modulos/comercial/test_repositorio.py -v`.
- [ ] **Passo 3: implementar e gerar a migração.** Confira o índice parcial, os CHECKs e as unicidades.
- [ ] **Passo 4: rodar e ver passar.** Rode `alembic upgrade head && alembic downgrade -1 && alembic upgrade head && alembic check && pytest testes/modulos/comercial testes/arquitetura testes/nucleo/test_banco.py -v`.
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): tabelas, migração e repositórios`.

### Tarefa 9: permissões, funções e produtividade pela API

**Arquivos:**
- Criar: `suite/backend/app/modulos/comercial/esquemas.py`, `servico.py`, `rotas.py`
- Modificar: `suite/backend/app/nucleo/perfis.py` (as 8 permissões do comercial), `suite/backend/app/main.py` (incluir `comercial.rotas.roteador`), `suite/backend/testes/isolamento/mundo.py` (`funcao_id`, `produtividade_id`), `suite/backend/testes/isolamento/test_isolamento.py` (`CRIACOES_SEM_REFERENCIA` acrescenta `POST /api/comercial/funcoes`, `POST /api/comercial/funcoes/semear`, `POST /api/comercial/produtividades`)
- Teste: `suite/backend/testes/modulos/comercial/test_tabelas.py`, `test_permissoes.py`

**Interfaces:**
- Produz:
  - `roteador = APIRouter(prefix="/api/comercial", tags=["comercial"])`
  - Esquemas: `FuncaoEntrada(EsquemaEntrada)(codigo, nome, salario_hora ≥ 0, encargos ≥ 0, ativo=True)`; `FuncaoAlteracao` com os mesmos campos opcionais, menos `codigo`; `FuncaoSaida(+ id, custo_hora)`; `ProdutividadeEntrada(item, unidade: Literal["m2","m","un","kW"], funcao_codigo, hh_por_unidade ≥ 0, fonte min 1)`; `ProdutividadeAlteracao(hh_por_unidade?, fonte?)`; `ProdutividadeSaida(+ id, funcao_id, fator_calibracao)`
  - Serviço:
    - `listar_funcoes(sessao, ctx, p) -> Pagina[FuncaoSaida]`, `criar_funcao(sessao, ctx, entrada)`, `alterar_funcao(sessao, ctx, funcao_id, alteracao)`. Código repetido: `Conflito("Já existe função com este código.")`.
    - `semear_funcoes(sessao, ctx) -> int`: cria as de `FUNCOES_PADRAO` que faltam, com salário e encargos 0, e devolve quantas criou.
    - `listar_produtividade(sessao, ctx, p, item: str | None) -> Pagina[ProdutividadeSaida]`, `criar_produtividade(...)`, `alterar_produtividade(...)`, `remover_produtividade(...)`. Unidade diferente da já usada no item: `ErroDominio("unidade_divergente", ..., 422, {"item", "unidade_existente"})`. Função inexistente: `NaoEncontrado("Função não encontrada.")`.
    - `tabelas_execucao(sessao, ctx, itens: set[str]) -> tuple[list[dict], dict[str, dict]]`: produtividade no formato da Tarefa 2 e funções no formato da Tarefa 4, só da empresa.
  - Rotas:
    - `GET /funcoes`, `GET /produtividades` (`comercial.ler`)
    - `POST /funcoes` (201), `PATCH /funcoes/{funcao_id}`, `POST /funcoes/semear`, `POST /produtividades` (201), `PATCH /produtividades/{produtividade_id}`, `DELETE /produtividades/{produtividade_id}` (204) (`comercial.tabelas`)

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_permissoes_do_comercial`: as 8 entradas de `PERMISSOES` são exatamente as da tabela da seção "Permissões".
  - `test_crud_de_funcao`: o POST devolve `custo_hora == 27.0`.
  - `test_funcao_duplicada_409`.
  - `test_semear_cria_seis_funcoes_uma_vez`: a primeira chamada devolve 6, a segunda 0.
  - `test_produtividade_unidade_divergente_422`.
  - `test_tabelas_execucao_so_da_empresa`: com `duto_m2` só na B, a A recebe `([], {})`.
- [ ] **Passo 2: rodar e ver falhar.** Rode `pytest testes/modulos/comercial testes/isolamento testes/nucleo/test_perfis.py -v`.
- [ ] **Passo 3: implementar e regenerar os tipos do front-end.**
- [ ] **Passo 4: rodar e ver passar.** Rode `pytest -v && ruff check .`.
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): permissões, funções e produtividade pela API`.

### Tarefa 10: parâmetros ABRAVA e configuração comercial da empresa

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`; `testes/isolamento/test_isolamento.py` (`CRIACOES_SEM_REFERENCIA` acrescenta `POST /api/comercial/parametros-abrava` e `PATCH /api/comercial/configuracao`)
- Teste: `suite/backend/testes/modulos/comercial/test_parametros_abrava.py`, `test_configuracao.py`

**Interfaces:**
- Consome: `TIPOS_INSTALACAO`, `ESCOPOS`, `TIPOS_VENTILACAO` (Tarefa 6); `AJUSTES_PADRAO`, `NIVEIS_RT` (Tarefa 7).
- Produz:
  - `ParametroAbravaEntrada(EsquemaEntrada)`. Campos: `nome`, `fonte` (min 1), `edicao` (min 1), `secao_tabela`, `regiao` (min 1), `edicao_superada`, mais os campos do dict da Tarefa 6. Validações: `custo_tr` com as 3 chaves de `TIPOS_INSTALACAO` e valores > 0; `fator_escopo` com as 4 chaves de `ESCOPOS`; `peso_ventilacao` só com chaves de `TIPOS_VENTILACAO`; `tipos_ambiente` com pelo menos 1; `curva_percentual` com pelo menos 1 ponto, sem custo repetido e `0 < pct < 1`; `densidade_tr_m2 > 0`, `fs > 0`.
  - `ParametroAbravaSaida(+ id, vigente, criado_em)`.
  - `criar_parametro_abrava(sessao, ctx, entrada)`: o novo conjunto fica vigente e o anterior deixa de ser. Não há edição: cada correção é um conjunto novo, e o antigo fica para as revisões que o citam.
  - `listar_parametros_abrava(sessao, ctx, p) -> Pagina[ParametroAbravaSaida]`.
  - `parametro_abrava_vigente(sessao, ctx) -> dict | None`, no formato da Tarefa 6.
  - `ConfiguracaoSaida(ajustes, salario_minimo, validade_padrao_dias, dias_alerta_validade, faixas_valor)` e `ConfiguracaoAlteracao` com os mesmos campos opcionais. Validações: os 4 níveis em `ajustes.fator_nivel_rt`, fatores > 0, `faixas_valor` crescente e positiva, `validade_padrao_dias >= 1`.
  - `obter_configuracao_comercial(sessao, ctx) -> ConfiguracaoSaida`: sem linha, devolve os padrões (`AJUSTES_PADRAO`, `None`, 15, 7, `[5000, 20000, 50000]`) sem gravar. `alterar_configuracao_comercial(sessao, ctx, alteracao)` grava a linha na primeira vez.
  - Rotas: `GET /parametros-abrava` e `GET /configuracao` (`comercial.ler`); `POST /parametros-abrava` (201, `comercial.tabelas`); `PATCH /configuracao` (`comercial.configurar`).

- [ ] **Passo 1: escrever os testes que falham.** Use `PARAMS_FICTICIOS`, com o comentário `# FICTÍCIO`.
  - `test_novo_conjunto_vira_vigente`.
  - `test_curva_com_custo_repetido_422`.
  - `test_custo_tr_sem_vrf_422`.
  - `test_parametro_de_outra_empresa_nao_vale`.
  - `test_configuracao_padrao_sem_gravar`: o fator de sênior é 1,4 e a validade é 15.
  - `test_alterar_salario_minimo_e_fator_licitacao`.
  - `test_comercial_nao_altera_configuracao_403`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar e regenerar os tipos.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): parâmetros privados ABRAVA e configuração comercial da empresa`.

### Tarefa 11: projeto em rascunho, itens de execução, catálogo e observações internas

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`; `testes/isolamento/mundo.py` (`proposta_id` e `item_execucao_id`, com `corpos` de `PUT .../documento` e `POST .../itens-execucao`); `testes/isolamento/test_isolamento.py` (`POST /api/comercial/propostas` entra no grupo das criações com referência no corpo, como `POST /obras`, coberto pelo teste `test_obra_de_outra_empresa_404` deste módulo)
- Teste: `suite/backend/testes/modulos/comercial/test_propostas.py`

**Interfaces:**
- Consome: `cadastro.servico.obter_obra`; `obter_empresa` (responsáveis); `obter_configuracao_comercial`; `orcamento.catalogo.carregar`, `parametros.carregar`, `proposta.padrao` e `completar`.
- Produz:
  - `PropostaCriar(EsquemaEntrada)(obra_id: UUID, documento: dict | None = None)`.
    - O `cliente_id` vem de `obter_obra`.
    - Sem documento, usa `pp.padrao(params)`; com documento (JSON importado do app atual), usa `pp.completar(documento, cat, params)`.
    - `documento["validade_dias"]` = o do JSON ou `validade_padrao_dias` da configuração.
    - O número é `documento["numero"]` quando veio no JSON; senão, `proximo_numero(hoje.year)`, que também é gravado no documento.
    - `responsavel_id` = primeiro RT não arquivado da empresa, ou `None`.
  - `PropostaAlteracao(EsquemaEntrada)(observacoes_internas?, responsavel_id?)`. RT de outra empresa ou inexistente: `NaoEncontrado("Responsável técnico não encontrado.")`.
  - `PropostaSaida(id, numero, cliente_id, obra_id, responsavel_id, situacao, documento, observacoes_internas, validade_dias, data_envio, vencimento, validade: Literal["valida","vencendo","vencida"] | None, valor_referencia, revisao_atual: int | None, historico, criado_em)`.
  - `ItemExecucaoEntrada(EsquemaEntrada)(opcao_id, frente min 1, item, descricao="", quantidade ≥ 0, altura="ate_3m", acesso="livre", ocupacao="desocupado", turno="diurno", custo_material_unit ≥ 0 = 0, categoria_material: Literal["material","equipamento"]="material")`; `ItemExecucaoAlteracao` com os mesmos campos opcionais; `ItemExecucaoSaida(+ id, ordem, unidade | None)`.
  - Serviço:
    - `criar_proposta(sessao, ctx, entrada, hoje)`, `obter_proposta(sessao, ctx, proposta_id, hoje)`, `listar_propostas(sessao, ctx, p, hoje, situacao=None, obra_id=None) -> Pagina[PropostaSaida]`
    - `alterar_proposta(sessao, ctx, proposta_id, alteracao, hoje)`, `salvar_documento(sessao, ctx, proposta_id, documento, hoje)`
    - `listar_itens_execucao(sessao, ctx, proposta_id)`, `criar_item_execucao(...)`, `alterar_item_execucao(sessao, ctx, item_execucao_id, ...)`, `remover_item_execucao(...)`
    - `propostas_da_obra(sessao, ctx, obra_id, hoje) -> list[PropostaSaida]` (histórico do empreendimento)
    - `catalogo() -> dict`
  - Regras:
    - A edição do documento e dos itens só é permitida em `rascunho` e `enviada`; fora disso, `ErroDominio("situacao_invalida", ..., 409, {"situacao"})`. As observações internas podem ser editadas em qualquer situação.
    - Documento que falha em `completar` (`KeyError` ou `ValueError`): `ErroDominio("documento_invalido", "Proposta inválida: {erro}", 422)`.
    - Número repetido: `ErroDominio("numero_duplicado", ..., 409)`.
    - Obra de outra empresa: `NaoEncontrado` (vem do cadastro).
  - Rotas:
    - `GET /propostas` (`?situacao=&obra_id=` + `ParametrosLista`), `GET /propostas/{proposta_id}`, `GET /propostas/{proposta_id}/itens-execucao`, `GET /obras/{obra_id}/propostas`, `GET /catalogo` (`comercial.ler`)
    - `POST /propostas` (201), `PATCH /propostas/{proposta_id}`, `PUT /propostas/{proposta_id}/documento`, `POST /propostas/{proposta_id}/itens-execucao` (201), `PATCH /itens-execucao/{item_execucao_id}`, `DELETE /itens-execucao/{item_execucao_id}` (204) (`comercial.editar_proposta`)

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_criar_projeto_vazio`: número "PC-001/2026", situação `rascunho`, opção "A", `validade_dias == 15` e `responsavel_id` do primeiro RT.
  - `test_importar_json_antigo_sem_fases`: `modelo_preco: "hora"` resulta em `fases[0].cobranca == "hora"`.
  - `test_servico_inexistente_422`: código `documento_invalido`.
  - `test_obra_de_outra_empresa_404`.
  - `test_editar_documento_de_proposta_aprovada_409`: a situação é preparada direto no banco.
  - `test_observacoes_internas_editaveis_sempre`.
  - `test_itens_crud_e_ordem`.
  - `test_varios_projetos_por_empreendimento`: duas propostas na obra; `GET /obras/{obra_id}/propostas` devolve as 2.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar e regenerar os tipos.**
- [ ] **Passo 4: rodar e ver passar.** Rode `pytest testes/modulos/comercial testes/isolamento -v`.
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): projetos em rascunho, itens de execução, catálogo e observações internas`.

### Tarefa 12: cálculo pela API (critérios de pronto e comparação HH × ABRAVA)

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`; `testes/isolamento/mundo.py` (`corpos` de `POST .../calculo`)
- Teste: `suite/backend/testes/modulos/comercial/test_calculo.py`, `suite/backend/testes/modulos/comercial/referencia.py`. O segundo traz os dados dos dois casos de referência, `RAIZ_PROPOSTAS = Path(orcamento.__file__).resolve().parents[1]`, `montar_obra_referencia(api, obra_id) -> UUID` (cria funções, produtividade, proposta com `execucao` modo prazo 10 e os 3 itens) e `ativar_abrava(api, proposta_id, adotar: bool)` (cadastra `PARAMS_FICTICIOS`, salário mínimo 1 500 e o `projeto_abrava` do caso 1 com os ajustes `AJ`).

**Interfaces:**
- Consome: `tabelas_execucao`, `parametro_abrava_vigente`, `obter_configuracao_comercial`, `honorario_abrava.aplicar_na_proposta` e `comparar_com_hh`, `execucao.precificar_com_execucao`.
- Produz:
  - `montar_entradas(sessao, ctx, proposta_id) -> dict`, com `{"documento", "itens_por_opcao", "produtividade", "funcoes", "parametros_abrava", "configuracao", "catalogo"}`. É JSON puro; é o que a revisão congela. Não leva `observacoes_internas`.
  - `calcular_entradas(entradas: dict) -> dict`, função pura, em três passos:
    1. `aplicar_na_proposta(documento, parametros_abrava, configuracao.ajustes, configuracao.salario_minimo)`.
    2. `precificar_com_execucao(catalogo, documento_abrava, itens_por_opcao, produtividade, funcoes)`.
    3. Para cada opção com ABRAVA, `comparar_com_hh(preco_servicos da fase, honorario_final)`.

    Devolve `{"documento_precificado", "orcamento", "execucao", "abrava": {opcao_id: {"abrava", "ajustes", "fase", "adotado", "comparacao"}}, "avisos", "versao_motor"}`. Os `ErroEntrada` viram `ErroDominio(e.codigo, e.mensagem, 422, e.detalhes)`, e os avisos do ABRAVA entram em `avisos`.
  - `calcular(sessao, ctx, proposta_id) -> ResultadoCalculoSaida`: calcula sem gravar.
  - `ResultadoCalculoSaida(opcoes: list[OpcaoResumo], avisos, versao_motor, detalhe: dict)`:
    - `OpcaoResumo(id, nome, interno, preco, preco_fixo, preco_estimado, total_h, prazo_dias_uteis, prazo_dias_corridos, fases: list[FaseResumo(id, nome, cobranca, preco, preco_servicos)], execucao: ExecucaoResumo | None, abrava: AbravaResumo | None)`
    - `ExecucaoResumo(hh_funcao, hh_funcao_base, equipe, cronograma, prazo_dias_uteis, prazo_dias_corridos, total_hh, custo_mo, preco_mo)`. `custo_mo` e `preco_mo` são as somas dos fornecimentos `mo_execucao` com fonte "HH de execução".
    - `AbravaResumo(area_corrigida, custo_base, pct, honorario_metodo, ajustes: list[linhas], honorario_calculado, honorario_final, diferenca_manual, referencial_licitacao, adotado, fase, comparacao, fonte, edicao)`
  - Rota: `POST /propostas/{proposta_id}/calculo` (`comercial.calcular`).

- [ ] **Passo 1: escrever os testes que falham**

```python
PRECOS_ESPERADOS = {"hvac_consultoria_2d_3d_bim.json": {"A": 55672.13, "B": 96243.17, "C": 140048.50},
                    "hvac_retrofit_fases.json": {"A": 138637.75, "B": 125937.62, "E": 1163417.61},
                    "nr13_inspecao.json": {"A": 29069.38}, "spci_projeto.json": {"A": 21622.49, "B": 32069.63}}

@pytest.mark.parametrize("arquivo", sorted(PRECOS_ESPERADOS))
def test_exemplos_dao_o_mesmo_preco_pela_api(arquivo, api_comercial, obra_teste):
    doc = json.loads((RAIZ_PROPOSTAS / "exemplos" / arquivo).read_text(encoding="utf-8"))
    pid = api_comercial.post("/api/comercial/propostas", json={"obra_id": str(obra_teste[1]), "documento": doc}).json()["id"]
    r = api_comercial.post(f"/api/comercial/propostas/{pid}/calculo").json()
    assert {o["id"]: round(o["preco"], 2) for o in r["opcoes"]} == PRECOS_ESPERADOS[arquivo]

def test_obra_de_referencia_pela_api(api_admin, obra_teste):
    pid = montar_obra_referencia(api_admin, obra_teste[1])
    o = api_admin.post(f"/api/comercial/propostas/{pid}/calculo").json()["opcoes"][0]
    ex = o["execucao"]
    assert ex["hh_funcao"] == pytest.approx({"encarregado": 10.7, "mecanico_refrigeracao": 96.1, "ajudante": 96.1})
    assert ex["equipe"] == {"encarregado": 1, "mecanico_refrigeracao": 2, "ajudante": 2}
    assert [(c["frente"], c["dias_uteis"]) for c in ex["cronograma"]] == [("Térreo", 7), ("Cobertura", 2)]
    assert (ex["prazo_dias_uteis"], ex["prazo_dias_corridos"]) == (9, 13)
    assert (ex["custo_mo"], ex["preco_mo"], o["preco"]) == pytest.approx((8554.50, 10436.49, 44921.49))
```

  Outros testes:
  - `test_produtividade_so_de_outra_empresa_422`: `item_sem_produtividade`, com `detalhes == {"item": "duto_m2"}`.
  - `test_equipe_fixa_incompleta_422`.
  - `test_abrava_comparado_sem_adotar`: `abrava.honorario_final ≈ 10 847,60` e `referencial_licitacao ≈ 9 220,46`; o preço da opção não muda; `comparacao.preco_hh == fases[0].preco_servicos`.
  - `test_abrava_adotado_vira_preco_da_fase`: proposta nova, sem execução nem fornecimentos, com `ativar_abrava(..., adotar=True)`; `fases[0].cobranca == "valor"` e `preco ≈ 10 847,60`.
  - `test_abrava_sem_parametros_422`: código `sem_parametros_abrava`.
  - `test_calculo_nao_grava`: `revisao_atual` continua `None`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar e regenerar os tipos.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): cálculo pela API — exemplos, obra de referência e comparação HH × ABRAVA`.

### Tarefa 13: gerar proposta (→ enviada), revisões e validade

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`; `testes/isolamento/mundo.py` (`revisao_id`)
- Teste: `suite/backend/testes/modulos/comercial/test_geracao_revisoes.py`

**Interfaces:**
- Consome: `montar_entradas`, `calcular_entradas`, `obter_configuracao_comercial`.
- Produz:
  - `situacao_validade(data_envio, validade_dias, situacao, hoje, dias_alerta) -> tuple[date | None, str | None]`.
    - Vencimento = `data_envio + validade_dias` (dias corridos). Só se avalia a situação `enviada`.
    - `"vencida"` se hoje > vencimento; `"vencendo"` se faltam de 0 a `dias_alerta` dias (padrão 7); senão `"valida"`.
    - Para outras situações: `(vencimento, None)`.
  - `gerar_proposta(sessao, ctx, proposta_id, hoje) -> RevisaoSaida`. É a ação "gerar proposta", e a situação passa a `enviada` automaticamente.
    - Só a partir de `rascunho` ou `enviada`.
    - O número da revisão é a última + 1, começando em 0. Antes de montar as entradas, o serviço grava `documento["revisao"] = f"{n:02d}"` e `documento["data"] = hoje.isoformat()`.
    - Grava `entradas`, `resultado`, `versao_motor`, `normas` (`[{"norma": fonte, "edicao", "secao": secao_tabela}]` do ABRAVA usado, ou `[]`), `emitida_em` e `emitida_por`.
    - A proposta recebe `situacao="enviada"`, `data_envio=hoje`, `valor_referencia` = menor `preco` entre as opções não internas (2 casas) e um registro no histórico: `{"de", "para", "em", "por", "revisao": n}`.
    - Erro de cálculo não grava nada.
  - `RevisaoSaida(id, numero, emitida_em, emitida_por, versao_motor, normas, resumo: ResultadoCalculoSaida)`; `listar_revisoes(sessao, ctx, proposta_id) -> list[RevisaoSaida]`; `obter_revisao(sessao, ctx, revisao_id)`.
  - Rotas: `POST /propostas/{proposta_id}/geracao` (201, `comercial.editar_proposta`); `GET /propostas/{proposta_id}/revisoes` e `GET /revisoes/{revisao_id}` (`comercial.ler`).

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_gerar_cria_revisao_00_e_envia`: com a obra de referência, a revisão tem preço 44 921,49, `versao_motor == orcamento.__version__`, a situação é `enviada` e `valor_referencia == 44921.49`.
  - `test_gerar_de_novo_depois_de_editar_cria_01`: a revisão 00 continua com 44 921,49.
  - `test_mudar_produtividade_ou_parametros_abrava_nao_altera_revisao`.
  - `test_revisao_sem_rota_de_alteracao`: `PUT /revisoes/{revisao_id}` dá 405.
  - `test_validade`: parametrizado com envio em 2026-11-01, validade de 15 dias (vencimento 16/11) e alerta de 7 dias. Em 08/11 é `valida`; em 09/11 e em 16/11, `vencendo`; em 17/11, `vencida`.
  - `test_observacoes_internas_fora_da_revisao`: o texto "segredo interno" não aparece em `json.dumps(entradas)` nem em `json.dumps(resultado)`.
  - `test_normas_da_revisao_com_abrava`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar e regenerar os tipos.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): gerar proposta com revisão imutável, histórico e validade`.

### Tarefa 14: gerar contrato (→ aprovada), recusa, entrega e desfazer

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`; `testes/isolamento/mundo.py` (`contrato_id` e os `corpos` de `.../contrato`, `.../recusa`)
- Teste: `suite/backend/testes/modulos/comercial/test_contrato_fluxo.py`

**Interfaces:**
- Consome: `RevisaoRepositorio.ultima`, `situacao_validade`.
- Produz, para a T3 e para a calibração:
  - `MarcoPagamento(marco, pct, valor)`; `FasePagamento(fase_id, fase, cobranca, preco, marcos)`.
  - `ContratoSaida(id, numero, proposta_id, proposta_numero, revisao_id, revisao_numero, opcao_id, cliente_id, obra_id, responsavel_id, valor_total, valor_fixo, valor_estimado, prazo_dias_uteis, prazo_dias_corridos, data_inicio, previsao_entrega, condicoes_pagamento: list[FasePagamento], hh_previsto_funcao, hh_previsto_funcao_base, tipo_instalacao, area_m2, situacao)`.
  - `gerar_contrato(sessao, ctx, proposta_id, revisao_id, opcao_id, hoje) -> ContratoSaida`. É a ação "gerar contrato", e a situação passa a `aprovada` automaticamente. Validações, nesta ordem:
    1. A situação é `enviada`; senão, `ErroDominio("situacao_invalida", 409)`.
    2. A revisão é da proposta e é a última; senão, `ErroDominio("revisao_desatualizada", 409, {"ultima": n})`. A revisão de outra proposta dá `NaoEncontrado`.
    3. A proposta não está vencida; senão, `ErroDominio("proposta_vencida", 409)`.
    4. A opção existe; senão, `ErroDominio("opcao_inexistente", 422)`.
    5. A opção não é interna; senão, `ErroDominio("opcao_interna", 422)`.

    Campos do contrato:
    - `numero`: o número da proposta com "PC-" trocado por "CT-", ou "CT-" + número quando ele não começa com "PC-".
    - Valores da opção em `resultado.orcamento`, com 2 casas.
    - `data_inicio = hoje` e `previsao_entrega = hoje + prazo_dias_corridos`.
    - Marcos por fase: `valor = round(pct × preço da fase, 2)`.
    - `hh_previsto_*` vêm de `resultado.execucao[opcao_id]`, ou `{}`.
    - `tipo_instalacao` vem do `projeto_abrava` da opção. `area_m2` = Σ climatizados (área × repetições), quando houver. Os dois servem ao R$/m² do painel.

    Na proposta: `situacao="aprovada"`, `valor_referencia=valor_total` e o histórico. O PDF do contrato sai na Tarefa 17.
  - `recusar_proposta(sessao, ctx, proposta_id, motivo, hoje)`: só a partir de `enviada`.
  - `registrar_entrega(...)`: `aprovada → entregue`. `desfazer_entrega(...)`: `entregue → aprovada`. Transições erradas dão `situacao_invalida`, e todas gravam no histórico.
  - `obter_contrato(sessao, ctx, contrato_id)`; `listar_contratos(sessao, ctx, p, situacao=None) -> Pagina[ContratoSaida]`; `contrato_da_proposta(sessao, ctx, proposta_id) -> ContratoSaida | None`.
  - Rotas:
    - `POST /propostas/{proposta_id}/contrato` com corpo `{revisao_id, opcao_id}` (201)
    - `POST /propostas/{proposta_id}/recusa` com corpo `{motivo}`
    - `POST /propostas/{proposta_id}/entrega` e `DELETE /propostas/{proposta_id}/entrega` (`comercial.editar_proposta`)
    - `GET /contratos`, `GET /contratos/{contrato_id}` (`comercial.ler`)

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_gerar_contrato_da_obra_de_referencia`: número "CT-001/2026"; `valor_total == 44921.49`; `prazo_dias_corridos == 13`; previsão de entrega = hoje + 13; marcos de 13 476,45 e 31 445,04; `hh_previsto_funcao["ajudante"] == 96.1`; situação da proposta `aprovada`.
  - `test_contrato_com_abrava_guarda_tipo_e_area`: VRF; área 160 + 2 × 48 = 256 m².
  - `test_revisao_antiga_409`, `test_vencida_409`, `test_opcao_interna_422` (exemplo `hvac_retrofit_fases.json`, opção E), `test_segundo_contrato_409`.
  - `test_recusar_e_historico`, `test_entregar_e_desfazer`, `test_entregar_rascunho_409`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar e regenerar os tipos.**
- [ ] **Passo 4: rodar e ver passar.** Rode também `testes/arquitetura` e `testes/isolamento`.
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): gerar contrato aprova a proposta; recusa, entrega e desfazer`.

### Tarefa 15: exportações XLSX, DOCX e viabilidade de uma revisão

**Arquivos:**
- Modificar: `comercial/servico.py`, `rotas.py`
- Teste: `suite/backend/testes/modulos/comercial/test_exportacoes.py`

**Interfaces:**
- Consome: `exportar_xlsx.gerar(cat, proposta, resultado) -> bytes`; `exportar_docx.gerar(...) -> list[(bytes, nome, pendencias)]` (uma por opção não interna, na ordem); `viabilidade.calcular`; `exportar_viabilidade.gerar`.
- Produz: `exportar_xlsx(sessao, ctx, revisao_id) -> tuple[bytes, str]`, `exportar_docx(sessao, ctx, revisao_id, opcao_id)` e `exportar_viabilidade(sessao, ctx, revisao_id)`. As três usam só o que a revisão congelou: `entradas["catalogo"]`, `resultado["documento_precificado"]` e `resultado["orcamento"]`. Erros: `ErroDominio("sem_viabilidade", 422)`; opção interna ou inexistente no DOCX, `ErroDominio("opcao_sem_proposta", 422)`.
- Rotas (`comercial.ler`): `GET /revisoes/{revisao_id}/xlsx`, `GET /revisoes/{revisao_id}/docx?opcao=A`, `GET /revisoes/{revisao_id}/viabilidade`, com `Content-Disposition: attachment; filename=<nome do motor>`.

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_xlsx_da_revisao`: abre com openpyxl e tem a aba `Resumo`.
  - `test_docx_da_revisao_por_opcao`: começa com `b"PK"` e `verificar(...)["logo"]` é verdadeiro.
  - `test_exportacao_usa_catalogo_congelado`: com monkeypatch, `orcamento.catalogo.carregar` passa a devolver um catálogo sem serviços, e a exportação continua funcionando.
  - `test_xlsx_com_valor_abrava_adotado`: a aba da opção mostra o valor definido.
  - `test_viabilidade_sem_alternativas_422`.
  - `test_observacoes_internas_fora_do_docx`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar e regenerar os tipos.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): exportações da revisão pelo motor (XLSX, DOCX, viabilidade)`.

### Tarefa 16: modelos de documento por seção (variáveis, ordem, seções novas, restaurar padrão)

**Arquivos:**
- Criar: `suite/backend/app/modulos/comercial/modelos_documento_padrao.py` (dados: seções padrão e variáveis)
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`; `testes/isolamento/test_isolamento.py` (`CRIACOES_SEM_REFERENCIA` acrescenta `PUT /api/comercial/modelos-documento` e `POST /api/comercial/modelos-documento/restaurar`)
- Teste: `suite/backend/testes/modulos/comercial/test_modelos_documento.py`

**Interfaces:**
- Produz:
  - `SECOES_PADRAO: dict[str, list[dict]]`, indexado por documento, com a lista ordenada de `{"chave", "titulo", "texto"}` (tabela abaixo).
  - `VARIAVEIS: dict[str, dict[str, str]]`, indexado por documento, com `{variavel: descrição}`. As variáveis são `string.Template`:
    - comuns: `$empresa`, `$empresa_cnpj`, `$cliente`, `$cliente_documento`, `$representante`, `$obra`, `$endereco_obra`, `$numero`, `$objeto`, `$data`, `$rt`, `$rt_registro`
    - proposta: `$validade`, `$valor`, `$prazo`
    - contrato: `$valor`, `$valor_extenso`, `$prazo`, `$foro`
    - recibo: `$valor`, `$valor_extenso`, `$referencia`, `$data_pagamento`
  - `SecaoEntrada(chave: str | None, titulo min 1, texto)`; `SecaoSaida(chave, titulo, texto, ordem, padrao: bool, alterada: bool)`. `alterada` indica texto ou título diferente do padrão.
  - `ModeloDocumentoSaida(documento, secoes: list[SecaoSaida], variaveis: dict[str, str], personalizado: bool)`.
  - `obter_modelo(sessao, ctx, documento) -> ModeloDocumentoSaida`: sem linhas da empresa, devolve o padrão.
  - `salvar_modelo(sessao, ctx, documento, secoes: list[SecaoEntrada]) -> ModeloDocumentoSaida`: substitui a lista inteira, e a ordem da lista é a ordem do documento. Uma seção nova sem chave recebe `f"secao_{uuid4().hex[:8]}"` e `padrao=False`.
  - `restaurar_modelo(sessao, ctx, documento, chave: str | None)`: com chave padrão, volta título e texto daquela seção, mantendo a ordem. Sem chave, apaga as linhas e volta ao padrão inteiro. Chave que não é padrão: `ErroDominio("secao_sem_padrao", 422)`.
  - `renderizar_secoes(sessao, ctx, documento, variaveis: dict[str, str]) -> list[tuple[str, str]]`: `(titulo, texto)` com `safe_substitute`.
  - Documento fora de proposta/contrato/recibo: `EntradaInvalida`.
  - Rotas, sem parâmetro de caminho: `GET /modelos-documento?documento=proposta` (`comercial.ler`; sem `documento`, devolve os três); `PUT /modelos-documento` com corpo `{documento, secoes}` e `POST /modelos-documento/restaurar` com corpo `{documento, chave?}` (`comercial.modelos_documento`).

Seções padrão. É texto inicial; o jurídico da KAPTEK revisa o contrato antes do uso:

| documento | chave | título | texto |
|---|---|---|---|
| proposta | `apresentacao` | Apresentação | "A $empresa apresenta a $cliente a proposta $numero para $objeto, no empreendimento $obra." |
| proposta | `condicoes` | Condições comerciais | "Os valores incluem os tributos incidentes. O pagamento segue os marcos de cada fase descritos nesta proposta." |
| proposta | `validade` | Validade | "Esta proposta é válida por $validade dias a partir de $data." |
| proposta | `encerramento` | Encerramento | "Ficamos à disposição para esclarecimentos. $rt — $rt_registro." |
| contrato | `partes` | Partes | "CONTRATADA: $empresa, CNPJ $empresa_cnpj. CONTRATANTE: $cliente, $cliente_documento, representada por $representante." |
| contrato | `objeto` | Objeto | "Prestação de serviços de $objeto no empreendimento $obra ($endereco_obra), conforme a proposta $numero." |
| contrato | `valor` | Valor e pagamento | "O valor total é de $valor ($valor_extenso), pago conforme as condições de pagamento deste contrato." |
| contrato | `prazo` | Prazo | "O prazo de execução é de $prazo dias corridos, contados da data de início." |
| contrato | `responsabilidade_tecnica` | Responsabilidade técnica | "Os serviços terão responsabilidade técnica de $rt ($rt_registro), com ART registrada." |
| contrato | `obrigacoes_contratante` | Obrigações do contratante | "O CONTRATANTE dará acesso ao local, as informações e os documentos necessários, e efetuará os pagamentos nas datas acordadas." |
| contrato | `rescisao` | Rescisão | "Qualquer parte pode rescindir este contrato por aviso escrito com 30 dias de antecedência, pagos os serviços executados." |
| contrato | `foro` | Foro | "Fica eleito o foro da comarca de $foro." |
| recibo | `declaracao` | Recibo | "Recebemos de $cliente ($cliente_documento) a importância de $valor ($valor_extenso), referente a $referencia, em $data_pagamento." |

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_padrao_sem_personalizacao`: 4 seções de proposta, `personalizado: false`.
  - `test_reordenar_editar_e_acrescentar_clausula`: a cláusula nova recebe chave `secao_` e fica na posição enviada.
  - `test_restaurar_uma_secao_mantem_ordem`.
  - `test_restaurar_documento_inteiro`.
  - `test_restaurar_secao_nova_422`.
  - `test_modelo_de_outra_empresa_nao_aparece`.
  - `test_variavel_desconhecida_fica_literal`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar e regenerar os tipos.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): modelos de documento por seção com variáveis e restaurar padrão`.

### Tarefa 17: PDFs de proposta, contrato e recibo com a identidade da empresa e do RT

**Arquivos:**
- Criar: `suite/backend/app/modulos/comercial/documentos_pdf.py` (renderização: HTML para PDF) e `suite/backend/app/modulos/comercial/modelos_pdf/{base,proposta,contrato,recibo}.html`, `estilo.css`
- Modificar: `comercial/servico.py`, `rotas.py`; `suite/backend/pyproject.toml` (`weasyprint>=62,<63`, `jinja2>=3.1,<4`, `num2words>=0.5.13,<0.6`; extra `dev`: `pdfplumber>=0.11,<0.12`); `suite/infra/backend.Dockerfile` (`apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 fonts-dejavu-core`); `.github/workflows/suite.yml` (job `backend`: `sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0`); `testes/isolamento/mundo.py` (`corpos` de `POST /contratos/{contrato_id}/recibo`)
- Teste: `suite/backend/testes/modulos/comercial/test_pdfs.py`

**Interfaces:**
- Consome: `obter_empresa`, `obter_arquivo` + `obter_armazenamento().ler`, `obter_cliente`, `obter_obra`, `renderizar_secoes`, `exportar_docx.moeda`, `catalogo.exclusoes_validas`, `ContratoSaida` e a revisão congelada.
- Produz:
  - `valor_por_extenso(valor: float) -> str`: `num2words(round(valor, 2), lang="pt_BR", to="currency")`.
  - `renderizar_pdf(modelo: str, contexto: dict) -> bytes`: Jinja2 com `autoescape=True` e WeasyPrint, A4, margens de 2 cm, fonte DejaVu Sans. O cabeçalho mostra logomarca (`data:` URI), razão social e CNPJ. O rodapé mostra "Responsável técnico: {nome} — {titulo} — {conselho} {registro}", com a assinatura do RT no contrato e no recibo.
  - RT do documento: `proposta.responsavel_id`, ou o primeiro RT não arquivado. Sem RT: `RegraNegocio("Cadastre um responsável técnico na configuração da empresa.")`.
  - `pdf_proposta(sessao, ctx, revisao_id, opcao_id) -> tuple[bytes, str]`: seções do modelo; tabela de fases (nome, cobrança, preço); prazo; marcos por fase; exclusões; resumo da execução (HH por função, equipe, cronograma por frentes), quando houver. Quando o honorário ABRAVA foi adotado, entra o quadro "Honorário de projeto" com o honorário do método e as linhas "Ajuste da empresa — …". O referencial de licitação não sai na proposta.
  - `pdf_contrato(sessao, ctx, contrato_id) -> tuple[bytes, str]`: seções do contrato mais a tabela de condições de pagamento.
  - `pdf_recibo(sessao, ctx, contrato_id, valor: float | None, referencia: str | None, data_pagamento: date) -> tuple[bytes, str]`. Sem valor, vale `valor_total`. Sem referência, vale `f"projeto completo — contrato {numero}"`. Valor ≤ 0 ou acima do total: `ErroDominio("valor_recibo_invalido", 422)`. A T3 chama esta função por parcela paga.
  - Rotas:
    - `GET /revisoes/{revisao_id}/pdf?opcao=A` e `GET /contratos/{contrato_id}/pdf` (`comercial.ler`)
    - `POST /contratos/{contrato_id}/recibo` com corpo `{valor?, referencia?, data_pagamento}` (`comercial.recibo`)

- [ ] **Passo 1: escrever os testes que falham.** O texto é extraído com `pdfplumber`, e a identidade é preparada com `alterar_empresa` e `criar_responsavel` da T0.

```python
def test_pdf_da_proposta(...):   # razao_social "Empresa Teste Ltda", RT "Fulano de Tal", CREA "000000/D"
    texto = extrair(api.get(f"/api/comercial/revisoes/{rev}/pdf?opcao=A").content)
    assert "Empresa Teste Ltda" in texto and "000000/D" in texto and "R$ 44.921,49" in texto and "Térreo" in texto
    assert "segredo interno" not in texto                         # observações internas nunca saem

def test_pdf_usa_modelo_personalizado(...)   # apresentação "Texto próprio $numero" → "Texto próprio PC-001/2026"
def test_pdf_abrava_mostra_ajustes_rotulados(...)   # "Ajuste da empresa — nível do RT (senior)" no texto; "licitação" ausente
def test_pdf_do_contrato(...)                # "R$ 13.476,45", "R$ 31.445,04", comarca do foro e representante legal do cliente
def test_recibo_por_parcela(...)             # valor 13476.45, referencia "parcela 1" → ambos no texto
def test_recibo_do_projeto_por_extenso(...)  # contrato de 90 000 gravado pelo repositório → "noventa mil reais"
def test_recibo_acima_do_total_422(...)
def test_sem_responsavel_tecnico_422(...)
```

- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar e regenerar os tipos.**
- [ ] **Passo 4: rodar e ver passar.** Rode também `docker compose -f suite/infra/docker-compose.yml build api`.
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): PDFs de proposta, contrato e recibo com identidade da empresa e do RT`.

### Tarefa 18: painel comercial

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`
- Teste: `suite/backend/testes/modulos/comercial/test_painel.py`

**Interfaces:**
- Consome: `situacao_validade`, `obter_configuracao_comercial` (`faixas_valor`, `dias_alerta_validade`).
- Produz:
  - `Painel(por_estagio, conversao_geral, conversao_por_faixa: list[FaixaConversao(rotulo, decididas, aprovadas, taxa)], valor_aguardando, total_aprovado, ticket_medio, vencendo, vencidas, prazo_estourado, rs_m2_por_tipo: dict[str, float])`.
  - `PropostaResumo(id, numero, cliente_id, valor_referencia, vencimento, dias_restantes)`; `ContratoResumo(id, numero, proposta_id, previsao_entrega, dias_atraso)`.
  - `painel(sessao, ctx, hoje, desde: date | None = None) -> Painel`. Definições:
    - `por_estagio`: as 5 situações, com zero quando vazias.
    - Ganhas = `aprovada` + `entregue`; decididas = ganhas + `recusada`. `conversao_geral` = ganhas ÷ decididas, ou None.
    - Faixas pelos limites `[5000, 20000, 50000]`, que geram "até R$ 5 mil", "R$ 5 mil a 20 mil", "R$ 20 mil a 50 mil" e "acima de R$ 50 mil". Cada faixa é (mínimo exclusivo, máximo inclusivo], aplicada sobre `valor_referencia`.
    - `valor_aguardando` = Σ das `enviada`. `total_aprovado` = Σ `contrato.valor_total` das ganhas. `ticket_medio` = total ÷ nº de ganhas.
    - `vencendo` e `vencidas` vêm de `situacao_validade`.
    - `prazo_estourado`: contratos de propostas `aprovada` com `previsao_entrega < hoje`.
    - `rs_m2_por_tipo`: para contratos de propostas ganhas com `tipo_instalacao` e `area_m2 > 0`, Σ valor ÷ Σ área por tipo (média ponderada pela área).
    - `desde` filtra pelo `criado_em` da proposta.
  - Rota: `GET /painel?desde=` (`comercial.painel`).

- [ ] **Passo 1: escrever o teste que falha.** A fixture `cenario_painel` grava direto pelos repositórios do comercial, com hoje = 2026-11-08:

| proposta | situação | valor_referencia | outros |
|---|---|---|---|
| P1 | aprovada | 10 000 | contrato 10 000, VRF, 200 m², previsão de entrega 2026-11-01 |
| P2 | recusada | 15 000 | |
| P3 | entregue | 50 000 | contrato 50 000, VRF, 500 m² |
| P4 | enviada | 200 000 | envio 2026-10-27, validade 15 → vence 11/11 |
| P5 | rascunho | — | |
| P6 | enviada | 30 000 | envio 2026-10-01, validade 15 → vencida |

```python
def test_painel_do_cenario(sessao, ctx_admin, cenario_painel):
    p = painel(sessao, ctx_admin, date(2026, 11, 8))
    assert p.por_estagio == {"rascunho": 1, "enviada": 2, "aprovada": 1, "recusada": 1, "entregue": 1}
    assert p.conversao_geral == pytest.approx(2 / 3)
    assert [(f.decididas, f.aprovadas, f.taxa) for f in p.conversao_por_faixa] == [(0, 0, None), (2, 1, 0.5), (1, 1, 1.0), (0, 0, None)]
    assert (p.valor_aguardando, p.total_aprovado, p.ticket_medio) == pytest.approx((230_000, 60_000, 30_000))
    assert [(x.numero, x.dias_restantes) for x in p.vencendo] == [("P4", 3)] and [x.numero for x in p.vencidas] == ["P6"]
    assert [(c.proposta_id, c.dias_atraso) for c in p.prazo_estourado] == [(cenario_painel["P1"], 7)]
    assert p.rs_m2_por_tipo == pytest.approx({"vrf": 60_000 / 700})

def test_painel_isolado_por_empresa(...)   # outra empresa: tudo zerado
def test_painel_vazio(...)                 # conversões None, ticket None, somas 0, rs_m2_por_tipo {}
```

- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar e regenerar os tipos.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): painel comercial`.

### Tarefa 19: interface de calibração pelo HH apontado (para a T2)

**Arquivos:**
- Modificar: `propostas/orcamento/execucao.py`, `propostas/testes/test_execucao.py`; `comercial/esquemas.py`, `servico.py`
- Teste: `suite/backend/testes/modulos/comercial/test_calibracao.py`

**Interfaces:**
- Produz (motor): `sugerir_calibracao(amostras: list[dict]) -> list[dict]`. Cada amostra é `{"funcao", "hh_base", "hh_realizado"}`. A saída é `[{"funcao", "amostras", "fator_sugerido"}]`, ordenada por função. O fator é `round(mediana(realizado ÷ base), 3)`, e amostras com base ≤ 0 são ignoradas.
- Produz (serviço; porta de entrada da T2, sem rota HTTP nesta trilha):
  - `AmostraHH(contrato_id: UUID, funcao: str, hh_realizado ≥ 0)`; `SugestaoCalibracao(funcao, amostras, fator_sugerido, fator_atual: float | None)`.
  - `sugerir_calibracao_execucao(sessao, ctx, amostras) -> list[SugestaoCalibracao]`. A base vem de `contrato.hh_previsto_funcao_base[funcao]`. Contrato de outra empresa dá `NaoEncontrado`; função ausente no contrato é ignorada.
  - `aplicar_calibracao_execucao(sessao, ctx, sugestoes, minimo_amostras: int = 3) -> int`: grava `fator_calibracao` em todas as linhas de produtividade da função e devolve quantas mudou.
- A T2 soma `apontamento_hh` por contrato e função e chama estas funções. Não há tabela nova.

- [ ] **Passo 1: escrever os testes que falham.**

```python
def test_sugerir_calibracao_mediana():
    a = [{"funcao": "mecanico_refrigeracao", "hh_base": 96.1, "hh_realizado": 105.71},
         {"funcao": "mecanico_refrigeracao", "hh_base": 50, "hh_realizado": 60},
         {"funcao": "mecanico_refrigeracao", "hh_base": 40, "hh_realizado": 40},
         {"funcao": "ajudante", "hh_base": 20, "hh_realizado": 10}, {"funcao": "ajudante", "hh_base": 0, "hh_realizado": 5}]
    assert ex.sugerir_calibracao(a) == [{"funcao": "ajudante", "amostras": 1, "fator_sugerido": 0.5},
                                        {"funcao": "mecanico_refrigeracao", "amostras": 3, "fator_sugerido": 1.1}]
```

  No back-end:
  - `test_calibracao_pelo_contrato_de_referencia`: ajudante com 105,71 h sugere 1,1.
  - `test_aplicar_respeita_minimo`.
  - `test_aplicar_nao_acumula`: depois de aplicar, `hh_funcao_base` continua 96,1 e um novo contrato sugere de novo 1,1.
  - `test_contrato_de_outra_empresa_404`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.** Rode `cd propostas && python3 -m pytest -q testes` e `cd suite/backend && pytest testes/modulos/comercial -v`.
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): interface de calibração da produtividade pelo HH apontado`.

### Tarefa 20: front-end, cliente do comercial e lista de projetos

**Arquivos:**
- Modificar: `suite/frontend/src/api/cliente.ts` (acrescentar `baixar`), `src/api/tipos.ts` (apelidos dos esquemas do comercial), `src/App.tsx`, `src/componentes/Menu.tsx` (item "Comercial" com `comercial.ler`)
- Criar: `suite/frontend/src/api/comercial.ts`, `src/paginas/comercial/ProjetosPagina.tsx`, `SeloSituacao.tsx`, `NovoProjeto.tsx`
- Teste: `src/api/cliente.test.ts` (acrescentar), `src/paginas/comercial/ProjetosPagina.test.tsx`

**Interfaces:**
- Consome: `api`, `ErroApi`, `useSessao().pode`; as rotas das Tarefas 9–19.
- Produz:
  - `baixar(caminho: string, metodo = "GET", corpo?: unknown): Promise<{ blob: Blob; nome: string }>`: lê o nome do `Content-Disposition`, usa `credentials: "include"` e transforma erro em `ErroApi`.
  - `api/comercial.ts`, uma função por rota:
    - projetos: `listarPropostas(filtros)`, `criarProposta(corpo)`, `obterProposta(id)`, `alterarProposta(id, alt)`, `salvarDocumento(id, doc)`
    - itens: `listarItens(id)`, `criarItem(id, item)`, `alterarItem(itemId, alt)`, `removerItem(itemId)`
    - fluxo: `calcular(id)`, `gerarProposta(id)`, `listarRevisoes(id)`, `obterRevisao(revisaoId)`, `gerarContrato(id, revisaoId, opcaoId)`, `recusar(id, motivo)`, `entregar(id)`, `desfazerEntrega(id)`
    - downloads: `baixarXlsx(revisaoId)`, `baixarDocx(revisaoId, opcao)`, `baixarViabilidade(revisaoId)`, `baixarPdfProposta(revisaoId, opcao)`, `baixarPdfContrato(contratoId)`, `baixarRecibo(contratoId, corpo)`
    - tabelas: `obterCatalogo()`, `listarFuncoes()`, `criarFuncao`, `alterarFuncao`, `semearFuncoes()`, `listarProdutividade(item?)`, `criarProdutividade`, `alterarProdutividade`, `removerProdutividade`, `listarParametrosAbrava()`, `criarParametroAbrava(p)`
    - configuração e modelos: `obterConfiguracao()`, `alterarConfiguracao(alt)`, `obterModelo(doc)`, `salvarModelo(doc, secoes)`, `restaurarModelo(doc, chave?)`
    - outros: `obterPainel(desde?)`, `listarContratos()`, `obterContrato(id)`, `propostasDaObra(obraId)`
  - `SeloSituacao({ situacao, validade })` mostra "Rascunho", "Proposta enviada", "Aprovado", "Recusado" ou "Entregue", com um selo "Vencendo" (amarelo) ou "Vencida" (vermelho).
  - `ProjetosPagina` (`/comercial/projetos`) tem uma tabela com número, cliente, empreendimento, situação + validade, valor e data de envio, filtro por situação e paginação de 50. O botão "Novo projeto" (com `comercial.editar_proposta`) abre `NovoProjeto`, onde se escolhe o empreendimento e, opcionalmente, se importa o `.json` do app atual.
  - Rotas: `/comercial/projetos`, `/comercial/projetos/:id`, `/comercial/contratos/:id`, `/comercial/tabelas`, `/comercial/configuracao`, `/comercial/modelos`, `/comercial/painel`.

- [ ] **Passo 1: escrever os testes que falham.**
  - `"baixar lê o nome do Content-Disposition"`.
  - `"mostra selo Vencendo"`.
  - `"filtra por situação"`: chama `listarPropostas({situacao: "enviada"})`.
  - `"importar JSON envia o documento"`: `documento.numero === "PC-KTK-EX04/2026"`.
  - `"financeiro não vê Novo projeto"`.
  - `"mostra a mensagem do ErroApi"`: `numero_duplicado`.
- [ ] **Passo 2: rodar e ver falhar.** Rode `cd suite/frontend && npm test`.
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.** Rode `npm run lint && npm test && npm run build`.
- [ ] **Passo 5: commit.** Mensagem: `feat(frontend/comercial): cliente da API e lista de projetos`.

### Tarefa 21: editor de escopo, fornecimentos e preço

**Arquivos:**
- Criar: `src/paginas/comercial/ProjetoPagina.tsx` (abas), `AbaDadosGerais.tsx`, `AbaEscopo.tsx`, `FormularioServico.tsx`, `AbaFornecimentos.tsx`, `AbaPreco.tsx`
- Teste: `src/paginas/comercial/FormularioServico.test.tsx`, `AbaPreco.test.tsx`, `AbaDadosGerais.test.tsx`

**Interfaces:**
- Consome: `obterProposta`, `alterarProposta`, `salvarDocumento`, `obterCatalogo`, `calcular`.
- Produz:
  - `ProjetoPagina` mantém o documento em estado local, com "Salvar" e aviso de alterações não salvas. As abas são: Dados gerais, Escopo, Fornecimentos, Honorário ABRAVA (Tarefa 22), Execução (Tarefa 23), Preço, Proposta e contrato (Tarefa 24). Fora de `rascunho`/`enviada`, tudo fica somente leitura, exceto as observações internas.
  - `AbaDadosGerais` edita cliente, objeto, contexto (complexidade, documentação, acesso, urgência, risco, `dist_km`, `area_ref`), `validade_dias`, o RT (lista de `obter_empresa().responsaveis`) e as "Observações internas (não saem em nenhum documento)".
  - `AbaEscopo` trabalha por opção: nome, modalidade, fases com nome e cobrança (`fechado | hora | percentual | pacote | valor`, com os campos de cada uma), serviços do catálogo por fase e `fator_manual`, além de "Duplicar opção".
  - `FormularioServico({ servico, dados, onChange })` gera os campos de `servico.dados` pelo `tipo`: `int` e `float` viram campo numérico com `lerDecimal`; `opcoes`, seleção; `bool`, caixa.
  - `AbaFornecimentos` mostra a tabela de fornecimentos.
  - `AbaPreco` chama `calcular` e mostra, por opção: preço, fixo + estimado, horas, prazo, fases (cobrança e preço) e avisos.

- [ ] **Passo 1: escrever os testes que falham.**
  - `"FormularioServico gera campo numérico, seleção e caixa"`.
  - `"aceita 1,5 em campo float"`.
  - `"AbaPreco mostra R$ 44.921,49 e avisos"`.
  - `"observações internas salvam por alterarProposta, não por salvarDocumento"`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.** Moeda com `Intl.NumberFormat("pt-BR", {style: "currency", currency: "BRL"})`.
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(frontend/comercial): editor de escopo, fornecimentos e preço`.

### Tarefa 22: tela do honorário ABRAVA, ajustes da empresa e comparação com o HH

**Arquivos:**
- Criar: `src/paginas/comercial/AbaHonorarioAbrava.tsx`, `TabelaAmbientes.tsx`, `QuadroAjustes.tsx`, `ComparacaoMetodos.tsx`
- Teste: `src/paginas/comercial/AbaHonorarioAbrava.test.tsx`, `QuadroAjustes.test.tsx`

**Interfaces:**
- Consome: `salvarDocumento`, `calcular`, `listarParametrosAbrava` (tipos de ambiente do conjunto vigente), `obterConfiguracao`.
- Produz:
  - `AbaHonorarioAbrava({ proposta, opcaoId })` edita `documento.opcoes[i].projeto_abrava`: ativo, fase, tipo de instalação, escopo, prazo de entrega (dias) e "Usar este valor como preço da fase" (`adotar`).
  - `TabelaAmbientes` tem duas tabelas. Climatizados: tipo (lista do conjunto vigente, agrupada por `edificacao`), área m² e repetições, com a ajuda "use repetições só quando o projeto do ambiente é realmente o mesmo". Ventilados: tipo e área.
  - O resultado mostra área corrigida, TR estimada, custo base, P e honorário do método, com o selo "Método ABRAVA/DNPC — {fonte} {edicao}".
  - `QuadroAjustes` fica separado, com o título "Ajustes da empresa (fora do método)". Ele tem: nível do RT (padrão da empresa, sobrescrevível), inclui planilha (com %), adicional %, desconto %, custos extras (descrição + valor), valor final manual com a diferença e o botão "Voltar ao calculado", e o referencial de licitação.
  - `ComparacaoMetodos` mostra lado a lado o preço por HH da fase e o honorário final, com a diferença em R$ e em %.

- [ ] **Passo 1: escrever os testes que falham.**
  - `"mostra área corrigida 309,6 m² e honorário do método R$ 6.119,00"` (resultado simulado do caso 1).
  - `"QuadroAjustes rotula cada linha como Ajuste da empresa"`.
  - `"valor manual mostra diferença −R$ 1.847,60 e Voltar ao calculado limpa o campo"`.
  - `"comparação mostra +35,6% para 10.847,60 × 8.000,00"`.
  - `"sem parâmetros vigentes mostra o aviso para cadastrar a tabela"`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(frontend/comercial): honorário ABRAVA, ajustes da empresa e comparação com o HH`.

### Tarefa 23: tela de execução (itens, equipe, prazo e cronograma)

**Arquivos:**
- Criar: `src/paginas/comercial/AbaExecucao.tsx`, `TabelaItensExecucao.tsx`, `CronogramaFrentes.tsx`
- Teste: `src/paginas/comercial/AbaExecucao.test.tsx`, `CronogramaFrentes.test.tsx`

**Interfaces:**
- Consome: `listarItens`, `criarItem`, `alterarItem`, `removerItem`, `listarProdutividade`, `calcular`, `salvarDocumento`.
- Produz:
  - `AbaExecucao({ proposta, opcaoId })` mostra a configuração (fase, modo prazo-alvo ou equipe fixa, horas por dia, eficiência e a tabela de fatores editável), os itens e o resultado (HH por função, equipe, prazo em dias úteis e corridos, custo e preço da MO).
  - `TabelaItensExecucao` tem as colunas frente, item (valores distintos da produtividade), unidade, quantidade, altura, acesso, ocupação, turno, material R$/un e categoria.
  - `CronogramaFrentes({ cronograma })` mostra uma barra por frente, de `inicio` a `fim`, com a legenda dos dias por função.

- [ ] **Passo 1: escrever os testes que falham.**
  - `"mostra equipe 1/2/2 e 9 dias úteis (13 corridos)"`.
  - `"modo equipe fixa mostra pessoas por função"`.
  - `"equipe_incompleta destaca a função de detalhes.funcao"`.
  - `"CronogramaFrentes desenha Térreo 1–7 e Cobertura 8–9"`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(frontend/comercial): HH de execução, equipe e cronograma por frentes`.

### Tarefa 24: gerar proposta, revisões, gerar contrato e documentos

**Arquivos:**
- Criar: `src/paginas/comercial/AbaPropostaContrato.tsx`, `DialogoContrato.tsx`, `ContratoPagina.tsx`, `DialogoRecibo.tsx`
- Teste: `src/paginas/comercial/AbaPropostaContrato.test.tsx`, `ContratoPagina.test.tsx`

**Interfaces:**
- Consome: `gerarProposta`, `listarRevisoes`, `gerarContrato`, `recusar`, `entregar`, `desfazerEntrega`, os downloads, `obterContrato`, `baixarRecibo`.
- Produz:
  - `AbaPropostaContrato` mostra o histórico de propostas geradas (revisão, data, autor, versão do motor, preço por opção) e o histórico de situação, com os downloads por revisão: PDF e DOCX por opção, XLSX e viabilidade. Os botões dependem da situação:
    - rascunho e enviada: "Gerar proposta" (ou "Gerar nova revisão"). A situação muda para "Proposta enviada".
    - enviada: "Gerar contrato", que muda para "Aprovado", e "Recusar".
    - aprovada: "Marcar entregue" e "Ver contrato".
    - entregue: "Desfazer entrega".
  - `DialogoContrato` lista só as opções não internas da última revisão.
  - `ContratoPagina` mostra valores, prazo, previsão de entrega, condições por fase e marco e HH previsto, com os botões "Contrato (PDF)" e "Recibo (PDF)". O recibo pode ser do projeto inteiro ou por parcela (valor, referência e data).

- [ ] **Passo 1: escrever os testes que falham.**
  - `"enviada mostra Gerar contrato e Recusar, sem Marcar entregue"`.
  - `"gerar contrato envia a última revisão e a opção e navega"`.
  - `"opção interna fora do diálogo"`.
  - `"proposta_vencida sugere gerar nova revisão"`.
  - `"recibo por parcela envia valor, referência e data"`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(frontend/comercial): gerar proposta e contrato, revisões e documentos`.

### Tarefa 25: tabelas, configuração comercial e modelos de documento

**Arquivos:**
- Criar: `src/paginas/comercial/TabelasPagina.tsx`, `TabelaFuncoes.tsx`, `TabelaProdutividade.tsx`, `ParametrosAbrava.tsx`, `ConfiguracaoPagina.tsx`, `ModelosDocumentoPagina.tsx`
- Teste: `src/paginas/comercial/TabelasPagina.test.tsx`, `ConfiguracaoPagina.test.tsx`, `ModelosDocumentoPagina.test.tsx`

**Interfaces:**
- Consome: as funções de tabelas, configuração e modelos de `api/comercial.ts`.
- Produz:
  - `TabelaFuncoes`: custo-hora calculado e "Criar funções padrão".
  - `TabelaProdutividade`: fonte obrigatória; unidade `m2/m/un/kW`, com a ajuda "Potência em kW".
  - `ParametrosAbrava`: histórico de conjuntos com selo no vigente e formulário de um novo conjunto (tipos de ambiente, pesos, fator de repetição, ventilação, densidade, FS, região, custo por TR por tipo, pontos da curva, fatores de escopo, piso, fonte, edição, seção/tabela, edição superada). O aviso fixo diz: "Valores da Metodologia ABRAVA/DNPC: dados privados da empresa."
  - `ConfiguracaoPagina` (`comercial.configurar`) tem: fatores por nível do RT e o nível padrão, adicional por planilha, fator de licitação, salário mínimo vigente, validade padrão, dias de alerta e faixas do painel. Todos sob o título "Ajustes da empresa".
  - `ModelosDocumentoPagina`: escolha do documento; seções com título e texto; mover para cima e para baixo; "Nova seção/cláusula"; "Restaurar padrão" por seção e do documento, com confirmação; lista de variáveis clicáveis que inserem `$variavel` no cursor.
  - A escrita fica desabilitada sem a permissão.

- [ ] **Passo 1: escrever os testes que falham.**
  - `"custo-hora 27,00 para 15,00 e 80%"`.
  - `"comercial vê produtividade mas não edita"`.
  - `"novo conjunto ABRAVA exige fonte e edição"`.
  - `"configuração salva fator sênior 1,40"`.
  - `"mover seção para cima envia a nova ordem"`.
  - `"restaurar padrão chama restaurarModelo com a chave"`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(frontend/comercial): tabelas, configuração comercial e modelos de documento`.

### Tarefa 26: tela do painel comercial

**Arquivos:**
- Criar: `src/paginas/comercial/PainelPagina.tsx`
- Teste: `src/paginas/comercial/PainelPagina.test.tsx`

**Interfaces:**
- Consome: `obterPainel(desde?)`.
- Produz: a tela tem, em ordem:
  1. Cartões: aguardando resposta, total aprovado, ticket médio, conversão geral.
  2. Barras por estágio.
  3. Conversão por faixa de valor ("—" quando nula).
  4. Listas "Vencendo (7 dias)", "Vencidas" e "Entregas atrasadas", com links.
  5. Tabela "R$/m² médio por tipo de instalação (contratos aprovados)".
  6. Filtro "desde".

  Percentuais com uma casa decimal. Quando vazio, aparece "Nenhum projeto no período".

- [ ] **Passo 1: escrever os testes que falham.**
  - `"conversão 66,7% e ticket R$ 30.000,00"` (cenário da Tarefa 18).
  - `"faixa sem decididas mostra —"`.
  - `"P4 em Vencendo com 3 dias"`.
  - `"VRF R$ 85,71/m²"`.
  - `"vazio mostra a mensagem"`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(frontend/comercial): painel comercial`.

### Tarefa 27: ponta a ponta (Playwright) e verificação dos critérios de pronto

**Arquivos:**
- Criar: `suite/frontend/e2e/comercial.spec.ts`. Se `entrar` e `sair` estiverem dentro de `cadastro.spec.ts`, mova-os para `e2e/apoio.ts` e importe nos dois arquivos.

**Interfaces:**
- Consome: os usuários de demonstração da T0 e todas as telas das Tarefas 20–26.

- [ ] **Passo 1: escrever os testes.**
  - `"obra de referência: do projeto ao recibo"`:
    1. `admin@demo-a.local` cria as funções e a produtividade do caso de referência e um RT.
    2. `comercial@demo-a.local` cria o projeto num empreendimento, lança os 3 itens e define o prazo-alvo de 10 dias.
    3. Confere "Equipe 1 · 2 · 2", "9 dias úteis" e "R$ 44.921,49".
    4. Clica em "Gerar proposta", e o selo passa a "Proposta enviada".
    5. Clica em "Gerar contrato" para a opção A, e o selo passa a "Aprovado".
    6. Baixa o PDF do contrato e o recibo de 30%.
    7. Clica em "Marcar entregue" e depois em "Desfazer entrega".
    8. O painel mostra "Total aprovado R$ 44.921,49".
  - `"exemplo importado dá o mesmo preço"`: importa `propostas/exemplos/nr13_inspecao.json` e confere "R$ 29.069,38".
  - `"financeiro vê o painel e não gera proposta"`.
- [ ] **Passo 2: rodar e ver falhar.** Suba a pilha da T0 (`docker compose ... up -d --build && bash suite/infra/fumaca.sh`) e rode `cd suite/frontend && BASE_URL=http://localhost:8080 npm run e2e`.
- [ ] **Passo 3: corrigir o que faltar.** Normalmente são `data-testid`, permissões ou entradas do `mundo`.
- [ ] **Passo 4: verificação final.** Todos estes comandos precisam passar:
  - `cd propostas && python3 -m pytest -q testes` (o caso oficial ABRAVA aparece como `skipped`)
  - `cd suite/backend && ruff check . && ruff format --check . && alembic check && pytest`
  - `cd suite/frontend && npm run lint && npm test && npm run build && npm run e2e`

  Os critérios de pronto são cobertos por `test_exemplos_dao_o_mesmo_preco_pela_api` e `test_obra_de_referencia_pela_api`.
- [ ] **Passo 5: commit.** Mensagem: `test(comercial): ponta a ponta do projeto ao recibo`.
