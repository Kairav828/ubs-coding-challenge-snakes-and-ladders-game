import logging
import socket
from flask import Flask, request, Response
from routes import app

logger = logging.getLogger(__name__)


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
def slpu():
    svg_xml = request.data.decode("utf-8")
    # Simple logic: parse board_size (example assumes 16x16 grid)
    # For real input, parse size from SVG if needed
    board_size = 256  # fallback example
    # If you can parse proper size from SVG, do so here
    rolls = winning_die_rolls(board_size)
    out_svg = f'<svg xmlns="http://www.w3.org/2000/svg"><text>{rolls}</text></svg>'
    return Response(out_svg, mimetype="image/svg+xml")

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
