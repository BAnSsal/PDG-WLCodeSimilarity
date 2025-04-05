# ---------------- parser_utils.py ----------------
from pycparser import c_parser

def parse_c_code(c_code):
    parser = c_parser.CParser()
    return parser.parse(c_code)