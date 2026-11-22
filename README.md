# GIMP PixelToolkit

Pixel-art utilities for GIMP 2 and GIMP 3. The implementations are kept separate because GIMP 2 uses the legacy `gimpfu` API while GIMP 3 uses Python 3, PyGObject, GTK, and GEGL APIs.

## Choose the implementation for your GIMP version

- `plugins/gimp2/` contains the legacy GIMP 2 plug-ins.
- `plugins/gimp3/` contains the current GIMP 3 plug-ins.
- GIMP 2 and GIMP 3 plug-ins must not be installed together in the same plug-in directory.

Do not copy the entire `plugins/` directory directly into GIMP. Copy only the contents for your GIMP version.

## GIMP 3 install

1. Clone the repository:

   ```bash
   git clone https://github.com/Brody-Clark/Gimp-PixelToolkit.git
   cd Gimp-PixelToolkit
   ```

2. Locate the GIMP 3 plug-in directory under `Edit > Preferences > Folders > Plug-ins`.

3. Copy the contents of `plugins/gimp3/` into that directory:

   ```text
   plugins/gimp3/
   ├── pixel_toolkit_common.py
   ├── color_palette_swap/
   │   └── color_palette_swap.py
   ├── sprite_sheet_layer_exporter/
   │   └── sprite_sheet_layer_exporter.py
   ├── sprite_sheet_slicer/
   │   └── sprite_sheet_slicer.py
   └── xbrz_pixel_scaler/
       └── xbrz_pixel_scaler.py
   ```

4. Keep each GIMP 3 folder and same-named Python script together. GIMP 3 expects the plug-in directory layout to match the script basename.

5. Copy the GIMP 3 plug-in files, restart GIMP, and look under `Image > PixelToolkit`.

Example installation for the current Linux user configuration:

```bash
cp -r plugins/gimp3/* ~/.config/GIMP/3.2/plug-ins/
chmod 755 ~/.config/GIMP/3.2/plug-ins/*/*.py
chmod 644 ~/.config/GIMP/3.2/plug-ins/pixel_toolkit_common.py
rm -f ~/.config/GIMP/3.2/pluginrc
```

The xBRZ GIMP 3 plug-in requires a native library. Build it with CMake:

```bash
cmake -S xbrz_wrapper -B xbrz_wrapper/build
cmake --build xbrz_wrapper/build --config Release
```

Copy the generated `xbrz.dll`, `libxbrz.dylib`, or `libxbrz.so` into `plugins/gimp3/xbrz_pixel_scaler/xbrz/` before copying the GIMP 3 plug-ins. The plug-in reports a clear error when the library is absent. The other GIMP 3 plug-ins do not depend on it.

## GIMP 2 legacy install

`plugins/gimp2/` contains the legacy GIMP 2 implementation and uses `gimpfu`:

```text
plugins/gimp2/
├── sprite_sheet_layer_exporter.py
├── sprite_sheet_slicer.py
└── xbrz_pixel_scaler.py
```

Copy these legacy scripts into the GIMP 2 plug-in directory reported under `Edit > Preferences > Folders > Plug-ins`. Make each script executable and restart GIMP 2.

GIMP 2 support is maintained as a legacy implementation. It is not the same codebase as the GIMP 3 plug-ins and does not include the GIMP 3 Color Palette Swap plug-in.

## Included GIMP 3 plug-ins

### Export As Sprite Sheet

Packs each top-level image layer into its own cell in a square sprite sheet and saves the result as PNG or JPEG. Source layers and the source image are not modified.

### Slice Sprite Sheet

Splits the selected layer into equal-sized tiles and displays a new image containing one layer per tile. Incomplete edges are skipped.

### xBRZ Scale

Scales the selected drawable by a factor from 2 to 6 and opens the result in a new image. Requires the native xBRZ library described above.

### Color Palette Swap

Shows the visible image composite and its unique colors, up to 256 entries. Edit swatches to preview replacements. Create adds the recolored composite as a layer in RGB images. For grayscale or indexed images, it opens the RGB result as a new image.

## Legacy GIMP 2 plug-ins

The GIMP 2 scripts provide:

- Export Sprite Sheet
- Slice Sprite Sheet
- xBRZ Pixel Scaling

GIMP 2 support is no longer the primary development target, but fixes that improve the legacy scripts can still be accepted without changing the GIMP 3 implementation.
