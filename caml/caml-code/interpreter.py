# interpreter.py
from nodes import *
import math, random, os
import tkinter as tk
from builtins import *

class Interpreter:
    def __init__(self):
        # Data stores
        self.variables = {}       # global variables
        self.functions = {}       # name -> FunctionDefNode
        self.objects = {}         # object name -> dict(properties, functions)
        self.lists = {}           # name -> python list
        self.dicts = {}           # name -> python dict
        self.modules = {}         # imports
        self.call_stack = []

        # GUI runtime
        self._root_created = False
        self.gui_root = None          # main tk root (tk.Tk)
        self.gui_windows = {}         # additional windows: name -> tk.Toplevel or root
        self.gui_buttons = {}         # name -> tk.Button

    # ---------- Visitor dispatcher ----------
    def visit(self, node):
        method = getattr(self, f'visit_{node.__class__.__name__}', None)
        if method is None:
            raise Exception(f"No visit handler for {node.__class__.__name__}")
        return method(node)

    # ---------- Display / Interact ----------
    def visit_DisplayNode(self, node):
        # node.value may be a FunctionCallNode or a literal/identifier
        if isinstance(node.value, FunctionCallNode):
            val = self.visit(node.value)
        else:
            val = self._resolve_value(node.value)

        out = val
        if node.bold:
            out = f"**{out}**"
        print(out)
        return out

    def visit_InteractNode(self, node):
        prompt = self._resolve_value(node.prompt)
        if node.bold:
            prompt = f"**{prompt}**"
        try:
            return input(str(prompt) + ": ")
        except KeyboardInterrupt:
            return ''

    # ---------- Variables ----------
    def visit_AssignNode(self, node):
        self._set_var(node.var_name, node.value)

    def visit_SetNode(self, node):
        # Setting variables OR could be setting GUI property if pattern matches
        self._set_var(node.var_name, node.value)

    def visit_ChangeNode(self, node):
        self._set_var(node.var_name, node.value)

    def visit_IncreaseNode(self, node):
        cur = self._get_var(node.var_name)
        val = self._resolve_value(node.value)
        if isinstance(cur, (int,float)) and isinstance(val, (int,float)):
            self._set_var(node.var_name, cur + val)
        else:
            raise TypeError("Increase supports numeric types only")

    def visit_DecreaseNode(self, node):
        cur = self._get_var(node.var_name)
        val = self._resolve_value(node.value)
        if isinstance(cur, (int,float)) and isinstance(val, (int,float)):
            self._set_var(node.var_name, cur - val)
        else:
            raise TypeError("Decrease supports numeric types only")

    def visit_MultiplyNode(self, node):
        cur = self._get_var(node.var_name)
        val = self._resolve_value(node.value)
        if isinstance(cur, (int,float)) and isinstance(val, (int,float)):
            self._set_var(node.var_name, cur * val)
        else:
            raise TypeError("Multiply supports numeric types only")

    def visit_DivideNode(self, node):
        cur = self._get_var(node.var_name)
        val = self._resolve_value(node.value)
        if isinstance(cur, (int,float)) and isinstance(val, (int,float)):
            self._set_var(node.var_name, cur / val)
        else:
            raise TypeError("Divide supports numeric types only")

    def visit_ExponentiateNode(self, node):
        cur = self._get_var(node.var_name)
        val = self._resolve_value(node.value)
        if isinstance(cur, (int,float)) and isinstance(val, (int,float)):
            self._set_var(node.var_name, cur ** val)
        else:
            raise TypeError("Exponentiate supports numeric types only")

    def visit_BlockVarNode(self, node):
        if node.var_name in self.variables:
            del self.variables[node.var_name]

    # ---------- Functions ----------
    def visit_FunctionDefNode(self, node):
        # store function AST node
        self.functions[node.name] = node

    def visit_FunctionCallNode(self, node):
        # look up defined function
        func = self.functions.get(node.name)
        if func:
            # create local variable mapping
            old_vars = self.variables.copy()
            local = {}
            for name, argval in zip(func.args, node.args):
                local[name] = self._resolve_value(argval)
            # merge locals (shadowing)
            self.variables = {**self.variables, **local}
            self.call_stack.append(func.name)
            ret = None
            for stmt in func.body:
                r = self.visit(stmt)
                if r is not None:
                    ret = r
            self.call_stack.pop()
            # restore outer environment (simple approach)
            self.variables = old_vars
            return ret
        # fallback to builtins (from builtins.py)
        builtin = globals().get(node.name) or locals().get(node.name)
        if callable(builtin):
            args = [self._resolve_value(a) for a in node.args]
            return builtin(*args)
        # maybe it's a variable/function stored in self.modules or self.objects
        # finally, if name is literal string, return it
        return node.name

    def visit_FunctionAbbrevNode(self, node):
        func = self.functions.get(node.original_name)
        if func:
            self.functions[node.new_name] = func

    # ---------- Conditionals ----------
    def visit_IfNode(self, node):
        if self._evaluate_condition(node.condition):
            for s in node.body:
                self.visit(s)

    def visit_OrIfNode(self, node):
        if self._evaluate_condition(node.condition):
            for s in node.body:
                self.visit(s)

    def visit_OtherwiseNode(self, node):
        for s in node.body:
            self.visit(s)

    # ---------- Loops ----------
    def visit_RepeatNode(self, node):
        times = int(self._resolve_value(node.times))
        for _ in range(times):
            for s in node.body:
                self.visit(s)

    def visit_DoUntilNode(self, node):
        while not self._evaluate_condition(node.condition):
            for s in node.body:
                self.visit(s)

    def visit_ForEachNode(self, node):
        iterable = None
        if node.iterable in self.lists:
            iterable = self.lists[node.iterable]
        else:
            iterable = self._get_var(node.iterable) or []
        if not isinstance(iterable, list):
            raise TypeError("ForEach expects a list")
        for item in iterable:
            self._set_var(node.var_name, item)
            for s in node.body:
                self.visit(s)

    # ---------- Lists / Dicts ----------
    def visit_ListNode(self, node):
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

    # ---------- Objects & GUI ----------
    def visit_ObjectNode(self, node):
        # create object container
        if node.name not in self.objects:
            self.objects[node.name] = {'properties': {}, 'functions': {}}
        # if this object is marked as a window, create or attach GUI window
        if node.properties.get('__is_window__'):
            self._ensure_root()
            # create a new Toplevel for named window unless root is unused
            if self.gui_root is None:
                # first created window uses root
                self.gui_root = tk.Tk()
                self.gui_windows[node.name] = self.gui_root
            else:
                top = tk.Toplevel(self.gui_root)
                self.gui_windows[node.name] = top
            # store link in object properties
            self.objects[node.name]['tk_window'] = self.gui_windows[node.name]

        # visit body to handle property-setting / nested widgets
        for stmt in node.body:
            # allow certain nodes to know their parent (button creation)
            if isinstance(stmt, ButtonNode):
                # if button has no parent specified, default to this window if this is window object
                if not stmt.parent and node.properties.get('__is_window__'):
                    stmt.parent = node.name
            self.visit(stmt)

    def visit_ObjectSetPropNode(self, node):
        # set property in object store
        obj = self.objects.get(node.object_name)
        if not obj:
            obj = {'properties': {}, 'functions': {}}
            self.objects[node.object_name] = obj
        val = self._resolve_value(node.value)
        obj['properties'][node.prop_name] = val

        # if object corresponds to a GUI window, apply properties
        if node.object_name in self.gui_windows:
            win = self.gui_windows[node.object_name]
            if node.prop_name.lower() == 'title':
                win.title(val)
            if node.prop_name.lower() in ('background','bg'):
                try:
                    win.configure(bg=val)
                except Exception:
                    pass

        # if object corresponds to a button, apply to the button
        if node.object_name in self.gui_buttons:
            btn = self.gui_buttons[node.object_name]
            if node.prop_name.lower() in ('text','display text'):
                btn.config(text=str(val))
            if node.prop_name.lower() in ('color','bg'):
                btn.config(bg=val)
            if node.prop_name.lower() == 'fg':
                btn.config(fg=val)

    def visit_ObjectChangePropNode(self, node):
        obj = self.objects.get(node.object_name)
        if obj and node.prop_name in obj['properties']:
            obj['properties'][node.prop_name] = self._resolve_value(node.value)
            # apply to GUI if applicable
            self.visit_ObjectSetPropNode(node)

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

    # Button node visitor
    def visit_ButtonNode(self, node):
        parent_name = node.parent
        if not parent_name:
            raise Exception(f"Button '{node.name}' has no parent window specified")
        if parent_name not in self.gui_windows:
            raise Exception(f"Parent window '{parent_name}' not found for button '{node.name}'")
        win = self.gui_windows[parent_name]
        text = node.properties.get('text', node.name or 'Button')
        btn = tk.Button(win, text=text)
        btn.pack()
        self.gui_buttons[node.name] = btn
        # apply any property statements in button body
        for stmt in node.body:
            # if body contains ObjectSetPropNode with object_name equal to button name, apply
            if isinstance(stmt, ObjectSetPropNode) and stmt.object_name == node.name:
                self.visit_ObjectSetPropNode(stmt)
            else:
                self.visit(stmt)

    # ---------- Math functions ----------
    def visit_MathFuncNode(self, node):
        args = [self._resolve_value(a) for a in node.args]
        if node.func_name == 'SQUARE':
            return args[0] ** 2
        if node.func_name == 'SQUAREROOT':
            return math.sqrt(args[0])
        if node.func_name == 'GCD':
            return math.gcd(int(args[0]), int(args[1]))
        if node.func_name == 'LCM':
            a,b = int(args[0]), int(args[1])
            return abs(a*b)//math.gcd(a,b)
        if node.func_name == 'RANDOM_INT':
            if len(args) == 2:
                return random.randint(int(args[0]), int(args[1]))
            return random.randint(1,10)
        return None

    # ---------- File handling ----------
    def visit_FileNode(self, node):
        if node.action == 'FILE_CREATE':
            open(node.filename, 'w').close()
        elif node.action == 'FILE_DELETE':
            if os.path.exists(node.filename):
                os.remove(node.filename)
        elif node.action == 'FILE_WRITE':
            if node.at_first:
                old = ''
                if os.path.exists(node.filename):
                    with open(node.filename, 'r') as f:
                        old = f.read()
                with open(node.filename, 'w') as f:
                    f.write(str(node.text) + '\n' + old)
            else:
                with open(node.filename, 'a') as f:
                    f.write(str(node.text) + '\n')
        elif node.action in ('FILE_FIND','FILE_REPLACE'):
            if os.path.exists(node.filename):
                with open(node.filename, 'r') as f:
                    content = f.read()
                if node.find_text is not None and node.replace_text is not None:
                    content = content.replace(node.find_text, node.replace_text)
                    with open(node.filename, 'w') as f:
                        f.write(content)
        elif node.action == 'FILE_RENAME':
            if node.old_name and node.new_name:
                os.rename(node.old_name, node.new_name)

    # ---------- Getters ----------
    def visit_GetLengthNode(self, node):
        t = self._resolve_value(node.target)
        try:
            return len(t)
        except:
            return 0

    def visit_GetCaseNode(self, node):
        t = self._resolve_value(node.target)
        mode = node.mode or 'lower'
        if mode == 'upper':
            return str(t).upper()
        if mode == 'lower':
            return str(t).lower()
        if mode in ('camel','pascal'):
            return ''.join(w.capitalize() for w in str(t).split())
        if mode == 'snake':
            return str(t).replace(' ', '_').lower()
        return str(t)

    def visit_GetTypeNode(self, node):
        t = self._resolve_value(node.target)
        if t is None:
            return 'null'
        return type(t).__name__

    # ---------- Modules ----------
    def visit_ImportNode(self, node):
        # store module name; not executing files here for safety
        self.modules[node.filename] = node.modules

    def visit_ExportNode(self, node):
        pass

    # ---------- Utilities ----------
    def _resolve_value(self, v):
        # if AST node, evaluate
        if isinstance(v, FunctionCallNode):
            return self.visit(v)
        if isinstance(v, (int, float, bool)) or v is None:
            return v
        if isinstance(v, str):
            # if v is list/dict/var name, resolve
            if v in self.lists:
                return self.lists[v]
            if v in self.dicts:
                return self.dicts[v]
            if v in self.variables:
                return self.variables[v]
            # otherwise it's a literal string (returned without quotes)
            return v
        return v

    def _get_var(self, name):
        return self.variables.get(name)

    def _set_var(self, name, value):
        self.variables[name] = self._resolve_value(value)

    def _evaluate_condition(self, cond):
        val = self._resolve_value(cond)
        return bool(val)

    # ensure main root exists for GUI
    def _ensure_root(self):
        if not self._root_created:
            # do not automatically create tk.Tk here; leave creation until first window visited
            self._root_created = True

    # ---------- Execution ----------
    def execute(self, ast):
        for node in ast:
            self.visit(node)
        # After running program, if any GUI windows were created, start mainloop
        if self.gui_root or self.gui_windows:
            # If no root created but windows exist, create a root
            if self.gui_root is None and self.gui_windows:
                # pick the first window as root
                first = next(iter(self.gui_windows))
                # already created as Toplevel earlier; to be safe, create root
                self.gui_root = tk.Tk()
                # If windows were created as Toplevels earlier they are fine; otherwise we assign root to first
            # Start mainloop (this will block until windows closed)
            try:
                # if a root exists, call mainloop once
                if self.gui_root:
                    self.gui_root.mainloop()
            except Exception:
                pass
