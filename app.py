import logging
from flask import Flask, request, Response
from xml.etree import ElementTree as ET
from collections import deque

logger = logging.getLogger(__name__)
app = Flask(__name__)

SQUARE_SIZE = 32  # as per problem statement

def parse_svg_board(svg_xml):
    """Parses input SVG to extract board size, jumps (snakes/ladders)."""
    tree = ET.fromstring(svg_xml)
    view_box = tree.attrib.get('viewBox')
    if view_box:  # format: min-x min-y width height
        _, _, width_px, height_px = map(float, view_box.split())
    else:
        width_px = height_px = SQUARE_SIZE * 16  # default to 16x16

    width_squares = int(width_px // SQUARE_SIZE)
    height_squares = int(height_px // SQUARE_SIZE)
    total_squares = width_squares * height_squares

    jumps = {}

    # Parse jump lines: color coded green=ladder, red=snake
    for elem in tree.iter():
        if elem.tag.endswith('line'):
            x1, y1 = float(elem.attrib.get('x1')), float(elem.attrib.get('y1'))
            x2, y2 = float(elem.attrib.get('x2')), float(elem.attrib.get('y2'))
            stroke = elem.attrib.get('stroke', '').lower()

            start_sq = coord_to_square(x1, y1, width_squares, height_squares)
            end_sq = coord_to_square(x2, y2, width_squares, height_squares)
            if start_sq is not None and end_sq is not None:
                jumps[start_sq] = end_sq

    return width_squares, height_squares, total_squares, jumps

def coord_to_square(x, y, width, height):
    """Convert coordinate to square number in boustrophedon order.
       Note: y=0 at top, but board starts numbering bottom left."""
    col = int(x // SQUARE_SIZE)
    row_from_top = int(y // SQUARE_SIZE)
    row = height - 1 - row_from_top  # invert y to row from bottom
    if row < 0 or col < 0 or row >= height or col >= width:
        return None
    # Boustrophedon numbering: rows alternate direction
    if row % 2 == 0:
        sq = row * width + col + 1
    else:
        sq = row * width + (width - 1 - col) + 1
    return sq

def bfs_shortest_path(total_squares, jumps):
    """Find dice roll sequence winning the game with power-up dice rules using BFS."""

    # state: (position, dice_type) dice_type=0 regular, 1 power-of-2
    # store rolls to get there
    from collections import deque

    queue = deque()
    queue.append( (0, 0, []) )  # position 0 means start before square 1
    visited = set()
    visited.add( (0, 0) )

    while queue:
        pos, dice_type, rolls = queue.popleft()
        if pos == total_squares:
            return rolls
        faces = range(1, 7)
        for face in faces:
            move = (2 ** face) if dice_type == 1 else face
            next_pos = pos + move
            if next_pos > total_squares:
                next_pos = total_squares - (next_pos - total_squares)
            if next_pos in jumps:
                next_pos = jumps[next_pos]
            # Dice power-up rules
            next_dice = dice_type
            if dice_type == 0 and face == 6:
                next_dice = 1
            elif dice_type == 1 and face == 1:
                next_dice = 0
            next_state = (next_pos, next_dice)
            if next_state not in visited:
                visited.add(next_state)
                queue.append( (next_pos, next_dice, rolls + [face]) )
    # No path found
    return []

@app.route('/', methods=['GET'])
def default_route():
    return 'Python Template'

def winning_die_rolls(board_size):
    # Example: move forward using only 6s until near end, then finish
    rolls = []
    pos = 0
    while pos < board_size:
        move = min(6, board_size - pos)
        rolls.append(str(move))
        pos += move
    return "".join(rolls)

@app.route("/slpu", methods=["POST"])
@app.route('/slpu', methods=['POST'])
def slpu():
    svg_xml = request.data.decode('utf-8')
    width, height, total_squares, jumps = parse_svg_board(svg_xml)
    rolls = bfs_shortest_path(total_squares, jumps)
    roll_str = "".join(str(r) for r in rolls)
    out_svg = f'<svg xmlns="http://www.w3.org/2000/svg"><text>{roll_str}</text></svg>'
    return Response(out_svg, mimetype='image/svg+xml')

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
