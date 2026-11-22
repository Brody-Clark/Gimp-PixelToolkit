#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scale a selected drawable with the native xBRZ library."""

import ctypes
import os
import platform
import sys

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gimp, GimpUi, GObject

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_ROOT)
from pixel_toolkit_common import (
    cancelled,
    failure,
    new_rgba_layer,
    read_rgba,
    show_image,
    succeeded,
)

PROCEDURE_NAME = "pixel-toolkit-xbrz-scale"


def load_xbrz_library():
    library_name = {
        "Windows": "xbrz.dll",
        "Darwin": "xbrz.dylib",
    }.get(platform.system(), "xbrz.so")
    library_root = os.path.join(os.path.dirname(__file__), "xbrz")
    for root, directories, filenames in os.walk(library_root):
        for filename in filenames:
            if filename.lower() == library_name.lower():
                return ctypes.CDLL(os.path.join(root, filename))
    raise RuntimeError(
        "%s was not found under %s. Build and install the xBRZ library first."
        % (library_name, library_root)
    )


def rgba_to_bgra(pixels):
    result = bytearray(pixels)
    for offset in range(0, len(result), 4):
        result[offset], result[offset + 2] = (result[offset + 2], result[offset])
    return result


def run(procedure, run_mode, image, drawables, config, data):
    if not drawables or not isinstance(drawables[0], Gimp.Drawable):
        return failure(procedure, "Select a drawable to scale.")

    if run_mode == Gimp.RunMode.INTERACTIVE:
        GimpUi.init("xbrz-pixel-scaler")
        dialog = GimpUi.ProcedureDialog.new(procedure, config, "xBRZ Pixel Scaler")
        GimpUi.window_set_transient(dialog)
        dialog.fill(["scale-factor"])
        accepted = dialog.run()
        dialog.destroy()
        if not accepted:
            return cancelled(procedure)

    scale_factor = config.get_property("scale-factor")
    if scale_factor < 2 or scale_factor > 6:
        return failure(procedure, "Scale factor must be between 2 and 6.")

    drawable = drawables[0]
    width = drawable.get_width()
    height = drawable.get_height()
    try:
        library = load_xbrz_library()
        library.Scale.argtypes = [
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
        ]
        library.Scale.restype = None

        source = rgba_to_bgra(read_rgba(drawable, width=width, height=height))
        source_pixels = (ctypes.c_uint32 * (width * height)).from_buffer(source)
        scaled_width = width * scale_factor
        scaled_height = height * scale_factor
        output_pixels = (ctypes.c_uint32 * (scaled_width * scaled_height))()
        library.Scale(
            scale_factor, source_pixels, output_pixels, width, height, 1, 0, height
        )
        output_bgra = ctypes.string_at(
            ctypes.addressof(output_pixels), ctypes.sizeof(output_pixels)
        )
        output_rgba = rgba_to_bgra(output_bgra)

        scaled_image = Gimp.Image.new(
            scaled_width, scaled_height, Gimp.ImageBaseType.RGB
        )
        new_rgba_layer(
            scaled_image, "Scaled Layer", scaled_width, scaled_height, output_rgba
        )
        show_image(scaled_image)
    except Exception as error:
        return failure(procedure, error)
    return succeeded(procedure)


class XbrzPixelScaler(Gimp.PlugIn):
    def do_query_procedures(self):
        return [PROCEDURE_NAME]

    def do_create_procedure(self, name):
        if name != PROCEDURE_NAME:
            return None
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, run, None
        )
        procedure.set_menu_label("xBRZ Scale")
        procedure.add_menu_path("<Image>/Image/PixelToolkit")
        procedure.set_attribution("Brody Clark", "Brody Clark", "2026")
        procedure.set_documentation(
            "xBRZ Scale", "Scale the selected drawable using the xBRZ algorithm.", name
        )
        procedure.add_int_argument(
            "scale-factor",
            "Scale Factor",
            "xBRZ scale factor",
            2,
            6,
            2,
            GObject.ParamFlags.READWRITE,
        )
        return procedure


Gimp.main(XbrzPixelScaler.__gtype__, sys.argv)
