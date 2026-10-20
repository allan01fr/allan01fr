# OpenFOAM — coifa A (ilha dos fogões) da cozinha de banquetes

Caso CFD 3D gerado **a partir do mesmo `saida/modelo.json`** do visualizador: coifa A, captores CP-A1/A2, ilha de fogões, bancadas, piso e laje. Serve a três coisas: medir o custo de uma simulação completa sem rodá-la até o fim, gerar os quadros de CFD da animação e ser o ponto de partida do estudo de captura real.

> **O que é e o que não é.** A geometria vem do desenho. Carga térmica dos fogões, ar de reposição, difusividade e paredes laterais do recorte são **hipóteses do caso** (lista abaixo), não dados do projeto. Os resultados são ilustrativos até que essas entradas sejam confirmadas.

## Resultados

- **Custo do caso completo no seu notebook** (Xeon E-2176M, 6 processos): ver [`saida/estimativa_cfd.md`](../saida/estimativa_cfd.md). Malha média (0,72 M células) ≈ 1,6 h; intermediária (1,5 M) ≈ 4,7 h; produção (3,13 M) ≈ 13 h, com faixa de 7 a 31 h. O tempo por iteração foi medido nas três malhas (1 a 4 processos) e o modelo prevê a malha média, sem usá-la no ajuste, com erro de 2,7 %. A passagem para o notebook é extrapolação pela banda de memória até que `bench_maquina.py` seja rodado nele.
- **O fim da simulação não se decide por resíduo.** Na malha média os resíduos estacionam em ≈ 3e-4 (U, h) e ≈ 1e-3 (p_rgh) a partir de ≈ 2.250 iterações, porque a pluma quente pulsa; o critério usual de 1e-4 não é atingido em 3.500 iterações. Grandezas integrais ficam em ±5 % de 1.000 iterações em diante, as pontuais oscilam ±40 a 90 %. Vale a média de uma janela de iterações.
- **Animação:** [`saida/animacao_cfd_coifa_A.mp4`](../saida/animacao_cfd_coifa_A.mp4), também embutida no HTML (botão **Animação CFD**).

## Arquivos

| Arquivo | Para quê |
|---|---|
| `gerar_caso.py` | gera o caso (STL, `blockMesh`, `snappyHexMesh`, campos `0/`, `system/`) em três níveis de malha: `grossa` (≈ 0,12 M células), `media` (≈ 0,72 M), `producao` (≈ 3,1 M) |
| `malha.sh` | blockMesh → snappyHexMesh → topoSet/createPatch → checkMesh, com tempos |
| `rodar_teste.py` | **teste de custo**: tempo de malha, tempo por iteração em 1…N processos, pico de memória (não vai até a convergência) |
| `convergencia.py` | roda N iterações e guarda o histórico de resíduos e os instantes gravados |
| `convergencia_monitores.py` | calcula T e \|U\| sob a coifa, T do ambiente e T/\|U\| numa sonda em cada instante gravado: mostra se o campo parou de mudar quando o resíduo estaciona |
| `medicoes/` | medições desta nuvem (custo por malha e nº de processos, resíduos, monitores, banda de memória): a entrada do estimador |
| `figura_convergencia.py` | figura dos resíduos (malhas grossa e média) e dos monitores físicos, usada em `saida/estimativa_cfd.md` |
| `estimar_duracao.py` | junta as medições e estima a duração do caso completo na sua máquina (relatório em Markdown, números em pt-BR) |
| `bench_banda.py`, `bench_maquina.py` | **calibração na sua máquina** (≈ 10 min): banda de memória e tempo por iteração na malha `media`; gravam `bench_maquina.json` com CPU, SO e medidas |
| `animacao.py` | **a animação em um comando**: caso Boussinesq → malha → escoamento estacionário → fumaça → quadros → MP4 (retomável) |
| `fumaca.py` | transporte de fumaça (escalar passivo, `scalarTransportFoam`) sobre o escoamento estacionário congelado; serial ou em paralelo |
| `quadros.py` | 4 cortes por quadro com linhas de corrente, coluna lateral com relógio, dados do caso e fumaça acumulada; MP4 1080p e 720p, capa e quadros-chave |
| `ler_vtu.py` | leitor dos campos exportados por `foamToVTK -ascii` (centros e caixas das células, instante gravado) |
| `env.sh` | ambiente mínimo do OpenFOAM v1912 do pacote Ubuntu |

Testes dos utilitários (sem OpenFOAM): `python3 ../verificacao/teste_openfoam_scripts.py`.

## Hipóteses do caso (não vêm do desenho)

- Vazão da coifa A = 220,78 m³/min (texto da prancha de 2006), dividida igualmente entre os dois captores.
- Topo dos fogões a 250 °C (compressível) ou 120 K acima do ambiente (Boussinesq, usado na animação); sem radiação.
- Ar de reposição = 100 % da exaustão, por 3 difusores de forro 0,60 × 0,60 m nas posições do as-built (DIF-03/04/05); sem porta de equilíbrio.
- Recorte da cozinha de 8,4 × 5,2 m em planta; paredes laterais fictícias, adiabáticas; k-ε padrão com funções de parede.
- Geometria limpa para CFD: frestas < 15 cm entre caixas e paredes são fechadas, as duas caixas da ilha são fundidas e as faces são alinhadas à grade (até meia célula, 2,5 cm na malha média). Chapas e chaminés da coifa ganham no mínimo 2 células de espessura.
- Fumaça: escalar passivo liberado pela superfície de cocção com difusividade efetiva de 0,01 m²/s (hipótese); o escoamento fica congelado no campo estacionário, então só a fumaça evolui no tempo. Não é uma simulação transiente do ar.

## Como rodar (Linux / WSL2)

```
source env.sh                                  # ou o bashrc do seu OpenFOAM ESI
python3 gerar_caso.py ./caso media 4           # nível: grossa | media | producao; 4 = nº de processos
./malha.sh ./caso
cd caso && decomposePar && mpirun -np 4 buoyantSimpleFoam -parallel && reconstructPar -latestTime
```

Teste de custo e estimativa (as medições desta nuvem estão em `medicoes/`; o relatório sai em `../saida/estimativa_cfd.md`):

```
python3 rodar_teste.py ./teste --nivel media --np 1,2,4,6 --iter 30
python3 convergencia.py ./conv --nivel media --solver compressivel --np 4 --iter 3500 --escreve 500
python3 convergencia_monitores.py ./conv/conv_media_compressivel ./conv/media_compressivel/caso.json --saida medicoes/monitores_media_compressivel.json
python3 estimar_duracao.py medicoes --md ../saida/estimativa_cfd.md --json ../saida/estimativa_cfd.json --figura estimativa_cfd_residuos.png
python3 figura_convergencia.py medicoes ../saida/estimativa_cfd_residuos.png
```

## Calibração na sua máquina (troca a extrapolação por medida)

1. **Só a banda de memória (≈ 20 s, qualquer Linux/WSL2 com Python e numpy; não precisa de OpenFOAM):**
   `python3 bench_banda.py 12`, e passe a linha dos 6 processos para o estimador:
   `python3 estimar_duracao.py medicoes --bw-medido <GB/s> --md estimativa_cfd.md`.
2. **Solver na malha média (≈ 10 min, precisa do OpenFOAM):** `python3 bench_maquina.py --np 1,2,4,6` grava `bench_maquina.json` (CPU, SO, banda e s/iteração) e imprime um resumo. Depois,
   `python3 estimar_duracao.py medicoes --usuario bench_maquina.json --md estimativa_cfd.md`.

`env.sh` usa o OpenFOAM que já estiver no PATH (ou procura um bashrc ESI conhecido); em último caso cai no ambiente mínimo do pacote Ubuntu. **Os scripts foram validados no OpenFOAM ESI v1912.** Em versões novas o `buoyantSimpleFoam` foi substituído por `buoyantFoam` e algumas chaves dos dicionários mudaram: `bench_maquina.py` confere os executáveis antes de começar e, se faltarem, indica o caminho da etapa 1.

## Windows, Garuda e Omarchy

| Parte | Windows | Garuda / Omarchy (Arch) |
|---|---|---|
| `bench_banda.py`, `estimar_duracao.py`, `figura_convergencia.py` (Python + numpy) | roda nativo (PowerShell, `py bench_banda.py 12`) | roda nativo |
| Solver, malha, `bench_maquina.py`, `animacao.py` | só dentro do WSL2 (Ubuntu) ou de um contêiner | nativo, se o OpenFOAM ESI estiver instalado (AUR ou contêiner Docker/Podman) |

O solver e o `snappyHexMesh` não rodam em Windows nativo. Em qualquer dos três, o caminho mais portátil é um contêiner do OpenFOAM ESI (Docker Desktop no Windows com WSL2, Podman ou Docker no Arch) com esta pasta montada; `env.sh` usa o que estiver no PATH dentro dele. **Não testei contêiner nem Arch**: os scripts só foram rodados no OpenFOAM ESI v1912 (Ubuntu). Versões novas trocam `buoyantSimpleFoam` por `buoyantFoam`, e `bench_maquina.py` avisa se o executável não existir. Em qualquer caso, a banda de memória (etapa 1 da calibração) já reduz a incerteza e não depende do OpenFOAM.

## Animação

Um comando, retomável (≈ 35 min com 4 núcleos na malha média: malha 1 min, estacionário 20 min, fumaça 13 min, quadros 2 min):

```
python3 animacao.py ./anim --nivel media --np 4 --iter 2000 --t-fim 90 --escreve 0.25 --t-lento 30 --passo-rapido 3 --fps 15
```

A fumaça é gravada a cada 0,25 s. O vídeo mostra todos os instantes até 30 s (3,8× o tempo real, quando a pluma se forma e satura) e depois avança de 3 em 3 s (45×, quando só o fundo do ambiente muda devagar); o fator aparece sob o relógio.

## Lições do pacote Ubuntu `openfoam` 1912 (as que custaram horas)

- **`snappyHexMesh` com `snap true` deforma as células** junto às superfícies (não-ortogonalidade ≈ 49°, razão de volume 0,09) e o solver diverge nas primeiras iterações, mesmo num caso nulo (sem vazão e sem calor). Com a geometria alinhada à grade e `snap false`, a malha sai hexaédrica (aspecto 1,02; assimetria 0,33; não-ortogonalidade ≤ 26° nos nós pendentes) e o solver roda estável.
- Os *function objects* (`probes`, `postProcess -func …`) falham com `error in IOstream "sha1"` nesta compilação. Os monitores saem do pós-processamento (`foamToVTK -ascii` ou leitura direta dos campos em Python).
- Sem Scotch: usar `method simple` no `decomposeParDict`.
- A vazão imposta com ar quente na exaustão precisa ser **mássica** (`massFlowRate`); vazões volumétricas iguais não fecham a continuidade quando a densidade difere. Escrever com `writePrecision 14`: o `decomposePar` regrava as condições de contorno com esse número de algarismos e o balanço reposição/exaustão precisa fechar em 1e-8.
- `flowRateOutletVelocity` extrapola a velocidade do interior (zero na partida): para saída com vazão imposta, `flowRateInletVelocity` com vazão negativa. As vazões entram em rampa de 150 iterações.
- `scalarTransportFoam` com `symGaussSeidel` dá exceção de ponto flutuante: usar `PBiCGStab` com `DILU`. O `phi` do `buoyantSimpleFoam` é mássico: a fumaça usa o campo do `buoyantBoussinesqSimpleFoam`, cujo `phi` é volumétrico.

## Armadilhas do pós-processamento

- O `foamToVTK` nomeia as pastas pelo **índice do passo** (`fumaca_1200`), não pelo tempo. O instante verdadeiro está no cabeçalho do `.vtu` (`time='60'`); `ler_vtu.tempo()` o lê.
- Nas células de interface entre níveis de refino (nós pendurados) a **média dos vértices não é o centro** da célula. Para saber qual célula contém um ponto, `quadros.py` usa a caixa envolvente de cada célula e a busca cresce de 12 a 192 vizinhos; um ponto que nenhuma caixa contém é sólido (célula ausente da malha), o que dá o contorno exato dos equipamentos e das chapas da coifa.
- Os campos de cada instante são lidos direto dos arquivos binários do OpenFOAM (`quadros.campo_foam`), sem exportar um `.vtu` por instante: o export em ascii de uma malha de 0,7 M células custa dezenas de MB por instante.
