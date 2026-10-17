# Ambiente mínimo para o OpenFOAM v1912 do pacote Ubuntu (o pacote não traz o bashrc completo do projeto).
export WM_PROJECT_DIR=/usr/share/openfoam FOAM_ETC=/usr/share/openfoam/etc WM_PROJECT=OpenFOAM WM_PROJECT_VERSION=v1912
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1   # só necessário em contêiner rodando como root
