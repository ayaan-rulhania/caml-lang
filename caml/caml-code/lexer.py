# lexer.py
import re
from collections import namedtuple

Token = namedtuple('Token', ['type', 'value'])

class Lexer:
    """
    Tokenizer for Caml (revised).
    - case-insensitive tokens (token.type is uppercase)
    - preserves strings exactly and does not strip articles or periods inside strings
    - emits IGNORE tokens for filler words: 'the', 'a', 'an' and for lone '.' as DOT
    - supports $ single-line and $$$ block comments
    - recognizes multi-word keywords
    - returns list of (indent, [Token,...]) per non-empty source line
    """

    def __init__(self, code):
        self.raw = code or ''
        self.lines = []
        self.tokens = []

        # Keywords mapping (lower -> TOKEN_TYPE)
        # Multi-word entries should be included so parser can match them
        self.keywords = {
            'display': 'DISPLAY',
            'interact': 'INTERACT',
            'plus bold': 'PLUS_BOLD',

            'assign': 'ASSIGN',
            'set variable': 'SET',
            'set': 'SET',
            'change': 'CHANGE',
            'increase': 'INCREASE',
            'decrease': 'DECREASE',
            'multiply': 'MULTIPLY',
            'divide': 'DIVIDE',
            'exponentiate': 'EXPONENTIATE',
            'block': 'BLOCK',
            'to': 'TO',
            'by': 'BY',

            'define function': 'DEFINE_FUNCTION',
            'which takes': 'WHICH_TAKES',
            'which does': 'WHICH_DOES',
            'call function': 'CALL_FUNCTION',
            'call': 'CALL_FUNCTION',
            'abbreviate function': 'ABBREV_FUNCTION',
            'abbreviate': 'ABBREV_FUNCTION',

            'if': 'IF',
            'or if': 'ORIF',
            'otherwise': 'OTHERWISE',

            'repeat this': 'REPEAT',
            'times': 'TIMES',
            'do this until': 'DOUNTIL',
            'for each': 'FOREACH',
            'in': 'IN',
            'do': 'DO',

            'square of': 'SQUARE',
            'squareroot of': 'SQUAREROOT',
            'gcd(': 'GCD',
            'lcm(': 'LCM',
            'generate random int': 'RANDOM_INT',

            'create list': 'CREATE_LIST',
            'containing contents': 'CONTENTS',
            'add': 'ADD',
            'remove': 'REMOVE',
            'create dictionary': 'CREATE_DICT',
            'containing': 'CONTAINING',

            'create object': 'CREATE_OBJECT',
            'create window': 'CREATE_WINDOW',
            'create a new button': 'CREATE_BUTTON',
            'create button': 'CREATE_BUTTON',
            'window': 'WINDOW',
            'button': 'BUTTON',
            'delete': 'DELETE',
            'add function': 'ADD_FUNCTION',

            'create new file': 'FILE_CREATE',
            'delete file': 'FILE_DELETE',
            'write': 'FILE_WRITE',
            'find': 'FILE_FIND',
            'replace': 'FILE_REPLACE',
            'rename file': 'FILE_RENAME',
            'access file': 'FILE_ACCESS',
            'at first line': 'AT_FIRST',

            'get length of': 'GET_LENGTH',
            'get case of': 'GET_CASE',
            'get data type of': 'GET_TYPE',
            'import': 'IMPORT',
            'exports are': 'EXPORTS',
            'exports': 'EXPORTS',

            'true': 'BOOLEAN',
            'false': 'BOOLEAN',
            'null': 'NULL',
            'undefined': 'NULL',

            'and': 'AND',
            'or': 'OR',
            'except': 'EXCEPT',
            'is equal to': 'EQ',
            'is greater than': 'GT',
            'is less than': 'LT',
            'return': 'RETURN',
        }

        # filler words to mark as IGNORED tokens (parser will drop these)
        self.filler_words = {'the','a','an'}

        self._preprocess()

    def _preprocess(self):
        # normalize newlines
        text = self.raw.replace('\r\n', '\n').replace('\r', '\n')

        # hide strings so we can manipulate outside strings safely
        string_pattern = re.compile(r'"(?:\\.|[^"\\])*"')
        strings = []
        def hide(m):
            strings.append(m.group(0))
            return f'__STR_{len(strings)-1}__'
        hidden = string_pattern.sub(hide, text)

        # remove block comments $$$...$$$
        # implement using simple state machine across lines
        lines = hidden.split('\n')
        out_lines = []
        in_block = False
        for ln in lines:
            s = ln.strip()
            if s.startswith('$$$'):
                in_block = not in_block
                continue
            if in_block:
                continue
            # strip single-line comment starting with $
            if '$' in ln:
                # only first $ indicates comment start (but not if $ is in string placeholder)
                idx = ln.find('$')
                ln = ln[:idx]
            out_lines.append(ln)
        # restore strings
        restored_text = '\n'.join(out_lines)
        def restore(m):
            idx = int(m.group(1))
            return strings[idx]
        restored = re.sub(r'__STR_(\d+)__', restore, restored_text)

        # Now lines preserved including indentation
        self.lines = restored.split('\n')

    def tokenize(self):
        """
        Tokenize each non-empty (non-whitespace) line.
        Return list of (indent_count, [Token,...])
        """

        token_lines = []
        for raw_line in self.lines:
            # preserve leading spaces for indent calculation
            if raw_line.strip() == '':
                continue
            indent = len(raw_line) - len(raw_line.lstrip(' '))
            line = raw_line.strip()

            i = 0
            tokens = []
            L = len(line)
            while i < L:
                ch = line[i]

                # strings (double-quoted)
                if ch == '"':
                    j = i+1
                    escaped = False
                    while j < L:
                        if line[j] == '"' and not escaped:
                            break
                        if line[j] == '\\' and not escaped:
                            escaped = True
                        else:
                            escaped = False
                        j += 1
                    if j >= L:
                        s = line[i+1:]
                        i = L
                    else:
                        s = line[i+1:j]
                        i = j+1
                    tokens.append(Token('STRING', s))
                    # skip whitespace
                    while i < L and line[i].isspace():
                        i += 1
                    continue

                # punctuation
                if ch in '(),:+-*/^':
                    tokens.append(Token(ch, ch))
                    i += 1
                    continue

                # standalone dot
                if ch == '.':
                    tokens.append(Token('DOT', '.'))
                    i += 1
                    continue

                # parenthesis and colon handled above
                # numbers (ints and floats, negative)
                if ch.isdigit() or (ch == '-' and i+1 < L and line[i+1].isdigit()):
                    m = re.match(r'-?\d+(\.\d+)?', line[i:])
                    if m:
                        num = m.group(0)
                        if '.' in num:
                            tokens.append(Token('FLOAT', float(num)))
                        else:
                            tokens.append(Token('INTEGER', int(num)))
                        i += len(num)
                        while i < L and line[i].isspace():
                            i += 1
                        continue

                # words and multi-word keywords
                # grab the next contiguous "word" sequence (includes apostrophes)
                m = re.match(r"[^\s,():+*/^]+", line[i:])
                if m:
                    word = m.group(0)
                    lw = word.lower()
                    # attempt to match up to 4-word keywords by peeking ahead
                    rest = line[i:].strip()
                    parts = rest.split()
                    chosen = None
                    chosen_len_chars = None
                    # try 4 -> 1
                    for plen in (4,3,2,1):
                        if len(parts) >= plen:
                            cand = ' '.join(parts[:plen]).strip(' ,:()')
                            if cand.lower() in self.keywords:
                                chosen = cand.lower()
                                # compute number of characters consumed from original line (including spaces)
                                consumed = len(' '.join(parts[:plen]))
                                chosen_len_chars = consumed
                                break
                    if chosen:
                        tok_type = self.keywords[chosen]
                        tokens.append(Token(tok_type, chosen))
                        i += chosen_len_chars
                        # skip any following spaces
                        while i < L and line[i].isspace():
                            i += 1
                        continue

                    # if word is a filler article, emit IGNORED so parser can drop it
                    if lw in self.filler_words:
                        tokens.append(Token('IGNORED', lw))
                    else:
                        # normal identifier or literal-like (true/false/null)
                        if lw in self.keywords:
                            tokens.append(Token(self.keywords[lw], lw))
                        else:
                            # treat as IDENTIFIER (preserve original case in value)
                            tokens.append(Token('IDENTIFIER', word))
                    i += len(word)
                    # skip spaces
                    while i < L and line[i].isspace():
                        i += 1
                    continue

                # fallback
                i += 1

            token_lines.append((indent, tokens))

        self.tokens = token_lines
        return token_lines

if __name__ == "__main__":
    sample = '''
    Display "Hello, Caml!" plus bold
    Assign 5 to x
    Increase x by 10
    Display x
    Create list mylist containing contents 1, 2, 3
    display mylist
    Add 4 to list mylist
    For each item in mylist do:
        Display item
    Define function "add" which takes (a, b) and does:
        return a  + b
    Display (Call function "add" with arguments (5, 7))
    '''
    l = Lexer(sample)
    toks = l.tokenize()
    for indent, tl in toks:
        print(' ' * indent + '|', tl)
