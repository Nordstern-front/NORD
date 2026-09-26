# Barber Simulator: working with Claude

## 3D asset pipeline (Higgsfield → Blender)
This repository configures the `blender` MCP server (`.mcp.json`, package `mcp-for-blender`).
It controls a Blender instance running locally, as long as the "MCP for Blender" add-on
has its server started (N in the 3D viewport → "MCP for Blender" tab → Start MCP Server).

When the user asks for a model (car, chair, prop, character...):
1. Higgsfield (claude.ai connector): generate a reference image of the object — a 3/4 view,
   the whole object visible, a plain white background, no logos or text.
   Check the cost with `get_cost: true`; on a free plan use `gpt_image_2`.
2. Higgsfield `generate_3d`: the cheapest option is `sam_3_3d` (~1 credit); for better quality, the Meshy
   `image_to_3d` models cost more (20–30 credits). Ask before spending more than a few credits.
3. Import the resulting GLB into Blender with the `blender` tool (execute code):
   download the result URL, `bpy.ops.import_scene.gltf`, scale to real size (a car is ~4.5–4.8 m),
   put it on the ground (Z=0) and centre it. The logic is ready in
   `assets/vehicles/peugeot_508_sw/blender/import_higgsfield.py` (swap `GLB_URL`).
4. Save the result in `assets/<category>/<name>/` (the .glb for the game + the .blend) and commit.

Procedural alternative (no credits): `assets/vehicles/peugeot_508_sw/blender/build_508_sw.py`.
