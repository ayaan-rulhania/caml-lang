# interpreter.py
from nodes import *
import math, random, os
from builtins import *

class Interpreter:
    def __init__(self):
        self.variables = {}       # global variables
        self.functions = {}       # function name -> FunctionDefNode
        self.objects = {}         # object name -> ObjectNode
        self.lists = {}           # name -> python list
        self.dicts = {}           # name -> python dict
        self.modules = {}         # imported modules (simple)
        # call stack for local scopes when calling functions
        self.call_stack = []

    # Dispatcher
    def visit(self, node):
        method_name = f'visit_{node.__class__.__name__}'
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"No visit method for {node.__class__.__name__}")
        return method(node)

    # --- Display / Interact ---
    def visit_DisplayNode(self, node):
        val = self._resolve_value(node.value)
        out = val
        if node.bold:
            out = f"**{out}**"
        print(out)

    def visit_InteractNode(self, node):
        prompt = self._resolve_value(node.prompt)
        if node.bold:
            prompt = f"**{prompt}**"
        try:
            return input(str(prompt) + ": ")
        except KeyboardInterrupt:
            return ''

    # --- Variables ---
    def visit_AssignNode(self, node):
        self._set_var(node.var_name, node.value)

    def visit_SetNode(self, node):
        self._set_var(node.var_name, node.value)

    def visit_ChangeNode(self, node):
        if node.var_name in self._current_vars():
            self._set_var(node.var_name, node.value)
        else:
            # set anyway (allow creation)
            self._set_var(node.var_name, node.value)

    def visit_IncreaseNode(self, node):
        varname = node.var_name
        val = self._resolve_value(node.value)
        cur = self._get_var(varname)
        if isinstance(cur, (int,float)):
            self._set_var(varname, cur + val)
        else:
            raise TypeError("Increase supports ints/floats only")

    def visit_DecreaseNode(self, node):
        varname = node.var_name
        val = self._resolve_value(node.value)
        cur = self._get_var(varname)
        if isinstance(cur, (int,float)):
            self._set_var(varname, cur - val)
        else:
            raise TypeError("Decrease supports ints/floats only")

    def visit_MultiplyNode(self, node):
        varname = node.var_name
        val = self._resolve_value(node.value)
        cur = self._get_var(varname)
        if isinstance(cur, (int,float)):
            self._set_var(varname, cur * val)
        else:
            raise TypeError("Multiply supports ints/floats only")

    def visit_DivideNode(self, node):
        varname = node.var_name
        val = self._resolve_value(node.value)
        cur = self._get_var(varname)
        if isinstance(cur, (int,float)):
            self._set_var(varname, cur / val)
        else:
            raise TypeError("Divide supports ints/floats only")

    def visit_ExponentiateNode(self, node):
        varname = node.var_name
        val = self._resolve_value(node.value)
        cur = self._get_var(varname)
        if isinstance(cur, (int,float)):
            self._set_var(varname, cur ** val)
        else:
            raise TypeError("Exponentiate supports ints/floats only")

    def visit_BlockVarNode(self, node):
        # block variable by deleting from current scope
        cur_vars = self._current_vars()
        if node.var_name in cur_vars:
            del cur_vars[node.var_name]

    # --- Functions ---
    def visit_FunctionDefNode(self, node):
        # store the function node (name can be string)
        self.functions[node.name] = node

    def visit_FunctionCallNode(self, node):
        # find function
        func = self.functions.get(node.name)
        if not func:
            # maybe built-in function in builtins.py
            builtin = globals().get(node.name) or locals().get(node.name)
            if callable(builtin):
                args = [self._resolve_value(a) for a in node.args]
                return builtin(*args)
            raise Exception(f"Function '{node.name}' not defined")
        # create new scope for function locals
        local_vars = {}
        # zip args -> func.args (note: our function arg parsing is minimal; we assume names align)
        for name, val in zip(func.args, node.args):
            local_vars[name] = self._resolve_value(val)
        # push current environment
        old_vars = self.variables
        self.variables = {**self.variables, **local_vars}
        self.call_stack.append(func.name)
        # execute body
        ret = None
        for stmt in func.body:
            res = self.visit(stmt)
            if res is not None:
                ret = res
        # restore environment
        self.call_stack.pop()
        self.variables = old_vars
        return ret

    def visit_FunctionAbbrevNode(self, node):
        func = self.functions.get(node.original_name)
        if func:
            self.functions[node.new_name] = func

    # --- Conditionals ---
    def visit_IfNode(self, node):
        cond = self._evaluate_condition(node.condition)
        if cond:
            for stmt in node.body:
                self.visit(stmt)

    def visit_OrIfNode(self, node):
        cond = self._evaluate_condition(node.condition)
        if cond:
            for stmt in node.body:
                self.visit(stmt)

    def visit_OtherwiseNode(self, node):
        for stmt in node.body:
            self.visit(stmt)

    # --- Loops ---
    def visit_RepeatNode(self, node):
        times = int(self._resolve_value(node.times))
        for _ in range(times):
            for stmt in node.body:
                self.visit(stmt)

    def visit_DoUntilNode(self, node):
        while not self._evaluate_condition(node.condition):
            for stmt in node.body:
                self.visit(stmt)

    def visit_ForEachNode(self, node):
        iterable = self.lists.get(node.iterable) or self._get_var(node.iterable) or []
        if not isinstance(iterable, list):
            raise TypeError("For each expects a list")
        for item in iterable:
            self._set_var(node.var_name, item)
            for stmt in node.body:
                self.visit(stmt)

    # --- Lists / Dictionaries ---
    def visit_ListNode(self, node):
        # elements may be literals or identifiers; resolve them
        resolved = [self._resolve_value(e) for e in node.elements]
        self.lists[node.name] = resolved

    def visit_ListAddNode(self, node):
        val = self._resolve_value(node.value)
        if node.list_name not in self.lists:
            self.lists[node.list_name] = []
        self.lists[node.list_name].append(val)

    def visit_ListRemoveNode(self, node):
        val = self._resolve_value(node.value)
        if node.list_name in self.lists and val in self.lists[node.list_name]:
            self.lists[node.list_name].remove(val)

    def visit_DictionaryNode(self, node):
        d = {}
        for k,v in node.elements.items():
            d[k] = self._resolve_value(v)
        self.dicts[node.name] = d

    def visit_DictAddNode(self, node):
        val = self._resolve_value(node.value)
        if node.dict_name not in self.dicts:
            self.dicts[node.dict_name] = {}
        self.dicts[node.dict_name][node.key] = val

    def visit_DictRemoveNode(self, node):
        if node.dict_name in self.dicts and node.key in self.dicts[node.dict_name]:
            del self.dicts[node.dict_name][node.key]

    # --- Objects ---
    def visit_ObjectNode(self, node):
        # initialize object container; its body will set properties via ObjectSetPropNode etc.
        self.objects[node.name] = {'properties': {}, 'functions': {}}
        # execute body statements in a temporary scope where object name refers to object
        # but for simplicity, process child nodes that manipulate object directly (we expect ObjectSetPropNode etc)
        for stmt in node.body:
            self.visit(stmt)

    def visit_ObjectSetPropNode(self, node):
        obj = self.objects.get(node.object_name)
        if not obj:
            self.objects[node.object_name] = {'properties': {}, 'functions': {}}
            obj = self.objects[node.object_name]
        obj['properties'][node.prop_name] = self._resolve_value(node.value)

    def visit_ObjectChangePropNode(self, node):
        obj = self.objects.get(node.object_name)
        if obj and node.prop_name in obj['properties']:
            obj['properties'][node.prop_name] = self._resolve_value(node.value)

    def visit_ObjectDeletePropNode(self, node):
        obj = self.objects.get(node.object_name)
        if obj and node.prop_name in obj['properties']:
            del obj['properties'][node.prop_name]

    def visit_ObjectBlockPropNode(self, node):
        obj = self.objects.get(node.object_name)
        if obj and node.prop_name in obj['properties']:
            obj['properties'][node.prop_name] = None

    def visit_ObjectAddFunctionNode(self, node):
        obj = self.objects.get(node.object_name)
        if not obj:
            self.objects[node.object_name] = {'properties': {}, 'functions': {}}
            obj = self.objects[node.object_name]
        obj['functions'][node.func_node.name] = node.func_node

    # --- Math Functions ---
    def visit_MathFuncNode(self, node):
        func = node.func_name
        args = [self._resolve_value(a) for a in node.args]
        # map tokens to builtins
        if func == 'SQUARE':
            return args[0] ** 2
        if func == 'SQUAREROOT':
            return math.sqrt(args[0])
        if func == 'GCD':
            return math.gcd(int(args[0]), int(args[1]))
        if func == 'LCM':
            a,b = int(args[0]), int(args[1])
            return abs(a*b) // math.gcd(a,b)
        if func == 'RANDOM_INT':
            if len(args) == 2:
                return random.randint(int(args[0]), int(args[1]))
            return random.randint(1,10)
        return None

    # --- File Handling ---
    def visit_FileNode(self, node):
        if node.action == 'FILE_CREATE':
            open(node.filename, 'w').close()
        elif node.action == 'FILE_DELETE':
            # ask interaction for confirmation? For non-interactive mode, delete directly
            if os.path.exists(node.filename):
                os.remove(node.filename)
        elif node.action == 'FILE_WRITE':
            mode = 'a'
            if node.at_first:
                # read old content then overwrite
                old = ''
                if os.path.exists(node.filename):
                    with open(node.filename,'r') as f:
                        old = f.read()
                with open(node.filename,'w') as f:
                    f.write(str(node.text) + '\n' + old)
            else:
                with open(node.filename, 'a') as f:
                    f.write(str(node.text) + '\n')
        elif node.action == 'FILE_FIND' or node.action == 'FILE_REPLACE':
            if os.path.exists(node.filename):
                with open(node.filename,'r') as f:
                    content = f.read()
                if node.find_text is not None and node.replace_text is not None:
                    content = content.replace(node.find_text, node.replace_text)
                    with open(node.filename,'w') as f:
                        f.write(content)
        elif node.action == 'FILE_RENAME':
            if node.old_name and node.new_name:
                os.rename(node.old_name, node.new_name)

    # --- Getters ---
    def visit_GetLengthNode(self, node):
        target = self._resolve_value(node.target)
        try:
            return len(target)
        except Exception:
            return 0

    def visit_GetCaseNode(self, node):
        target = self._resolve_value(node.target)
        m = node.mode or 'undefined'
        if m == 'upper':
            return str(target).upper()
        if m == 'lower':
            return str(target).lower()
        if m == 'camel' or m == 'pascal':
            return ''.join(w.capitalize() for w in str(target).split())
        if m == 'snake':
            return str(target).replace(' ', '_').lower()
        return str(target)

    def visit_GetTypeNode(self, node):
        target = self._resolve_value(node.target)
        if target is None:
            return 'null'
        return type(target).__name__

    # --- Modules ---
    def visit_ImportNode(self, node):
        # Simple import: load file and parse/execute it (very basic)
        # For security and simplicity, just store filename
        self.modules[node.filename] = node.modules

    def visit_ExportNode(self, node):
        # Not implemented in detail
        pass

    # --- Utilities ---
    def _resolve_value(self, v):
        # if literal types, return as-is
        if isinstance(v, (int, float, bool)) or v is None:
            return v
        if isinstance(v, str):
            # if it matches a variable name, return var, else raw string
            if v in self.lists:
                return self.lists[v]
            if v in self.dicts:
                return self.dicts[v]
            if v in self.variables:
                return self.variables[v]
            # bare quoted strings arrived as string already
            return v
        # fallback
        return v

    def _get_var(self, name):
        if name in self.variables:
            return self.variables[name]
        return None

    def _set_var(self, name, value):
        resolved = self._resolve_value(value)
        self.variables[name] = resolved

    def _current_vars(self):
        return self.variables

    def _evaluate_condition(self, cond):
        # cond may be literal or identifier or bool
        val = self._resolve_value(cond)
        return bool(val)

    # --- Execute AST ---
    def execute(self, ast):
        # ast expected to be a list of nodes
        for node in ast:
            self.visit(node)
