#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preview and replace colors in the visible image composite."""

import os
import sys

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gimp, GimpUi, Gtk

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


# if os.environ.get("GIMP_PLUGIN_DEBUG") == "1":
#     import debugpy

#     debugpy.listen(("127.0.0.1", 5678))

#     if os.environ.get("GIMP_PLUGIN_DEBUG_WAIT") == "1":
#         debugpy.wait_for_client()

PROCEDURE_NAME = "pixel-toolkit-color-palette-swap"
MAX_PALETTE_COLORS = 256


def build_palette(pixels):
    palette = []
    color_indices = {}
    pixel_indices = bytearray()
    for offset in range(0, len(pixels), 4):
        color = tuple(pixels[offset : offset + 3])
        index = color_indices.get(color)
        if index is None:
            if len(palette) == MAX_PALETTE_COLORS:
                raise ValueError("This image has more than 256 visible colors.")
            index = len(palette)
            color_indices[color] = index
            palette.append(color)
        pixel_indices.append(index)
    return palette, pixel_indices


def apply_palette(pixels, pixel_indices, palette):
    result = bytearray(len(pixels))
    for pixel_number, palette_index in enumerate(pixel_indices):
        offset = pixel_number * 4
        replacement = palette[palette_index]
        result[offset : offset + 3] = bytes(replacement[:3])
        result[offset + 3] = pixels[offset + 3]
    return bytes(result)


def color_hex(color):
    return "#%02x%02x%02x" % (color[0], color[1], color[2])


def read_visible_composite(image):
    composite_image = image.duplicate()
    try:
        if composite_image.get_base_type() != Gimp.ImageBaseType.RGB:
            composite_image.convert_rgb()
        composite_layer = composite_image.merge_visible_layers(
            Gimp.MergeType.CLIP_TO_IMAGE
        )
        if composite_layer is None:
            raise ValueError("The image has no visible layers to preview.")
        width = composite_layer.get_width()
        height = composite_layer.get_height()
        return width, height, read_rgba(composite_layer, width=width, height=height)
    finally:
        composite_image.delete()


class PaletteSwapDialog(object):
    def __init__(self, width, height, pixels, palette, pixel_indices):
        self.width = width
        self.height = height
        self.pixels = pixels
        self.palette = list(palette)
        self.pixel_indices = pixel_indices
        self.preview_bytes = None

        self.dialog = Gtk.Dialog(title="Color Palette Swap", modal=True)
        self.dialog.set_default_size(760, 520)
        self.dialog.set_resizable(True)
        self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.dialog.add_button("Create", Gtk.ResponseType.OK)
        GimpUi.window_set_transient(self.dialog)

        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        body.set_border_width(12)
        self.dialog.get_content_area().pack_start(body, True, True, 0)

        palette_frame = Gtk.Frame(label="Image Colors (%d)" % len(self.palette))
        body.pack_start(palette_frame, False, True, 0)
        palette_scroll = Gtk.ScrolledWindow()
        palette_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        palette_scroll.set_size_request(250, 420)
        palette_frame.add(palette_scroll)

        palette_grid = Gtk.Grid()
        palette_grid.set_row_spacing(4)
        palette_grid.set_column_spacing(4)
        palette_grid.set_border_width(8)
        palette_scroll.add(palette_grid)
        for index, color in enumerate(self.palette):
            button = Gtk.ColorButton()
            button.set_use_alpha(False)
            gtk_color = Gdk.RGBA()
            gtk_color.parse(color_hex(color))
            button.set_rgba(gtk_color)
            button.set_tooltip_text("Color %d: %s" % (index + 1, color_hex(color)))
            button.connect("color-set", self.on_color_changed, index)
            palette_grid.attach(button, index % 8, index // 8, 1, 1)

        preview_frame = Gtk.Frame(label="Preview")
        body.pack_start(preview_frame, True, True, 0)
        preview_alignment = Gtk.Alignment.new(0.5, 0.5, 0.0, 0.0)
        preview_alignment.set_padding(12, 12, 12, 12)
        preview_frame.add(preview_alignment)
        self.preview = Gtk.Image()
        preview_alignment.add(self.preview)
        self.update_preview()
        self.dialog.show_all()

    def on_color_changed(self, button, index):
        color = button.get_rgba()
        self.palette[index] = (
            int(color.red * 255 + 0.5),
            int(color.green * 255 + 0.5),
            int(color.blue * 255 + 0.5),
        )
        button.set_tooltip_text(
            "Color %d: %s" % (index + 1, color_hex(self.palette[index]))
        )
        self.update_preview()

    def update_preview(self):
        self.preview_bytes = GLib.Bytes.new(
            apply_palette(self.pixels, self.pixel_indices, self.palette)
        )
        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
            self.preview_bytes,
            GdkPixbuf.Colorspace.RGB,
            True,
            8,
            self.width,
            self.height,
            self.width * 4,
        )
        scale = min(480.0 / self.width, 360.0 / self.height, 1.0)
        preview_width = max(1, int(self.width * scale))
        preview_height = max(1, int(self.height * scale))
        if preview_width != self.width or preview_height != self.height:
            pixbuf = pixbuf.scale_simple(
                preview_width, preview_height, GdkPixbuf.InterpType.NEAREST
            )
        self.preview.set_from_pixbuf(pixbuf)

    def run(self):
        response = self.dialog.run()
        self.dialog.destroy()
        return response


def run(procedure, run_mode, image, drawables, config, data):
    if run_mode != Gimp.RunMode.INTERACTIVE:
        return failure(procedure, "Color Palette Swap requires interactive mode.")
    try:
        width, height, pixels = read_visible_composite(image)
        palette, pixel_indices = build_palette(pixels)
        GimpUi.init("color-palette-swap")
        dialog = PaletteSwapDialog(width, height, pixels, palette, pixel_indices)
        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            return cancelled(procedure)

        output_pixels = apply_palette(pixels, pixel_indices, dialog.palette)
        if image.get_base_type() == Gimp.ImageBaseType.RGB:
            image.undo_group_start()
            try:
                new_rgba_layer(image, "Palette Swapped", width, height, output_pixels)
            finally:
                image.undo_group_end()
            Gimp.displays_flush()
        else:
            output_image = Gimp.Image.new(width, height, Gimp.ImageBaseType.RGB)
            new_rgba_layer(
                output_image, "Palette Swapped", width, height, output_pixels
            )
            show_image(output_image)
    except Exception as error:
        return failure(procedure, error)
    return succeeded(procedure)


class ColorPaletteSwap(Gimp.PlugIn):
    def do_query_procedures(self):
        return [PROCEDURE_NAME]

    def do_create_procedure(self, name):
        if name != PROCEDURE_NAME:
            return None
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, run, None
        )
        procedure.set_menu_label("Color Palette Swap")
        procedure.add_menu_path("<Image>/Image/PixelToolkit")
        procedure.set_attribution("Brody Clark", "Brody Clark", "2026")
        procedure.set_documentation(
            "Color Palette Swap",
            "Preview and replace up to 256 colors in the visible composite.",
            name,
        )
        return procedure


Gimp.main(ColorPaletteSwap.__gtype__, sys.argv)
