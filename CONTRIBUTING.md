# Contributing

## Development setup

Clone the repository and use the checked-out source as the development copy:

```bash
cd Gimp-PixelToolkit
python3 -m compileall -q plugins
```

Verify that the expected plug-in structure is preserved when you install or copy files:

```text
plugins/
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

GIMP 3 expects the executable Python file to be in a subdirectory, and this project also requires the script basename to match its containing folder. Keep the checked-in layout and copy the complete plug-in folder rather than only the `.py` file.

## Installing a development copy

Find GIMP's configured plug-in directories under:

`Edit > Preferences > Folders > Plug-ins`

On Linux, the common user plug-in directory is:

```text
~/.config/GIMP/3.2/plug-ins/
```

Copy the source files into that directory. For example:

```bash
cp -r plugins/* ~/.config/GIMP/3.2/plug-ins/
chmod 755 ~/.config/GIMP/3.2/plug-ins/*/*.py
chmod 644 ~/.config/GIMP/3.2/plug-ins/pixel_toolkit_common.py
```

Only the plug-in entry scripts need to be executable. Shared modules such as `pixel_toolkit_common.py` should not be executable.

After copying or changing plug-ins, rebuild GIMP's plug-in cache:

```bash
rm -f ~/.config/GIMP/3.2/pluginrc
```

Completely restart GIMP before testing. The plug-in cache is stored at:

```text
~/.config/GIMP/3.2/pluginrc
```

## Starting GIMP with diagnostics

Use GIMP's verbose and console output modes while reproducing a loading or runtime problem:

```bash
gimp --new-instance --verbose --console-messages --no-splash
```

Close GIMP and save the startup log for inspection:

```bash
gimp --new-instance --verbose --console-messages --no-splash 2>&1 | tee ~/gimp-plugin-debug.log
```

Search the log for plug-in names and errors:

```bash
grep -nEi 'pixel|toolkit|sprite|palette|xbrz|Skipping|Traceback|AssertionError|Failed|error' ~/gimp-plugin-debug.log
```

Relevant startup locations and files include:

- Plug-in directory: `~/.config/GIMP/3.2/plug-ins/`
- Plug-in cache: `~/.config/GIMP/3.2/pluginrc`
- GIMP configuration: `~/.config/GIMP/3.2/`
- GIMP console output: terminal started with `--console-messages`
- Snap GIMP package data: `/snap/gimp/current/`

## Checking plug-in discovery

Before starting GIMP, inspect the installed files and permissions:

```bash
find ~/.config/GIMP/3.2/plug-ins -maxdepth 2 -type f -printf '%p %m\n'
```

Check whether GIMP registered a procedure after startup:

```bash
grep -nEi 'pixel-toolkit|color_palette|sprite_sheet|xbrz' ~/.config/GIMP/3.2/pluginrc || true
```

Common discovery messages include:

- `Skipping potential plug-in ... plug-ins must be installed in subdirectories`: the `.py` file is not nested correctly, or GIMP is scanning the wrong layout.
- `Traceback` or `AssertionError`: GIMP found the script but failed while loading it.
- `unexpected EOF` while querying or initializing a plug-in: the plug-in process exited during startup or registration.

Also confirm that GIMP is actually using the plug-in directory reported in `Edit > Preferences > Folders > Plug-ins`. Multiple GIMP installations or GIMP packaging formats can use different paths.

## Syntax and import checks

Compile the Python source before copying it:

```bash
python3 -m compileall -q plugins
```

To validate only the changed plug-in:

```bash
python3 -m compileall -q plugins/color_palette_swap/color_palette_swap.py
```

Do not expect direct execution from a normal host terminal to prove that a GIMP plug-in works. GIMP 3's `Gimp`, `GimpUi`, and GTK introspection namespaces are provided by GIMP's runtime environment and may not be available to the system Python.

## GTK and GDK issues

GTK and GDK namespace versions should be explicit before importing them. For example:

```python
gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
```

Pinning the GIMP 3 plug-ins to GTK 3/GDK 3 prevents accidental loading of GTK 4 introspection and GTK 4 overrides when running in an environment that provides conflicting libraries.

A `GLib-GIRepository-WARNING` about `libgtk-4.so.1`, a missing symbol, or an `AssertionError` in `gi/overrides/Gdk.py` may indicate a package/runtime library mismatch rather than a problem in the plug-in's menu or procedure registration. Prefer a GIMP build whose GTK, PyGObject, and Gimp typelib versions come from the same package environment.

## Reproducing runtime failures

When a plug-in appears in the menu but fails when run:

1. Close GIMP completely.
2. Start GIMP with `--verbose --console-messages --no-splash`.
3. Open or create an image suitable for the plug-in.
4. Run the plug-in from `Image > PixelToolkit`.
5. Capture the traceback and save the relevant line from the terminal.
6. Check the GIMP console first for the Python traceback and then inspect `~/.config/GIMP/3.2/pluginrc` for registration problems.

Include this information in bug reports:

- GIMP version and packaging format (`gimp --version`, for example Snap or distro package)
- Linux distribution and version
- GTK/Python traceback
- Installed plug-in layout and permissions
- Exact GIMP plug-in directory
- Steps and image type used to reproduce the failure
- Whether the plug-in loaded at startup and only failed when invoked
