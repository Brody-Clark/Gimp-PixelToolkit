#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Slice a selected layer into equal-sized tiles."""

import os
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

PROCEDURE_NAME = "pixel-toolkit-slice-sprite-sheet"


def crop_rgba(pixels, source_width, x, y, width, height):
    result = bytearray(width * height * 4)
    for row in range(height):
        source_start = ((y + row) * source_width + x) * 4
        target_start = row * width * 4
        result[target_start:target_start + width * 4] = \
            pixels[source_start:source_start + width * 4]
    return bytes(result)


def run(procedure, run_mode, image, drawables, config, data):
    if not drawables or not isinstance(drawables[0], Gimp.Layer):
        return failure(procedure, "Select a layer to slice.")

    if run_mode == Gimp.RunMode.INTERACTIVE:
        GimpUi.init("sprite-sheet-slicer")
        dialog = GimpUi.ProcedureDialog.new(
            procedure, config, "Slice Sprite Sheet")
        GimpUi.window_set_transient(dialog)
        dialog.fill(["tile-width", "tile-height"])
        accepted = dialog.run()
        dialog.destroy()
        if not accepted:
            return cancelled(procedure)

    tile_width = config.get_property("tile-width")
    tile_height = config.get_property("tile-height")
    drawable = drawables[0]
    source_width = drawable.get_width()
    source_height = drawable.get_height()
    if tile_width < 4 or tile_height < 4:
        return failure(procedure, "Tile dimensions must be at least 4 pixels.")
    if source_width < 4 or source_height < 4:
        return failure(procedure, "The selected layer is smaller than 4x4.")

    tile_width = min(tile_width, source_width)
    tile_height = min(tile_height, source_height)
    if source_width % tile_width or source_height % tile_height:
        Gimp.message(
            "Layer dimensions are not evenly divisible by the tile size; incomplete edges will be skipped.")

    columns = source_width // tile_width
    rows = source_height // tile_height
    source_pixels = read_rgba(
        drawable, width=source_width, height=source_height)
    tile_image = Gimp.Image.new(
        tile_width, tile_height, Gimp.ImageBaseType.RGB)
    tile_number = 0
    for column in range(columns):
        for row in range(rows):
            tile = crop_rgba(
                source_pixels, source_width,
                column * tile_width, row * tile_height,
                tile_width, tile_height)
            new_rgba_layer(tile_image, str(tile_number),
                           tile_width, tile_height, tile)
            tile_number += 1

    show_image(tile_image)
    return succeeded(procedure)


class SpriteSheetSlicer(Gimp.PlugIn):
    def do_query_procedures(self):
        return [PROCEDURE_NAME]

    def do_create_procedure(self, name):
        if name != PROCEDURE_NAME:
            return None
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, run, None)
        procedure.set_menu_label("Slice Sprite Sheet")
        procedure.add_menu_path("<Image>/Image/PixelToolkit")
        procedure.set_attribution("Brody Clark", "Brody Clark", "2026")
        procedure.set_documentation(
            "Slice Sprite Sheet",
            "Split the selected layer into equal-sized tiles.",
            name)
        flags = GObject.ParamFlags.READWRITE
        procedure.add_int_argument(
            "tile-width", "Tile Width", "Width of each tile",
            4, 16384, 16, flags)
        procedure.add_int_argument(
            "tile-height", "Tile Height", "Height of each tile",
            4, 16384, 16, flags)
        return procedure


Gimp.main(SpriteSheetSlicer.__gtype__, sys.argv)