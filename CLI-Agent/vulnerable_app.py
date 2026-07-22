import ast

def calculate_user_expression(user_input: str):
    """
    Safely evaluates a string containing a Python literal structure.
    Handles non-literal input gracefully by catching ValueError.
    """

    print(f"Attempting to evaluate structural expression input: {user_input}")

    try:
        result = ast.literal_eval(user_input)
        return result
    except ValueError as e:
        print(f"Error: Invalid literal expression provided. {e}")
        return "Invalid Expression" # Return a safe default or error message

if __name__=="__main__":
    # Test cases for safe evaluation
    print(f"Result for '[1, 2, 3]': {calculate_user_expression('[1, 2, 3]')}")
    print(f"Result for '{"key": "value"}': {calculate_user_expression('{"key": "value"}')}")
    print(f"Result for '123': {calculate_user_expression('123')}")
    print(f"Result for 'None': {calculate_user_expression('None')}")
    print(f"Result for 'True': {calculate_user_expression('True')}")
    
    # Malicious payload (will be caught by ValueError and handled gracefully)
    malicious_payload = "__import__('os').system('echo VULNERABILITY_EXPLOITED')"
    print(f"Result for malicious payload: {calculate_user_expression(malicious_payload)}")
