# lexer.py
import re
from collections import namedtuple

Token = namedtuple('Token', ['type', 'value'])

class Lexer:
    """
    Line-based lexer. Handles:
    - case-insensitivity
    - removes 'the', 'a', 'an' and periods
    - string literals in double quotes
    - comments: $ single-line, $$$ multi-line block
    - produces tokens per line with indentation measured
    """

    def __init__(self, code):
        self.raw = code
        self.lines = []
        self.tokens = []
        self._preprocess()

        # Define multi-word keywords (lowercase)
        # keys are phrase -> token type
        self.keywords = {
            # Display / Interact
            'display': 'DISPLAY',
            'interact': 'INTERACT',
            'plus bold': 'PLUS_BOLD',

            # Variables
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

            # Functions
            'define function': 'DEFINE_FUNCTION',
            'which takes': 'WHICH_TAKES',
            'which does': 'WHICH_DOES',
            'call function': 'CALL_FUNCTION',
            'call': 'CALL_FUNCTION',
            'abbreviate function': 'ABBREV_FUNCTION',
            'abbreviate': 'ABBREV_FUNCTION',

            # Conditionals
            'if': 'IF',
            'or if': 'ORIF',
            'otherwise': 'OTHERWISE',

            # Loops
            'repeat this': 'REPEAT',
            'times': 'TIMES',
            'do this until': 'DOUNTIL',
            'for each': 'FOREACH',
            'in': 'IN',
            'do': 'DO',

            # Math
            'square of': 'SQUARE',
            'squareroot of': 'SQUAREROOT',
            'gcd(': 'GCD',
            'lcm(': 'LCM',
            'generate random int': 'RANDOM_INT',

            # Lists / Dictionaries
            'create list': 'CREATE_LIST',
            'containing contents': 'CONTENTS',
            'add': 'ADD',
            'remove': 'REMOVE',
            'create dictionary': 'CREATE_DICT',
            'containing': 'CONTAINING',

            # Objects
            'create object': 'CREATE_OBJECT',
            'delete': 'DELETE',
            'add function': 'ADD_FUNCTION',
            'set': 'SET',

            # Files
            'create new file': 'FILE_CREATE',
            'delete file': 'FILE_DELETE',
            'write': 'FILE_WRITE',
            'find': 'FILE_FIND',
            'replace': 'FILE_REPLACE',
            'rename file': 'FILE_RENAME',
            'access file': 'FILE_ACCESS',
            'at first line': 'AT_FIRST',

            # Getters
            'get length of': 'GET_LENGTH',
            'get case of': 'GET_CASE',
            'get data type of': 'GET_TYPE',
            'get data type': 'GET_TYPE',

            # Modules
            'import': 'IMPORT',
            'exports are': 'EXPORTS',
            'exports': 'EXPORTS',

            # Booleans / Null
            'true': 'BOOLEAN',
            'false': 'BOOLEAN',
            'null': 'NULL',
            'undefined': 'NULL',

            # Keywords
            'and': 'AND',
            'or': 'OR',
            'except': 'EXCEPT',
            'is equal to': 'EQ',
            'is greater than': 'GT',
            'is less than': 'LT',
            '==': 'EQSYM',
            '!==': 'NEQSYM',
            '!=': 'NEQSYM',
            '~==': 'CLOSEEST',
            '~': 'ESTIMATE'
        }

    def _preprocess(self):
        text = self.raw

        # Normalize newlines
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove periods and the articles the,a,an (as words)
        # But preserve periods inside strings — so first extract strings.
        string_pattern = re.compile(r'"(?:\\.|[^"\\])*"')
        strings = []
        def _hide_string(m):
            strings.append(m.group(0))
            return f'__STR_{len(strings)-1}__'
        text_hidden = string_pattern.sub(_hide_string, text)

        # remove the, a, an words and periods
        text_hidden = re.sub(r'\b(the|a|an)\b', '', text_hidden, flags=re.IGNORECASE)
        text_hidden = text_hidden.replace('.', '')

        # restore strings
        def _restore(m):
            idx = int(m.group(1))
            return strings[idx]
        text = re.sub(r'__STR_(\d+)__', _restore, text_hidden)

        # Handle block comments $$$ ... $$$
        lines = text.split('\n')
        out_lines = []
        in_block = False
        for ln in lines:
            if ln.strip().startswith('$$$'):
                if not in_block:
                    in_block = True
                    # if there's content after $$$ on same line, ignore
                    continue
                else:
                    in_block = False
                    continue
            if in_block:
                continue
            # handle single-line comment starting with $
            if '$' in ln:
                idx = ln.index('$')
                ln = ln[:idx]
            out_lines.append(ln.rstrip('\n'))
        # Save lines with original indentation counts (spaces)
        self.lines = out_lines

    def tokenize(self):
        """
        Produce a list of token dicts: each item is (indent, tokens_for_line)
        tokens_for_line: list of Token(type,value)
        """
        token_lines = []
        for raw_line in self.lines:
            if raw_line.strip() == '':
                continue
            indent = len(raw_line) - len(raw_line.lstrip(' '))
            line = raw_line.strip()

            # simple tokenization preserving strings
            tokens = []
            i = 0
            while i < len(line):
                ch = line[i]
                if ch == '"':
                    # string literal
                    j = i+1
                    while j < len(line):
                        if line[j] == '"' and line[j-1] != '\\':
                            break
                        j += 1
                    if j >= len(line):
                        s = line[i+1:]
                        i = len(line)
                    else:
                        s = line[i+1:j]
                        i = j+1
                    tokens.append(Token('STRING', s))
                    # skip any following space
                    while i < len(line) and line[i] == ' ':
                        i += 1
                    continue
                # numbers (int/float)
                if ch.isdigit() or (ch == '-' and i+1 < len(line) and line[i+1].isdigit()):
                    m = re.match(r'-?\d+(\.\d+)?', line[i:])
                    if m:
                        num = m.group(0)
                        if '.' in num:
                            tokens.append(Token('FLOAT', float(num)))
                        else:
                            tokens.append(Token('INTEGER', int(num)))
                        i += len(num)
                        while i < len(line) and line[i] == ' ':
                            i += 1
                        continue
                # punctuation
                if ch in '(),:':
                    tokens.append(Token(ch, ch))
                    i += 1
                    continue
                # otherwise words/words-with-symbols
                m = re.match(r"[^\s,():]+", line[i:])
                if m:
                    word = m.group(0)
                    lw = word.lower()
                    # try longest multi-word match by peeking ahead in the line
                    # we'll build a small buffer from here to end and search keywords
                    rest = line[i:].lower()
                    # longest first: check 3-word then 2-word then 1-word
                    chosen = None
                    for phrase_len in (3,2,1):
                        parts = rest.split()
                        if len(parts) >= phrase_len:
                            ph = ' '.join(parts[:phrase_len])
                            # strip trailing punctuation from ph
                            ph_clean = ph.strip(' ,:()')
                            if ph_clean in self.keywords:
                                chosen = ph_clean
                                break
                    if chosen:
                        tok_type = self.keywords[chosen]
                        tokens.append(Token(tok_type, chosen))
                        # consume chosen by characters
                        # find how many chars consumed in original case-sensitive rest
                        consumed = len(' '.join(rest.split()[:len(chosen.split())]))
                        i += consumed
                        # skip trailing spaces
                        while i < len(line) and line[i] == ' ':
                            i += 1
                        continue
                    # otherwise single word: check if keyword
                    if lw in self.keywords:
                        tokens.append(Token(self.keywords[lw], lw))
                    else:
                        # handle ==, !=, !==, ~==, ~ etc inside word
                        if lw in ('==', '!=', '!==', '~==', '~'):
                            tt = self.keywords.get(lw, lw)
                            tokens.append(Token(tt, lw))
                        else:
                            # default identifier or literal (true/false/null handled above)
                            tokens.append(Token('IDENTIFIER', word))
                    i += len(word)
                    while i < len(line) and line[i] == ' ':
                        i += 1
                    continue
                i += 1

            token_lines.append((indent, tokens))
        self.tokens = token_lines
        return self.tokens

# quick test when run directly
if __name__ == "__main__":
    code = '''
    Display "Hello, Caml!" plus bold
    Assign 5 to x
    Increase x by 10
    Display x
    Create list mylist containing contents 1, 2, 3
    Add 4 to list mylist
    For each item in mylist do:
        Display item
    '''
    l = Lexer(code)
    toks = l.tokenize()
    for indent, tl in toks:
        print(' ' * indent + '|', tl)
