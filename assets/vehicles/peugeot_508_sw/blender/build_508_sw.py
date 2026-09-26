"""Builds a low/mid-poly 3D model of an estate car inspired by the Peugeot 508 SW.

How to use in Blender (3.0+):
  Scripting tab -> Open -> this file -> Run Script (Alt+P).
The car is created in the "Peugeot508SW" collection (re-running replaces it).
Units are metres, Z up, origin on the ground under the car centre, front facing -Y
(so the Blender "Front" view looks at the car's nose).

Optional: set CAR_EXPORT_DIR to a folder to also export .glb (and save .blend when
running headless).  Export from the UI with File -> Export -> glTF 2.0.
"""
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

CAR_NAME = "Peugeot508SW"
LENGTH = 4.78
WHEEL_R = 0.34
WHEEL_W = 0.225
TRACK_HALF = 0.80
REAR_AXLE_L = 1.04
FRONT_AXLE_L = 3.83


def y_of(l):
    """Length coordinate (0 = rear bumper, LENGTH = nose) -> Blender Y (front at -Y)."""
    return -(l - LENGTH / 2)


# --------------------------------------------------------------------------- materials

def set_input(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return


def material(name, color, metallic=0.0, roughness=0.5, emission=None, strength=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    set_input(bsdf, ["Base Color"], (*color, 1.0))
    set_input(bsdf, ["Metallic"], metallic)
    set_input(bsdf, ["Roughness"], roughness)
    set_input(bsdf, ["Coat Weight", "Clearcoat"], 0.6 if name.endswith("Paint") else 0.0)
    if emission:
        set_input(bsdf, ["Emission Color", "Emission"], (*emission, 1.0))
        set_input(bsdf, ["Emission Strength"], strength)
    mat.diffuse_color = (*color, 1.0)  # viewport solid colour
    return mat


def make_materials():
    return {
        "paint": material(f"{CAR_NAME}_Paint", (0.025, 0.07, 0.20), 0.6, 0.28),
        "glass": material(f"{CAR_NAME}_Glass", (0.01, 0.015, 0.02), 0.0, 0.05),
        "trim": material(f"{CAR_NAME}_Trim", (0.012, 0.012, 0.014), 0.0, 0.3),
        "plastic": material(f"{CAR_NAME}_Plastic", (0.02, 0.02, 0.022), 0.0, 0.7),
        "chrome": material(f"{CAR_NAME}_Chrome", (0.8, 0.8, 0.82), 1.0, 0.12),
        "tire": material(f"{CAR_NAME}_Tire", (0.018, 0.018, 0.018), 0.0, 0.85),
        "rim": material(f"{CAR_NAME}_Rim", (0.55, 0.56, 0.58), 1.0, 0.25),
        "rim_dark": material(f"{CAR_NAME}_RimDark", (0.05, 0.05, 0.055), 0.8, 0.35),
        "head": material(f"{CAR_NAME}_HeadLight", (0.9, 0.92, 1.0), 0.0, 0.1, (0.9, 0.95, 1.0), 4.0),
        "tail": material(f"{CAR_NAME}_TailLight", (0.5, 0.0, 0.01), 0.0, 0.15, (1.0, 0.02, 0.02), 3.0),
        "plate": material(f"{CAR_NAME}_Plate", (0.85, 0.85, 0.85), 0.0, 0.4),
        "well": material(f"{CAR_NAME}_WheelWell", (0.008, 0.008, 0.008), 0.0, 0.9),
    }


# --------------------------------------------------------------------------- helpers

def new_object(name, mesh, col, mats, parent=None):
    obj = bpy.data.objects.new(name, mesh)
    for m in mats:
        mesh.materials.append(m)
    col.objects.link(obj)
    obj.parent = parent
    return obj


def shade_smooth(mesh):
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))


def _snapshot(bm):
    return set(bm.verts)


def _new_verts(bm, old):
    return [v for v in bm.verts if v not in old]


def bm_box(bm, size, matrix, mat_index=0, bevel=0.0):
    old = _snapshot(bm)
    geom = bmesh.ops.create_cube(bm, size=1.0)
    verts = geom["verts"]
    bmesh.ops.transform(bm, matrix=Matrix.Diagonal((*size, 1.0)), verts=verts)
    if bevel:
        edges = list({e for v in verts for e in v.link_edges})
        bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=2, profile=0.5, affect="EDGES")
        verts = _new_verts(bm, old)
    faces = {f for v in verts for f in v.link_faces}
    bmesh.ops.transform(bm, matrix=matrix, verts=verts)
    for f in faces:
        f.material_index = mat_index


def bm_cylinder_x(bm, radius, depth, center, mat_index=0, segments=32, bevel=0.0):
    """Cylinder whose axis is the X axis."""
    old = _snapshot(bm)
    geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=segments,
                                 radius1=radius, radius2=radius, depth=depth)
    verts = geom["verts"]
    if bevel:
        edges = [e for e in {e for v in verts for e in v.link_edges}
                 if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-6]
        bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=3, profile=0.5, affect="EDGES")
        verts = _new_verts(bm, old)
    faces = {f for v in verts for f in v.link_faces}
    mat = Matrix.Translation(center) @ Matrix.Rotation(math.radians(90), 4, "Y")
    bmesh.ops.transform(bm, matrix=mat, verts=verts)
    for f in faces:
        f.material_index = mat_index


def mesh_from_bm(name, bm):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def bake_modifiers(obj):
    """Apply the modifier stack without relying on operator context."""
    dg = bpy.context.evaluated_depsgraph_get()
    new_mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    obj.modifiers.clear()
    obj.data = new_mesh
    bpy.data.meshes.remove(old)


# --------------------------------------------------------------------------- body

# Key cross-sections along the car:
# L (from rear), z bottom, z beltline, z top, half-width at shoulder, half-width at roof, roof crown
KEYS = [
    (0.00, 0.40, 0.60, 0.72, 0.80, 0.72, 0.00),
    (0.05, 0.28, 0.82, 0.90, 0.89, 0.80, 0.00),
    (0.12, 0.20, 0.90, 1.08, 0.92, 0.72, 0.01),
    (0.30, 0.18, 0.92, 1.34, 0.93, 0.64, 0.02),
    (0.45, 0.17, 0.93, 1.40, 0.93, 0.63, 0.03),
    (1.40, 0.16, 0.93, 1.43, 0.93, 0.63, 0.03),
    (2.30, 0.16, 0.95, 1.42, 0.93, 0.64, 0.03),
    (2.72, 0.17, 0.96, 1.36, 0.93, 0.66, 0.03),
    (2.97, 0.17, 0.96, 1.19, 0.93, 0.74, 0.02),
    (3.22, 0.18, 0.95, 1.01, 0.93, 0.84, 0.01),
    (3.60, 0.19, 0.93, 0.98, 0.92, 0.85, 0.01),
    (4.00, 0.20, 0.89, 0.94, 0.91, 0.84, 0.01),
    (4.35, 0.22, 0.84, 0.89, 0.89, 0.80, 0.01),
    (4.60, 0.26, 0.77, 0.81, 0.84, 0.74, 0.00),
    (4.74, 0.31, 0.68, 0.72, 0.76, 0.66, 0.00),
    (4.78, 0.36, 0.60, 0.64, 0.66, 0.58, 0.00),
]
# Extra stations so that window/pillar boundaries fall on edges.
STATIONS = sorted({k[0] for k in KEYS} | {0.58, 0.66, 1.0, 1.78, 1.86})


def section(l):
    for a, b in zip(KEYS, KEYS[1:]):
        if a[0] <= l <= b[0]:
            t = (l - a[0]) / (b[0] - a[0])
            return [pa + (pb - pa) * t for pa, pb in zip(a[1:], b[1:])]
    raise ValueError(l)


def ring(zb, zs, zt, w, wt, crown):
    right = [(w - 0.07, zb), (w, zb + 0.15), (w, zs - 0.10), (w - 0.015, zs),
             (wt, zt - 0.03), (wt - 0.08, zt)]
    return [(0.0, zb)] + right + [(0.0, zt + crown)] + [(-x, z) for x, z in reversed(right)]


# ring edge k joins ring point k and k+1 (14 points, closed)
BOTTOM, SIDE_GLASS, TOP = {0, 13}, {4, 9}, {5, 6, 7, 8}


def segment_materials(lm, M):
    """Material index per ring edge for the segment whose middle is at lm."""
    mats = {k: M["paint"] for k in range(14)}
    for k in BOTTOM:
        mats[k] = M["plastic"]
    if 0.12 < lm < 0.45:                              # tailgate window
        for k in TOP:
            mats[k] = M["glass"]
    if 0.30 < lm < 2.72:                              # side windows + C/B pillars
        pillar = 0.58 < lm < 0.66 or 1.78 < lm < 1.86
        for k in SIDE_GLASS:
            mats[k] = M["trim"] if pillar else M["glass"]
    if 2.72 < lm < 3.22:                              # windscreen + black A pillars
        for k in TOP:
            mats[k] = M["glass"]
        for k in SIDE_GLASS:
            mats[k] = M["trim"]
    return mats


def build_body(col, M, parent):
    order = list(M)
    verts, faces, face_mats = [], [], []
    n = 14
    for l in STATIONS:
        for x, z in ring(*section(l)):
            verts.append((x, y_of(l), z))
    for i in range(len(STATIONS) - 1):
        mats = segment_materials((STATIONS[i] + STATIONS[i + 1]) / 2, M)
        a, b = i * n, (i + 1) * n
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((a + k, a + k2, b + k2, b + k))
            face_mats.append(order.index(next(key for key in M if M[key] == mats[k])))
    last = (len(STATIONS) - 1) * n
    faces.append(tuple(reversed(range(n))))                  # rear cap
    face_mats.append(order.index("paint"))
    faces.append(tuple(range(last, last + n)))               # nose cap
    face_mats.append(order.index("paint"))

    mesh = bpy.data.meshes.new(f"{CAR_NAME}_Body")
    mesh.from_pydata(verts, [], faces)
    mesh.polygons.foreach_set("material_index", face_mats)
    mesh.update()
    # make normals point outwards
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    shade_smooth(mesh)
    body = new_object(f"{CAR_NAME}_Body", mesh, col, [M[k] for k in order], parent)

    sub = body.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = sub.render_levels = 2

    # wheel arches: boolean cutters (one per wheel, so there is no tunnel under the car)
    cutters = []
    for l in (REAR_AXLE_L, FRONT_AXLE_L):
        for side in (1, -1):
            bm = bmesh.new()
            bm_cylinder_x(bm, 0.395, 0.6, Vector((side * 0.95, y_of(l), WHEEL_R + 0.02)), segments=48)
            cut = new_object("ArchCutter", mesh_from_bm("ArchCutter", bm), col, [M["well"]])
            cut.hide_render = True
            cut.display_type = "WIRE"
            mod = body.modifiers.new(f"Arch{len(cutters)}", "BOOLEAN")
            mod.operation = "DIFFERENCE"
            mod.solver = "EXACT"
            mod.object = cut
            cutters.append(cut)
    bake_modifiers(body)
    for cut in cutters:
        bpy.data.meshes.remove(cut.data)
    shade_smooth(body.data)
    return body


# --------------------------------------------------------------------------- details

def surface(body, origin, direction):
    hit, loc, normal, _ = body.ray_cast(Vector(origin), Vector(direction).normalized())
    return (loc, normal) if hit else (None, None)


def place_on(body, origin, direction, size, sink=0.35):
    """Matrix for a box whose -Y face points along the surface normal at the hit point."""
    loc, normal = surface(body, origin, direction)
    if loc is None:
        return None
    rot = Vector((0, -1, 0)).rotation_difference(normal).to_matrix().to_4x4()
    return Matrix.Translation(loc - normal * size[1] * sink) @ rot


def build_details(body, col, M, parent):
    order = ["paint", "chrome", "head", "tail", "plate", "plastic", "trim"]
    idx = {k: i for i, k in enumerate(order)}
    bm = bmesh.new()

    def add(origin, direction, size, mat, bevel=0.0, sink=0.35):
        m = place_on(body, origin, direction, size, sink)
        if m is not None:
            bm_box(bm, size, m, idx[mat], bevel)

    front, rear = (0, 1, 0), (0, -1, 0)  # ray directions into the body
    for s in (1, -1):
        # slim headlamps + vertical "fang" daytime running lights
        add((s * 0.60, -3, 0.72), front, (0.36, 0.05, 0.075), "head", 0.01)
        add((s * 0.71, -3, 0.50), front, (0.035, 0.04, 0.24), "head", 0.008)
        # "claw" tail lamps
        add((s * 0.60, 3, 0.80), rear, (0.40, 0.05, 0.10), "tail", 0.01)
        add((s * 0.86, 2.2, 0.80), (-s, 0, 0), (0.18, 0.04, 0.09), "tail", 0.01)
        # flush door handles
        for l in (1.25, 2.40):
            add((s * 2, y_of(l), 0.83), (-s, 0, 0), (0.17, 0.02, 0.028), "chrome", 0.006)
        # mirrors (painted cap on a black arm)
        y = y_of(2.92)
        arm = Matrix.Translation((s * 0.97, y, 0.99))
        bm_box(bm, (0.12, 0.08, 0.04), arm, idx["trim"])
        cap = Matrix.Translation((s * 1.04, y + 0.03, 1.02))
        bm_box(bm, (0.08, 0.20, 0.12), cap, idx["paint"], 0.03)
    # front grille, lower intake, plates, rear diffuser
    add((0, -3, 0.55), front, (1.00, 0.06, 0.22), "trim", 0.02, sink=0.5)
    add((0, -3, 0.34), front, (1.30, 0.06, 0.10), "plastic", 0.02, sink=0.5)
    add((0, -3, 0.44), front, (0.52, 0.02, 0.11), "plate", 0.005, sink=0.0)
    add((0, 3, 0.64), rear, (0.52, 0.02, 0.11), "plate", 0.005, sink=0.0)
    add((0, 3, 0.47), rear, (1.30, 0.06, 0.12), "plastic", 0.02, sink=0.5)
    # shark-fin antenna
    loc, _ = surface(body, (0, y_of(0.7), 3), (0, 0, -1))
    if loc:
        bm_box(bm, (0.05, 0.16, 0.06), Matrix.Translation(loc + Vector((0, 0, 0.02))), idx["trim"], 0.02)

    mesh = mesh_from_bm(f"{CAR_NAME}_Details", bm)
    shade_smooth(mesh)
    new_object(f"{CAR_NAME}_Details", mesh, col, [M[k] for k in order], parent)


def curve_mesh(name, points, radius, mat, col, parent):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    spline = cu.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1.0)
    tmp = bpy.data.objects.new(name, cu)
    col.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    shade_smooth(mesh)
    return new_object(name, mesh, col, [mat], parent)


def build_trim(body, col, M, parent):
    samples = [0.30 + i * (2.72 - 0.30) / 24 for i in range(25)]
    for s in (1, -1):
        # chrome window line along the beltline
        pts = []
        for l in samples:
            _, zs, *_ = section(l)
            loc, n = surface(body, (s * 2, y_of(l), zs + 0.015), (-s, 0, 0))
            if loc:
                pts.append(loc + n * 0.004)
        if len(pts) > 1:
            curve_mesh(f"{CAR_NAME}_WindowTrim", pts, 0.009, M["chrome"], col, parent)
        # roof rails
        rail = []
        for i in range(13):
            l = 0.50 + i * (2.35 - 0.50) / 12
            loc, _ = surface(body, (s * 0.55, y_of(l), 3), (0, 0, -1))
            if loc:
                lift = 0.05 if 0 < i < 12 else 0.0
                rail.append(loc + Vector((0, 0, lift)))
        if len(rail) > 1:
            curve_mesh(f"{CAR_NAME}_RoofRail", rail, 0.016, M["trim"], col, parent)


def build_wheel(name, center, side, col, M, parent):
    order = ["tire", "rim", "rim_dark", "chrome"]
    i = {k: n for n, k in enumerate(order)}
    bm = bmesh.new()
    c = Vector(center)
    out = Vector((side, 0, 0))
    bm_cylinder_x(bm, WHEEL_R, WHEEL_W, c, i["tire"], 40, bevel=0.06)
    bm_cylinder_x(bm, 0.235, 0.02, c + out * (WHEEL_W / 2 - 0.005), i["rim"], 40)
    bm_cylinder_x(bm, 0.205, 0.02, c + out * (WHEEL_W / 2 + 0.002), i["rim_dark"], 40)
    for k in range(5):  # 5 double spokes
        ang = math.radians(72 * k)
        for off in (-0.028, 0.028):
            m = (Matrix.Translation(c + out * (WHEEL_W / 2 + 0.01))
                 @ Matrix.Rotation(ang, 4, "X")
                 @ Matrix.Translation((0, off, 0.105)))
            bm_box(bm, (0.02, 0.03, 0.20), m, i["rim"])
    bm_cylinder_x(bm, 0.055, 0.03, c + out * (WHEEL_W / 2 + 0.018), i["chrome"], 24)
    mesh = mesh_from_bm(name, bm)
    shade_smooth(mesh)
    return new_object(name, mesh, col, [M[k] for k in order], parent)


# --------------------------------------------------------------------------- main

def build():
    old = bpy.data.collections.get(CAR_NAME)
    if old:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    col = bpy.data.collections.new(CAR_NAME)
    bpy.context.scene.collection.children.link(col)

    root = bpy.data.objects.new(CAR_NAME, None)
    root.empty_display_type = "PLAIN_AXES"
    col.objects.link(root)

    M = make_materials()
    body = build_body(col, M, root)
    build_details(body, col, M, root)
    build_trim(body, col, M, root)
    for tag, l in (("Rear", REAR_AXLE_L), ("Front", FRONT_AXLE_L)):
        for side_name, s in (("L", -1), ("R", 1)):
            build_wheel(f"{CAR_NAME}_Wheel{tag}{side_name}",
                        (s * TRACK_HALF, y_of(l), WHEEL_R), s, col, M, root)
    return col


def export(col, folder):
    os.makedirs(folder, exist_ok=True)
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj.name in col.objects)
    bpy.ops.export_scene.gltf(filepath=os.path.join(folder, "peugeot_508_sw.glb"),
                              export_format="GLB", use_selection=True, export_apply=True)


if __name__ == "__main__":
    collection = build()
    out_dir = os.environ.get("CAR_EXPORT_DIR")
    if out_dir:
        export(collection, out_dir)
        if bpy.app.background:
            bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "peugeot_508_sw.blend"))
    print(f"{CAR_NAME}: built", len(collection.objects), "objects")
