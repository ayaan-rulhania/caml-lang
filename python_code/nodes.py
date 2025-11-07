# nodes.py
# AST nodes for Caml Language 🐪

# --- Display / Interact ---
class DisplayNode:
    def __init__(self, value, bold=False):
        self.value = value
        self.bold = bold

class InteractNode:
    def __init__(self, prompt, bold=False):
        self.prompt = prompt
        self.bold = bold

# --- Comments (not present in AST; parsed away) ---

# --- Variables ---
class AssignNode:
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

class SetNode:
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

class ChangeNode:
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

class IncreaseNode:
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

class DecreaseNode:
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

class MultiplyNode:
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

class DivideNode:
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

class ExponentiateNode:
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

class BlockVarNode:
    def __init__(self, var_name):
        self.var_name = var_name

# --- Functions ---
class FunctionDefNode:
    def __init__(self, name, args, body):
        self.name = name
        self.args = args
        self.body = body

class FunctionCallNode:
    def __init__(self, name, args):
        self.name = name
        self.args = args

class FunctionAbbrevNode:
    def __init__(self, original_name, new_name):
        self.original_name = original_name
        self.new_name = new_name

# --- Conditionals ---
class IfNode:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class OrIfNode:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class OtherwiseNode:
    def __init__(self, body):
        self.body = body

# --- Loops ---
class RepeatNode:
    def __init__(self, times, body):
        self.times = times
        self.body = body

class DoUntilNode:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class ForEachNode:
    def __init__(self, var_name, iterable, body):
        self.var_name = var_name
        self.iterable = iterable
        self.body = body

# --- Lists / Dictionaries ---
class ListNode:
    def __init__(self, name, elements):
        self.name = name
        self.elements = elements

class ListAddNode:
    def __init__(self, list_name, value):
        self.list_name = list_name
        self.value = value

class ListRemoveNode:
    def __init__(self, list_name, value):
        self.list_name = list_name
        self.value = value

class DictionaryNode:
    def __init__(self, name, elements):
        self.name = name
        self.elements = elements

class DictAddNode:
    def __init__(self, dict_name, key, value):
        self.dict_name = dict_name
        self.key = key
        self.value = value

class DictRemoveNode:
    def __init__(self, dict_name, key):
        self.dict_name = dict_name
        self.key = key

# --- Objects ---
class ObjectNode:
    def __init__(self, name, body):
        self.name = name
        self.body = body
        self.properties = {}
        self.functions = {}

class ObjectSetPropNode:
    def __init__(self, object_name, prop_name, value):
        self.object_name = object_name
        self.prop_name = prop_name
        self.value = value

class ObjectChangePropNode:
    def __init__(self, object_name, prop_name, value):
        self.object_name = object_name
        self.prop_name = prop_name
        self.value = value

class ObjectDeletePropNode:
    def __init__(self, object_name, prop_name):
        self.object_name = object_name
        self.prop_name = prop_name

class ObjectBlockPropNode:
    def __init__(self, object_name, prop_name):
        self.object_name = object_name
        self.prop_name = prop_name

class ObjectAddFunctionNode:
    def __init__(self, object_name, func_node):
        self.object_name = object_name
        self.func_node = func_node

# --- Math Functions ---
class MathFuncNode:
    def __init__(self, func_name, args):
        self.func_name = func_name
        self.args = args

# --- File Handling ---
class FileNode:
    def __init__(self, action, filename, text=None):
        self.action = action
        self.filename = filename
        self.text = text
        self.at_first = False  # Set True if writing at first line
        self.find_text = None
        self.replace_text = None
        self.old_name = None
        self.new_name = None

# --- Getters ---
class GetLengthNode:
    def __init__(self, target):
        self.target = target

class GetCaseNode:
    def __init__(self, target, mode=None):
        self.target = target
        self.mode = mode

class GetTypeNode:
    def __init__(self, target):
        self.target = target

# --- Modules ---
class ImportNode:
    def __init__(self, modules, filename):
        self.modules = modules
        self.filename = filename

class ExportNode:
    def __init__(self, modules):
        self.modules = modules
