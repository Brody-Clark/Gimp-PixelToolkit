"""Shared GEGL and procedure helpers for the PixelToolkit plug-ins."""

import gi

gi.require_version("Gegl", "0.4")
gi.require_version("Gimp", "3.0")
from gi.repository import Gegl, Gio, GLib, Gimp


RGBA_FORMAT = "R'G'B'A u8"


def rectangle(x, y, width, height):
    return Gegl.Rectangle.new(x, y, width, height)


def read_rgba(drawable, x=0, y=0, width=None, height=None):
    if width is None:
        width = drawable.get_width()
    if height is None:
        height = drawable.get_height()
    buffer = drawable.get_buffer()
    region = rectangle(x, y, width, height)
    return bytes(buffer.get(region, 1.0, RGBA_FORMAT,
                            Gegl.AbyssPolicy.NONE))


def write_rgba(drawable, pixels, x=0, y=0, width=None, height=None):
    if width is None:
        width = drawable.get_width()
    if height is None:
        height = drawable.get_height()
    if len(pixels) != width * height * 4:
        raise ValueError("Pixel buffer size does not match the layer bounds.")
    buffer = drawable.get_buffer()
    region = rectangle(x, y, width, height)
    buffer.set(region, RGBA_FORMAT, bytes(pixels))
    buffer.flush()
    drawable.update(x, y, width, height)


def new_rgba_layer(image, name, width, height, pixels):
    layer = Gimp.Layer.new(
        image, name, width, height, Gimp.ImageType.RGBA_IMAGE,
        100.0, Gimp.LayerMode.NORMAL)
    image.insert_layer(layer, None, 0)
    write_rgba(layer, pixels, width=width, height=height)
    return layer


def show_image(image):
    Gimp.Display.new(image)
    Gimp.displays_flush()


def failure(procedure, message):
    return procedure.new_return_values(
        Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(str(message)))


def cancelled(procedure):
    return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)


def succeeded(procedure):
    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)


def export_image(image, file_path, export_format, drawable=None):
    procedure_name = "file-%s-export" % export_format
    file_procedure = Gimp.get_pdb().lookup_procedure(procedure_name)
    if file_procedure is None:
        raise RuntimeError("GIMP does not provide %s." % procedure_name)

    config = file_procedure.create_config()
    available_properties = set(
        prop.name for prop in config.list_properties())
    if "run-mode" in available_properties:
        config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
    if "image" in available_properties:
        config.set_property("image", image)
    if "file" in available_properties:
        config.set_property("file", Gio.File.new_for_path(file_path))
    if drawable is not None and "drawables" in available_properties:
        config.set_property("drawables", [drawable])

    result = file_procedure.run(config)
    if result.index(0) != Gimp.PDBStatusType.SUCCESS:
        raise RuntimeError("GIMP could not export %s." % file_path)