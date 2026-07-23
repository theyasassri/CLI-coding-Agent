import ast

# sandbox/vulnerable_app.py

def calculate_stuff(user_input):
    # Using ast.literal_eval to safely evaluate literals.
    # This prevents arbitrary code execution.
    # Note: ast.literal_eval can only evaluate literals (strings, numbers, tuples, lists, dicts, booleans, and None).
    # It cannot evaluate arbitrary expressions like "10 + 20".
    return ast.literal_eval(user_input)

if __name__ == "__main__":
    # Example updated to use a valid literal for ast.literal_eval
    print(calculate_stuff("30"))