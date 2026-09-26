# Peugeot 508 SW–style estate (side view)

Sample vehicle sprite for Barber Simulator: a side view of an estate car inspired by the Peugeot 508 SW. The car faces right.

- `508_sw_<color>.svg`: vector version (480×160, ground line at y=150). Colors: blue, grey, white, black, red.
- `png/508_sw_<color>@1x.png` (480×160) and `@2x.png` (960×320): transparent PNGs, ready to use in a game engine.
- `generate.py`: generates the SVGs. Add a color to `COLORS` and run `python3 generate.py`.
- `export_png.sh`: renders SVG → PNG (headless Chromium).

Details: long roof with rails, frameless side windows with a chrome surround, "claw" LED tail lamps, slim headlamp with a vertical "fang" DRL, sculpted lower door crease, 5-spoke wheels.
To flip the car so it faces left, flip it horizontally (`scaleX = -1`).

## 3D model (Blender)

### A) Procedural model: `blender/`
- `peugeot_508_sw.glb`: ready-made model for the game (glTF 2.0, metres, ~6.8k faces, PBR materials).
- `peugeot_508_sw.blend`: the same model as a Blender file.
- `build_508_sw.py`: generator. In Blender go to **Scripting → Open → Run Script** and the car is created in the `Peugeot508SW` collection. Separate objects: body, details (lights, grille, plates, mirrors), roof rails, chrome trim, 4 wheels (they can be rotated in the game).
- `renders/`: previews.

Axes: Z up, the car's front faces −Y, the origin is on the ground at the car's centre. The glTF export converts to Y-up automatically.

### B) Model from Higgsfield (AI)
Pipeline: Higgsfield `gpt_image_2` (reference image of a 508 SW-style estate) → `sam_3_3d` (image → textured GLB).

- `blender/import_higgsfield.py`: run it in Blender (Scripting → Run Script). It downloads the GLB from Higgsfield, scales it to 4.78 m, sets it on the ground and centres it in the `Higgsfield` collection.
  To import another generation, paste its GLB link into `GLB_URL`.
- Higgsfield jobs: image `e2dc20fe-0bf6-42d2-b4c2-fd3b41898c66`, 3D `d980be0f-fb34-475c-9271-5f3667a81467`.
