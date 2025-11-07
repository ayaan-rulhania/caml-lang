# parser.py
from nodes import *
from lexer import Token

class Parser:
    """
    Simple indentation-based parser.
    Receives token_lines: list of (indent, [Token,...])
    Produces list of AST nodes.
    """

    def __init__(self, token_lines):
        self.token_lines = token_lines
        self.pos = 0
        self.total = len(token_lines)

    def current(self):
        if self.pos < self.total:
            return self.token_lines[self.pos]
        return None

    def advance(self):
        self.pos += 1

    def peek_tokens(self, idx=0):
        cur = self.current()
        if not cur:
            return []
        return cur[1]

    def parse(self):
        ast = []
        while self.pos < self.total:
            node = self.parse_statement()
            if node is not None:
                if isinstance(node, list):
                    ast.extend(node)
                else:
                    ast.append(node)
        return ast

    def parse_statement(self):
        item = self.current()
        if item is None:
            return None
        indent, tokens = item
        if not tokens:
            self.advance()
            return None

        # helper to read tokens conveniently
        t0 = tokens[0]
        t0_type = t0.type if isinstance(t0, Token) else None

        # DISPLAY
        if any(tok.type == 'DISPLAY' for tok in tokens):
            return self.parse_display()
        if any(tok.type == 'INTERACT' for tok in tokens):
            return self.parse_interact()

        # LIST creation: "Create list mylist containing contents 1, 2, 3"
        if any(tok.type == 'CREATE_LIST' for tok in tokens):
            return self.parse_list()

        # ADD to list
        if any(tok.type == 'ADD' for tok in tokens) and 'list' in [tok.value.lower() if tok.type=='IDENTIFIER' else '' for tok in tokens]:
            return self.parse_list_add()

        # For each ... do:
        if any(tok.type == 'FOREACH' for tok in tokens):
            return self.parse_for_each()

        # Assign / Set / Change / Increase / Decrease / Multiply / Divide / Exponentiate / Block
        types = [tok.type for tok in tokens]
        if 'ASSIGN' in types or 'SET' in types or 'CHANGE' in types or 'INCREASE' in types or 'DECREASE' in types or 'MULTIPLY' in types or 'DIVIDE' in types or 'EXPONENTIATE' in types or 'BLOCK' in types:
            return self.parse_variable_statement()

        # FUNCTION definitions
        if any(tok.type == 'DEFINE_FUNCTION' for tok in tokens):
            return self.parse_function_def()

        # CALL function
        if any(tok.type == 'CALL_FUNCTION' for tok in tokens) or tokens[0].type == 'IDENTIFIER' and len(tokens) > 1 and tokens[1].type == '(':
            # support both "Call function 'add' with arguments (6,7)" and "callname(args)"
            return self.parse_function_call()

        # Abbreviate function
        if any(tok.type == 'ABBREV_FUNCTION' for tok in tokens):
            return self.parse_function_abbrev()

        # Conditionals
        if any(tok.type == 'IF' for tok in tokens):
            return self.parse_if()
        if any(tok.type == 'ORIF' for tok in tokens):
            return self.parse_or_if()
        if any(tok.type == 'OTHERWISE' for tok in tokens):
            return self.parse_otherwise()

        # Repeat times
        if any(tok.type == 'REPEAT' for tok in tokens):
            return self.parse_repeat()

        # DOUNTIL
        if any(tok.type == 'DOUNTIL' for tok in tokens):
            return self.parse_do_until()

        # Math functions like "Square of n" or "Generate random int"
        if any(tok.type in ('SQUARE', 'SQUAREROOT', 'GCD', 'LCM', 'RANDOM_INT') for tok in tokens):
            return self.parse_math_func()

        # Files
        if any(tok.type.startswith('FILE') for tok in tokens):
            return self.parse_file()

        # Getters
        if any(tok.type in ('GET_LENGTH','GET_CASE','GET_TYPE') for tok in tokens):
            return self.parse_getter()

        # Import / Export
        if any(tok.type == 'IMPORT' for tok in tokens):
            return self.parse_import()
        if any(tok.type == 'EXPORTS' for tok in tokens):
            return self.parse_export()

        # Dictionaries
        if any(tok.type == 'CREATE_DICT' for tok in tokens) or any(tok.type == 'CONTAINING' for tok in tokens):
            return self.parse_dictionary()

        # default: skip unknown line
        self.advance()
        return None

    # --- helpers to get tokens on current line ---
    def _line_tokens(self):
        cur = self.current()
        if cur:
            return cur[1]
        return []

    def _consume(self):
        tokens = self._line_tokens()
        self.advance()
        return tokens

    # --- Display / Interact ---
    def parse_display(self):
        tokens = self._consume()
        # find string or identifier or variable name
        bold = any(tok.type == 'PLUS_BOLD' for tok in tokens)
        # find first STRING or IDENTIFIER or INTEGER/FLOAT
        val = None
        for tok in tokens:
            if tok.type == 'STRING':
                val = tok.value
                break
            if tok.type in ('INTEGER','FLOAT','BOOLEAN','NULL'):
                val = tok.value
                break
            if tok.type == 'IDENTIFIER':
                val = tok.value
                break
        return DisplayNode(val, bold=bold)

    def parse_interact(self):
        tokens = self._consume()
        bold = any(tok.type == 'PLUS_BOLD' for tok in tokens)
        val = None
        for tok in tokens:
            if tok.type == 'STRING':
                val = tok.value
                break
            if tok.type == 'IDENTIFIER':
                val = tok.value
                break
        return InteractNode(val, bold=bold)

    # --- Variables and arithmetic updates ---
    def parse_variable_statement(self):
        tokens = self._consume()
        # normalize to lower values for matching values in tokens
        types = [tok.type for tok in tokens]
        vals = [tok.value if hasattr(tok,'value') else None for tok in tokens]
        # ASSIGN ... to var
        if 'ASSIGN' in types:
            # find value then 'TO' then IDENTIFIER
            # find first literal or identifier after ASSIGN
            try:
                idx = types.index('ASSIGN')
            except ValueError:
                idx = -1
            # naive: value is first literal/identifier after ASSIGN
            val = None
            var = None
            for tok in tokens[idx+1:]:
                if tok.type in ('STRING','INTEGER','FLOAT','BOOLEAN','NULL','IDENTIFIER'):
                    val = tok.value
                    break
            # find 'TO' then identifier after
            for i,tok in enumerate(tokens):
                if tok.type == 'TO' and i+1 < len(tokens) and tokens[i+1].type == 'IDENTIFIER':
                    var = tokens[i+1].value
                    break
            if var is None and isinstance(val, str) and val.isidentifier():
                # maybe syntax: Assign x y  (fallback)
                var = val
                val = None
            return AssignNode(var, val)
        if 'SET' in types and 'VARIABLE' not in types:
            # patterns: Set variable boy to 'Tom'  OR Set boy to 'Tom' (we removed "variable" in preprocessing mostly)
            var = None
            val = None
            # find IDENTIFIER (first after SET)
            for i,tok in enumerate(tokens):
                if tok.type == 'IDENTIFIER':
                    var = tok.value
                    # check for TO after that
                    for j in range(i+1, len(tokens)):
                        if tokens[j].type == 'TO' and j+1 < len(tokens) and tokens[j+1].type in ('STRING','INTEGER','FLOAT','IDENTIFIER','BOOLEAN','NULL'):
                            val = tokens[j+1].value
                            break
                    break
            return SetNode(var, val)
        if 'CHANGE' in types:
            # Change {var} to {new}
            var = None
            val = None
            for i,tok in enumerate(tokens):
                if tok.type == 'IDENTIFIER':
                    var = tok.value
                    # find TO
                    for j in range(i+1,len(tokens)):
                        if tokens[j].type == 'TO' and j+1 < len(tokens):
                            val = tokens[j+1].value
                            break
                    break
            return ChangeNode(var, val)
        if 'INCREASE' in types or 'DECREASE' in types or 'MULTIPLY' in types or 'DIVIDE' in types or 'EXPONENTIATE' in types:
            op = None
            for k in ('INCREASE','DECREASE','MULTIPLY','DIVIDE','EXPONENTIATE'):
                if k in types:
                    op = k
                    break
            var = None
            val = None
            # pattern: Increase x by 10
            for i,tok in enumerate(tokens):
                if tok.type == op:
                    # next IDENTIFIER likely
                    if i+1 < len(tokens) and tokens[i+1].type == 'IDENTIFIER':
                        var = tokens[i+1].value
                    # find BY
                    for j in range(i+1,len(tokens)):
                        if tokens[j].type == 'BY' and j+1 < len(tokens):
                            val = tokens[j+1].value
                            break
                    break
            if op == 'INCREASE':
                return IncreaseNode(var, val)
            if op == 'DECREASE':
                return DecreaseNode(var, val)
            if op == 'MULTIPLY':
                return MultiplyNode(var, val)
            if op == 'DIVIDE':
                return DivideNode(var, val)
            if op == 'EXPONENTIATE':
                return ExponentiateNode(var, val)
        if 'BLOCK' in types:
            # Block var
            for tok in tokens:
                if tok.type == 'IDENTIFIER':
                    return BlockVarNode(tok.value)
            return None
        # fallback
        return None

    # --- Lists & dicts ---
    def parse_list(self):
        tokens = self._consume()
        # Create list <name> containing contents <a, b, c>
        name = None
        elements = []
        for i,tok in enumerate(tokens):
            if tok.type == 'IDENTIFIER':
                name = tok.value
                break
        # find numbers/strings after CONTENTS token on same line; else could be commas separated identifiers
        for tok in tokens:
            if tok.type in ('INTEGER','FLOAT','STRING','IDENTIFIER','BOOLEAN'):
                elements.append(tok.value)
        return ListNode(name, elements)

    def parse_list_add(self):
        tokens = self._consume()
        # Add 4 to list mylist
        val = None
        lst = None
        for i,tok in enumerate(tokens):
            if tok.type in ('INTEGER','FLOAT','STRING','IDENTIFIER','BOOLEAN'):
                # first such is value
                val = tok.value
                break
        # find IDENTIFIER after 'list' word or last IDENTIFIER
        idents = [tok.value for tok in tokens if tok.type == 'IDENTIFIER']
        if idents:
            lst = idents[-1]
        return ListAddNode(lst, val)

    def parse_for_each(self):
        indent, tokens = self.current()
        # For each item in mylist do:
        # consume this line then parse indented block as body
        self.advance()
        var_name = None
        iterable = None
        for i,tok in enumerate(tokens):
            if tok.type == 'IDENTIFIER' and var_name is None:
                var_name = tok.value
            if tok.type == 'IN' and i+1 < len(tokens) and tokens[i+1].type == 'IDENTIFIER':
                iterable = tokens[i+1].value
        # parse block at larger indent
        body = self._collect_block(indent)
        return ForEachNode(var_name, iterable, body)

    # --- Functions ---
    def parse_function_def(self):
        # Expect: Define function 'name' which takes (a, b) and does:
        tokens = self._consume()
        name = None
        args = []
        # look for first STRING or IDENTIFIER after DEFINE_FUNCTION
        for i,tok in enumerate(tokens):
            if tok.type == 'STRING':
                name = tok.value
                break
            if tok.type == 'IDENTIFIER':
                # might be bare name
                name = tok.value
                break
        # find args in parentheses after WHICH_TAKES token on same line
        # if not present, args=[]
        # now parse body block
        # body starts on next indented lines
        # collect block
        indent = None
        # current indent is of the DEFINE line; collect block from next lines
        cur = self.current()
        if cur:
            indent = cur[0]
        body = self._collect_block(indent if indent is not None else 0)
        return FunctionDefNode(name, args, body)

    def parse_function_call(self):
        tokens = self._consume()
        # Support "Call function 'add' with arguments (6, 7)"
        # or "add(6,7)" style: in latter tokenization may output IDENTIFIER '(' ... ')'
        name = None
        args = []
        # look for STRING or IDENTIFIER after CALL_FUNCTION
        for i,tok in enumerate(tokens):
            if tok.type == 'STRING':
                name = tok.value
                break
            if tok.type == 'IDENTIFIER':
                # if first token is CALL_FUNCTION it may be followed by STRING/IDENTIFIER; else, if first token is IDENTIFIER followed by '(' it's a call
                if tokens[0].type != 'IDENTIFIER' or (len(tokens)>1 and tokens[1].type != '('):
                    name = tok.value
                    break
                else:
                    name = tok.value
                    # try to parse args after '(' in remaining tokens (unlikely in our simple tokenizer but include safeguard)
                    for j in range(1,len(tokens)):
                        if tokens[j].type in ('INTEGER','FLOAT','STRING','IDENTIFIER','BOOLEAN'):
                            args.append(tokens[j].value)
                    break
        # also collect numeric/string tokens as arguments if present
        for tok in tokens:
            if tok.type in ('INTEGER','FLOAT','STRING','BOOLEAN'):
                args.append(tok.value)
        return FunctionCallNode(name, args)

    def parse_function_abbrev(self):
        tokens = self._consume()
        original = None
        new = None
        # Abbreviate function 'add' to 'a'
        for i,tok in enumerate(tokens):
            if tok.type == 'STRING' and original is None:
                original = tok.value
            elif tok.type == 'STRING' and original is not None:
                new = tok.value
            if tok.type == 'IDENTIFIER' and original is None:
                original = tok.value
            elif tok.type == 'IDENTIFIER' and original is not None:
                new = tok.value
        return FunctionAbbrevNode(original, new)

    # --- Conditionals & loops ---
    def parse_if(self):
        indent, tokens = self.current()
        self.advance()
        # next tokens form condition (simple literal/identifier)
        cond = None
        for tok in tokens:
            if tok.type in ('STRING','INTEGER','FLOAT','BOOLEAN','NULL','IDENTIFIER'):
                cond = tok.value
                break
        body = self._collect_block(indent)
        return IfNode(cond, body)

    def parse_or_if(self):
        indent, tokens = self.current()
        self.advance()
        cond = None
        for tok in tokens:
            if tok.type in ('STRING','INTEGER','FLOAT','BOOLEAN','NULL','IDENTIFIER'):
                cond = tok.value
                break
        body = self._collect_block(indent)
        return OrIfNode(cond, body)

    def parse_otherwise(self):
        indent, tokens = self.current()
        self.advance()
        body = self._collect_block(indent)
        return OtherwiseNode(body)

    def parse_repeat(self):
        tokens = self._consume()
        times = None
        for tok in tokens:
            if tok.type in ('INTEGER','IDENTIFIER'):
                times = tok.value
                break
        # parse following block (indent increase)
        body = self._collect_block(None)
        return RepeatNode(times, body)

    def parse_do_until(self):
        indent, tokens = self.current()
        self.advance()
        cond = None
        for tok in tokens:
            if tok.type in ('STRING','INTEGER','FLOAT','BOOLEAN','IDENTIFIER','NULL'):
                cond = tok.value
                break
        body = self._collect_block(indent)
        return DoUntilNode(cond, body)

    # --- Math functions ---
    def parse_math_func(self):
        tokens = self._consume()
        # identify function name token
        for tok in tokens:
            if tok.type in ('SQUARE','SQUAREROOT','GCD','LCM','RANDOM_INT'):
                func_name = tok.type
                break
        args = [tok.value for tok in tokens if tok.type in ('INTEGER','FLOAT','IDENTIFIER')]
        return MathFuncNode(func_name, args)

    # --- Files ---
    def parse_file(self):
        tokens = self._consume()
        action = None
        filename = None
        text = None
        for i,tok in enumerate(tokens):
            if tok.type.startswith('FILE_'):
                action = tok.type
            if tok.type == 'STRING':
                filename = tok.value
        # if there is trailing STRING after filename treat as text
        if len([t for t in tokens if t.type=='STRING']) >= 2:
            text = [t.value for t in tokens if t.type=='STRING'][1]
        node = FileNode(action, filename, text)
        # check special tokens
        if any(t.type == 'AT_FIRST' for t in tokens):
            node.at_first = True
        if any(t.type == 'FILE_FIND' for t in tokens) and any(t.type == 'FILE_REPLACE' for t in tokens):
            # find/replace parsing handled in interpreter by reading node.find_text/replace_text set during parse if present
            strs = [t.value for t in tokens if t.type == 'STRING']
            if len(strs) >= 3:
                node.find_text = strs[1]
                node.replace_text = strs[2]
        return node

    # --- Getters ---
    def parse_getter(self):
        tokens = self._consume()
        target = None
        mode = None
        for i,tok in enumerate(tokens):
            if tok.type in ('IDENTIFIER','STRING'):
                target = tok.value
                break
        # for case mode, see if mode exists later
        for tok in tokens:
            if isinstance(tok.value,str) and tok.value.lower() in ('upper','lower','camel','snake','pascal'):
                mode = tok.value.lower()
        if any(t.type == 'GET_LENGTH' for t in tokens):
            return GetLengthNode(target)
        if any(t.type == 'GET_CASE' for t in tokens):
            return GetCaseNode(target, mode)
        if any(t.type == 'GET_TYPE' for t in tokens):
            return GetTypeNode(target)
        return None

    # --- Modules ---
    def parse_import(self):
        tokens = self._consume()
        modules = []
        filename = None
        for i,tok in enumerate(tokens):
            if tok.type == 'IDENTIFIER':
                modules.append(tok.value)
            if tok.type == 'STRING':
                filename = tok.value
        return ImportNode(modules, filename)

    def parse_export(self):
        tokens = self._consume()
        modules = [tok.value for tok in tokens if tok.type == 'IDENTIFIER']
        return ExportNode(modules)

    # --- Dictionaries ---
    def parse_dictionary(self):
        tokens = self._consume()
        name = None
        elements = {}
        # find dict name
        for tok in tokens:
            if tok.type == 'IDENTIFIER':
                name = tok.value
                break
        # parse key:value pairs on same line using tokens sequence (IDENTIFIER COLON <value>)
        # simpler: find pairs of IDENTIFIER and next token as value if that's a STRING/INTEGER
        it = iter(tokens)
        last_key = None
        for tok in it:
            if tok.type == 'IDENTIFIER':
                last_key = tok.value
                # try to see colon and value
                # lookahead may not be straightforward; so try scanning rest tokens
                # find next value-like token after this key
                rest = tokens[tokens.index(tok)+1:]
                for r in rest:
                    if r.type in ('STRING','INTEGER','FLOAT','BOOLEAN','IDENTIFIER'):
                        elements[last_key] = r.value
                        break
        return DictionaryNode(name, elements)

    # --- Block collector ---
    def _collect_block(self, parent_indent):
        """
        Collects subsequent lines with greater indentation than parent_indent.
        parent_indent: indentation count of the parent line. If None, use indentation of next line as base.
        Returns list of parsed statements (AST nodes).
        """
        # use current position as start of block (we advanced past header)
        if self.pos >= self.total:
            return []
        # determine base indent
        if parent_indent is None:
            parent_indent = self.token_lines[self.pos-1][0] if self.pos-1 >= 0 else 0
        block = []
        base_indent = None
        # If next line has indent <= parent_indent: empty block
        if self.pos < self.total:
            next_indent = self.token_lines[self.pos][0]
            if next_indent <= parent_indent:
                return []
            base_indent = next_indent
        while self.pos < self.total and self.token_lines[self.pos][0] >= base_indent:
            node = self.parse_statement()
            if node is not None:
                if isinstance(node, list):
                    block.extend(node)
                else:
                    block.append(node)
        return block
