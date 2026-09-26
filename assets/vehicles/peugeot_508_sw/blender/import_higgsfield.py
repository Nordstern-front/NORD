"""Downloads a GLB generated in Higgsfield and imports it into the open Blender scene.

Scripting tab -> Open -> this file -> Run Script (Alt+P).
The model is scaled to a real car length (LENGTH_M), set on the ground (Z=0)
and centred, then placed in the "Higgsfield" collection.  From there:
File -> Export -> glTF 2.0 (.glb) and add it to the game.
"""
import os
import tempfile
import urllib.request

import bpy
from mathutils import Vector

# Result of the Higgsfield job (SAM 3 3D, from the image of a 508 SW-style estate).
# Paste the link to another generation from Higgsfield here.
GLB_URL = ("https://d8j0ntlcm91z4.cloudfront.net/user_3JpqXMrTZYTLhJpX9HQK5eX9mtC/"
           "hf_20260926_111607_d980be0f-fb34-475c-9271-5f3667a81467.glb")
NAME = "Higgsfield_508SW"
LENGTH_M = 4.78


def download(url):
    path = os.path.join(tempfile.gettempdir(), NAME + ".glb")
    urllib.request.urlretrieve(url, path)
    return path


def world_bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def main():
    path = download(GLB_URL)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    if not new:
        raise RuntimeError("GLB import produced no objects")

    col = bpy.data.collections.get("Higgsfield") or bpy.data.collections.new("Higgsfield")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)

    root = bpy.data.objects.new(NAME, None)
    col.objects.link(root)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        if o.parent is None:
            o.parent = root

    bpy.context.view_layer.update()
    lo, hi = world_bounds(new)
    size = hi - lo
    scale = LENGTH_M / max(size.x, size.y)  # the car's longest horizontal axis = its length
    root.scale = (scale, scale, scale)
    centre = (lo + hi) / 2
    root.location = (-centre.x * scale, -centre.y * scale, -lo.z * scale)
    print(f"{NAME}: imported {len(new)} objects, scale {scale:.3f}")


main()
