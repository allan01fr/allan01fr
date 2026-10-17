# OpenFOAM — coifa A (ilha dos fogões) da cozinha de banquetes

Caso CFD 3D gerado **a partir do mesmo `saida/modelo.json`** do visualizador: coifa A, captores CP-A1/A2, ilha de fogões, bancadas, piso e laje. Serve a três coisas: medir o custo de uma simulação completa, gerar os quadros de CFD da animação e ser o ponto de partida do estudo de captura real.

> **O que é e o que não é.** A geometria vem do desenho. Carga térmica dos fogões, ar de reposição, difusividade e paredes laterais do recorte são **hipóteses do caso** (lista abaixo), não dados do projeto. Os resultados são ilustrativos até que essas entradas sejam confirmadas.

## Arquivos

| Arquivo | Para quê |
|---|---|
| `gerar_caso.py` | gera o caso (STL, `blockMesh`, `snappyHexMesh`, campos `0/`, `system/`) em três níveis de malha: `grossa` (≈ 0,12 M células), `media` (≈ 0,72 M), `producao` (≈ 3,1 M) |
| `malha.sh` | blockMesh → snappyHexMesh → topoSet/createPatch → checkMesh, com tempos |
| `rodar_teste.py` | **teste de custo**: tempo de malha, tempo por iteração em 1…N processos, pico de memória (não vai até a convergência) |
| `convergencia.py` | roda N iterações e mede em quantas o caso converge (histórico de resíduos) |
| `estimar_duracao.py` | junta as medições e estima a duração do caso completo na sua máquina |
| `bench_banda.py`, `bench_maquina.py` | **calibração na sua máquina** (≈ 10 min): banda de memória e tempo por iteração na malha `media` |
| `fumaca.py`, `quadros.py` | animação: transporte de fumaça sobre o escoamento estacionário → MP4 |
| `ler_vtu.py` | leitor dos campos exportados por `foamToVTK -ascii` |
| `env.sh` | ambiente mínimo do OpenFOAM v1912 do pacote Ubuntu |

## Hipóteses do caso (não vêm do desenho)

- Vazão da coifa A = 220,78 m³/min (texto da prancha de 2006), dividida igualmente entre os dois captores.
- Topo dos fogões a 250 °C (compressível) ou 120 K acima do ambiente (Boussinesq); sem radiação.
- Ar de reposição = 100 % da exaustão, por 3 difusores de forro 0,60 × 0,60 m nas posições do as-built (DIF-03/04/05); sem porta de equilíbrio.
- Recorte da cozinha de 8,4 × 5,2 m em planta; paredes laterais fictícias, adiabáticas; k-ε padrão com funções de parede.
- Geometria limpa para CFD: frestas < 15 cm entre caixas e paredes são fechadas, as duas caixas da ilha são fundidas e as faces são alinhadas à grade (até meia célula, 2,5 cm na malha média). Chapas e chaminés da coifa ganham no mínimo 2 células de espessura.

## Como rodar (Linux / WSL2)

```
source env.sh                                  # ou o bashrc do seu OpenFOAM ESI
python3 gerar_caso.py ./caso media 4           # nível: grossa | media | producao; 4 = nº de processos
./malha.sh ./caso
cd caso && decomposePar && mpirun -np 4 buoyantSimpleFoam -parallel && reconstructPar -latestTime
```

Teste de custo e calibração:

```
python3 rodar_teste.py ./teste --nivel media --np 1,2,4,6 --iter 30
python3 bench_maquina.py --np 1,2,4,6         # grava bench_maquina.json: devolve o resumo para recalibrar a estimativa
```

## Lições do pacote Ubuntu `openfoam` 1912 (as que custaram horas)

- **`snappyHexMesh` com `snap true` deforma as células** junto às superfícies (não-ortogonalidade ≈ 49°, razão de volume 0,09) e o solver diverge nas primeiras iterações, mesmo num caso nulo (sem vazão e sem calor). Com a geometria alinhada à grade e `snap false`, a malha sai hexaédrica (aspecto 1,02; assimetria 0,33; não-ortogonalidade ≤ 26° nos nós pendentes) e o solver roda estável.
- Os *function objects* (`probes`, `postProcess -func …`) falham com `error in IOstream "sha1"` nesta compilação. Os monitores saem do pós-processamento (`foamToVTK -ascii` + Python).
- Sem Scotch: usar `method simple` no `decomposeParDict`.
- A vazão imposta com ar quente na exaustão precisa ser **mássica** (`massFlowRate`); vazões volumétricas iguais não fecham a continuidade quando a densidade difere.
- `flowRateOutletVelocity` extrapola a velocidade do interior (zero na partida): para saída com vazão imposta, `flowRateInletVelocity` com vazão negativa.
- As vazões entram em rampa de 150 iterações; o balanço reposição/exaustão precisa fechar em 1e-8 (escrever com 12 algarismos).
