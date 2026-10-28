#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pack each top-level image layer into a sprite-sheet cell."""

import math
import os
import sys

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gimp, GimpUi, Gtk

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_ROOT)
from pixel_toolkit_common import (
    cancelled,
    export_image,
    failure,
    new_rgba_layer,
    read_rgba,
    succeeded,
)

PROCEDURE_NAME = "pixel-toolkit-export-sprite-sheet"


def make_sprite_sheet(image):
    layers = list(image.get_layers())
    if not layers:
        raise ValueError("The image has no layers to export.")

    cell_width = image.get_width()
    cell_height = image.get_height()
    columns = int(math.ceil(math.sqrt(len(layers))))
    sheet_width = columns * cell_width
    sheet_height = columns * cell_height
    sheet_pixels = bytearray(sheet_width * sheet_height * 4)

    for index, layer in enumerate(layers):
        layer_width = layer.get_width()
        layer_height = layer.get_height()
        source = read_rgba(layer, width=layer_width, height=layer_height)
        offsets_valid, layer_x, layer_y = layer.get_offsets()
        if not offsets_valid:
            layer_x = 0
            layer_y = 0

        cell_x = (index % columns) * cell_width
        cell_y = (index // columns) * cell_height
        for source_y in range(layer_height):
            target_y = cell_y + layer_y + source_y
            if target_y < cell_y or target_y >= cell_y + cell_height:
                continue
            for source_x in range(layer_width):
                target_x = cell_x + layer_x + source_x
                if target_x < cell_x or target_x >= cell_x + cell_width:
                    continue
                source_offset = (source_y * layer_width + source_x) * 4
                target_offset = (target_y * sheet_width + target_x) * 4
                sheet_pixels[target_offset : target_offset + 4] = source[
                    source_offset : source_offset + 4
                ]

    return sheet_width, sheet_height, bytes(sheet_pixels)


def choose_export_file():
    dialog = Gtk.FileChooserDialog(
        title="Export Sprite Sheet", action=Gtk.FileChooserAction.SAVE
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Save", Gtk.ResponseType.ACCEPT)
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_current_name("sprite-sheet.png")

    png_filter = Gtk.FileFilter()
    png_filter.set_name("PNG image")
    png_filter.add_pattern("*.png")
    dialog.add_filter(png_filter)
    jpeg_filter = Gtk.FileFilter()
    jpeg_filter.set_name("JPEG image")
    jpeg_filter.add_pattern("*.jpg")
    jpeg_filter.add_pattern("*.jpeg")
    dialog.add_filter(jpeg_filter)

    GimpUi.window_set_transient(dialog)
    response = dialog.run()
    file_path = dialog.get_filename() if response == Gtk.ResponseType.ACCEPT else None
    dialog.destroy()
    return file_path


def run(procedure, run_mode, image, drawables, config, data):
    GimpUi.init("sprite-sheet-layer-exporter")
    file_path = choose_export_file()
    if file_path is None:
        return cancelled(procedure)

    extension = os.path.splitext(file_path)[1].lower()
    export_format = {
        ".png": "png",
        ".jpg": "jpeg",
        ".jpeg": "jpeg",
    }.get(extension)
    if export_format is None:
        return failure(procedure, "Choose a .png, .jpg, or .jpeg file name.")

    temp_image = None
    try:
        width, height, pixels = make_sprite_sheet(image)
        temp_image = Gimp.Image.new(width, height, Gimp.ImageBaseType.RGB)
        output_layer = new_rgba_layer(temp_image, "Sprite Sheet", width, height, pixels)
        export_image(temp_image, file_path, export_format, output_layer)
    except Exception as error:
        return failure(procedure, error)
    finally:
        if temp_image is not None:
            temp_image.delete()
    return succeeded(procedure)


class SpriteSheetExporter(Gimp.PlugIn):
    def do_query_procedures(self):
        return [PROCEDURE_NAME]

    def do_create_procedure(self, name):
        if name != PROCEDURE_NAME:
            return None
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, run, None
        )
        procedure.set_menu_label("Export As Sprite Sheet")
        procedure.add_menu_path("<Image>/Image/PixelToolkit")
        procedure.set_attribution("Brody Clark", "Brody Clark", "2026")
        procedure.set_documentation(
            "Export As Sprite Sheet",
            "Pack each top-level image layer into a sprite-sheet cell.",
            name,
        )
        return procedure


Gimp.main(SpriteSheetExporter.__gtype__, sys.argv)
