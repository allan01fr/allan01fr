# Plano de execução

**Objetivo:** um scanner LiDAR de mão que gere nuvens de pontos georreferenciáveis (LAZ/PLY)
de ambientes internos e externos. A meta de recursos é a do Peppe's Ghost: SLAM no aparelho,
botões e LEDs, cor RGB e streaming opcional para o celular.

**Estratégia:** começar pelo hardware e software do **Mandeye** (já testados e com BOM e peças
3MF prontos) e só depois acrescentar o que o Peppe's Ghost tem a mais. Cada fase termina com
algo que já funciona.

## Arquitetura

```
 Bateria 14,4 V ─ fusível ─ chave ─┬─────────────► Livox Mid-360 (LiDAR + IMU)
                                   │                     │ Ethernet 100 Mb (192.168.1.x)
                                   └─ step-down 5 V/5 A ─► Raspberry Pi 5 ◄── 2× câmera CSI (fase 4)
                                                         │  ├─ GPIO: 2 botões, 3 LEDs, buzzer
                                                         │  ├─ SSD NVMe / pendrive (scans)
                                                         │  └─ Wi-Fi hotspot (app web, fase 5)
                                                         ▼
                                   PC: HDMapping (LIO + SLAM + exportação LAZ)
```

## Fase 0: preparação (1–2 semanas, enquanto espera as compras)

- [ ] Comprar o Mid-360 primeiro. É o item de entrega mais lenta e o mais caro.
- [ ] Ler `referencias/mandeye_controller/README.md`, `doc/BIM.md` e `doc/wiring/wiring.md`.
- [ ] Assistir ao [vídeo de montagem do Mandeye](https://youtu.be/BXBbuSJMFEo).
- [ ] Abrir o CAD no [Onshape](https://cad.onshape.com/documents/a6c6019ccb399ad39d830fad) e checar:
  - [ ] se o Pi 5 cabe (furação igual à do Pi 4, mas o cooler ativo é mais alto);
  - [ ] se há espaço para o HAT NVMe;
  - [ ] o encaixe da bateria escolhida.
  Adaptar o modelo se precisar.
- [ ] Compilar o HDMapping no PC (`referencias/HDMapping`) e testar com um dataset de exemplo
  do projeto. Assim o processamento já é conhecido antes de ter o hardware.

## Fase 1: bancada (Mid-360 + Pi 5 na mesa)

- [ ] Gravar o Raspberry Pi OS **Bookworm 64 bits**. O Livox SDK exige 64 bits.
- [ ] Configurar IP fixo na `eth0`: `192.168.1.5/24` (comando `nmcli` no README do Mandeye).
- [ ] Ligar o Mid-360 numa fonte de bancada de 12 V e confirmar o ping no LiDAR (`192.168.1.1xx`).
- [ ] Compilar o `mandeye_controller` com `-DMANDEYE_HARDWARE_HEADER=mandeye-standard-rpi5.h`.
- [ ] Ligar botões, LEDs e buzzer na protoboard e testar com `./led_demo` e `./button_demo`.
- [ ] Configurar o automount USB (`usbmount`) ou montar o SSD em `/media/usb`.
- [ ] Fazer uma gravação de teste e abrir no HDMapping.

**Critério de saída:** um scan da bancada abre no HDMapping.

## Fase 2: aparelho de mão (energia + carcaça)

- [ ] Imprimir `referencias/mandeye_controller/3mf/ScannerAssembly.3mf` (adaptado na fase 0)
  e `LivoxCap.3mf`, em PETG, 0,2 mm, ~30% de preenchimento.
- [ ] Montar o circuito de energia: bateria → fusível → chave → Mid-360 e step-down 5,1 V.
  **Medir a tensão sob carga no Pi** (`vcgencmd get_throttled` deve dar `0x0`).
- [ ] Crimpar o RJ45 ou usar o cabo Livox. Fazer a fiação final do GPIO conforme a lista de materiais.
- [ ] Ativar o serviço systemd do Mandeye para gravar ao apertar o botão, sem PC por perto.
- [ ] Testar autonomia: gravar com a bateria cheia até desligar e anotar o tempo.

**Critério de saída:** escanear um cômodo e um trecho externo (~100 m) só com o aparelho,
processar no HDMapping e exportar LAZ.

Procedimento de varredura (vale para todas as fases):

1. Ficar 5–10 s parado no início e no fim, para a IMU inicializar.
2. Andar devagar e sem giros bruscos.
3. Fechar laços, voltando ao ponto de partida.

## Fase 3: SLAM no aparelho (FAST-LIO2 no Pi 5, como o Peppe's Ghost)

- [ ] Instalar ROS 2 Jazzy. O caminho mais simples é Ubuntu 24.04 arm64 no Pi 5 (suporte Tier 1),
  ou ROS 2 em Docker sobre o Raspberry Pi OS, como o `livo-handheld` faz. No Debian Bookworm
  o ROS 2 só tem suporte Tier 3, com compilação pelo código-fonte.
- [ ] Compilar `Livox-SDK2` e `livox_ros_driver2`. Configurar o IP do host em `MID360_config.json`.
- [ ] Compilar o FAST_LIO no branch `ROS2` (`git -C referencias/FAST_LIO fetch origin ROS2`)
  usando `config/mid360.yaml`.
- [ ] Ajustar para o Pi:
  - [ ] `point_filter_num` 3–4;
  - [ ] voxel `filter_size_map` 0,5;
  - [ ] desligar o `pcd_save` contínuo e salvar só o mapa final.
- [ ] Gravar em **MCAP** (`ros2 bag record -s mcap`) os tópicos `/livox/lidar`, `/livox/imu`,
  `/Odometry` e `/cloud_registered`. Visualizar no [Foxglove](https://foxglove.dev)
  ou no [Rerun](https://rerun.io).
- [ ] Integrar os botões e LEDs: um nó Python com `gpiozero` que inicia e para o launch e o bag.
- [ ] Medir CPU e temperatura. Se o Pi não aguentar em tempo real, manter o SLAM no PC
  (HDMapping) e usar o Pi só para gravar.

**Critério de saída:** a trajetória e o mapa saem prontos do aparelho, sem pós-processamento.

> Licença: o FAST-LIO é GPL-2.0. Ao distribuir um firmware ou imagem que o contenha,
> o código-fonte também precisa ser distribuído.

## Fase 4: cor (câmeras RGB)

- [ ] Instalar 2 câmeras CSI no Pi 5 (frente e trás, ou duas laterais).
- [ ] Publicar as imagens no ROS 2 (`camera_ros` com libcamera) com timestamp sincronizado.
  O Mid-360 e o Pi podem usar PTP: ver `referencias/mandeye_controller/doc/appendix_ptp.md`.
- [ ] Calibrar:
  - [ ] intrínseca (OpenCV, tabuleiro);
  - [ ] extrínseca câmera↔LiDAR com [direct_visual_lidar_calibration](https://github.com/koide3/direct_visual_lidar_calibration),
    o mesmo fluxo do `atlas-scanner` (`referencias/atlas-scanner/docs/calibration.md`).
- [ ] Colorir a nuvem em pós-processamento: projetar cada ponto na imagem mais próxima no tempo,
  usando a pose do FAST-LIO.
- [ ] (Opcional) Exportar no formato COLMAP para Gaussian Splatting, como o `atlas-scanner` faz.

## Fase 5: usabilidade

- [ ] Hotspot Wi-Fi + app web para iniciar, parar e ver o status pelo celular
  (o `referencias/livo-handheld/webinterface` já faz isso).
- [ ] Streaming ao vivo da nuvem para o celular via WebSocket (Foxglove Bridge).
- [ ] Script de cópia e conversão: MCAP → PLY/LAZ/E57.
- [ ] Encaixe 1/4" para bastão ou tripé e modo estático (TLS), já suportado pelo HDMapping_TLS.

## Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Mid-360 esgotado, caro ou retido na alfândega | Comprar cedo. Alternativa: Mid-360S, também suportado pelo driver |
| Pi 5 desligando ou com throttling | Step-down de 5 A com cabo curto e grosso, cooler ativo, `get_throttled` |
| FAST-LIO pesado demais para o Pi | Gravar no aparelho e processar no PC (HDMapping), que é o fluxo do Mandeye |
| Deriva em corredores longos ou ambientes sem feições | Fechar laços, andar devagar, usar o SLAM com pose graph do HDMapping |
| Borrão nas câmeras | Câmera global shutter, exposição curta e boa iluminação |

## Entregáveis por fase

| Fase | Entregável |
|---|---|
| 0 | HDMapping rodando no PC, CAD adaptado ao Pi 5 |
| 1 | Primeiro scan de bancada |
| 2 | Scanner de mão gravando de forma autônoma + LAZ exportado |
| 3 | Mapa e trajetória gerados no aparelho, arquivo MCAP |
| 4 | Nuvem colorida |
| 5 | Controle e visualização pelo celular |
