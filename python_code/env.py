# env.py
from builtins import *

class Environment:
    def __init__(self, parent=None):
        # Variables, functions, lists, dictionaries, objects
        self.variables = {}
        self.functions = {}
        self.lists = {}
        self.dicts = {}
        self.objects = {}
        self.parent = parent  # For nested blocks/scopes
        self.modules = {}

    # --- Variables ---
    def set_var(self, name, value):
        self.variables[name] = value

    def get_var(self, name):
        if name in self.variables:
            return self.variables[name]
        elif self.parent:
            return self.parent.get_var(name)
        else:
            raise NameError(f"Variable '{name}' not defined")

    def delete_var(self, name):
        if name in self.variables:
            del self.variables[name]

    # --- Functions ---
    def set_func(self, name, func):
        self.functions[name] = func

    def get_func(self, name):
        if name in self.functions:
            return self.functions[name]
        elif self.parent:
            return self.parent.get_func(name)
        else:
            raise NameError(f"Function '{name}' not defined")

    # --- Lists ---
    def set_list(self, name, lst):
        self.lists[name] = lst

    def get_list(self, name):
        if name in self.lists:
            return self.lists[name]
        elif self.parent:
            return self.parent.get_list(name)
        else:
            raise NameError(f"List '{name}' not defined")

    # --- Dictionaries ---
    def set_dict(self, name, dct):
        self.dicts[name] = dct

    def get_dict(self, name):
        if name in self.dicts:
            return self.dicts[name]
        elif self.parent:
            return self.parent.get_dict(name)
        else:
            raise NameError(f"Dictionary '{name}' not defined")

    # --- Objects ---
    def set_object(self, name, obj):
        self.objects[name] = obj

    def get_object(self, name):
        if name in self.objects:
            return self.objects[name]
        elif self.parent:
            return self.parent.get_object(name)
        else:
            raise NameError(f"Object '{name}' not defined")

    # --- Scope (blocks) ---
    def create_block(self):
        return Environment(parent=self)

    # --- Modules ---
    def import_module(self, module_name, module_obj):
        self.modules[module_name] = module_obj

    def get_module(self, module_name):
        if module_name in self.modules:
            return self.modules[module_name]
        elif self.parent:
            return self.parent.get_module(module_name)
        else:
            raise NameError(f"Module '{module_name}' not imported")

# --- Test ---
if __name__ == "__main__":
    env = Environment()
    env.set_var("x", 10)
    print("x =", env.get_var("x"))

    # Nested block
    block = env.create_block()
    block.set_var("y", 20)
    print("y in block =", block.get_var("y"))
    print("x in block =", block.get_var("x"))  # Inherited from parent

    # Lists
    env.set_list("mylist", [1,2,3])
    print("mylist:", env.get_list("mylist"))

    # Dictionaries
    env.set_dict("mydict", {"a":1})
    print("mydict:", env.get_dict("mydict"))
