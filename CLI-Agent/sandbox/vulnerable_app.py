import ast

# sandbox/vulnerable_app.py

def calculate_stuff(user_input):
    return eval(user_input)

if __name__ == "__main__":
    print(calculate_stuff("10 + 20"))