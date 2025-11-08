# run_caml.py
import sys
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

def run_file(path):
    with open(path, 'r') as f:
        code = f.read()
    lexer = Lexer(code)
    token_lines = lexer.tokenize()
    parser = Parser(token_lines)
    ast = parser.parse()
    interpreter = Interpreter()
    interpreter.execute(ast)

if __name__ == "__main__":
    # Replace test.caml with an actual file that exists in the same directory
    # Example code to place in test.caml
    '''
    '''
    path = "test.caml"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    run_file(path)
