# builtins.py
import math, random, os

def add(a,b):
    return a + b

def subtract(a,b):
    return a - b

def multiply(a,b):
    return a * b

def divide(a,b):
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

def exponentiate(a,b):
    return a ** b

def square_of(n):
    return n ** 2

def squareroot_of(n):
    return math.sqrt(n)

def gcd(a,b):
    return math.gcd(int(a), int(b))

def lcm(a,b):
    return abs(int(a) * int(b)) // math.gcd(int(a), int(b))

def generate_random_int(a=1,b=10):
    return random.randint(int(a), int(b))

def concat(a,b):
    return str(a) + str(b)

def get_length(obj):
    try:
        return len(obj)
    except:
        return 0

def get_case(obj, case_type="lower"):
    if case_type.lower() == "upper":
        return str(obj).upper()
    if case_type.lower() == "lower":
        return str(obj).lower()
    if case_type.lower() == "camel":
        return ''.join(w.capitalize() for w in str(obj).split())
    if case_type.lower() == "snake":
        return str(obj).replace(' ', '_').lower()
    if case_type.lower() == "pascal":
        return ''.join(w.capitalize() for w in str(obj).split())
    return str(obj)

def get_type(obj):
    if obj is None:
        return 'null'
    return type(obj).__name__
