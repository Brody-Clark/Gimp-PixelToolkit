# GIMP PixelToolkit

Pixel-art utilities for GIMP 3, implemented with GIMP's bundled Python 3, PyGObject, GTK, and GEGL APIs.

## Install

1. In GIMP, locate the plug-in directory under `Edit > Preferences > Folders > Plug-ins`.
2. Copy `plugins/pixel_toolkit_common.py` and the four plug-in folders from `plugins` into that directory. Keep each folder and its same-named Python script together; GIMP 3 expects each script name to match its containing plug-in folder.
3. Restart GIMP. The commands appear under `Image > PixelToolkit`.

The xBRZ scaler also requires the native xBRZ shared library. Build it with CMake:

```powershell
cmake -S xbrz_wrapper -B xbrz_wrapper/build
cmake --build xbrz_wrapper/build --config Release
```

Copy the generated `xbrz.dll`, `libxbrz.dylib`, or `libxbrz.so` into `plugins/xbrz_pixel_scaler/xbrz` before installing the scaler folder. The scaler reports a clear error when the library is absent; the other plug-ins do not depend on it.

## Plug-ins

### Export As Sprite Sheet

Packs each top-level image layer into its own cell in a square sprite sheet and saves the result as PNG or JPEG. Source layers and the source image are not modified.

### Slice Sprite Sheet

Splits the selected layer into equal-sized tiles and displays a new image containing one layer per tile. Incomplete edges are skipped.

### xBRZ Scale

Scales the selected drawable by a factor from 2 to 6 and opens the result in a new image. Requires the native xBRZ library described above.

### Color Palette Swap

Shows the visible image composite and its unique colors, up to 256 entries. Edit swatches to preview replacements. Create adds the recolored composite as a layer in RGB images; for grayscale or indexed images, it opens the RGB result as a new image.
