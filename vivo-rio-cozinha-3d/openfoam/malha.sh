#!/bin/bash
# Gera a malha do caso (blockMesh -> snappyHexMesh -> topoSet/createPatch -> checkMesh) e imprime os tempos.
# Uso: ./malha.sh <pasta_do_caso>
set -e
AQUI="$(dirname "$(readlink -f "$0")")"; cd "$1"; source "$AQUI/env.sh"
t0=$(date +%s.%N); rm -rf constant/polyMesh [1-9]* processor*
blockMesh > log.blockMesh 2>&1
t1=$(date +%s.%N); snappyHexMesh -overwrite > log.snappy 2>&1
t2=$(date +%s.%N); topoSet > log.topoSet 2>&1; createPatch -overwrite > log.createPatch 2>&1
t3=$(date +%s.%N); checkMesh > log.checkMesh 2>&1 || true
printf "blockMesh %.1f s | snappyHexMesh %.1f s | topoSet+createPatch %.1f s | células %s\n" $(echo "$t1 - $t0" | bc) $(echo "$t2 - $t1" | bc) $(echo "$t3 - $t2" | bc) $(grep -m1 "cells:" log.checkMesh | awk '{print $2}')
grep -E "Max skewness|Max non-orth|Max aspect|Mesh OK|Failed" log.checkMesh | head -5
