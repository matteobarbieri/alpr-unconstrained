def draw_corners(x, y, w, h, segment_length,
                 pil_draw, color=(0, 255, 0), width=3):
    """
    Draw four corners around at the edges of a bounding box

    Parameters
    ----------

    x : int
        The x coordinate of the top left corner of the bounding box.

    y : int
        The y coordinate of the top left corner of the bounding box.

    w : int
        The width of the bounding box.

    h : int
        The height of the bounding box.

    segment_length : int
        The length of the segments composing the corner.

    pil_draw : PIL.ImageDraw
        The ImageDraw object required for drawing on a pil image.

    color : tuple
        A 3-tuple representing the RGB values of the lines' color.

    width : int
        The width of the segments composing the corner.

    >>> from PIL import Image, ImageDraw
    >>> pil_image = Image.open('/path/to/image.png')
    >>> pil_draw = ImageDraw(pil_image)
    >>> draw_corners(30, 40, 100, 60, 12, pil_draw)
    """

    # Draw two lines for each corner

    # NW
    pil_draw.line([x, y, x+segment_length, y], fill=color, width=width)
    pil_draw.line([x, y, x, y+segment_length], fill=color, width=width)

    # NE
    pil_draw.line([x+w-segment_length, y, x+w, y], fill=color, width=width)
    pil_draw.line([x+w, y, x+w, y+segment_length], fill=color, width=width)

    # SE
    pil_draw.line([x+w-segment_length, y+h, x+w, y+h], fill=color, width=width)
    pil_draw.line([x+w, y+h-segment_length, x+w, y+h], fill=color, width=width)

    # SW
    pil_draw.line([x, y+h, x+segment_length, y+h], fill=color, width=width)
    pil_draw.line([x, y+h-segment_length, x, y+h], fill=color, width=width)


def annotate_object(x, y, w, h, annotation_text, pil_draw,
                    font, padding, segment_length_ratio, line_length_ratio,
                    line_width,
                    outline_color, text_color, bg_color,
                    scale=1,
                    object_symbol=None, font_symbol=None,
                    bg_color_symbol=None):
    """
    line_length_ration : float
        Between 0 and 1, the length of the central top line
    """

    # Create a transparent version of the color
    # bg_color_transparent = (*outline_color, 128)

    # Adjust geometry to take padding into account
    x_p = x - padding
    y_p = y - padding
    w_p = w + 2 * padding
    h_p = h + 2 * padding

    # Compute length of corner segment in pixel
    segment_length = w_p * segment_length_ratio

    # Draw corners
    draw_corners(x_p, y_p, w_p, h_p, segment_length,
                 pil_draw, color=outline_color, width=line_width)

    # Compute the length of the horizontal line
    line_length = w_p * line_length_ratio
    line_height = 1.5 * line_length

    # Adapt line height to scale
    line_height = line_height if scale == 1 else line_height * 1.5

    # Compute x coordinate of the lp center
    x_c = x_p + w_p/2

    # Draw the horizontal line
    pil_draw.line([x_c - line_length/2, y_p, x_c + line_length/2, y_p],
                  fill=outline_color, width=line_width)

    # Draw the vertical line
    pil_draw.line([x_c, y_p-line_height, x_c, y_p],
                  fill=outline_color, width=line_width)

    # Compute coordinates for the label
    # x_symbol = x_c + 8
    x_symbol = x_c + 3 + scale * 5
    y_symbol = y_p - line_height

    # Draw the square for the symbol
    # TEXT_BOX_WIDTH = (len(annotation_text)) * 21
    TEXT_BOX_WIDTH = (len(annotation_text)) * 21 * scale
    TEXT_BOX_HEIGHT = 30 * scale

    # Draw the rectangle for the symbol
    pil_draw.rectangle(
        [x_symbol, y_symbol, x_symbol+TEXT_BOX_HEIGHT,
         y_symbol + TEXT_BOX_HEIGHT],
        fill=outline_color,
        outline=(0, 0, 0))

    # Compute coordinates for the acutal LP text
    x_text = x_symbol + TEXT_BOX_HEIGHT + 5 * scale
    y_text = y_symbol

    # Draw the rectangle for the text
    pil_draw.rectangle(
        [x_text, y_text, x_text+TEXT_BOX_WIDTH, y_text + TEXT_BOX_HEIGHT],
        fill=(255, 255, 255),
        outline=(0, 0, 0))

    # Draw the symbol corresponding to the identified vehicle
    pil_draw.text(
        # (x_symbol + 3, y_symbol - 8),
        (x_symbol + 3*scale, y_symbol - 3 - 5*scale),
        # VEHICLE_SYMBOLS[vehicle_category],
        object_symbol,
        text_color, font=font_symbol)

    # Finally, write the actual LP text in the square
    pil_draw.text(
        # (x_text + 4, y_text - 2),  # for nerdfonts
        (x_text + 4*scale, y_text - 7*scale),  # for open sans
        annotation_text, text_color, font=font)
