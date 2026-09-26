# Peugeot 508 SW–style estate (side view)

Sample vehicle sprite for Barber Simulator: a side view of an estate car inspired by the Peugeot 508 SW. The car faces right.

- `508_sw_<color>.svg`: vector version (480×160, ground line at y=150). Colors: blue, grey, white, black, red.
- `png/508_sw_<color>@1x.png` (480×160) and `@2x.png` (960×320): transparent PNGs, ready to use in a game engine.
- `generate.py`: generates the SVGs. Add a color to `COLORS` and run `python3 generate.py`.
- `export_png.sh`: renders SVG → PNG (headless Chromium).

Details: long roof with rails, frameless side windows with a chrome surround, "claw" LED tail lamps, slim headlamp with a vertical "fang" DRL, sculpted lower door crease, 5-spoke wheels.
To flip the car so it faces left, flip it horizontally (`scaleX = -1`).
