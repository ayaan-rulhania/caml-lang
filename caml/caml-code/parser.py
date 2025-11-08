# parser.py
from nodes import *
from lexer import Token

# Token types produced by lexer that should be ignored in parser decisions
IGNORED_TOKEN_TYPES = {'IGNORED', 'DOT'}

class Parser:
    """
    Robust indentation-based parser for Caml.

    Behavior notes:
    - parse_statement() reads the current line, filters tokens, advances the cursor,
      then dispatches to a parse_* helper with the filtered tokens and the line's indent.
    - Helpers accept tokens and indent so they don't re-consume the same line.
    - _filtered_tokens is defensive and returns a finite list.
    """

    def __init__(self, token_lines):
        self.token_lines = token_lines or []
        self.pos = 0
        self.total = len(self.token_lines)

    def current(self):
        if self.pos < self.total:
            return self.token_lines[self.pos]
        return None

    def advance(self):
        self.pos += 1

    def _filtered_tokens(self, tokens):
        """
        Safely convert tokens (possibly generator-like) to a list and filter ignored types.
        """
        if not tokens:
            return []
        # ensure list
        try:
            if not isinstance(tokens, list):
                tokens = list(tokens)
        except Exception:
            # fallback: iterate manually
            tmp = []
            for t in tokens:
                tmp.append(t)
            tokens = tmp
        out = []
        for t in tokens:
            t_type = getattr(t, 'type', None)
            if t_type and t_type not in IGNORED_TOKEN_TYPES:
                out.append(t)
        return out

    def parse(self):
        ast = []
        while self.pos < self.total:
            node = self.parse_statement()
            if node is None:
                continue
            if isinstance(node, list):
                ast.extend(node)
            else:
                ast.append(node)
        return ast

    def parse_statement(self):
        cur = self.current()
        if not cur:
            return None
        indent, raw_tokens = cur
        # filter tokens but do NOT advance inside helpers; parse_statement will advance once
        tokens = self._filtered_tokens(raw_tokens)

        # Always advance here so we don't re-read the same line.
        self.advance()

        if not tokens:
            return None

        types = [getattr(t, 'type', None) for t in tokens]

        # Dispatch to handlers, always passing tokens and indent
        if 'DISPLAY' in types:
            return self.parse_display(tokens, indent)
        if 'INTERACT' in types:
            return self.parse_interact(tokens, indent)

        if 'CREATE_WINDOW' in types or 'WINDOW' in types:
            return self.parse_window(tokens, indent)
        if 'CREATE_BUTTON' in types or 'BUTTON' in types:
            return self.parse_button(tokens, indent)

        if 'CREATE_LIST' in types:
            return self.parse_list(tokens, indent)
        if 'ADD' in types and any(t.type == 'IDENTIFIER' and getattr(t,'value','').lower() == 'list' for t in tokens):
            return self.parse_list_add(tokens, indent)

        if any(t in types for t in ('ASSIGN','SET','CHANGE','INCREASE','DECREASE','MULTIPLY','DIVIDE','EXPONENTIATE','BLOCK')):
            return self.parse_variable_statement(tokens, indent)

        if 'DEFINE_FUNCTION' in types:
            return self.parse_function_def(tokens, indent)

        if 'CALL_FUNCTION' in types or (tokens and tokens[0].type == 'IDENTIFIER' and any(t.type in ('INTEGER','FLOAT','STRING','BOOLEAN') for t in tokens[1:])):
            return self.parse_function_call(tokens, indent)

        if 'ABBREV_FUNCTION' in types:
            return self.parse_function_abbrev(tokens, indent)

        if 'IF' in types:
            return self.parse_if(tokens, indent)
        if 'ORIF' in types:
            return self.parse_or_if(tokens, indent)
        if 'OTHERWISE' in types:
            return self.parse_otherwise(tokens, indent)
        if 'REPEAT' in types:
            return self.parse_repeat(tokens, indent)
        if 'DOUNTIL' in types:
            return self.parse_do_until(tokens, indent)
        if 'FOREACH' in types:
            return self.parse_for_each(tokens, indent)

        if any(t in types for t in ('SQUARE','SQUAREROOT','GCD','LCM','RANDOM_INT')):
            return self.parse_math_func(tokens, indent)

        if any((t or '').startswith('FILE') for t in types if isinstance(t, str)):
            return self.parse_file(tokens, indent)

        if any(t in ('GET_LENGTH','GET_CASE','GET_TYPE') for t in types):
            return self.parse_getter(tokens, indent)

        if 'IMPORT' in types:
            return self.parse_import(tokens, indent)
        if 'EXPORTS' in types:
            return self.parse_export(tokens, indent)
        if 'CREATE_DICT' in types or 'CONTAINING' in types:
            return self.parse_dictionary(tokens, indent)

        # Unknown line -> skip (we already advanced)
        return None

    # --- helpers for consuming / blocks ---
    def _collect_block(self, parent_indent):
        """
        Collect indented block lines with indent >= base_indent where base_indent is the indent
        of the first block line (must be > parent_indent).
        Returns list of AST nodes (parsed by parse_statement).
        """
        if self.pos >= self.total:
            return []

        # if next line isn't more-indented than parent_indent, block is empty
        next_indent = self.token_lines[self.pos][0]
        if next_indent <= parent_indent:
            return []

        base_indent = next_indent
        block_nodes = []
        # parse statements while indent >= base_indent
        while self.pos < self.total and self.token_lines[self.pos][0] >= base_indent:
            node = self.parse_statement()
            if node is not None:
                if isinstance(node, list):
                    block_nodes.extend(node)
                else:
                    block_nodes.append(node)
        return block_nodes

    # -----------------------------
    # Display / Interact
    # -----------------------------
    def parse_display(self, tokens=None, indent=None):
        """
        tokens: filtered tokens for the current line (already consumed by parse_statement)
        indent: the indent level of this line (needed if we collect an indented block)
        """
        if tokens is None:
            tokens = self._consume()

        if not tokens:
            return None

        # If the tokens indicate a function call, build a FunctionCallNode and use that as value
        if any(getattr(t,'type',None) == 'CALL_FUNCTION' for t in tokens) or any(t.type == '(' for t in tokens):
            fcall = self._build_function_call_from_tokens(tokens)
            # remove None-name calls defensively
            return DisplayNode(fcall, bold=any(getattr(t,'type',None)=='PLUS_BOLD' for t in tokens))

        # otherwise pick first literal-like token
        val = None
        for t in tokens:
            ttype = getattr(t, 'type', None)
            if ttype == 'STRING':
                val = t.value
                break
            if ttype in ('INTEGER','FLOAT','BOOLEAN','NULL'):
                val = t.value
                break
            if ttype == 'IDENTIFIER':
                val = t.value
                break

        bold = any(getattr(t,'type',None) == 'PLUS_BOLD' for t in tokens)
        return DisplayNode(val, bold=bold)

    def parse_interact(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        if not tokens:
            return None
        val = None
        for t in tokens:
            if getattr(t,'type',None) in ('STRING','IDENTIFIER'):
                val = t.value
                break
        bold = any(getattr(t,'type',None) == 'PLUS_BOLD' for t in tokens)
        return InteractNode(val, bold=bold)

    # -----------------------------
    # Windows / Buttons
    # -----------------------------
    def parse_window(self, tokens=None, indent=None):
        # tokens already filtered and current line consumed by parse_statement
        if tokens is None:
            tokens = self._consume()
        name = None
        for t in tokens:
            if getattr(t,'type',None) == 'IDENTIFIER':
                name = t.value
                break
            if getattr(t,'type',None) == 'STRING':
                name = t.value
                break
        # collect body using the indent of header (indent argument provided by parse_statement)
        body = self._collect_block(indent if indent is not None else 0)
        node = ObjectNode(name, body)
        node.properties['__is_window__'] = True
        return node

    def parse_button(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        name = None
        parent = None
        for i,t in enumerate(tokens):
            if getattr(t,'type',None) == 'IDENTIFIER' and name is None:
                name = t.value
        # find explicit parent "in <Name>"
        for i,t in enumerate(tokens):
            if getattr(t,'type',None) == 'IN' and i+1 < len(tokens) and tokens[i+1].type == 'IDENTIFIER':
                parent = tokens[i+1].value
                break
        body = self._collect_block(indent if indent is not None else 0)
        return ButtonNode(name, parent, body)

    # -----------------------------
    # Functions
    # -----------------------------
    def parse_function_def(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        name = None
        args = []
        for t in tokens:
            if getattr(t,'type',None) == 'STRING':
                name = t.value
                break
            if getattr(t,'type',None) == 'IDENTIFIER':
                # first identifier after 'define function' is likely the name
                name = t.value
                break
        # gather args if parentheses present
        types = [getattr(t,'type',None) for t in tokens]
        if '(' in types:
            collecting = False
            for t in tokens:
                if getattr(t,'type',None) == '(':
                    collecting = True
                    continue
                if getattr(t,'type',None) == ')':
                    collecting = False
                    continue
                if collecting and getattr(t,'type',None) == 'IDENTIFIER':
                    args.append(t.value)
        body = self._collect_block(indent if indent is not None else 0)
        return FunctionDefNode(name, args, body)

    def _build_function_call_from_tokens(self, tokens):
        """
        Robustly construct a FunctionCallNode from the given filtered token list.
        Supports:
            - CALL_FUNCTION 'name' with arguments (6,7)
            - name(6,7)
            - name 6 7  (space-separated)
        """
        if not tokens:
            return FunctionCallNode(None, [])

        name = None
        args = []

        # prefer explicit CALL_FUNCTION pattern
        for i,t in enumerate(tokens):
            if getattr(t,'type',None) == 'CALL_FUNCTION':
                # next STRING or IDENTIFIER is name
                for j in range(i+1, len(tokens)):
                    if tokens[j].type in ('STRING','IDENTIFIER'):
                        name = tokens[j].value
                        # collect any args afterwards
                        for k in range(j+1, len(tokens)):
                            if tokens[k].type in ('INTEGER','FLOAT','STRING','BOOLEAN','IDENTIFIER'):
                                args.append(tokens[k].value)
                        break
                break

        if name is None:
            # try function-style IDENTIFIER '(' ... ')'
            for i,t in enumerate(tokens):
                if getattr(t,'type',None) == 'IDENTIFIER':
                    # look for '(' after identifier
                    if i+1 < len(tokens) and tokens[i+1].type == '(':
                        name = t.value
                        k = i+2
                        while k < len(tokens) and tokens[k].type != ')':
                            if tokens[k].type in ('INTEGER','FLOAT','STRING','BOOLEAN','IDENTIFIER'):
                                args.append(tokens[k].value)
                            k += 1
                        break
                    else:
                        # identifier followed by literal tokens -> treat as call
                        name = t.value
                        for k in range(i+1, len(tokens)):
                            if tokens[k].type in ('INTEGER','FLOAT','STRING','BOOLEAN','IDENTIFIER'):
                                args.append(tokens[k].value)
                        break

        return FunctionCallNode(name, args)

    def parse_function_call(self, tokens=None, indent=None):
        # tokens passed in by parse_statement (already consumed)
        if tokens is None:
            tokens = self._consume()
        return self._build_function_call_from_tokens(tokens)

    def parse_function_abbrev(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        original = None
        new = None
        for t in tokens:
            if getattr(t,'type',None) in ('STRING','IDENTIFIER'):
                if original is None:
                    original = t.value
                else:
                    new = t.value
        return FunctionAbbrevNode(original, new)

    # -----------------------------
    # Variables & Lists
    # -----------------------------
    def parse_variable_statement(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        types = [getattr(t,'type',None) for t in tokens]

        if 'ASSIGN' in types:
            val = None
            var = None
            try:
                idx = types.index('ASSIGN')
            except ValueError:
                idx = -1
            for t in tokens[idx+1:]:
                if getattr(t,'type',None) in ('STRING','INTEGER','FLOAT','BOOLEAN','IDENTIFIER','NULL'):
                    val = t.value
                    break
            for i,t in enumerate(tokens):
                if getattr(t,'type',None) == 'TO' and i+1 < len(tokens) and tokens[i+1].type == 'IDENTIFIER':
                    var = tokens[i+1].value
                    break
            if var is None and isinstance(val, str) and val.isidentifier():
                var = val
                val = None
            return AssignNode(var, val)

        if 'SET' in types:
            var = None
            val = None
            for i,t in enumerate(tokens):
                if getattr(t,'type',None) == 'IDENTIFIER':
                    var = t.value
                    for j in range(i+1, len(tokens)):
                        if getattr(tokens[j],'type',None) == 'TO' and j+1 < len(tokens):
                            val = tokens[j+1].value
                            break
                    break
            return SetNode(var, val)

        if 'CHANGE' in types:
            var = None
            val = None
            for i,t in enumerate(tokens):
                if getattr(t,'type',None) == 'IDENTIFIER':
                    var = t.value
                    for j in range(i+1, len(tokens)):
                        if getattr(tokens[j],'type',None) == 'TO' and j+1 < len(tokens):
                            val = tokens[j+1].value
                            break
                    break
            return ChangeNode(var, val)

        for op_token, node_cls in (('INCREASE', IncreaseNode), ('DECREASE', DecreaseNode),
                                   ('MULTIPLY', MultiplyNode), ('DIVIDE', DivideNode),
                                   ('EXPONENTIATE', ExponentiateNode)):
            if op_token in types:
                var = None
                val = None
                for i,t in enumerate(tokens):
                    if getattr(t,'type',None) == op_token:
                        if i+1 < len(tokens) and getattr(tokens[i+1],'type',None) == 'IDENTIFIER':
                            var = tokens[i+1].value
                        for j in range(i+1, len(tokens)):
                            if getattr(tokens[j],'type',None) == 'BY' and j+1 < len(tokens):
                                val = tokens[j+1].value
                                break
                        break
                return node_cls(var, val)

        if 'BLOCK' in types:
            for t in tokens:
                if getattr(t,'type',None) == 'IDENTIFIER':
                    return BlockVarNode(t.value)
            return None

        return None

    def parse_list(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        name = None
        elements = []
        for t in tokens:
            if getattr(t,'type',None) == 'IDENTIFIER' and name is None:
                name = t.value
            if getattr(t,'type',None) in ('INTEGER','FLOAT','STRING','IDENTIFIER','BOOLEAN'):
                elements.append(t.value)
        return ListNode(name, elements)

    def parse_list_add(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        val = None
        lst = None
        for t in tokens:
            if getattr(t,'type',None) in ('INTEGER','FLOAT','STRING','IDENTIFIER','BOOLEAN'):
                val = t.value
                break
        idents = [t.value for t in tokens if getattr(t,'type',None) == 'IDENTIFIER']
        if idents:
            lst = idents[-1]
        return ListAddNode(lst, val)

    # -----------------------------
    # Conditionals & loops
    # -----------------------------
    def parse_if(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        cond = None
        for t in tokens:
            if getattr(t,'type',None) in ('STRING','INTEGER','FLOAT','BOOLEAN','NULL','IDENTIFIER'):
                cond = t.value
                break
        body = self._collect_block(indent if indent is not None else 0)
        return IfNode(cond, body)

    def parse_or_if(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        cond = None
        for t in tokens:
            if getattr(t,'type',None) in ('STRING','INTEGER','FLOAT','BOOLEAN','NULL','IDENTIFIER'):
                cond = t.value
                break
        body = self._collect_block(indent if indent is not None else 0)
        return OrIfNode(cond, body)

    def parse_otherwise(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        body = self._collect_block(indent if indent is not None else 0)
        return OtherwiseNode(body)

    def parse_repeat(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        times = None
        for t in tokens:
            if getattr(t,'type',None) in ('INTEGER','IDENTIFIER'):
                times = t.value
                break
        body = self._collect_block(indent if indent is not None else 0)
        return RepeatNode(times, body)

    def parse_do_until(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        cond = None
        for t in tokens:
            if getattr(t,'type',None) in ('STRING','INTEGER','FLOAT','BOOLEAN','IDENTIFIER','NULL'):
                cond = t.value
                break
        body = self._collect_block(indent if indent is not None else 0)
        return DoUntilNode(cond, body)

    def parse_for_each(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        var_name = None
        iterable = None
        for i,t in enumerate(tokens):
            if getattr(t,'type',None) == 'IDENTIFIER' and var_name is None:
                var_name = t.value
            if getattr(t,'type',None) == 'IN' and i+1 < len(tokens) and getattr(tokens[i+1],'type',None) == 'IDENTIFIER':
                iterable = tokens[i+1].value
        body = self._collect_block(indent if indent is not None else 0)
        return ForEachNode(var_name, iterable, body)

    # -----------------------------
    # Math / Files / Getters / Modules
    # -----------------------------
    def parse_math_func(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        func = None
        args = []
        for t in tokens:
            if getattr(t,'type',None) in ('SQUARE','SQUAREROOT','GCD','LCM','RANDOM_INT'):
                func = t.type
            if getattr(t,'type',None) in ('INTEGER','FLOAT','IDENTIFIER'):
                args.append(t.value)
        return MathFuncNode(func, args)

    def parse_file(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        action = None
        filename = None
        text = None
        for t in tokens:
            tt = getattr(t,'type',None)
            if tt and isinstance(tt,str) and tt.startswith('FILE_'):
                action = tt
            if tt == 'STRING':
                if filename is None:
                    filename = t.value
                else:
                    text = t.value
        node = FileNode(action, filename, text)
        if any(getattr(t,'type',None) == 'AT_FIRST' for t in tokens):
            node.at_first = True
        if any(getattr(t,'type',None) == 'FILE_FIND' for t in tokens) and any(getattr(t,'type',None) == 'FILE_REPLACE' for t in tokens):
            strs = [t.value for t in tokens if getattr(t,'type',None) == 'STRING']
            if len(strs) >= 3:
                node.find_text = strs[1]
                node.replace_text = strs[2]
        return node

    def parse_getter(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        target = None
        mode = None
        for t in tokens:
            if getattr(t,'type',None) in ('IDENTIFIER','STRING'):
                target = t.value
                break
        for t in tokens:
            if isinstance(getattr(t,'value',None), str) and t.value.lower() in ('upper','lower','camel','snake','pascal'):
                mode = t.value.lower()
        if any(getattr(t,'type',None) == 'GET_LENGTH' for t in tokens):
            return GetLengthNode(target)
        if any(getattr(t,'type',None) == 'GET_CASE' for t in tokens):
            return GetCaseNode(target, mode)
        if any(getattr(t,'type',None) == 'GET_TYPE' for t in tokens):
            return GetTypeNode(target)
        return None

    def parse_import(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        modules = []
        filename = None
        for t in tokens:
            if getattr(t,'type',None) == 'IDENTIFIER':
                modules.append(t.value)
            if getattr(t,'type',None) == 'STRING':
                filename = t.value
        return ImportNode(modules, filename)

    def parse_export(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        modules = [t.value for t in tokens if getattr(t,'type',None) == 'IDENTIFIER']
        return ExportNode(modules)

    def parse_dictionary(self, tokens=None, indent=None):
        if tokens is None:
            tokens = self._consume()
        name = None
        elements = {}
        for i,t in enumerate(tokens):
            if getattr(t,'type',None) == 'IDENTIFIER' and name is None:
                name = t.value
        for idx,t in enumerate(tokens):
            if getattr(t,'type',None) == 'IDENTIFIER':
                key = t.value
                for r in tokens[idx+1:]:
                    if getattr(r,'type',None) in ('STRING','INTEGER','FLOAT','BOOLEAN','IDENTIFIER'):
                        elements[key] = r.value
                        break
        return DictionaryNode(name, elements)

    # Convenience: if a helper wants to consume the current line itself, use this.
    def _consume(self):
        cur = self.current()
        if not cur:
            return []
        # advance and return filtered tokens
        self.advance()
        return self._filtered_tokens(cur[1])
