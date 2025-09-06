import logging
from flask import Flask, request, Response
from xml.etree import ElementTree as ET
from collections import deque

logger = logging.getLogger(__name__)
app = Flask(__name__)

SQUARE_SIZE = 32

def parse_svg_board(svg_xml):
    """Extract number of squares (width/height) and jumps from SVG."""
    tree = ET.fromstring(svg_xml)
    view_box = tree.attrib.get('viewBox')
    if view_box:  # [min-x min-y width height]
        _, _, width_px, height_px = map(float, view_box.split())
    else:
        width_px = float(tree.attrib.get('width', SQUARE_SIZE*16))
        height_px = float(tree.attrib.get('height', SQUARE_SIZE*16))

    width_squares = round(width_px / SQUARE_SIZE)
    height_squares = round(height_px / SQUARE_SIZE)
    total_squares = width_squares * height_squares

    jumps = {}

    for elem in tree.iter():
        if elem.tag.endswith('line'):
            x1, y1 = float(elem.attrib['x1']), float(elem.attrib['y1'])
            x2, y2 = float(elem.attrib['x2']), float(elem.attrib['y2'])
            stroke = elem.attrib.get('stroke', '').lower()
            start_sq = coord_to_square(x1, y1, width_squares, height_squares)
            end_sq = coord_to_square(x2, y2, width_squares, height_squares)
            if start_sq and end_sq:
                jumps[start_sq] = end_sq

    return width_squares, height_squares, total_squares, jumps

def coord_to_square(x, y, width, height):
    """Maps (x, y) to 1-based boustrophedon square ID, bottom left is 1, top left is last."""
    col = int(x // SQUARE_SIZE)
    row_from_top = int(y // SQUARE_SIZE)
    row = height - 1 - row_from_top  # invert Y; 0 is bottom, height-1 is top
    if row < 0 or col < 0 or row >= height or col >= width:
        return None
    # Rows: even rows L→R, odd rows R→L
    if row % 2 == 0:
        square = row * width + col + 1
    else:
        square = row * width + (width - 1 - col) + 1
    return square

def bfs_shortest_path(total_squares, jumps):
    """Return shortest roll sequence for winning, with full rules."""
    queue = deque()
    queue.append((0, 0, []))  # position, dice_type(0=reg, 1=power), rolls
    visited = set()
    visited.add((0, 0))
    while queue:
        pos, dice_type, rolls = queue.popleft()
        if pos == total_squares:
            return rolls
        for face in range(1, 7):
            move = (2 ** face) if dice_type == 1 else face
            next_pos = pos + move
            # If overshoot, go backward
            if next_pos > total_squares:
                next_pos = total_squares - (next_pos - total_squares)
            # Apply jump if present
            if next_pos in jumps:
                next_pos = jumps[next_pos]
            # Enforce dice switching
            next_dice = dice_type
            if dice_type == 0 and face == 6:
                next_dice = 1
            elif dice_type == 1 and face == 1:
                next_dice = 0
            if (next_pos, next_dice) not in visited:
                visited.add((next_pos, next_dice))
                queue.append((next_pos, next_dice, rolls + [face]))
    return []

@app.route('/', methods=['GET'])
def default_route():
    return "Snakes & Ladders Power Up"

@app.route("/slpu", methods=["POST"])
def slpu():
    svg_xml = request.data.decode('utf-8')
    width, height, total_squares, jumps = parse_svg_board(svg_xml)
    rolls = bfs_shortest_path(total_squares, jumps)
    roll_str = "".join(str(r) for r in rolls)
    out_svg = f'<svg xmlns="http://www.w3.org/2000/svg"><text>{roll_str}</text></svg>'
    return Response(out_svg, mimetype='image/svg+xml')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
