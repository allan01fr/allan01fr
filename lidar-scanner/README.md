# Scanner LiDAR portátil (open source)

Projeto para montar um scanner LiDAR de mão parecido com o
[Peppe's Ghost](https://peppesghost.xyz/), mas usando somente projetos de código aberto.

O Peppe's Ghost não é open source. O plano de montagem é vendido por £128 e o
aparelho pronto por £2.950. Segundo a
[matéria da Raspberry Pi](https://www.raspberrypi.com/news/peppes-ghost-lidar-scanner/),
ele usa:

- um Raspberry Pi 5;
- um Livox Mid-360 ligado por Ethernet;
- duas câmeras Pi nas portas CSI;
- um SSD;
- FAST-LIO2 rodando no próprio aparelho;
- gravação em arquivos MCAP;
- botões e LEDs no lugar de tela.

Esta pasta junta projetos abertos que cobrem essas mesmas peças.

## Documentos

- [PLANO.md](PLANO.md): plano de execução em fases.
- [LISTA_DE_MATERIAIS.md](LISTA_DE_MATERIAIS.md): lista de materiais com custos estimados.

## Projetos de referência (em `referencias/`, como submódulos git)

| Repositório | O que fornece | Licença | Uso aqui |
|---|---|---|---|
| [mandeye_controller](https://github.com/JanuszBedkowski/mandeye_controller) | Hardware aberto completo: Pi 4/5 + Mid-360, peças em 3MF, BOM, fiação, botões/LEDs, gravação em pendrive | MIT | **Base do hardware** |
| [HDMapping](https://github.com/MapsHD/HDMapping) | Software de pós-processamento do Mandeye: LiDAR-inertial odometry, SLAM com pose graph, exportação LAS/LAZ | MIT | **Processamento no PC** |
| [FAST_LIO](https://github.com/hku-mars/FAST_LIO) | LiDAR-inertial odometry (o mesmo algoritmo do Peppe's Ghost); roda em ARM | GPL-2.0 | SLAM no próprio aparelho (fase 3) |
| [livox_ros_driver2](https://github.com/Livox-SDK/livox_ros_driver2) / [Livox-SDK2](https://github.com/Livox-SDK/Livox-SDK2) | Drivers oficiais do Mid-360 | MIT | Drivers |
| [livo-handheld](https://github.com/RomanStadlhuber/livo-handheld) | Variante do Mandeye com câmera global shutter, ROS 2 em Docker e controle por app web via hotspot | MIT | Referência para câmera e app web |
| [atlas-scanner](https://github.com/Eecornwell/atlas-scanner) | Scanner com Mid-360 + câmera 360°, calibração câmera↔LiDAR, nuvem colorida, exportação COLMAP/Gaussian Splatting | MIT | Referência para cor e calibração |

Descartados:

- [OpenSLAM (A2Lab)](https://github.com/Werdna0107/OpenSLAM): o hardware é aberto, mas o software vem só
  em binários (`.exe` e `.apk`), sem código-fonte.
- GitLab: não achei nenhum scanner portátil completo hospedado lá. O projeto relevante é o
  [Kitware LiDAR SLAM](https://gitlab.kitware.com/keu-computervision/slam), uma biblioteca de SLAM
  usada pelo LidarView. O host `gitlab.kitware.com` está bloqueado na rede deste
  ambiente, então ele não foi incluído como submódulo. Para clonar na sua máquina:
  `git clone https://gitlab.kitware.com/keu-computervision/slam.git`

## Como baixar as referências

```bash
git submodule update --init --depth 1
```
