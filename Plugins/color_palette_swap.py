"""Swap colors in the visible image composite and add the result as a layer."""

from gimpfu import *
import gtk

MAX_COLORS = 256
PALETTE_COLUMNS = 8
PREVIEW_MAX_WIDTH = 480
PREVIEW_MAX_HEIGHT = 360


def read_composite(image):
    """Return RGBA pixels from a merged-visible duplicate of image."""
    composite_image = pdb.gimp_image_duplicate(image)
    pdb.gimp_image_convert_rgb(composite_image)
    composite_layer = pdb.gimp_image_merge_visible_layers(
        composite_image, CLIP_TO_IMAGE)
    if composite_layer is None:
        pdb.gimp_image_delete(composite_image)
        raise RuntimeError("The image has no visible layers to preview.")

    if not composite_layer.has_alpha:
        pdb.gimp_layer_add_alpha(composite_layer)

    composite_layer.flush()
    composite_layer.update(0, 0, composite_layer.width, composite_layer.height)
    region = composite_layer.get_pixel_rgn(
        0, 0, composite_layer.width, composite_layer.height, False, False)
    pixels = bytearray(region[0:composite_layer.width,
                              0:composite_layer.height])
    width = int(composite_layer.width)
    height = int(composite_layer.height)
    pdb.gimp_image_delete(composite_image)
    return width, height, pixels


def build_palette(pixels):
    """Return unique RGBA colors and a palette index for each pixel."""
    palette = []
    color_indices = {}
    pixel_indices = bytearray()

    for offset in range(0, len(pixels), 4):
        color = (pixels[offset], pixels[offset + 1],
                 pixels[offset + 2], pixels[offset + 3])
        index = color_indices.get(color)
        if index is None:
            if len(palette) == MAX_COLORS:
                raise ValueError(
                    "This image has more than 256 visible colors.")
            index = len(palette)
            color_indices[color] = index
            palette.append(color)
        pixel_indices.append(index)

    return palette, pixel_indices


def color_to_hex(color):
    return "#%02x%02x%02x" % (color[0], color[1], color[2])


def mapped_pixels(pixels, pixel_indices, palette):
    result = bytearray(len(pixels))
    for pixel_number, palette_index in enumerate(pixel_indices):
        source_offset = pixel_number * 4
        color = palette[palette_index]
        result[source_offset] = color[0]
        result[source_offset + 1] = color[1]
        result[source_offset + 2] = color[2]
        result[source_offset + 3] = pixels[source_offset + 3]
    return result


class PaletteSwapDialog(object):
    def __init__(self, image, width, height, pixels, palette, pixel_indices):
        self.image = image
        self.width = width
        self.height = height
        self.pixels = pixels
        self.palette = list(palette)
        self.pixel_indices = pixel_indices
        self.preview_data = None

        self.dialog = gtk.Dialog(
            "Color Palette Swap",
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
             "Create", gtk.RESPONSE_OK))
        self.dialog.set_default_size(760, 520)
        self.dialog.set_resizable(True)

        content = self.dialog.vbox
        body = gtk.HBox(False, 12)
        body.set_border_width(12)
        content.pack_start(body, True, True, 0)

        palette_frame = gtk.Frame("Image Colors (%d)" % len(self.palette))
        palette_frame.set_shadow_type(gtk.SHADOW_IN)
        body.pack_start(palette_frame, False, True, 0)

        palette_scroll = gtk.ScrolledWindow()
        palette_scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        palette_scroll.set_size_request(250, 420)
        palette_frame.add(palette_scroll)

        rows = (len(self.palette) + PALETTE_COLUMNS - 1) // PALETTE_COLUMNS
        palette_table = gtk.Table(rows, PALETTE_COLUMNS, True)
        palette_table.set_row_spacings(4)
        palette_table.set_col_spacings(4)
        palette_table.set_border_width(8)
        palette_scroll.add_with_viewport(palette_table)

        for index, color in enumerate(self.palette):
            button = gtk.ColorButton()
            button.set_use_alpha(False)
            button.set_color(gtk.gdk.color_parse(color_to_hex(color)))
            button.set_tooltip_text("Color %d: %s" %
                                    (index + 1, color_to_hex(color)))
            button.connect("color-set", self.on_color_changed, index)
            row = index // PALETTE_COLUMNS
            column = index % PALETTE_COLUMNS
            palette_table.attach(button, column, column + 1,
                                 row, row + 1,
                                 gtk.EXPAND | gtk.FILL,
                                 gtk.EXPAND | gtk.FILL, 2, 2)

        preview_frame = gtk.Frame("Preview")
        preview_frame.set_shadow_type(gtk.SHADOW_IN)
        body.pack_start(preview_frame, True, True, 0)
        preview_alignment = gtk.Alignment(0.5, 0.5, 0.0, 0.0)
        preview_alignment.set_padding(12, 12, 12, 12)
        preview_frame.add(preview_alignment)
        self.preview = gtk.Image()
        preview_alignment.add(self.preview)

        self.update_preview()
        self.dialog.show_all()

    def on_color_changed(self, button, index):
        color = button.get_color()
        self.palette[index] = (
            (color.red * 255 + 32767) // 65535,
            (color.green * 255 + 32767) // 65535,
            (color.blue * 255 + 32767) // 65535,
            self.palette[index][3])
        button.set_tooltip_text("Color %d: %s" %
                                (index + 1, color_to_hex(self.palette[index])))
        self.update_preview()

    def update_preview(self):
        self.preview_data = bytes(mapped_pixels(
            self.pixels, self.pixel_indices, self.palette))
        pixbuf = gtk.gdk.pixbuf_new_from_data(
            self.preview_data,
            gtk.gdk.COLORSPACE_RGB,
            True,
            8,
            self.width,
            self.height,
            self.width * 4)
        scale = min(float(PREVIEW_MAX_WIDTH) / self.width,
                    float(PREVIEW_MAX_HEIGHT) / self.height,
                    1.0)
        preview_width = max(1, int(self.width * scale))
        preview_height = max(1, int(self.height * scale))
        if preview_width != self.width or preview_height != self.height:
            pixbuf = pixbuf.scale_simple(
                preview_width, preview_height, gtk.gdk.INTERP_NEAREST)
        self.preview.set_from_pixbuf(pixbuf)

    def run(self):
        response = self.dialog.run()
        self.dialog.destroy()
        return response


def color_palette_swap(image, drawable):
    try:
        width, height, pixels = read_composite(image)
        palette, pixel_indices = build_palette(pixels)
        dialog = PaletteSwapDialog(
            image, width, height, pixels, palette, pixel_indices)
        response = dialog.run()
    except (RuntimeError, ValueError) as error:
        gimp.message(str(error))
        return

    if response != gtk.RESPONSE_OK:
        return

    result = mapped_pixels(pixels, pixel_indices, dialog.palette)
    pdb.gimp_image_undo_group_start(image)
    try:
        output_layer = gimp.Layer(
            image,
            "Palette Swapped",
            width,
            height,
            RGBA_IMAGE,
            100,
            NORMAL_MODE)
        image.add_layer(output_layer, 0)
        output_region = output_layer.get_pixel_rgn(
            0, 0, width, height, True, True)
        output_region[0:width, 0:height] = bytes(result)
        output_layer.flush()
        output_layer.merge_shadow(True)
        output_layer.update(0, 0, width, height)
    finally:
        pdb.gimp_image_undo_group_end(image)
    pdb.gimp_displays_flush()


register(
    "color_palette_swap",
    "Swap Colors in Image",
    "Preview and replace colors from the visible image composite.",
    "Brody Clark",
    "MIT License",
    "2026",
    "<Image>/Image/PixelToolkit/Color Palette Swap",
    "*",
    [],
    [],
    color_palette_swap)

main()
