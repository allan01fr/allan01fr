# Renderiza saida/modelo.ifc (tesselação do IfcOpenShell, cores dos estilos do IFC) para conferência visual.
import os, numpy as np, ifcopenshell, ifcopenshell.geom
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
f = ifcopenshell.open(os.path.join(ROOT, "saida", "modelo.ifc"))
st = ifcopenshell.geom.settings(); st.set("use-world-coords", True)
it = ifcopenshell.geom.iterator(st, f, include=f.by_type("IfcDistributionElement") + f.by_type("IfcWall") + f.by_type("IfcPlate"))
tris, cols = [], []
if it.initialize():
    while True:
        s = it.get(); g = s.geometry; v = np.array(g.verts).reshape(-1, 3); fc = np.array(g.faces).reshape(-1, 3)
        mats = g.materials; mid = np.array(g.material_ids)
        for k, t in enumerate(fc):
            m = mats[mid[k]] if len(mats) and mid[k] >= 0 else None
            c = list(m.diffuse.components) if m is not None else [.7, .7, .7]
            a = 0.08 if s.type in ("IfcWall", "IfcPlate") else (1 - (m.transparency if m is not None and m.transparency == m.transparency else 0)) * 0.95
            tris.append(v[t]); cols.append((*c[:3], max(a, 0.15) if s.type not in ("IfcWall", "IfcPlate") else a))
        if not it.next(): break
fig = plt.figure(figsize=(16, 10), dpi=110); ax = fig.add_subplot(111, projection="3d")
ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolors="none"))
ax.set_xlim(-10, 24); ax.set_ylim(-1, 17); ax.set_zlim(-3, 2.5); ax.set_box_aspect((34, 18, 5.5 * 1.6))
ax.view_init(elev=32, azim=-62); ax.set_axis_off()
ax.set_title("modelo.ifc — subsolo (tubos, dutos, terminais; paredes translúcidas) · tesselação IfcOpenShell")
out = os.path.join(HERE, "screenshots", "ifc_render_subsolo.png"); plt.savefig(out, bbox_inches="tight"); print(out, len(tris), "triângulos")
