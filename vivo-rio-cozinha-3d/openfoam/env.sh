# Ambiente do OpenFOAM para os scripts desta pasta. Ordem:
#   1) o que já estiver carregado (você deu `source` no bashrc do seu OpenFOAM e blockMesh está no PATH);
#   2) um bashrc de instalação ESI conhecido (/usr/lib/openfoam/openfoam*/etc/bashrc, /opt/openfoam*/etc/bashrc, ~/OpenFOAM/OpenFOAM-v*/etc/bashrc);
#   3) o pacote Ubuntu/Debian `openfoam` v1912, que não traz o bashrc completo: ambiente mínimo.
# Os scripts foram validados no OpenFOAM ESI v1912; em versões novas confira os nomes dos solvers (ver README).
if ! { command -v blockMesh >/dev/null 2>&1 && [ -n "$WM_PROJECT_DIR" ]; }; then
  for rc in /usr/lib/openfoam/openfoam*/etc/bashrc /opt/openfoam*/etc/bashrc "$HOME"/OpenFOAM/OpenFOAM-v*/etc/bashrc; do
    if [ -f "$rc" ]; then source "$rc" >/dev/null 2>&1 || true; command -v blockMesh >/dev/null 2>&1 && break; fi
  done
fi
if ! command -v blockMesh >/dev/null 2>&1 || [ -z "$WM_PROJECT_DIR" ]; then
  export WM_PROJECT_DIR=/usr/share/openfoam FOAM_ETC=/usr/share/openfoam/etc WM_PROJECT=OpenFOAM WM_PROJECT_VERSION=v1912
fi
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1   # só necessário em contêiner rodando como root
