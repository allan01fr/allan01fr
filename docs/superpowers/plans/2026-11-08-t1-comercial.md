# T1 Comercial: plano de implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para executar este plano tarefa por tarefa. Os passos usam caixas de seleção (`- [ ]`) para acompanhamento.

**Objetivo:** fazer proposta, HH de execução, equipe, prazo, preço, contrato, documentos e painel comercial pela web. O preço vem do motor `propostas/orcamento`, que a suíte instala como pacote e não copia.

**Arquitetura:** a parte nova de cálculo (HH de execução, equipe e prazo, preço de obra, honorário pelo método área, calibração) entra no pacote `orcamento` como módulos puros: `execucao.py`, `honorario_area.py` e `erros.py`. O módulo `suite/backend/app/modulos/comercial` segue o fluxo `rotas.py → esquemas.py → servico.py → repositorio.py → modelos.py`. Ele só monta as entradas, chama o motor e grava. Toda revisão enviada fica congelada, com entradas, resultado, versão do motor e normas (regra 7). O front-end React tem as telas do módulo em `suite/frontend/src/modulos/comercial`.

**Tecnologias:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (sessão síncrona), Alembic, PostgreSQL 16, WeasyPrint + Jinja2 (PDF), num2words (valor por extenso), openpyxl/python-docx (já usados pelo motor), React + TypeScript + Vite, Vitest + Testing Library, Playwright.

**Especificação:** `docs/superpowers/specs/2026-11-08-suite-hvacr-design.md` (seções 3, 4, 5 linha `comercial`, 6 T1). Requisitos adicionais do usuário, recebidos pelo coordenador em 2026-11-08: método área ABRAVA/DNPC, fluxo de situação, PDFs com identidade e painel comercial. Estão incorporados nas Tarefas 5, 8, 11, 12, 14, 15, 16 e 19–23.

## Restrições globais

- Python `>=3.12`. O motor `orcamento` continua rodando os seus testes com o Python local: `cd propostas && python3 -m pytest -q testes` precisa passar ao fim de cada tarefa (hoje são 155 testes).
- O motor não é copiado para `suite/`. Ele é instalado em modo editável (`pip install -e propostas`), porque os módulos acham `dados/` e `modelos/` pelo caminho do pacote (`RAIZ = pasta acima de orcamento/`).
- Toda tabela do comercial tem `empresa_id` não nulo. As consultas passam pelo repositório base da T0, que filtra por empresa (regra 2).
- Só o comercial grava nas tabelas `proposta`, `proposta_revisao`, `item_execucao`, `produtividade`, `funcao`, `contrato`, `parametro_honorario_area` e `texto_documento`. Os outros módulos leem pelo `comercial/servico.py` (regra 1). O comercial lê o cadastro só pelo `cadastro/servico.py`.
- Perfis: `admin`, `engenharia`, `comercial`, `financeiro`, `campo`. A matriz do comercial está nesta seção, em "Matriz de perfis".
- Erro: `{"codigo": "...", "mensagem": "...", "detalhes": {...}}`, com mensagens em português (regra 4).
- Unidades na API e no banco: `m2`, `m`, `un`, `kW` (regra 5). Não existe item em TR nem em Btu/h. A potência é sempre em kW.
- Rastreabilidade (regra 7): cada revisão guarda `versao_motor = orcamento.__version__`, `entradas`, `resultado`, `normas` e `emitida_em`. Revisão não se altera; mudança gera revisão nova.
- Parâmetros de tabela de honorários (ABRAVA/DNPC) e de norma ficam como dados privados por empresa, com fonte, edição e seção/tabela (regra 9). Nenhum valor real de tabela entra no repositório. Nos testes, os valores são marcados `# FICTÍCIO`.
- Datas: "hoje" é `orcamento.parametros.hoje()` (horário de Brasília). As funções de serviço que dependem da data recebem `hoje: date` como parâmetro.
- Qualidade: ruff limpo, um assunto por arquivo, legível por um júnior, o mesmo fluxo para o mesmo tipo de trabalho (seção 8).

### Matriz de perfis (constantes em `comercial/rotas.py`)

| Constante | Perfis | Rotas |
|---|---|---|
| `LEITURA` | admin, engenharia, comercial, financeiro | todos os `GET` de propostas, revisões, contratos, catálogo, tabelas, textos e documentos |
| `ESCRITA_PROPOSTA` | admin, comercial | criar/editar proposta e itens, enviar, aprovar, recusar, entregar, desfazer entrega |
| `CALCULO` | admin, comercial, engenharia | `POST /propostas/{id}/calculo` |
| `TABELAS` | admin, engenharia | escrita em funções, produtividade e parâmetros do método área |
| `TEXTOS` | admin, comercial | escrita e restauração dos textos de documento |
| `PAINEL_RECIBO` | admin, comercial, financeiro | `GET /painel`, `POST /contratos/{id}/recibo.pdf` |

O perfil `campo` não acessa nada no comercial.

## Interfaces esperadas da T0

O plano da T0 (`docs/superpowers/plans/2026-11-08-t0-fundacao.md`) não existia quando este plano foi escrito. Antes da Tarefa 6, o executor compara a lista abaixo com o que a T0 entregou. Se algum nome for diferente, ele usa o nome da T0 em todo o plano, com uma tabela de troca no commit da Tarefa 6. A semântica não muda.

Back-end (`suite/backend/app/`):

| Interface | Uso na T1 |
|---|---|
| `nucleo/banco.py`: `Base` (DeclarativeBase); `obter_sessao() -> Iterator[Session]` (dependência FastAPI, sessão síncrona, commit no fim da requisição); mixin `ModeloEmpresa` com `id: Mapped[int]` (PK), `empresa_id: Mapped[int]` (FK `empresa.id`, não nulo, indexado), `criado_em: Mapped[datetime]` | modelos e rotas |
| `nucleo/repositorio.py`: `class RepositorioEmpresa(Generic[M])` com atributo de classe `modelo`, `__init__(self, sessao: Session, empresa_id: int)`, `consulta() -> Select` (já filtrada), `obter(id: int) -> M` (lança `NaoEncontrado`), `listar(*condicoes) -> list[M]`, `adicionar(obj: M) -> M` (preenche `empresa_id` e faz flush), `remover(obj: M) -> None` | repositórios |
| `nucleo/perfis.py`: `class Perfil(StrEnum)` (`ADMIN="admin"`, `ENGENHARIA`, `COMERCIAL`, `FINANCEIRO`, `CAMPO`); `@dataclass UsuarioAtual(id: int, empresa_id: int, perfis: frozenset[Perfil])`; `exigir_perfis(*perfis: Perfil) -> Callable[..., UsuarioAtual]` (dependência: 401 sem sessão, 403 sem perfil) | todas as rotas |
| `nucleo/erros.py`: `class ErroDominio(Exception)` com `__init__(self, codigo: str, mensagem: str, detalhes: dict | None = None)` e atributo `status`; `NaoEncontrado` (404), `Conflito` (409), `RegraViolada` (422); tratador global que gera o formato da regra 4 | serviço |
| `nucleo/empresa.py`: `obter_identidade(sessao, empresa_id) -> IdentidadeEmpresa` com `razao_social`, `cnpj`, `endereco`, `telefone`, `email`, `logo: bytes | None`, `rt_nome`, `rt_titulo`, `rt_registro` (ex.: "CREA-RJ 123456/D"), `rt_assinatura: bytes | None` | PDFs (Tarefa 15) |
| `modulos/cadastro/servico.py`: `obter_cliente(sessao, empresa_id, cliente_id) -> ClienteLido(id, razao_social, cnpj_cpf, cidade, uf)`; `obter_obra(sessao, empresa_id, obra_id) -> ObraLida(id, cliente_id, nome, endereco, uf)`; ambos lançam `NaoEncontrado` | proposta, contrato |
| `app/main.py`: `criar_app() -> FastAPI`, que inclui os roteadores dos módulos | a T1 inclui `comercial.rotas.roteador` com prefixo `/api/comercial` |
| `migracoes/` (Alembic) em `suite/backend/migracoes/`; testes em `suite/backend/testes/` | Tarefa 6 |
| `testes/conftest.py`: fixtures `sessao` (transação desfeita no fim), `empresa_a`, `empresa_b` (ids), `cliente_como(perfil: Perfil, empresa_id: int) -> TestClient`, `criar_cliente(empresa_id) -> int`, `criar_obra(empresa_id, cliente_id, uf="RJ") -> int`, `definir_identidade(empresa_id, **campos)` | testes |
| `testes/test_arquitetura.py`: falha quando um módulo importa `modelos`/`repositorio` de outro | vale para a T1 sem mudança |
| Dependências instaladas por `suite/backend/requirements.txt`; imagem `suite/infra/Dockerfile.api` com contexto na raiz do repositório | Tarefas 1 e 15 |

A árvore da seção 3 da especificação desenha `migracoes/` e `testes/` dentro de `plugin-bonsai/`. Isso é erro de indentação. Este plano usa `suite/backend/migracoes/` e `suite/backend/testes/`.

Front-end (`suite/frontend/src/`):

| Interface | Uso |
|---|---|
| `nucleo/api.ts`: `api<T>(metodo: "GET"|"POST"|"PUT"|"DELETE", caminho: string, corpo?: unknown): Promise<T>`; `baixar(caminho: string, metodo?: string, corpo?: unknown): Promise<Blob>`; `class ErroApi extends Error { codigo; mensagem; detalhes; status }` | cliente do comercial |
| `nucleo/usuario.ts`: `usePerfis(): Perfil[]` | esconder botões sem permissão |
| `rotas.tsx`: lista `ROTAS_MODULOS` à qual o módulo acrescenta as suas rotas; `nucleo/menu.ts`: lista `ITENS_MENU` | navegação |
| `testes/renderizar.tsx`: `renderizar(ui, { perfis, rota })` | testes de componente |
| `e2e/apoio.ts`: `entrarComo(page, perfil)`, `semearEmpresa(request) -> { empresaId, clienteId, obraId }` | Playwright |

## Caso de referência (obra), conferido à mão

Este caso é usado pelos testes das Tarefas 2, 3, 4, 10 e 24. Ele usa três itens, três funções e duas frentes, com horas por dia = 8 e eficiência = 0,8.

Fatores padrão (`FATORES_PADRAO`, valores iniciais a confirmar pela engenharia KAPTEK; são dados da empresa, não de norma):

| Fator | Opções → multiplicador |
|---|---|
| altura | `ate_3m` 1,00 · `de_3_a_6m` 1,15 · `acima_6m` 1,30 |
| acesso | `livre` 1,00 · `restrito` 1,15 · `confinado` 1,30 |
| ocupacao | `desocupado` 1,00 · `ocupado` 1,20 |
| turno | `diurno` 1,00 · `noturno` 1,25 |

Funções (custo-hora com encargos = salário-hora × (1 + encargos)):

| Função | salário-hora | encargos | custo-hora |
|---|---|---|---|
| `encarregado` | 40,00 | 0,80 | 72,00 |
| `mecanico_refrigeracao` | 30,00 | 0,80 | 54,00 |
| `ajudante` | 15,00 | 0,80 | 27,00 |

Produtividade (hh por unidade; fonte "caso de referência T1"):

| item (unidade) | encarregado | mecânico | ajudante |
|---|---|---|---|
| `duto_m2` (m2) | 0,05 | 0,40 | 0,40 |
| `linha_frigorifica_m` (m) | 0,02 | 0,30 | 0,30 |
| `evaporadora_un` (un) | 0,50 | 4,00 | 4,00 |

Itens:

| # | frente | item | qtd | altura | acesso | ocupação | turno | fator | material R$/un (categoria) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Térreo | duto_m2 | 100 | de_3_a_6m | livre | ocupado | diurno | 1,15×1,20 = 1,38 | 120,00 (material) |
| 2 | Térreo | linha_frigorifica_m | 50 | ate_3m | livre | ocupado | noturno | 1,20×1,25 = 1,50 | 85,00 (material) |
| 3 | Cobertura | evaporadora_un | 4 | ate_3m | restrito | desocupado | diurno | 1,15 | 3 500,00 (equipamento) |

HH = quantidade × hh/unidade × fator × calibração (calibração = 1):

| | encarregado | mecânico | ajudante |
|---|---|---|---|
| item 1 | 100×0,05×1,38 = 6,90 | 100×0,40×1,38 = 55,20 | 55,20 |
| item 2 | 50×0,02×1,50 = 1,50 | 50×0,30×1,50 = 22,50 | 22,50 |
| item 3 | 4×0,50×1,15 = 2,30 | 4×4,00×1,15 = 18,40 | 18,40 |
| **total** | **10,70** | **96,10** | **96,10** (soma 202,90) |
| frente Térreo | 8,40 | 77,70 | 77,70 |
| frente Cobertura | 2,30 | 18,40 | 18,40 |

Modo "prazo" (prazo-alvo 10 dias úteis): capacidade por pessoa = 8 × 10 × 0,8 = 64 h. Encarregado ⌈10,7/64⌉ = 1. Mecânico ⌈96,1/64 = 1,50⌉ = 2. Ajudante = 2.
Cronograma com equipe (1, 2, 2), frentes em sequência, dias da frente = máx. por função de ⌈HH ÷ (8 × pessoas × 0,8)⌉:
- Térreo: encarregado ⌈8,4/6,4⌉ = 2; mecânico ⌈77,7/12,8 = 6,07⌉ = 7; ajudante 7. A frente leva **7 dias** (dias 1–7).
- Cobertura: encarregado ⌈2,3/6,4⌉ = 1; mecânico ⌈18,4/12,8 = 1,44⌉ = 2; ajudante 2. A frente leva **2 dias** (dias 8–9).
- Prazo = **9 dias úteis**, e 9 ≤ 10, então não há aviso. Dias corridos = ⌈9 × 7/5⌉ = **13**.

Modo "equipe" (equipe fixa: encarregado 1, mecânico 3, ajudante 3):
- Térreo: mecânico ⌈77,7/19,2 = 4,05⌉ = 5; encarregado 2. A frente leva 5 dias.
- Cobertura: ⌈18,4/19,2⌉ = 1. A frente leva 1 dia.
- Prazo = **6 dias úteis**.

Preço de obra, pelo motor (BDI padrão de `dados/parametros.json`: `mo_execucao` 0,22, `material` 0,14, `equipamento` 0,14):
- MO = 10,7×72 + 96,1×54 + 96,1×27 = 770,40 + 5 189,40 + 2 594,70 = **8 554,50** → preço 8 554,50 × 1,22 = **10 436,49**.
- Materiais e equipamentos = 12 000,00 + 4 250,00 + 14 000,00 = **30 250,00** → preço × 1,14 = **34 485,00**.
- A proposta tem uma opção A com uma fase F1 de escopo fechado, sem serviços de engenharia. Preço da opção = **44 921,49**. O motor dá a etapa `obra` com 9 dias úteis e 13 corridos e o pagamento padrão 30% + 70%. Isso foi conferido rodando `motor.precificar` com esses fornecimentos.

## Preços de referência dos exemplos (motor atual, conferidos com `python -m orcamento.cli`)

| arquivo | opção → preço |
|---|---|
| `hvac_consultoria_2d_3d_bim.json` | A 55 672,13 · B 96 243,17 · C 140 048,50 |
| `hvac_retrofit_fases.json` | A 138 637,75 · B 125 937,62 · E 1 163 417,61 (estimativa interna) |
| `nr13_inspecao.json` | A 29 069,38 |
| `spci_projeto.json` | A 21 622,49 · B 32 069,63 |

## Foco de revisão

1. **Arredondamento de pessoas e dias com ponto flutuante.** Quando HH ÷ capacidade dá um inteiro exato (ex.: 64 h com capacidade de 64 h), o resultado é 1 pessoa, não 2. Regra: `math.ceil(round(x, 9))`. O teste fica na Tarefa 3.
2. **Equipe fixa sem uma função que tem HH.** O sistema responde 422 `equipe_incompleta` com a função em `detalhes`. Não pode dar divisão por zero nem prazo infinito. O teste fica nas Tarefas 3 e 10.
3. **Item sem produtividade na empresa,** mas com produtividade em outra empresa. O sistema responde 422 `item_sem_produtividade` e não usa nem revela a tabela alheia. O teste fica na Tarefa 10.
4. **Revisão antiga e proposta vencida.** Aprovar uma revisão que não é a última responde 409 `revisao_desatualizada`. Aprovar uma proposta vencida responde 409 `proposta_vencida`. Mudar produtividade ou catálogo depois do envio não altera a revisão nem a sua planilha. Os testes ficam nas Tarefas 11, 12 e 13.
5. **JSON antigo do app Streamlit** (sem `fases`, com `modelo_preco`). Importado pela API, ele dá o mesmo preço da CLI, porque passa por `proposta.completar`. Um serviço inexistente no catálogo responde 422 `documento_invalido`, sem erro 500. Os testes ficam nas Tarefas 9 e 10.

---

### Tarefa 1: pacote `orcamento` instalável

**Arquivos:**
- Criar: `propostas/pyproject.toml`
- Modificar: `propostas/orcamento/__init__.py` (acrescentar `__version__`)
- Modificar: `propostas/README.md` (seção curta "Como pacote")
- Teste: `propostas/testes/test_pacote.py`
- Modificar: `suite/backend/requirements.txt` (linha `-e ../../propostas`), `suite/infra/Dockerfile.api` (`COPY propostas /src/propostas` e `pip install -e /src/propostas`)

**Interfaces:**
- Produz: `orcamento.__version__ = "1.0.0"`; distribuição `kaptek-orcamento` que expõe o pacote `orcamento` sem `app/` nem `testes/`.

- [ ] **Passo 1: escrever os testes que falham**

```python
# propostas/testes/test_pacote.py
import os, subprocess, sys, venv
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

- [ ] **Passo 2: rodar e ver falhar**

Rode `cd propostas && python3 -m pytest -q testes/test_pacote.py`. Resultado esperado: FAIL com `AttributeError: module 'orcamento' has no attribute '__version__'`.

- [ ] **Passo 3: criar `pyproject.toml` e `__version__`**

Use setuptools (`>=68`). Valores: `name = "kaptek-orcamento"`, `requires-python = ">=3.12"`, `dynamic = ["version"]` com `[tool.setuptools.dynamic] version = {attr = "orcamento.__version__"}`, `[tool.setuptools] packages = ["orcamento"]`, `dependencies = ["openpyxl>=3.1,<4", "python-docx>=1.1,<2"]` e `[project.optional-dependencies] referencias = ["pdfplumber>=0.11,<0.12"]`. Não altere `requirements.txt` nem `app/requirements.txt`, porque `test_requisitos_da_nuvem_acompanham_os_locais` compara os dois. No README, diga que o pacote se instala só em modo editável, porque `dados/` e `modelos/` ficam fora do pacote.

- [ ] **Passo 4: rodar todos os testes do motor**

Rode `cd propostas && python3 -m pytest -q testes`. Resultado esperado: `157 passed`.

- [ ] **Passo 5: commit**

```bash
git add propostas/pyproject.toml propostas/orcamento/__init__.py propostas/README.md propostas/testes/test_pacote.py suite/backend/requirements.txt suite/infra/Dockerfile.api
git commit -m "build(orcamento): instalável como pacote kaptek-orcamento (modo editável)"
```

### Tarefa 2: HH de execução (`orcamento/execucao.py`)

**Arquivos:**
- Criar: `propostas/orcamento/erros.py`, `propostas/orcamento/execucao.py`
- Teste: `propostas/testes/test_execucao.py`

**Interfaces:**
- Produz (`erros.py`): `class ErroEntrada(ValueError)` com `__init__(self, codigo: str, mensagem: str, detalhes: dict | None = None)` e atributos `codigo`, `mensagem`, `detalhes`.
- Produz (`execucao.py`):
  - `FUNCOES_PADRAO: dict[str, str]` = `{"encarregado": "Encarregado", "mecanico_refrigeracao": "Mecânico de refrigeração", "ajudante": "Ajudante", "soldador": "Soldador", "eletricista": "Eletricista", "tecnico_tab": "Técnico de TAB"}`
  - `UNIDADES_ITEM = ("m2", "m", "un", "kW")`
  - `ITENS_SUGERIDOS: dict[str, str]` = `{"duto_m2": "m2", "linha_frigorifica_m": "m", "evaporadora_un": "un", "condensadora_un": "un", "capacidade_kw": "kW", "ponto_eletrico_un": "un", "difusor_un": "un"}`
  - `FATORES_PADRAO: dict[str, dict[str, float]]`: a tabela do caso de referência, com as chaves `altura`, `acesso`, `ocupacao`, `turno`
  - `config_padrao(fase: str = "F1") -> dict`, que devolve `{"fase": fase, "modo": "prazo", "prazo_alvo_dias": 20, "equipe": {}, "horas_dia": 8.0, "eficiencia": 0.8, "fatores": deepcopy(FATORES_PADRAO)}`
  - Item (dict): `{"id": str, "frente": str, "item": str, "unidade": str, "descricao": str, "quantidade": float, "altura": str, "acesso": str, "ocupacao": str, "turno": str, "custo_material_unit": float, "categoria_material": "material"|"equipamento"}`
  - Produtividade (dict): `{"item": str, "funcao": str, "hh_por_unidade": float, "fator_calibracao": float, "fonte": str}`
  - `fator_item(fatores: dict, item: dict) -> tuple[float, dict[str, float]]`
  - `hh_execucao(itens: list[dict], produtividade: list[dict], fatores: dict) -> dict`, que devolve `{"linhas": [{"item_id", "frente", "item", "funcao", "quantidade", "hh_por_unidade", "fator", "fator_calibracao", "hh_base", "hh"}], "hh_funcao": {funcao: hh}, "hh_funcao_base": {funcao: hh sem calibração}, "hh_frente_funcao": {frente: {funcao: hh}}, "frentes": [frentes na ordem da primeira aparição], "total_hh": float}`

Fórmula: `hh_base = quantidade × hh_por_unidade × Π fatores do item`, `hh = hh_base × fator_calibracao`. O item gera uma linha para cada função que tem produtividade nele.

- [ ] **Passo 1: escrever os testes que falham.** Use as constantes `FATORES`, `PRODUTIVIDADE_REF` e `ITENS_REF` do caso de referência, no topo do arquivo de teste.

```python
def test_fator_item_multiplica_os_quatro_fatores():
    fator, det = ex.fator_item(ex.FATORES_PADRAO, ITENS_REF[0])
    assert fator == pytest.approx(1.38)
    assert det == {"altura": 1.15, "acesso": 1.0, "ocupacao": 1.2, "turno": 1.0}

def test_hh_do_caso_de_referencia():
    r = ex.hh_execucao(ITENS_REF, PRODUTIVIDADE_REF, ex.FATORES_PADRAO)
    assert r["hh_funcao"] == pytest.approx({"encarregado": 10.7, "mecanico_refrigeracao": 96.1, "ajudante": 96.1})
    assert r["total_hh"] == pytest.approx(202.9)
    assert r["frentes"] == ["Térreo", "Cobertura"]
    assert r["hh_frente_funcao"]["Térreo"] == pytest.approx({"encarregado": 8.4, "mecanico_refrigeracao": 77.7, "ajudante": 77.7})
    assert len(r["linhas"]) == 9

def test_calibracao_multiplica_hh_mas_nao_o_base():
    prod = [{**p, "fator_calibracao": 1.1} if p["funcao"] == "ajudante" else p for p in PRODUTIVIDADE_REF]
    r = ex.hh_execucao(ITENS_REF, prod, ex.FATORES_PADRAO)
    assert r["hh_funcao"]["ajudante"] == pytest.approx(105.71)
    assert r["hh_funcao_base"]["ajudante"] == pytest.approx(96.1)

@pytest.mark.parametrize("alteracao, codigo", [
    ({"item": "inexistente"}, "item_sem_produtividade"),
    ({"quantidade": -1}, "quantidade_negativa"),
    ({"altura": "no_teto"}, "fator_desconhecido"),
])
def test_entradas_invalidas(alteracao, codigo):
    with pytest.raises(ErroEntrada) as e:
        ex.hh_execucao([{**ITENS_REF[0], **alteracao}], PRODUTIVIDADE_REF, ex.FATORES_PADRAO)
    assert e.value.codigo == codigo
```

- [ ] **Passo 2: rodar e ver falhar.** Rode `cd propostas && python3 -m pytest -q testes/test_execucao.py`. Resultado esperado: FAIL com `ModuleNotFoundError: orcamento.execucao`.
- [ ] **Passo 3: implementar `erros.py` e `execucao.py`.** Faça só as constantes e as funções acima. A docstring do módulo traz as fórmulas e o caminho do caso de referência. Em `detalhes`, os erros levam `{"item": ...}` ou `{"fator": ..., "valor": ...}`.
- [ ] **Passo 4: rodar e ver passar.** Rode o mesmo comando. Resultado esperado: PASS. Depois rode `python3 -m pytest -q testes` (todos passam).
- [ ] **Passo 5: commit.** Rode `git add propostas/orcamento/erros.py propostas/orcamento/execucao.py propostas/testes/test_execucao.py && git commit -m "feat(orcamento): HH de execução por função com fatores e calibração"`.

### Tarefa 3: equipe, prazo e cronograma por frentes

**Arquivos:**
- Modificar: `propostas/orcamento/execucao.py`
- Teste: `propostas/testes/test_execucao.py`

**Interfaces:**
- Consome: `hh_execucao` (Tarefa 2).
- Produz:
  - `dimensionar_equipe(hh_funcao: dict[str, float], horas_dia: float, prazo_dias: int, eficiencia: float) -> dict[str, int]`: calcula `n = ceil(round(HH ÷ (horas_dia × prazo_dias × eficiencia), 9))` quando HH > 0. Quando HH = 0, n = 0.
  - `cronograma_frentes(hh_frente_funcao: dict, frentes: list[str], equipe: dict[str, int], horas_dia: float, eficiencia: float) -> list[dict]`: cada elemento é `{"frente", "dias_uteis", "inicio", "fim", "dias_funcao": {funcao: int}}`. Os dias de cada função são `ceil(round(HH ÷ (horas_dia × pessoas × eficiencia), 9))`, e a frente leva o máximo deles. As frentes correm em sequência na ordem de `frentes`, e a primeira começa no dia 1. A função lança `ErroEntrada("equipe_incompleta", ..., {"funcao": f})` quando uma função tem HH > 0 e 0 pessoas.
  - `planejar_execucao(itens: list[dict], produtividade: list[dict], config: dict) -> dict`: devolve o resultado de `hh_execucao` mais `{"modo", "equipe", "cronograma", "prazo_dias_uteis", "prazo_dias_corridos", "avisos": list[str]}`. No modo `"prazo"`, a equipe vem de `dimensionar_equipe` com `prazo_alvo_dias`. No modo `"equipe"`, a equipe vem de `config["equipe"]`. Dias corridos = `ceil(dias_uteis × 7 / 5)`, como em `motor.cronograma`. Se `prazo_dias_uteis > prazo_alvo_dias` no modo prazo, entra o aviso `"O cronograma por frentes dá {n} dias úteis, acima do prazo-alvo de {alvo}, pelo arredondamento de cada frente."`. A função valida `horas_dia > 0`, `0 < eficiencia <= 1`, `prazo_alvo_dias >= 1` e equipe inteira `>= 0`; fora disso lança `ErroEntrada("parametro_invalido", ..., {"campo": nome})`. Sem itens, devolve HH 0, equipe `{}`, cronograma `[]` e prazo 0.

- [ ] **Passo 1: escrever os testes que falham**

```python
def test_equipe_no_modo_prazo_do_caso_de_referencia():
    cfg = {**ex.config_padrao(), "prazo_alvo_dias": 10}
    p = ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, cfg)
    assert p["equipe"] == {"encarregado": 1, "mecanico_refrigeracao": 2, "ajudante": 2}
    assert [(c["frente"], c["dias_uteis"], c["inicio"], c["fim"]) for c in p["cronograma"]] == [("Térreo", 7, 1, 7), ("Cobertura", 2, 8, 9)]
    assert (p["prazo_dias_uteis"], p["prazo_dias_corridos"], p["avisos"]) == (9, 13, [])

def test_prazo_ao_contrario_com_equipe_fixa():
    cfg = {**ex.config_padrao(), "modo": "equipe", "equipe": {"encarregado": 1, "mecanico_refrigeracao": 3, "ajudante": 3}}
    p = ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, cfg)
    assert [c["dias_uteis"] for c in p["cronograma"]] == [5, 1]
    assert p["prazo_dias_uteis"] == 6

def test_divisao_exata_nao_soma_uma_pessoa():
    assert ex.dimensionar_equipe({"ajudante": 64.0}, 8, 10, 0.8) == {"ajudante": 1}
    assert ex.dimensionar_equipe({"ajudante": 0.0}, 8, 10, 0.8) == {"ajudante": 0}

def test_equipe_fixa_sem_funcao_com_hh():
    cfg = {**ex.config_padrao(), "modo": "equipe", "equipe": {"encarregado": 1, "mecanico_refrigeracao": 3}}
    with pytest.raises(ErroEntrada) as e:
        ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, cfg)
    assert (e.value.codigo, e.value.detalhes) == ("equipe_incompleta", {"funcao": "ajudante"})

def test_aviso_quando_arredondamento_por_frente_passa_do_alvo():
    cfg = {**ex.config_padrao(), "prazo_alvo_dias": 8}
    p = ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, cfg)
    assert p["prazo_dias_uteis"] > 8 and "acima do prazo-alvo de 8" in p["avisos"][0]

@pytest.mark.parametrize("campo, valor", [("eficiencia", 0), ("eficiencia", 1.2), ("horas_dia", 0), ("prazo_alvo_dias", 0)])
def test_parametros_invalidos(campo, valor):
    with pytest.raises(ErroEntrada) as e:
        ex.planejar_execucao(ITENS_REF, PRODUTIVIDADE_REF, {**ex.config_padrao(), campo: valor})
    assert e.value.codigo == "parametro_invalido" and e.value.detalhes == {"campo": campo}
```

Para o teste do aviso, confira à mão com prazo-alvo 8 (capacidade de 51,2 h): mecânico ⌈96,1/51,2⌉ = 2, então a equipe e o cronograma são os do alvo 10, prazo 9 > 8.

- [ ] **Passo 2: rodar e ver falhar.** Rode `cd propostas && python3 -m pytest -q testes/test_execucao.py`. Resultado esperado: FAIL com `AttributeError: ... planejar_execucao`.
- [ ] **Passo 3: implementar as três funções em `execucao.py`.**
- [ ] **Passo 4: rodar e ver passar.** Rode o mesmo comando e depois `python3 -m pytest -q testes`. Resultado esperado: PASS.
- [ ] **Passo 5: commit.** Mensagem: `feat(orcamento): equipe, prazo e cronograma por frentes`.

### Tarefa 4: preço de obra no mesmo motor

**Arquivos:**
- Modificar: `propostas/orcamento/execucao.py`
- Teste: `propostas/testes/test_execucao.py`

**Interfaces:**
- Consome: `planejar_execucao`; `orcamento.proposta.novo_fornecimento`; `orcamento.proposta.completar`; `orcamento.motor.precificar`.
- Produz:
  - `fornecimentos_execucao(plano: dict, itens: list[dict], funcoes: dict[str, dict], fase: str) -> list[dict]`. O argumento `funcoes` tem a forma `{codigo: {"nome": str, "custo_hora": float}}`. Para cada função com HH > 0, a função gera um fornecimento `novo_fornecimento(descricao=f"Mão de obra de execução — {nome}", categoria="mo_execucao", unid="h", qtd=HH, custo_unit=custo_hora, fonte="HH de execução", fase=fase)`. Para cada item com `custo_material_unit > 0`, gera `novo_fornecimento(descricao=item["descricao"] or item["item"], categoria=item["categoria_material"], unid=item["unidade"], qtd=quantidade, custo_unit=custo_material_unit, fonte="item de execução", fase=fase)`. Função com HH > 0 ausente de `funcoes` ou com `custo_hora <= 0` (ex.: função semeada com salário 0) lança `ErroEntrada("funcao_sem_custo", ..., {"funcao": f})`.
  - `precificar_com_execucao(cat: dict, proposta: dict, itens_por_opcao: dict[str, list[dict]], produtividade: list[dict], funcoes: dict[str, dict]) -> dict`. Devolve `{"proposta": dict, "orcamento": dict, "execucao": {opcao_id: plano}}`. Ela trabalha numa cópia profunda da proposta, sem alterar a original. Para cada opção com itens, ela usa `opcao.get("execucao") or config_padrao(primeira fase)`, chama `planejar_execucao`, acrescenta `fornecimentos_execucao(...)` aos fornecimentos da opção, define `opcao["prazo_execucao_dias"] = plano["prazo_dias_uteis"]` e chama `motor.precificar(cat, proposta)`. A fase de execução que não existe na opção lança `ErroEntrada("fase_inexistente", ..., {"opcao": id, "fase": fase})`. Em `orcamento["avisos"]`, ela tira só estes dois textos exatos do motor, e só para opções e fases com execução: `f"{nome_opcao}: nenhum serviço com horas — adicione serviços na aba Escopo."` e `f"{nome_opcao} / {nome_fase}: fase sem serviços."`. Os avisos do plano entram prefixados com `f"{nome_opcao}: "`.

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
    assert sum(f["custo"] for f in mo) == pytest.approx(8554.50)
    assert sum(f["preco"] for f in mo) == pytest.approx(10436.49)
    assert o["preco_fornec"] - sum(f["preco"] for f in mo) == pytest.approx(34485.00)
    assert o["preco"] == pytest.approx(44921.49)
    assert (o["prazo_dias_uteis"], o["prazo_dias_corridos"]) == (9, 13)
    assert r["orcamento"]["avisos"] == []
    assert "execucao" in p["opcoes"][0] and p["opcoes"][0]["fornecimentos"] == []   # original intacta

def test_opcao_sem_itens_da_o_mesmo_preco_do_motor(cat, params):
    for caminho in EXEMPLOS:
        p = abrir_exemplo(caminho, cat, params)
        esperado = [o["preco"] for o in motor.precificar(cat, p)["opcoes"]]
        r = ex.precificar_com_execucao(cat, p, {}, [], {})
        assert [o["preco"] for o in r["orcamento"]["opcoes"]] == pytest.approx(esperado)

def test_funcao_sem_custo_hora(cat, params):
    with pytest.raises(ErroEntrada) as e:
        ex.precificar_com_execucao(cat, _proposta_obra(cat, params), {"A": ITENS_REF}, PRODUTIVIDADE_REF,
                                   {k: v for k, v in FUNCOES_REF.items() if k != "ajudante"})
    assert e.value.codigo == "funcao_sem_custo"
```

- [ ] **Passo 2: rodar e ver falhar.** Rode `cd propostas && python3 -m pytest -q testes/test_execucao.py`. Resultado esperado: FAIL com `AttributeError: ... precificar_com_execucao`.
- [ ] **Passo 3: implementar `fornecimentos_execucao` e `precificar_com_execucao`.**
- [ ] **Passo 4: rodar e ver passar.** Rode o mesmo comando e depois `python3 -m pytest -q testes`. Resultado esperado: PASS.
- [ ] **Passo 5: commit.** Mensagem: `feat(orcamento): preço de obra (HH × custo-hora + materiais + BDI) no motor`.

### Tarefa 5: honorário de projeto pelo método área (`orcamento/honorario_area.py`)

**Arquivos:**
- Criar: `propostas/orcamento/honorario_area.py`
- Teste: `propostas/testes/test_honorario_area.py`

**Interfaces:**
- Consome: `ErroEntrada`.
- Produz:
  - `TIPOS_INSTALACAO = ("expansao_direta", "agua_gelada", "vrf")`
  - Parâmetros (dict, privados por empresa): `{"custo_basico": {tipo: R$/m²}, "fator_experiencia": {nivel: float}, "curva": [{"area_m2": float, "pct": float}], "fonte": str, "edicao": str, "secao_tabela": str, "edicao_superada": bool}`
  - `percentual_curva(curva: list[dict], area_m2: float) -> float`: interpola linearmente entre os pontos ordenados por área e usa o valor da ponta fora da faixa. Curva vazia lança `ErroEntrada("curva_vazia", ...)`.
  - `honorario_area(parametros: dict, entrada: dict) -> dict`. A `entrada` é `{"tipo_instalacao", "area_m2", "nivel_rt"}`. A função devolve `{"area_m2", "tipo_instalacao", "custo_basico", "pct", "nivel_rt", "fator_experiencia", "honorario", "fonte", "edicao", "secao_tabela", "avisos"}`. **Fórmula: honorário = área × custo básico unitário do tipo × pct(área) × fator de experiência do RT.** Com `edicao_superada`, o resultado leva o aviso `"Parâmetros do método área de edição superada ({edicao}): confira a tabela vigente."`. Tipo ou nível ausente nos parâmetros lança `ErroEntrada("parametro_area_ausente", ..., {"campo": ..., "valor": ...})`. Área ≤ 0 lança `ErroEntrada("area_invalida", ...)`.
  - `comparar_opcao(res_opcao: dict, cfg: dict, parametros: dict) -> dict`. O `cfg` é `{"ativo": bool, "fase": str, "tipo_instalacao", "area_m2", "nivel_rt"}`. A função devolve `{"fase", "preco_hh": preco_servicos da fase, "honorario_area", "diferenca": honorario_area − preco_hh, "razao": honorario_area ÷ preco_hh ou None, "detalhe": honorario_area(...)}`.

- [ ] **Passo 1: escrever os testes que falham.** Use estes parâmetros:

```python
# FICTÍCIO: valores inventados para teste; as tabelas ABRAVA/DNPC ainda não estão disponíveis.
PARAMS_FICTICIOS = {"custo_basico": {"expansao_direta": 1000.0, "agua_gelada": 1400.0, "vrf": 1200.0},
                    "fator_experiencia": {"junior": 0.9, "pleno": 1.0, "senior": 1.2},
                    "curva": [{"area_m2": 0, "pct": 0.05}, {"area_m2": 1000, "pct": 0.04}, {"area_m2": 5000, "pct": 0.03}],
                    "fonte": "FICTÍCIO — teste", "edicao": "teste", "secao_tabela": "—", "edicao_superada": False}

@pytest.mark.parametrize("tipo, area, nivel, pct, honorario", [
    ("expansao_direta", 2000, "senior", 0.0375, 90_000.0),    # 0,04 + (1000/4000)×(−0,01); 2000×1000×0,0375×1,2
    ("agua_gelada", 6000, "pleno", 0.03, 252_000.0),          # acima da curva: ponta 0,03; 6000×1400×0,03
    ("vrf", 500, "junior", 0.045, 24_300.0),                  # 500×1200×0,045×0,9
])
def test_honorario_pelo_metodo_area(tipo, area, nivel, pct, honorario):
    r = ha.honorario_area(PARAMS_FICTICIOS, {"tipo_instalacao": tipo, "area_m2": area, "nivel_rt": nivel})
    assert r["pct"] == pytest.approx(pct) and r["honorario"] == pytest.approx(honorario)

def test_comparacao_com_o_preco_hh():
    res = {"fases": [{"id": "F1", "preco_servicos": 60_000.0}]}
    c = ha.comparar_opcao(res, {"ativo": True, "fase": "F1", "tipo_instalacao": "expansao_direta", "area_m2": 2000,
                                "nivel_rt": "senior"}, PARAMS_FICTICIOS)
    assert (c["preco_hh"], c["honorario_area"], c["diferenca"], c["razao"]) == pytest.approx((60_000, 90_000, 30_000, 1.5))

def test_aviso_de_edicao_superada(): ...   # edicao_superada=True → texto do aviso com a edição
def test_tipo_sem_parametro(): ...         # tipo "vrf" removido de custo_basico → codigo "parametro_area_ausente"
```

- [ ] **Passo 2: rodar e ver falhar.** Rode `cd propostas && python3 -m pytest -q testes/test_honorario_area.py`. Resultado esperado: FAIL na importação.
- [ ] **Passo 3: implementar `honorario_area.py`.** A docstring diz que a fórmula segue a descrição do usuário e precisa ser conferida no documento ABRAVA/DNPC quando ele estiver disponível. O módulo não traz nenhum valor de tabela.
- [ ] **Passo 4: rodar e ver passar.** Depois rode `python3 -m pytest -q testes`.
- [ ] **Passo 5: commit.** Mensagem: `feat(orcamento): honorário de projeto pelo método área, com parâmetros externos`.

### Tarefa 6: modelos, migração e repositórios do comercial

**Arquivos:**
- Criar: `suite/backend/app/modulos/comercial/__init__.py`, `modelos.py`, `repositorio.py`
- Criar: `suite/backend/migracoes/versions/<rev>_comercial.py` (gerada por autogenerate e revisada)
- Teste: `suite/backend/testes/comercial/__init__.py`, `suite/backend/testes/comercial/test_repositorio.py`

**Interfaces:**
- Consome: `Base`, `ModeloEmpresa`, `RepositorioEmpresa` (T0).
- Produz os modelos (todos com `ModeloEmpresa`, ou seja, `id`, `empresa_id` e `criado_em`):

| Modelo (tabela) | Colunas | Restrições |
|---|---|---|
| `Funcao` (`funcao`) | `codigo` str(40), `nome` str(80), `salario_hora` Numeric(10,2), `encargos` Numeric(6,4), `ativo` bool | único (`empresa_id`, `codigo`); propriedade `custo_hora = salario_hora × (1 + encargos)` |
| `Produtividade` (`produtividade`) | `item` str(60), `unidade` str(4) ∈ `UNIDADES_ITEM`, `funcao_id` FK `funcao.id`, `hh_por_unidade` Numeric(10,4) ≥ 0, `fator_calibracao` Numeric(6,3) padrão 1, `fonte` str(200) não nulo | único (`empresa_id`, `item`, `funcao_id`) |
| `ParametroHonorarioArea` (`parametro_honorario_area`) | `nome`, `fonte`, `edicao`, `secao_tabela` str, `edicao_superada` bool, `custo_basico`, `fator_experiencia`, `curva` JSONB, `vigente` bool | índice único parcial (`empresa_id`) onde `vigente` |
| `TextoDocumento` (`texto_documento`) | `documento` str(20) ∈ {proposta, contrato, recibo}, `secao` str(40), `texto` Text, `atualizado_em` | único (`empresa_id`, `documento`, `secao`) |
| `Proposta` (`proposta`) | `numero` str(40), `cliente_id` int, `obra_id` int nulo, `situacao` str(12) ∈ {rascunho, enviada, aprovada, recusada, entregue}, `documento` JSONB, `valor_referencia` Numeric(14,2) nulo, `data_envio` date nulo, `validade_dias` int, `historico` JSONB (lista), `atualizado_em` | único (`empresa_id`, `numero`) |
| `ItemExecucao` (`item_execucao`) | `proposta_id` FK, `opcao_id` str(2), `ordem` int, `frente` str(80), `item` str(60), `descricao` str(200), `quantidade` Numeric(14,3), `altura`, `acesso`, `ocupacao`, `turno` str(20), `custo_material_unit` Numeric(14,2) padrão 0, `categoria_material` str(12) padrão "material" | |
| `PropostaRevisao` (`proposta_revisao`) | `proposta_id` FK, `numero` int, `entradas` JSONB, `resultado` JSONB, `versao_motor` str(20), `normas` JSONB, `emitida_em` datetime, `emitida_por` int | único (`proposta_id`, `numero`) |
| `Contrato` (`contrato`) | `numero` str(40), `proposta_id` FK único, `revisao_id` FK, `opcao_id` str(2), `cliente_id`, `obra_id` nulo, `valor_total`, `valor_fixo`, `valor_estimado` Numeric(14,2), `prazo_dias_uteis`, `prazo_dias_corridos` int, `data_inicio`, `previsao_entrega` date, `condicoes_pagamento`, `hh_previsto_funcao`, `hh_previsto_funcao_base` JSONB, `situacao` str(12) padrão "vigente" | único (`empresa_id`, `numero`) |

- Produz os repositórios (`RepositorioEmpresa[...]`): `RepoFuncao.por_codigo(codigo) -> Funcao | None`; `RepoProdutividade.dos_itens(itens: set[str]) -> list[Produtividade]`; `RepoParametroArea.vigente() -> ParametroHonorarioArea | None`; `RepoTexto.da_secao(documento, secao) -> TextoDocumento | None`; `RepoProposta.proximo_numero(ano: int) -> str` (`f"PC-{n:03d}/{ano}"`, com n = propostas da empresa com esse sufixo + 1); `RepoItemExecucao.da_proposta(proposta_id) -> list[ItemExecucao]` (ordenado por `opcao_id`, `ordem`); `RepoRevisao.ultima(proposta_id) -> PropostaRevisao | None` e `RepoRevisao.da_proposta(proposta_id) -> list`; `RepoContrato.da_proposta(proposta_id) -> Contrato | None`.
- O repositório de revisão não tem método de atualizar.

- [ ] **Passo 1: escrever os testes que falham**

```python
def test_migracao_cria_as_tabelas_do_comercial(sessao):
    nomes = set(inspect(sessao.get_bind()).get_table_names())
    assert {"funcao", "produtividade", "parametro_honorario_area", "texto_documento", "proposta",
            "item_execucao", "proposta_revisao", "contrato"} <= nomes

def test_repositorio_nao_ve_outra_empresa(sessao, empresa_a, empresa_b):
    RepoFuncao(sessao, empresa_a).adicionar(Funcao(codigo="ajudante", nome="Ajudante", salario_hora=15, encargos=0.8))
    assert RepoFuncao(sessao, empresa_b).por_codigo("ajudante") is None
    assert RepoFuncao(sessao, empresa_a).por_codigo("ajudante").custo_hora == Decimal("27.00")

def test_numero_da_proposta_e_sequencial_por_empresa(sessao, empresa_a, empresa_b, criar_cliente): ...
    # duas propostas na empresa A → "PC-001/2026", "PC-002/2026"; a primeira da B → "PC-001/2026"

def test_produtividade_unica_por_item_e_funcao(sessao, empresa_a): ...   # segunda linha igual → IntegrityError
```

- [ ] **Passo 2: rodar e ver falhar.** Rode `cd suite/backend && python -m pytest -q testes/comercial/test_repositorio.py`. Resultado esperado: FAIL na importação de `app.modulos.comercial.modelos`.
- [ ] **Passo 3: implementar modelos e repositórios e gerar a migração.** Rode `cd suite/backend && alembic revision --autogenerate -m "comercial"`. Confira à mão que a migração tem o índice parcial e as restrições únicas e que o `down_revision` é a cabeça da T0 (`alembic heads`).
- [ ] **Passo 4: rodar e ver passar.** Rode `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` e o pytest. Rode também `python -m pytest -q testes/test_arquitetura.py`.
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): tabelas, migração e repositórios`.

### Tarefa 7: funções e produtividade pela API

**Arquivos:**
- Criar: `suite/backend/app/modulos/comercial/esquemas.py`, `servico.py`, `rotas.py`
- Modificar: `suite/backend/app/main.py` (incluir `comercial.rotas.roteador`, prefixo `/api/comercial`)
- Teste: `suite/backend/testes/comercial/test_tabelas.py`, `suite/backend/testes/comercial/test_perfis_isolamento.py` (novo; as tarefas seguintes acrescentam linhas a ele)

**Interfaces:**
- Produz (esquemas): `FuncaoEntrada(codigo, nome, salario_hora: float ≥ 0, encargos: float ≥ 0, ativo=True)`, `FuncaoSaida(+ id, custo_hora)`, `ProdutividadeEntrada(item: str, unidade: Literal["m2","m","un","kW"], funcao_codigo: str, hh_por_unidade: float ≥ 0, fonte: str (min 1))`, `ProdutividadeSaida(+ id, fator_calibracao)`.
- Produz (serviço):
  - `listar_funcoes(sessao, empresa_id) -> list[FuncaoSaida]`
  - `criar_funcao(sessao, empresa_id, dados: FuncaoEntrada) -> FuncaoSaida` (código repetido gera `Conflito("funcao_duplicada")`)
  - `atualizar_funcao(sessao, empresa_id, funcao_id, dados) -> FuncaoSaida`
  - `semear_funcoes(sessao, empresa_id) -> int`: cria as funções de `FUNCOES_PADRAO` que faltam, com salário 0 e encargos 0, e devolve quantas criou
  - `listar_produtividade(sessao, empresa_id, item: str | None) -> list[ProdutividadeSaida]`
  - `criar_produtividade(...)`, `atualizar_produtividade(...)`, `remover_produtividade(...)`. Se a unidade for diferente de outra linha do mesmo item, a criação gera `RegraViolada("unidade_divergente", detalhes={"item", "unidade_existente"})`.
  - `tabelas_execucao(sessao, empresa_id, itens: set[str]) -> tuple[list[dict], dict[str, dict]]`: devolve a produtividade no formato da Tarefa 2 e as funções no formato `{codigo: {"nome", "custo_hora"}}` da Tarefa 4, só da empresa. Usada na Tarefa 10.
- Produz (rotas): `GET/POST /funcoes`, `PUT /funcoes/{id}`, `POST /funcoes/semear`, `GET/POST /produtividades`, `PUT/DELETE /produtividades/{id}`. Escrita com `TABELAS`, leitura com `LEITURA`.
- Produz (teste): em `test_perfis_isolamento.py`, a lista `ROTAS: list[tuple[str, str, frozenset[Perfil]]]` (método, caminho com `{id}`, perfis permitidos) e dois testes parametrizados:
  - `test_perfil_sem_permissao_recebe_403`: para cada rota e cada perfil fora do conjunto, a resposta é 403.
  - `test_perfil_permitido_nao_recebe_403`: a resposta não é 401 nem 403.
  Também traz `ROTAS_COM_ID` e `test_recurso_de_outra_empresa_da_404`, com uma fixture `recursos_empresa_a`. Essa fixture cria os recursos necessários pelos serviços e cresce a cada tarefa.

- [ ] **Passo 1: escrever os testes que falham.** Em `test_tabelas.py`:
  - `test_crud_de_funcao`: o POST devolve 201 com `custo_hora == 27.0` para salário 15 e encargos 0,8.
  - `test_funcao_duplicada_409`: o corpo é `{"codigo": "funcao_duplicada", ...}`.
  - `test_semear_cria_seis_funcoes_uma_vez`: a primeira chamada devolve 6 e a segunda devolve 0.
  - `test_produtividade_unidade_divergente_422`.
  - `test_tabelas_execucao_so_da_empresa`: com produtividade de `duto_m2` só na empresa B, `tabelas_execucao(sessao, empresa_a, {"duto_m2"})` devolve `([], {})`.

  Em `test_perfis_isolamento.py`, as linhas das rotas desta tarefa.
- [ ] **Passo 2: rodar e ver falhar.** Rode `cd suite/backend && python -m pytest -q testes/comercial`. Resultado esperado: FAIL com 404 nas rotas.
- [ ] **Passo 3: implementar esquemas, serviço e rotas e incluir o roteador em `main.py`.**
- [ ] **Passo 4: rodar e ver passar.** Rode `python -m pytest -q testes/comercial testes/test_arquitetura.py`.
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): funções e produtividade pela API`.

### Tarefa 8: parâmetros do método área por empresa

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`
- Teste: `suite/backend/testes/comercial/test_parametros_area.py`; acrescentar linhas a `test_perfis_isolamento.py`

**Interfaces:**
- Consome: `orcamento.honorario_area.TIPOS_INSTALACAO`, `percentual_curva`.
- Produz:
  - `ParametroAreaEntrada(nome, fonte: str min 1, edicao: str min 1, secao_tabela: str, edicao_superada: bool, custo_basico: dict[Literal[*TIPOS_INSTALACAO], float > 0], fator_experiencia: dict[str, float > 0] (min 1), curva: list[{area_m2 ≥ 0, pct: 0 < pct < 1}] (min 1, áreas sem repetição))`
  - `ParametroAreaSaida(+ id, vigente)`
  - `criar_parametro_area(sessao, empresa_id, dados) -> ParametroAreaSaida`: o novo conjunto fica vigente e o anterior deixa de ser
  - `listar_parametros_area(sessao, empresa_id)`
  - `parametro_area_vigente(sessao, empresa_id) -> dict | None`, no formato da Tarefa 5
- Rotas: `GET/POST /parametros-area` (escrita `TABELAS`).
- Não há PUT. Uma correção cria um conjunto novo, e o antigo fica como histórico para as revisões que o citam.

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_novo_conjunto_vira_vigente`: dois POST; o GET mostra só o segundo com `vigente: true`.
  - `test_curva_com_area_repetida_422`.
  - `test_parametro_de_outra_empresa_nao_vale`: a empresa B não tem vigente mesmo com a A tendo.

  Use `PARAMS_FICTICIOS` (comentário `# FICTÍCIO`).
- [ ] **Passo 2: rodar e ver falhar.** Rode `python -m pytest -q testes/comercial/test_parametros_area.py`.
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar** (todo `testes/comercial`).
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): parâmetros privados do método área (regra 9)`.

### Tarefa 9: proposta em rascunho, itens de execução e catálogo

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`
- Teste: `suite/backend/testes/comercial/test_propostas.py`; linhas em `test_perfis_isolamento.py`

**Interfaces:**
- Consome: `cadastro.servico.obter_cliente` e `obter_obra`; `orcamento.catalogo.carregar`; `orcamento.parametros.carregar`; `orcamento.proposta.padrao`, `completar` e `carregar_json`.
- Produz:
  - `PropostaCriar(cliente_id: int, obra_id: int | None, documento: dict | None)`. Sem documento, o serviço usa `pp.padrao(params)`. Com documento, usa `pp.completar(documento, cat, params)`. O número vem de `documento["numero"]`, se veio no JSON importado; senão, de `RepoProposta.proximo_numero(hoje.year)`, que também é gravado em `documento["numero"]`.
  - `PropostaSaida(id, numero, cliente_id, obra_id, situacao, documento, validade_dias, data_envio, vencimento: date | None, validade: Literal["valida","vencendo","vencida"] | None, valor_referencia, revisao_atual: int | None, historico)`
  - `ItemExecucaoEntrada(opcao_id, frente (min 1), item, descricao="", quantidade ≥ 0, altura="ate_3m", acesso="livre", ocupacao="desocupado", turno="diurno", custo_material_unit ≥ 0 = 0, categoria_material: Literal["material","equipamento"] = "material")`
  - `ItemExecucaoSaida(+ id, ordem, unidade)`, com a unidade lida da produtividade do item
  - Serviço:
    - `criar_proposta(sessao, empresa_id, dados, usuario_id, hoje) -> PropostaSaida`
    - `obter_proposta(sessao, empresa_id, proposta_id, hoje) -> PropostaSaida`
    - `listar_propostas(sessao, empresa_id, hoje, situacao: str | None = None, obra_id: int | None = None) -> list[PropostaSaida]`
    - `atualizar_documento(sessao, empresa_id, proposta_id, documento: dict, hoje) -> PropostaSaida`
    - `criar_item_execucao(...)`, `atualizar_item_execucao(...)`, `remover_item_execucao(...)`, `listar_itens_execucao(sessao, empresa_id, proposta_id)`
    - `catalogo() -> dict`, que devolve `orcamento.catalogo.carregar()`
  - Regras:
    - A edição só é permitida em `rascunho` e `enviada`. Fora disso, o serviço gera `Conflito("situacao_invalida", detalhes={"situacao": ...})`.
    - Um documento que falha em `completar`, por `KeyError` de serviço desconhecido ou `ValueError`, gera `RegraViolada("documento_invalido", mensagem com o erro)`.
    - Número repetido gera `Conflito("numero_duplicado")`.
    - Obra de outro cliente gera `RegraViolada("obra_de_outro_cliente")`.
    - `validade_dias` vem de `documento["validade_dias"]`.
  - Rotas:
    - `GET/POST /propostas` (`?situacao=&obra_id=`), `GET /propostas/{id}`, `PUT /propostas/{id}/documento`
    - `GET/POST /propostas/{id}/itens-execucao`, `PUT/DELETE /propostas/{id}/itens-execucao/{item_id}`
    - `GET /catalogo`, `GET /obras/{obra_id}/propostas`
  - A rota obtém a data com `from orcamento.parametros import hoje`, para que os testes possam fazer monkeypatch.

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_criar_proposta_vazia_gera_numero`: o número é `"PC-001/2026"`, a situação é `rascunho` e há uma opção `"A"`.
  - `test_importar_json_antigo_sem_fases`: o JSON tem `modelo_preco: "hora"`; a resposta tem `fases[0]["cobranca"] == "hora"`.
  - `test_servico_inexistente_422`: o código é `documento_invalido`.
  - `test_obra_de_outro_cliente_422`.
  - `test_editar_proposta_aprovada_409`: a situação é alterada direto no banco para preparar o teste.
  - `test_itens_de_execucao_crud_e_ordem`.
  - `test_propostas_da_obra`: o histórico do projeto lista só as propostas daquela obra.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar** (todo `testes/comercial`).
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): propostas em rascunho, itens de execução e catálogo`.

### Tarefa 10: cálculo pela API (critérios de pronto)

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`
- Teste: `suite/backend/testes/comercial/test_calculo.py`, `suite/backend/testes/comercial/referencia.py` (dados do caso de referência; `RAIZ_PROPOSTAS = Path(orcamento.__file__).resolve().parents[1]`; `montar_obra_referencia(cli: TestClient, cliente_id: int, modo: str = "prazo") -> int`, que cria funções, produtividade, proposta e itens pela API e devolve o id da proposta)

**Interfaces:**
- Consome: `tabelas_execucao`, `parametro_area_vigente`, `orcamento.execucao.precificar_com_execucao`, `orcamento.honorario_area.comparar_opcao`, `orcamento.__version__`.
- Produz:
  - `montar_entradas(sessao, empresa_id, proposta_id) -> dict`, que devolve `{"documento", "itens_por_opcao", "produtividade", "funcoes", "parametros_area", "catalogo"}`. É tudo JSON puro e é o que a revisão congela.
  - `calcular_entradas(entradas: dict) -> dict`. É uma função pura. Ela devolve `{"documento_precificado", "orcamento", "execucao", "honorario_area": {opcao_id: comparacao}, "avisos", "versao_motor"}`. Para cada opção com `documento.opcoes[i].honorario_area.ativo`, ela chama `comparar_opcao` com o resultado da opção. Sem parâmetro vigente, gera `RegraViolada("sem_parametros_area")`. Os `ErroEntrada` do motor viram `RegraViolada(e.codigo, e.mensagem, e.detalhes)`. Os avisos do método área entram em `avisos`.
  - `calcular(sessao, empresa_id, proposta_id) -> ResultadoCalculoSaida`. Calcula sem gravar.
  - `ResultadoCalculoSaida(opcoes: list[OpcaoResumo], avisos: list[str], versao_motor: str, detalhe: dict)`.
    - `OpcaoResumo(id, nome, interno: bool, preco, preco_fixo, preco_estimado, total_h, prazo_dias_uteis, prazo_dias_corridos, fases: list[FaseResumo(id, nome, cobranca, preco, preco_servicos)], execucao: ExecucaoResumo | None, honorario_area: dict | None)`
    - `ExecucaoResumo(hh_funcao, hh_funcao_base, equipe, cronograma, prazo_dias_uteis, prazo_dias_corridos, total_hh, custo_mo, preco_mo)`
    - `detalhe` é o resultado bruto do motor.
  - Rota: `POST /propostas/{id}/calculo` (perfis `CALCULO`).

- [ ] **Passo 1: escrever os testes que falham.**

```python
PRECOS_ESPERADOS = {"hvac_consultoria_2d_3d_bim.json": {"A": 55672.13, "B": 96243.17, "C": 140048.50},
                    "hvac_retrofit_fases.json": {"A": 138637.75, "B": 125937.62, "E": 1163417.61},
                    "nr13_inspecao.json": {"A": 29069.38},
                    "spci_projeto.json": {"A": 21622.49, "B": 32069.63}}

@pytest.mark.parametrize("arquivo", sorted(PRECOS_ESPERADOS))
def test_exemplos_dao_o_mesmo_preco_pela_api(arquivo, cliente_como, empresa_a, criar_cliente):
    cli = cliente_como(Perfil.COMERCIAL, empresa_a)
    doc = json.loads((RAIZ_PROPOSTAS / "exemplos" / arquivo).read_text(encoding="utf-8"))
    pid = cli.post("/api/comercial/propostas", json={"cliente_id": criar_cliente(empresa_a), "documento": doc}).json()["id"]
    r = cli.post(f"/api/comercial/propostas/{pid}/calculo").json()
    assert {o["id"]: round(o["preco"], 2) for o in r["opcoes"]} == PRECOS_ESPERADOS[arquivo]

def test_obra_de_referencia_pela_api(cliente_como, empresa_a, criar_cliente):
    cli = cliente_como(Perfil.ADMIN, empresa_a)
    pid = montar_obra_referencia(cli, criar_cliente(empresa_a))
    o = cli.post(f"/api/comercial/propostas/{pid}/calculo").json()["opcoes"][0]
    ex = o["execucao"]
    assert ex["hh_funcao"] == pytest.approx({"encarregado": 10.7, "mecanico_refrigeracao": 96.1, "ajudante": 96.1})
    assert ex["equipe"] == {"encarregado": 1, "mecanico_refrigeracao": 2, "ajudante": 2}
    assert [(c["frente"], c["dias_uteis"]) for c in ex["cronograma"]] == [("Térreo", 7), ("Cobertura", 2)]
    assert (ex["prazo_dias_uteis"], ex["prazo_dias_corridos"]) == (9, 13)
    assert (ex["custo_mo"], ex["preco_mo"]) == pytest.approx((8554.50, 10436.49))
    assert o["preco"] == pytest.approx(44921.49)
```

  Outros testes:
  - `test_produtividade_so_de_outra_empresa_422`: a empresa B tem `duto_m2` e a A não; o código é `item_sem_produtividade` e `detalhes == {"item": "duto_m2"}`.
  - `test_equipe_fixa_incompleta_422`: o código é `equipe_incompleta`.
  - `test_metodo_area_na_comparacao`: o documento tem `honorario_area` ativo na opção A, F1, `expansao_direta`, 2000 m², `senior`, e os parâmetros são `PARAMS_FICTICIOS`; `honorario_area["honorario_area"] == 90000`.
  - `test_metodo_area_sem_parametros_422`.
  - `test_calculo_nao_grava`: depois do cálculo, `revisao_atual` continua `None` e o documento é o mesmo.
- [ ] **Passo 2: rodar e ver falhar.** Rode `python -m pytest -q testes/comercial/test_calculo.py`.
- [ ] **Passo 3: implementar.** `custo_mo` e `preco_mo` são as somas de `custo` e `preco` dos fornecimentos `mo_execucao` com fonte "HH de execução" da opção.
- [ ] **Passo 4: rodar e ver passar** (todo `testes/comercial`).
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): cálculo de proposta e obra pela API (exemplos e obra de referência)`.

### Tarefa 11: envio, revisões imutáveis, histórico e validade

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`
- Teste: `suite/backend/testes/comercial/test_envio_revisoes.py`; linhas em `test_perfis_isolamento.py`

**Interfaces:**
- Consome: `montar_entradas`, `calcular_entradas`.
- Produz:
  - `DIAS_ALERTA_VALIDADE = 5`
  - `situacao_validade(data_envio: date | None, validade_dias: int, situacao: str, hoje: date) -> tuple[date | None, str | None]`: o vencimento é `data_envio + validade_dias` (dias corridos). A função só avalia propostas `enviada`. O resultado é `"vencida"` se `hoje > vencimento`, `"vencendo"` se faltam de 0 a 5 dias, e `"valida"` nos demais casos. Para outras situações devolve `(vencimento, None)`.
  - `enviar_proposta(sessao, empresa_id, proposta_id, usuario_id, hoje) -> RevisaoSaida`. A proposta precisa estar em `rascunho` ou `enviada`. O número da revisão é a última + 1, começando em 0. Antes de montar as entradas, o serviço grava `documento["revisao"] = f"{n:02d}"`. A revisão guarda as entradas, `resultado = calcular_entradas(entradas)`, `versao_motor`, `normas`, `emitida_em` e `emitida_por`. As normas são `[{"norma": fonte, "edicao", "secao": secao_tabela}]` dos parâmetros de área usados, ou `[]`. A proposta passa a `situacao = "enviada"` e `data_envio = hoje`. O `valor_referencia` é o menor `preco` entre as opções não internas, arredondado a 2 casas. O histórico recebe `{"de", "para", "em": iso, "por": usuario_id, "revisao": n}`. Erros de cálculo saem como na Tarefa 10, e nada é gravado.
  - `RevisaoSaida(id, numero, emitida_em, emitida_por, versao_motor, normas, resumo: ResultadoCalculoSaida)`; `listar_revisoes(sessao, empresa_id, proposta_id)`; `obter_revisao(sessao, empresa_id, proposta_id, numero) -> RevisaoSaida`.
  - Rotas: `POST /propostas/{id}/envio` (201), `GET /propostas/{id}/revisoes`, `GET /propostas/{id}/revisoes/{numero}`.

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_enviar_cria_revisao_00_e_muda_situacao`: com a obra de referência, a revisão 0 tem `resumo.opcoes[0].preco == 44921.49`, `versao_motor == orcamento.__version__`, a situação é `enviada` e `valor_referencia == 44921.49`.
  - `test_reenviar_depois_de_editar_cria_revisao_01`: muda a quantidade do item 1 para 200, reenvia e confere que a revisão 0 continua com 44 921,49.
  - `test_mudar_produtividade_nao_altera_revisao`.
  - `test_revisao_nao_tem_rota_de_alteracao`: `PUT .../revisoes/0` devolve 405.
  - `test_validade`: parametrizado com envio em 2026-11-01, validade de 15 dias e vencimento em 16/11. Em 10/11 o resultado é `valida`. Em 11/11 e em 16/11 é `vencendo`. Em 17/11 é `vencida`.
  - `test_normas_da_revisao_com_metodo_area`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): envio com revisão imutável, histórico e validade`.

### Tarefa 12: aprovação, recusa, entrega e contrato

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`
- Teste: `suite/backend/testes/comercial/test_fluxo_contrato.py`; linhas em `test_perfis_isolamento.py`

**Interfaces:**
- Consome: `RepoRevisao.ultima`, `situacao_validade`.
- Produz (para a T3 e para a calibração):
  - `MarcoPagamento(marco: str, pct: float, valor: float)`, `FasePagamento(fase_id, fase, cobranca, preco, marcos: list[MarcoPagamento])`
  - `ContratoLido(id, numero, proposta_id, proposta_numero, revisao: int, opcao_id, cliente_id, obra_id, valor_total, valor_fixo, valor_estimado, prazo_dias_uteis, prazo_dias_corridos, data_inicio, previsao_entrega, condicoes_pagamento: list[FasePagamento], hh_previsto_funcao: dict[str, float], hh_previsto_funcao_base: dict[str, float], situacao)`
  - `aprovar_proposta(sessao, empresa_id, proposta_id, revisao: int, opcao_id: str, usuario_id, hoje) -> ContratoLido`. Regras, nesta ordem:
    1. A situação é `enviada`; senão, `Conflito("situacao_invalida")`.
    2. A revisão é a última; senão, `Conflito("revisao_desatualizada", detalhes={"ultima": n})`.
    3. A proposta não está vencida; senão, `Conflito("proposta_vencida")`.
    4. A opção existe na revisão; senão, `RegraViolada("opcao_inexistente")`.
    5. A opção não é interna; senão, `RegraViolada("opcao_interna")`.

    O contrato:
    - `numero` = número da proposta com `"PC-"` trocado por `"CT-"`, ou `"CT-" + numero` quando o número não começa com `"PC-"`.
    - Os valores vêm de `resultado.orcamento` da opção e são arredondados a 2 casas.
    - `data_inicio = hoje` e `previsao_entrega = hoje + prazo_dias_corridos`.
    - As condições de pagamento saem de cada fase: `marcos` de `fase["pagamento"]`, com `valor = round(pct × preco da fase, 2)`.
    - `hh_previsto_*` vêm de `resultado.execucao[opcao_id]`, ou `{}`.

    A proposta passa a `aprovada`, com `valor_referencia = valor_total`, e o histórico recebe o registro.
  - `recusar_proposta(sessao, empresa_id, proposta_id, motivo: str, usuario_id, hoje) -> PropostaSaida`: só a partir de `enviada`; grava o motivo no histórico.
  - `registrar_entrega(...)`: `aprovada → entregue`.
  - `desfazer_entrega(...)`: `entregue → aprovada`. As duas gravam no histórico, e as transições erradas geram `Conflito("situacao_invalida")`.
  - `obter_contrato(sessao, empresa_id, contrato_id) -> ContratoLido`; `listar_contratos(sessao, empresa_id, situacao: str | None = None) -> list[ContratoLido]`; `contrato_da_proposta(sessao, empresa_id, proposta_id) -> ContratoLido | None`
  - Rotas:
    - `POST /propostas/{id}/aprovacao` com corpo `{revisao, opcao_id}` (201, devolve `ContratoLido`)
    - `POST /propostas/{id}/recusa` com corpo `{motivo}`
    - `POST /propostas/{id}/entrega`, `DELETE /propostas/{id}/entrega`
    - `GET /contratos`, `GET /contratos/{id}`

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_aprovar_gera_contrato_da_obra_de_referencia`: o contrato tem `numero == "CT-001/2026"`, `valor_total == 44921.49`, `prazo_dias_corridos == 13`, `previsao_entrega == hoje + 13 dias`, uma fase com marcos 30%/70% e valores 13 476,45 e 31 445,04, e `hh_previsto_funcao["ajudante"] == 96.1`.
  - `test_aprovar_revisao_antiga_409`.
  - `test_aprovar_vencida_409`.
  - `test_aprovar_opcao_interna_422` (exemplo `hvac_retrofit_fases.json`, opção E).
  - `test_segunda_aprovacao_409` (a situação já é `aprovada`).
  - `test_recusar_e_historico`.
  - `test_entregar_e_desfazer`.
  - `test_entregar_rascunho_409`.

  Conferência de 30%/70%: 0,3 × 44 921,49 = 13 476,447, que arredonda para 13 476,45. 0,7 × 44 921,49 = 31 445,043, que arredonda para 31 445,04.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.** Rode também `testes/test_arquitetura.py`.
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): aprovação gera contrato; recusa, entrega e desfazer`.

### Tarefa 13: exportações XLSX, DOCX e viabilidade de uma revisão

**Arquivos:**
- Modificar: `comercial/servico.py`, `rotas.py`
- Teste: `suite/backend/testes/comercial/test_exportacoes.py`

**Interfaces:**
- Consome: `orcamento.exportar_xlsx.gerar(cat, proposta, resultado) -> bytes`; `orcamento.exportar_docx.gerar(cat, proposta, resultado) -> list[(bytes, nome, pendencias)]`, uma por opção não interna e na ordem; `orcamento.viabilidade.calcular(v, precos)`; `orcamento.exportar_viabilidade.gerar(proposta, estudo) -> bytes`.
- Produz:
  - `exportar_xlsx(sessao, empresa_id, proposta_id, numero) -> tuple[bytes, str]`
  - `exportar_docx(sessao, empresa_id, proposta_id, numero, opcao_id) -> tuple[bytes, str]`
  - `exportar_viabilidade(sessao, empresa_id, proposta_id, numero) -> tuple[bytes, str]`

  As três funções usam só o que a revisão congelou: `entradas["catalogo"]`, `resultado["documento_precificado"]` e `resultado["orcamento"]`. Sem alternativas de viabilidade, o serviço gera `RegraViolada("sem_viabilidade")`. Opção interna ou inexistente no DOCX gera `RegraViolada("opcao_sem_proposta")`.
- Rotas: `GET /propostas/{id}/revisoes/{numero}/proposta.xlsx`, `.../docx/{opcao_id}`, `.../viabilidade.xlsx` (`LEITURA`), com `Content-Disposition: attachment; filename=...`, usando o nome que o motor gera.

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_xlsx_da_revisao_abre_e_tem_o_preco`: abre com openpyxl e acha a aba `Resumo`.
  - `test_docx_da_revisao_por_opcao`: o conteúdo começa com `b"PK"` e `exportar_docx.verificar(...)["logo"]` é verdadeiro.
  - `test_exportacao_usa_catalogo_congelado`: com monkeypatch, `orcamento.catalogo.carregar` passa a devolver um catálogo sem os serviços, e a exportação continua funcionando.
  - `test_viabilidade_sem_alternativas_422`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): exportações da revisão pelo motor (XLSX, DOCX, viabilidade)`.

### Tarefa 14: textos de documento editáveis por empresa

**Arquivos:**
- Criar: `suite/backend/app/modulos/comercial/textos_padrao.py` (só os textos padrão, que são dados do módulo)
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`
- Teste: `suite/backend/testes/comercial/test_textos.py`; linhas em `test_perfis_isolamento.py`

**Interfaces:**
- Produz:
  - `TEXTOS_PADRAO: dict[str, dict[str, str]]`, indexado por documento e depois por seção, com os textos padrão abaixo. As variáveis seguem `string.Template` (`$nome`): `$empresa`, `$cliente`, `$numero`, `$objeto`, `$valor`, `$valor_extenso`, `$prazo`, `$validade`, `$rt`, `$data`, `$referencia`.
  - `TextoSaida(documento, secao, texto, personalizado: bool)`
  - `listar_textos(sessao, empresa_id, documento) -> list[TextoSaida]`: todas as seções do padrão, com o texto da empresa quando existe
  - `salvar_texto(sessao, empresa_id, documento, secao, texto) -> TextoSaida`
  - `restaurar_texto(sessao, empresa_id, documento, secao) -> TextoSaida`: apaga o personalizado e devolve o padrão
  - `texto_renderizado(sessao, empresa_id, documento, secao, variaveis: dict[str, str]) -> str`: usa `safe_substitute`
  - Documento ou seção fora do padrão gera `RegraViolada("secao_desconhecida")`.
  - Rotas: `GET /textos/{documento}`, `PUT /textos/{documento}/{secao}` com corpo `{texto}`, `DELETE /textos/{documento}/{secao}` (restaurar padrão; devolve 200 com o padrão). Escrita com `TEXTOS`.

Textos padrão. É texto inicial; o jurídico da KAPTEK revisa o contrato antes do uso:

| documento | seção | texto |
|---|---|---|
| proposta | `apresentacao` | "A $empresa apresenta a $cliente a proposta $numero para $objeto." |
| proposta | `condicoes` | "Os valores incluem os tributos incidentes. O pagamento segue os marcos de cada fase descritos nesta proposta." |
| proposta | `validade` | "Esta proposta é válida por $validade dias a partir da data de emissão." |
| proposta | `encerramento` | "Ficamos à disposição para esclarecimentos. $rt" |
| contrato | `objeto` | "Prestação de serviços de $objeto, conforme a proposta $numero aceita pelo CONTRATANTE." |
| contrato | `valor` | "O valor total é de $valor ($valor_extenso), pago conforme as condições de pagamento deste contrato." |
| contrato | `prazo` | "O prazo de execução é de $prazo dias corridos, contados da data de início." |
| contrato | `obrigacoes_contratada` | "A CONTRATADA executará os serviços com responsabilidade técnica de $rt, com ART registrada." |
| contrato | `obrigacoes_contratante` | "O CONTRATANTE dará acesso ao local, informações e documentos necessários e efetuará os pagamentos nas datas acordadas." |
| contrato | `rescisao` | "O contrato pode ser rescindido por qualquer parte, mediante aviso por escrito com 30 dias de antecedência, pagos os serviços executados." |
| contrato | `foro` | "Fica eleito o foro da comarca da sede da CONTRATADA." |
| recibo | `declaracao` | "Recebemos de $cliente a importância de $valor ($valor_extenso), referente a $referencia." |

- [ ] **Passo 1: escrever os testes que falham.**
  - `test_lista_traz_padrao_quando_nao_ha_personalizado`: são 4 seções de proposta, todas com `personalizado: false`.
  - `test_salvar_e_restaurar_padrao`.
  - `test_texto_de_outra_empresa_nao_aparece`.
  - `test_secao_desconhecida_422`.
  - `test_variavel_ausente_fica_literal`: `$foo` permanece no texto.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): textos de documento por empresa com restaurar padrão`.

### Tarefa 15: PDFs de proposta, contrato e recibo com a identidade da empresa e do RT

**Arquivos:**
- Criar: `suite/backend/app/modulos/comercial/documentos_pdf.py` (renderização; HTML para PDF)
- Criar: `suite/backend/app/modulos/comercial/modelos_pdf/base.html`, `proposta.html`, `contrato.html`, `recibo.html`, `estilo.css`
- Modificar: `comercial/servico.py`, `rotas.py`; `suite/backend/requirements.txt` (`weasyprint>=62,<63`, `jinja2>=3.1,<4`, `num2words>=0.5.13,<0.6`, `pdfplumber>=0.11,<0.12` para os testes); `suite/infra/Dockerfile.api` (`apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0`)
- Teste: `suite/backend/testes/comercial/test_pdfs.py`; linhas em `test_perfis_isolamento.py`

**Interfaces:**
- Consome: `nucleo.empresa.obter_identidade`; `texto_renderizado`; `orcamento.exportar_docx.moeda`; `ContratoLido`; a revisão congelada; `orcamento.catalogo.exclusoes_validas`.
- Produz:
  - `valor_por_extenso(valor: float) -> str`: `num2words(round(valor, 2), lang="pt_BR", to="currency")`
  - `renderizar_pdf(modelo: str, contexto: dict) -> bytes`: Jinja2 com `autoescape=True` e WeasyPrint. O logo e a assinatura do RT entram como `data:` URI. O cabeçalho mostra razão social, CNPJ e logo. O rodapé mostra "Responsável técnico: {rt_nome} — {rt_titulo} — {rt_registro}".
  - `pdf_proposta(sessao, empresa_id, proposta_id, numero_revisao, opcao_id) -> tuple[bytes, str]`. O conteúdo é: textos da proposta, tabela de fases (nome, cobrança, preço), prazo, marcos de pagamento por fase, exclusões e, quando houver, o resumo da execução (HH por função, equipe, cronograma por frentes).
  - `pdf_contrato(sessao, empresa_id, contrato_id) -> tuple[bytes, str]`: as seções do contrato mais a tabela de condições de pagamento.
  - `pdf_recibo(sessao, empresa_id, contrato_id, valor: float | None, referencia: str | None, data_pagamento: date) -> tuple[bytes, str]`. Sem valor, vale `contrato.valor_total`. Sem referência, vale `f"projeto completo — contrato {numero}"`. Valor ≤ 0 ou acima do total gera `RegraViolada("valor_recibo_invalido")`. A T3 chama esta função por parcela paga.
  - Rotas:
    - `GET /propostas/{id}/revisoes/{numero}/pdf/{opcao_id}` (`LEITURA`)
    - `GET /contratos/{id}/contrato.pdf` (`LEITURA`)
    - `POST /contratos/{id}/recibo.pdf` com corpo `{valor?, referencia?, data_pagamento}` (`PAINEL_RECIBO`)

- [ ] **Passo 1: escrever os testes que falham.** Use `pdfplumber` para extrair o texto de todas as páginas.

```python
def test_pdf_da_proposta_tem_identidade_e_preco(...):   # definir_identidade(empresa_a, razao_social="Empresa Teste Ltda", rt_nome="Fulano de Tal", rt_registro="CREA-RJ 000000/D")
    texto = extrair(cli.get(f"/api/comercial/propostas/{pid}/revisoes/0/pdf/A").content)
    assert "Empresa Teste Ltda" in texto and "CREA-RJ 000000/D" in texto and "R$ 44.921,49" in texto
    assert "Térreo" in texto                                                   # cronograma por frentes

def test_pdf_usa_texto_personalizado(...):        # salvar_texto(proposta/apresentacao, "Texto próprio $numero") → "Texto próprio PC-001/2026" no PDF
def test_pdf_do_contrato_tem_marcos(...):          # "R$ 13.476,45" e "R$ 31.445,04"
def test_recibo_por_parcela(...):                  # valor 13476.45, referencia "parcela 1" → "R$ 13.476,45" e "parcela 1"
def test_recibo_projeto_inteiro_por_extenso(...):  # contrato de valor 90 000 gravado direto pelo repositório → "noventa mil reais" no texto
def test_recibo_acima_do_total_422(...)
```

- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar `documentos_pdf.py`, os modelos HTML e as funções do serviço.** Os modelos usam fonte embutida do sistema (DejaVu Sans) e página A4 com margens de 2 cm.
- [ ] **Passo 4: rodar e ver passar.** Rode também a imagem: `docker compose -f suite/infra/docker-compose.yml build api` termina sem erro.
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): PDFs de proposta, contrato e recibo com identidade da empresa e do RT`.

### Tarefa 16: painel comercial

**Arquivos:**
- Modificar: `comercial/esquemas.py`, `servico.py`, `rotas.py`
- Teste: `suite/backend/testes/comercial/test_painel.py`; linha em `test_perfis_isolamento.py`

**Interfaces:**
- Consome: `situacao_validade`, `RepoProposta`, `RepoContrato`.
- Produz:
  - `FAIXAS_VALOR = ((0, 20_000, "até R$ 20 mil"), (20_000, 100_000, "R$ 20 mil a 100 mil"), (100_000, 500_000, "R$ 100 mil a 500 mil"), (500_000, None, "acima de R$ 500 mil"))`. Cada faixa é (mínimo exclusivo, máximo inclusivo, rótulo).
  - `Painel(por_estagio: dict[str, int], conversao_geral: float | None, conversao_por_faixa: list[FaixaConversao(rotulo, decididas, aprovadas, taxa: float | None)], valor_aguardando: float, total_aprovado: float, ticket_medio: float | None, vencendo: list[PropostaResumo], vencidas: list[PropostaResumo], prazo_estourado: list[ContratoResumo])`
  - `PropostaResumo(id, numero, cliente_id, valor_referencia, vencimento, dias_restantes)`; `ContratoResumo(id, numero, proposta_id, previsao_entrega, dias_atraso)`
  - `painel(sessao, empresa_id, hoje: date, desde: date | None = None) -> Painel`. Definições:
    - `por_estagio`: contagem das 5 situações, com zero quando não há proposta naquela situação.
    - Ganhas = `aprovada` + `entregue`. Decididas = ganhas + `recusada`.
    - `conversao_geral` = ganhas ÷ decididas, ou None quando não há decididas.
    - A faixa de cada proposta vem do `valor_referencia`.
    - `valor_aguardando` = Σ `valor_referencia` das `enviada`, vencidas incluídas.
    - `total_aprovado` = Σ `contrato.valor_total` das ganhas.
    - `ticket_medio` = total_aprovado ÷ nº de ganhas.
    - `vencendo` e `vencidas` vêm de `situacao_validade`.
    - `prazo_estourado`: contratos de propostas `aprovada` (não entregue) com `previsao_entrega < hoje`.
    - `desde` filtra propostas por `criado_em >= desde`.
  - Rota: `GET /painel?desde=` (`PAINEL_RECIBO`).

- [ ] **Passo 1: escrever o teste que falha.** A fixture `cenario_painel` grava direto pelos repositórios do comercial, com hoje = 2026-11-08:

| proposta | situação | valor_referencia | outros |
|---|---|---|---|
| P1 | aprovada | 10 000 | contrato 10 000, previsão de entrega 2026-11-01 |
| P2 | recusada | 15 000 | |
| P3 | entregue | 50 000 | contrato 50 000 |
| P4 | enviada | 200 000 | envio 2026-10-27, validade 15 → vence 11/11 (3 dias) |
| P5 | rascunho | — | |
| P6 | enviada | 30 000 | envio 2026-10-01, validade 15 → vencida |

```python
def test_painel_do_cenario(sessao, empresa_a, cenario_painel):
    p = painel(sessao, empresa_a, date(2026, 11, 8))
    assert p.por_estagio == {"rascunho": 1, "enviada": 2, "aprovada": 1, "recusada": 1, "entregue": 1}
    assert p.conversao_geral == pytest.approx(2 / 3)
    assert [(f.decididas, f.aprovadas, f.taxa) for f in p.conversao_por_faixa] == [(2, 1, 0.5), (1, 1, 1.0), (0, 0, None), (0, 0, None)]
    assert (p.valor_aguardando, p.total_aprovado, p.ticket_medio) == pytest.approx((230_000, 60_000, 30_000))
    assert [x.numero for x in p.vencendo] == ["P4"] and p.vencendo[0].dias_restantes == 3
    assert [x.numero for x in p.vencidas] == ["P6"]
    assert [(c.proposta_id, c.dias_atraso) for c in p.prazo_estourado] == [(cenario_painel["P1"], 7)]

def test_painel_isolado_por_empresa(...)   # empresa B vê tudo zerado
def test_painel_vazio(...)                 # sem propostas: conversões None, ticket None, somas 0
```

- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): painel comercial`.

### Tarefa 17: interface de calibração pelo HH apontado (para a T2)

**Arquivos:**
- Modificar: `propostas/orcamento/execucao.py`; `propostas/testes/test_execucao.py`
- Modificar: `comercial/esquemas.py`, `servico.py`
- Teste: `suite/backend/testes/comercial/test_calibracao.py`

**Interfaces:**
- Produz (motor): `sugerir_calibracao(amostras: list[dict]) -> list[dict]`. Cada amostra é `{"funcao", "hh_base", "hh_realizado"}`. A saída é `[{"funcao", "amostras", "fator_sugerido"}]`, ordenada por função. O fator é `round(mediana(hh_realizado ÷ hh_base), 3)`, e amostras com `hh_base <= 0` são ignoradas. Como a razão é tomada sobre o HH sem calibração, aplicar de novo não acumula, igual a `orcamento.calibracao`.
- Produz (serviço; é a porta de entrada da T2, sem rota HTTP nesta trilha):
  - `AmostraHH(contrato_id: int, funcao: str, hh_realizado: float ≥ 0)`; `SugestaoCalibracao(funcao, amostras, fator_sugerido, fator_atual: float | None)`
  - `sugerir_calibracao_execucao(sessao, empresa_id, amostras: list[AmostraHH]) -> list[SugestaoCalibracao]`. O `hh_base` vem de `contrato.hh_previsto_funcao_base[funcao]`. Contrato de outra empresa gera `NaoEncontrado`, e função ausente no contrato é ignorada. `fator_atual` é a mediana dos `fator_calibracao` das linhas de produtividade da função, ou None quando não há linhas.
  - `aplicar_calibracao_execucao(sessao, empresa_id, sugestoes: list[SugestaoCalibracao], minimo_amostras: int = 3) -> int`: grava `fator_calibracao = fator_sugerido` em todas as linhas de produtividade da função que têm amostras suficientes e devolve o número de linhas alteradas.
- A T2 agrega `apontamento_hh` por contrato e função (soma das horas de `inicio`–`fim`) e chama estas duas funções. A T1 não cria tabela nova para isso.

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
  - `test_calibracao_pelo_contrato_de_referencia`: um contrato aprovado da obra de referência com amostra ajudante de 105,71 h dá o fator sugerido 1,1.
  - `test_aplicar_respeita_minimo_de_amostras`: com 1 amostra e mínimo 3, nada muda.
  - `test_aplicar_nao_acumula`: depois de aplicar 1,1 e recalcular, `hh_funcao_base` continua 96,1, e um novo contrato com o mesmo realizado sugere de novo 1,1.
  - `test_contrato_de_outra_empresa_404`.
- [ ] **Passo 2: rodar e ver falhar.** Rode os dois comandos de teste.
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.** Rode `cd propostas && python3 -m pytest -q testes` e `cd suite/backend && python -m pytest -q testes/comercial`.
- [ ] **Passo 5: commit.** Mensagem: `feat(comercial): interface de calibração da produtividade pelo HH apontado`.

### Tarefa 18: front-end, cliente da API e lista de propostas

**Arquivos:**
- Criar: `suite/frontend/src/modulos/comercial/api.ts`, `tipos.ts`, `rotas.tsx`, `paginas/ListaPropostas.tsx`, `componentes/SeloSituacao.tsx`, `componentes/NovaProposta.tsx`
- Modificar: `suite/frontend/src/rotas.tsx` (acrescentar `ROTAS_COMERCIAL`), `suite/frontend/src/nucleo/menu.ts` ("Comercial", visível para admin, engenharia, comercial e financeiro)
- Teste: `suite/frontend/src/modulos/comercial/__testes__/ListaPropostas.test.tsx`

**Interfaces:**
- Consome: `api`, `baixar`, `ErroApi`, `usePerfis`, `renderizar` (T0); as rotas das Tarefas 7–16.
- Produz:
  - `tipos.ts`: tipos TS espelhando os esquemas: `Proposta`, `ItemExecucao`, `ResultadoCalculo`, `OpcaoResumo`, `ExecucaoResumo`, `Revisao`, `Contrato`, `Funcao`, `Produtividade`, `ParametroArea`, `Texto`, `Painel`.
  - `api.ts`: uma função por rota, com os nomes:
    - `listarPropostas(filtros)`, `criarProposta(corpo)`, `obterProposta(id)`, `salvarDocumento(id, doc)`
    - `listarItens(id)`, `criarItem(id, item)`, `salvarItem(id, itemId, item)`, `removerItem(id, itemId)`
    - `calcular(id)`, `enviar(id)`, `listarRevisoes(id)`, `obterRevisao(id, n)`
    - `aprovar(id, revisao, opcaoId)`, `recusar(id, motivo)`, `entregar(id)`, `desfazerEntrega(id)`
    - `baixarXlsx(id, n)`, `baixarDocx(id, n, opcao)`, `baixarViabilidade(id, n)`, `baixarPdfProposta(id, n, opcao)`, `baixarPdfContrato(contratoId)`, `baixarRecibo(contratoId, corpo)`
    - `obterCatalogo()`, `listarFuncoes()`, `salvarFuncao(f)`, `semearFuncoes()`, `listarProdutividade(item?)`, `salvarProdutividade(p)`, `removerProdutividade(id)`
    - `listarParametrosArea()`, `criarParametroArea(p)`, `listarTextos(doc)`, `salvarTexto(doc, secao, texto)`, `restaurarTexto(doc, secao)`
    - `obterPainel(desde?)`, `listarContratos()`, `obterContrato(id)`, `propostasDaObra(obraId)`
  - `SeloSituacao({ situacao, validade })` mostra o rótulo da situação ("Rascunho", "Enviada", "Aprovada", "Recusada", "Entregue") e, quando há validade, um selo "Vencendo" (amarelo) ou "Vencida" (vermelho).
  - `ListaPropostas` mostra uma tabela com número, cliente, situação + validade, valor de referência e envio, com filtro por situação. O botão "Nova proposta" abre `NovaProposta`, que permite escolher cliente e obra e importar opcionalmente um `.json` do app atual.
  - Rotas: `/comercial/propostas`, `/comercial/propostas/:id`, `/comercial/contratos/:id`, `/comercial/tabelas`, `/comercial/painel`.

- [ ] **Passo 1: escrever os testes que falham** (Vitest, com `vi.mock("../api")`):
  - `"mostra selo Vencendo para proposta enviada perto do vencimento"`.
  - `"filtra por situação chamando listarPropostas({situacao: 'enviada'})"`.
  - `"importar JSON envia o documento lido do arquivo"`: o teste usa `userEvent.upload` e verifica `criarProposta` com `documento.numero === "PC-KTK-EX04/2026"`.
  - `"perfil financeiro não vê o botão Nova proposta"`.
  - `"mostra a mensagem do ErroApi"`: com `numero_duplicado`, aparece a mensagem do servidor.
- [ ] **Passo 2: rodar e ver falhar.** Rode `cd suite/frontend && npx vitest run src/modulos/comercial`.
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.** Rode também `npm run lint && npx tsc --noEmit`.
- [ ] **Passo 5: commit.** Mensagem: `feat(web/comercial): cliente da API e lista de propostas`.

### Tarefa 19: editor de escopo e preço, com comparação HH × área

**Arquivos:**
- Criar: `suite/frontend/src/modulos/comercial/paginas/EditorProposta.tsx` (abas), `componentes/AbaDadosGerais.tsx`, `componentes/AbaEscopo.tsx`, `componentes/FormularioServico.tsx`, `componentes/AbaFornecimentos.tsx`, `componentes/AbaPreco.tsx`, `componentes/ComparacaoArea.tsx`
- Teste: `__testes__/FormularioServico.test.tsx`, `__testes__/AbaPreco.test.tsx`

**Interfaces:**
- Consome: `obterProposta`, `salvarDocumento`, `obterCatalogo`, `calcular`.
- Produz:
  - `EditorProposta` mantém o `documento` em estado local e salva com `salvarDocumento`. Há um botão "Salvar" e um aviso de alterações não salvas. As abas são: Dados gerais, Escopo, Fornecimentos, Execução (Tarefa 20), Preço, Revisões (Tarefa 21). Em situações não editáveis, tudo fica somente leitura.
  - `AbaDadosGerais` edita `cliente`, `objeto`, `contexto` (complexidade, documentação, acesso, urgência, risco, `dist_km`, `area_ref`) e `validade_dias`.
  - `AbaEscopo` trabalha por opção: nome, modalidade (`fases`/`estimativa`), fases com nome e cobrança (`fechado`/`hora`/`percentual`/`pacote`, com os campos de cada uma vindos de `nova_fase`), serviços do catálogo por fase e `fator_manual`. O botão "Duplicar opção" copia a opção com a próxima letra livre.
  - `FormularioServico({ servico, dados, onChange })` gera os campos de `servico.dados` pelo `tipo`: `int` e `float` viram campo numérico com `min` e unidade; `opcoes` vira seleção com `rotulo`; `bool` vira caixa de seleção.
  - `AbaFornecimentos` mostra uma tabela com descrição, categoria, unidade, quantidade, custo unitário, fonte e fase.
  - `AbaPreco` chama `calcular` e mostra, por opção: preço, fixo + estimado, horas, prazo, tabela de fases (cobrança e preço) e avisos.
  - `ComparacaoArea` aparece quando a opção tem `honorario_area`. Ela mostra preço HH da fase, honorário pela área, diferença em R$ e em % e a fonte/edição dos parâmetros. A configuração (ativo, fase, tipo de instalação, área, nível do RT) é editada nesta mesma aba e gravada em `documento.opcoes[i].honorario_area`.

- [ ] **Passo 1: escrever os testes que falham.**
  - `"FormularioServico gera campo numérico, seleção e caixa conforme o tipo"`: usa um serviço sintético com os quatro tipos.
  - `"alterar campo chama onChange com o valor convertido em número"`.
  - `"AbaPreco mostra R$ 44.921,49 e os avisos do cálculo"`.
  - `"ComparacaoArea mostra diferença de +50% para 90.000 × 60.000"`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.** Os valores em reais usam `Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" })`.
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(web/comercial): editor de escopo, preço e comparação HH × área`.

### Tarefa 20: tela de execução (itens, equipe, prazo e cronograma)

**Arquivos:**
- Criar: `suite/frontend/src/modulos/comercial/componentes/AbaExecucao.tsx`, `componentes/TabelaItensExecucao.tsx`, `componentes/CronogramaFrentes.tsx`
- Teste: `__testes__/AbaExecucao.test.tsx`, `__testes__/CronogramaFrentes.test.tsx`

**Interfaces:**
- Consome: `listarItens`, `criarItem`, `salvarItem`, `removerItem`, `listarProdutividade`, `calcular`, `salvarDocumento`.
- Produz:
  - `AbaExecucao({ proposta, opcaoId })` mostra a configuração da opção (`documento.opcoes[i].execucao`): fase, modo prazo-alvo ou equipe fixa, horas por dia, eficiência e a tabela de fatores, que é editável por proposta. Abaixo ficam os itens. O resultado (HH por função, equipe, prazo em dias úteis e corridos, custo e preço da MO) vem de `calcular`.
  - `TabelaItensExecucao` tem as colunas frente, item, unidade, quantidade, altura, acesso, ocupação, turno, material R$/un e categoria. A lista de itens aceitos vem de `listarProdutividade`, com valores distintos de `item`.
  - `CronogramaFrentes({ cronograma })` mostra uma barra por frente, do dia `inicio` ao `fim`, com a legenda de dias por função.

- [ ] **Passo 1: escrever os testes que falham.**
  - `"mostra equipe 1/2/2 e prazo 9 dias úteis (13 corridos)"`: o resultado de `calcular` é simulado com o caso de referência.
  - `"modo equipe fixa mostra campos de pessoas por função"`.
  - `"erro equipe_incompleta destaca a função"`: o `ErroApi` traz `detalhes.funcao`.
  - `"CronogramaFrentes desenha Térreo 1–7 e Cobertura 8–9"`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(web/comercial): tela de HH de execução, equipe e cronograma por frentes`.

### Tarefa 21: envio, revisões, aprovação, contrato e documentos

**Arquivos:**
- Criar: `suite/frontend/src/modulos/comercial/componentes/AbaRevisoes.tsx`, `componentes/DialogoAprovacao.tsx`, `paginas/PaginaContrato.tsx`, `componentes/DialogoRecibo.tsx`
- Teste: `__testes__/AbaRevisoes.test.tsx`, `__testes__/PaginaContrato.test.tsx`

**Interfaces:**
- Consome: `enviar`, `listarRevisoes`, `aprovar`, `recusar`, `entregar`, `desfazerEntrega`, os downloads, `obterContrato`, `baixarRecibo`.
- Produz:
  - `AbaRevisoes` mostra o histórico de revisões (número, data, autor, versão do motor, preço por opção) e o histórico de situação. Os botões dependem da situação:
    - rascunho e enviada: "Enviar" (ou "Enviar nova revisão").
    - enviada: "Aprovar" e "Recusar" (com motivo).
    - aprovada: "Marcar entregue" e "Ver contrato".
    - entregue: "Desfazer entrega".

    Cada revisão tem os downloads XLSX, DOCX/PDF por opção e viabilidade.
  - `DialogoAprovacao` lista só as opções não internas da última revisão.
  - `PaginaContrato` mostra valores, prazo, previsão de entrega, condições de pagamento por fase e marco e HH previsto por função, com os botões "Contrato (PDF)" e "Recibo (PDF)". O recibo pode ser do projeto inteiro ou por parcela (valor e referência).

- [ ] **Passo 1: escrever os testes que falham.**
  - `"proposta enviada mostra Aprovar e Recusar, e não Marcar entregue"`.
  - `"aprovar envia a última revisão e a opção escolhida e navega para o contrato"`.
  - `"opção interna não aparece no diálogo de aprovação"`.
  - `"erro proposta_vencida mostra a mensagem e sugere enviar nova revisão"`.
  - `"recibo por parcela envia valor e referência"`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(web/comercial): envio, revisões, aprovação, contrato e documentos`.

### Tarefa 22: tabelas da empresa e textos de documento

**Arquivos:**
- Criar: `suite/frontend/src/modulos/comercial/paginas/TabelasComercial.tsx`, `componentes/TabelaFuncoes.tsx`, `componentes/TabelaProdutividade.tsx`, `componentes/ParametrosArea.tsx`, `componentes/EditorTextos.tsx`
- Teste: `__testes__/TabelasComercial.test.tsx`, `__testes__/EditorTextos.test.tsx`

**Interfaces:**
- Consome: as funções de tabelas e textos de `api.ts`.
- Produz:
  - `TabelaFuncoes` edita salário-hora e encargos e mostra o custo-hora calculado. O botão "Criar funções padrão" chama `semearFuncoes`.
  - `TabelaProdutividade` tem um filtro por item. A fonte é obrigatória. A unidade é escolhida em `m2/m/un/kW`, com o texto de ajuda "Potência em kW (rótulo de catálogo em TR fica no motor de seleção)".
  - `ParametrosArea` mostra o histórico de conjuntos, com um selo no vigente, e o formulário de um novo conjunto (custo básico por tipo, fatores do RT, pontos da curva, fonte, edição, seção/tabela, edição superada). Há um aviso fixo: "Valores das tabelas ABRAVA/DNPC: dados privados da empresa."
  - `EditorTextos` tem seleção de documento, uma área de texto por seção, as variáveis disponíveis listadas, "Salvar" e "Restaurar padrão" com confirmação.
  - Os componentes de escrita ficam desabilitados para perfis sem permissão (matriz).

- [ ] **Passo 1: escrever os testes que falham.**
  - `"custo-hora mostra 27,00 para 15,00 com encargos 80%"`.
  - `"perfil comercial vê produtividade mas não edita"`.
  - `"novo conjunto do método área exige fonte e edição"`.
  - `"Restaurar padrão chama restaurarTexto e mostra o texto padrão"`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(web/comercial): tabelas da empresa e textos de documento`.

### Tarefa 23: tela do painel comercial

**Arquivos:**
- Criar: `suite/frontend/src/modulos/comercial/paginas/PainelComercial.tsx`
- Teste: `__testes__/PainelComercial.test.tsx`

**Interfaces:**
- Consome: `obterPainel(desde?)`; o tipo `Painel`.
- Produz: a tela tem, em ordem:
  1. Cartões: valor aguardando resposta, total aprovado, ticket médio, conversão geral.
  2. Barras de propostas por estágio.
  3. Tabela de conversão por faixa de valor, com "—" quando a taxa é nula.
  4. Listas "Vencendo", "Vencidas" e "Prazo de entrega estourado", com link para a proposta ou o contrato.
  5. Filtro "desde".

  Percentuais com uma casa decimal ("66,7%"). Quando o painel está vazio, aparece "Nenhuma proposta no período".

- [ ] **Passo 1: escrever os testes que falham.**
  - `"mostra conversão 66,7% e ticket R$ 30.000,00 do cenário"`: usa o mesmo cenário da Tarefa 16.
  - `"faixa sem decididas mostra —"`.
  - `"lista P4 em Vencendo com 3 dias"`.
  - `"painel vazio mostra a mensagem"`.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar e ver passar.**
- [ ] **Passo 5: commit.** Mensagem: `feat(web/comercial): painel comercial`.

### Tarefa 24: ponta a ponta (Playwright) e verificação dos critérios de pronto

**Arquivos:**
- Criar: `suite/frontend/e2e/comercial.spec.ts`
- Modificar: `suite/backend/testes/comercial/test_perfis_isolamento.py` (conferir que toda rota de `roteador.routes` está em `ROTAS`)

**Interfaces:**
- Consome: `entrarComo`, `semearEmpresa` (T0); todas as telas das Tarefas 18–23.

- [ ] **Passo 1: escrever os testes.**
  - Back-end, `test_toda_rota_do_comercial_esta_na_matriz`: o conjunto (método, caminho) de `app.modulos.comercial.rotas.roteador.routes` é igual ao conjunto de `ROTAS`.
  - Playwright, `"obra de referência: da proposta ao recibo"`:
    1. Entra como admin e cria as funções e a produtividade do caso de referência.
    2. Entra como comercial, cria a proposta, lança os 3 itens com os fatores e define o prazo-alvo de 10 dias.
    3. Confere na tela "Equipe 1 · 2 · 2", "9 dias úteis" e "R$ 44.921,49".
    4. Envia, aprova a opção A, abre o contrato, baixa o PDF do contrato e o recibo da parcela de 30% e confere os downloads.
    5. Confere no painel "Total aprovado R$ 44.921,49".
  - Playwright, `"exemplo importado dá o mesmo preço"`: importa `propostas/exemplos/nr13_inspecao.json`, calcula e confere "R$ 29.069,38".
- [ ] **Passo 2: rodar e ver falhar.** Rode `cd suite/frontend && npx playwright test e2e/comercial.spec.ts` (com a pilha do `docker compose` da T0 no ar) e `cd suite/backend && python -m pytest -q testes/comercial/test_perfis_isolamento.py`.
- [ ] **Passo 3: corrigir o que faltar.** Normalmente são linhas de `ROTAS` esquecidas ou `data-testid` ausentes.
- [ ] **Passo 4: verificação final.** Todos estes comandos precisam passar:
  - `cd propostas && python3 -m pytest -q testes` (157 + os novos testes do motor)
  - `cd suite/backend && ruff check . && python -m pytest -q`
  - `cd suite/frontend && npm run lint && npx vitest run && npx playwright test`

  Os dois critérios de pronto da especificação são cobertos por `test_exemplos_dao_o_mesmo_preco_pela_api` e `test_obra_de_referencia_pela_api`.
- [ ] **Passo 5: commit.** Mensagem: `test(comercial): ponta a ponta e matriz completa de perfis`.
