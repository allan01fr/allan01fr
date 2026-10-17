#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Transporte de fumaça (escalar passivo) sobre o campo de escoamento estacionário já calculado (scalarTransportFoam).
A superfície de cocção (patch hotTop) libera concentração 1; a exaustão (inletOutlet) e o ar de reposição (0) fecham o balanço.
O escoamento fica congelado: o que anima é a fumaça, não o escoamento (que é estacionário). Isso é pós-processamento, não uma simulação transiente.
Uso: python3 fumaca.py <caso_estacionario> <destino> [--t-fim 60] [--dt 0.05] [--DT 0.01]"""
import argparse, os, re, shutil, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import rodar_teste as RT, gerar_caso as G

def cab(cls, obj, loc): return G.cab(cls, obj, loc)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("caso"); ap.add_argument("dest"); ap.add_argument("--t-fim", type=float, default=60.0)
    ap.add_argument("--dt", type=float, default=0.05); ap.add_argument("--DT", type=float, default=0.01); ap.add_argument("--escreve", type=float, default=1.0)
    a = ap.parse_args()
    tempos = sorted((d for d in os.listdir(a.caso) if re.fullmatch(r"\d+(\.\d+)?", d) and float(d) > 0), key=float)
    if not tempos: sys.exit("o caso estacionário não tem tempo > 0 gravado")
    ult = tempos[-1]; d = a.dest; shutil.rmtree(d, ignore_errors=True)
    for sub in ("constant", "system", "0"): os.makedirs(os.path.join(d, sub))
    shutil.copytree(os.path.join(a.caso, "constant/polyMesh"), os.path.join(d, "constant/polyMesh"))
    for f in ("U", "phi"): shutil.copy(os.path.join(a.caso, ult, f), os.path.join(d, "0", f))
    # patches (a partir da malha)
    bd = open(os.path.join(d, "constant/polyMesh/boundary")).read()
    patches = re.findall(r"\n\s{4}(\w+)\n\s{4}\{\n(.*?)\n\s{4}\}", bd, re.S)
    corpo = ""
    for nome, _ in patches:
        if nome == "hotTop": bc = "        type fixedValue;\n        value uniform 1;"
        elif nome.startswith("reposicao"): bc = "        type fixedValue;\n        value uniform 0;"
        elif nome.startswith("exaustao"): bc = "        type inletOutlet;\n        inletValue uniform 0;\n        value uniform 0;"
        else: bc = "        type zeroGradient;"
        corpo += f"    {nome}\n    {{\n{bc}\n    }}\n"
    open(os.path.join(d, "0/T"), "w").write(cab("volScalarField", "T", "0") + f"dimensions      [0 0 0 0 0 0 0];\n\ninternalField   uniform 0;\n\nboundaryField\n{{\n{corpo}}}\n")
    open(os.path.join(d, "constant/transportProperties"), "w").write(cab("dictionary", "transportProperties", "constant") + f"DT              DT [0 2 -1 0 0 0 0] {a.DT};\n")
    open(os.path.join(d, "system/controlDict"), "w").write(cab("dictionary", "controlDict", "system") + f"""application     scalarTransportFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {a.t_fim};
deltaT          {a.dt};
writeControl    adjustableRunTime;
writeInterval   {a.escreve};
purgeWrite      0;
writeFormat     binary;
writePrecision  14;
timeFormat      general;
timePrecision   6;
runTimeModifiable false;
""")
    open(os.path.join(d, "system/fvSchemes"), "w").write(cab("dictionary", "fvSchemes", "system") + """ddtSchemes      { default Euler; }
gradSchemes     { default Gauss linear; }
divSchemes      { default none; div(phi,T) Gauss limitedLinear 1; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes   { default corrected; }
""")
    open(os.path.join(d, "system/fvSolution"), "w").write(cab("dictionary", "fvSolution", "system") + """solvers
{
    T { solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol 0; }
}
SIMPLE { nNonOrthogonalCorrectors 0; }
""")
    t0 = time.time(); seg, mem, rc = RT.sh("scalarTransportFoam", d, "log.fumaca"); print(f"scalarTransportFoam: rc={rc}, {seg:.0f} s, pico {mem:.0f} MB, campo de partida = tempo {ult}")

if __name__ == "__main__": main()
