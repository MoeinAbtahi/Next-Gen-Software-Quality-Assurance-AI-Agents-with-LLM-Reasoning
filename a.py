# Python file with 10 issues

def add_numbers(a, b):
    result = a + b
    return result

def subtract_numbers(a, b):
    return a - b

def multiply_numbers(a, b):
    return a * b

# Issue 1: Unused function
def divide_numbers(a, b):
    return a / b

# Issue 2: Syntax error, missing closing parenthesis
def print_sum(a, b:
    print(a + b)

# Issue 3: NameError, variable not defined
def print_difference(a, b):
    print(c)

# Issue 4: TypeError, trying to add a string to a number
def concatenate(a, b):
    return a + b

# Issue 5: ZeroDivisionError, divide by zero
def safe_divide(a, b):
    return a / 0

# Issue 6: IndentationError
def some_function():
print("This is incorrect indentation.")

# Issue 7: Missing return statement
def multiply(a, b):
    result = a * b

# Issue 8: ValueError, passing incompatible types to the function
def convert_to_integer(a):
    return int(a)

# Issue 9: ImportError, incorrect import statement
from math import somemathfunction

# Issue 10: AssertionError, incorrect assertion
assert add_numbers(5, 10) == 10
