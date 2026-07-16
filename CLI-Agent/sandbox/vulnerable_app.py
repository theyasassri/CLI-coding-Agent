def calculate_user_expression(user_input: str):
    """
    DANGEROUS: Takes direct raw string input from an untrusted source
    and passes it straight into the native interpreter evaluation engine.
    """

    print(f"Processing structural expression input: {user_input}")

    result = eval(user_input)

    return result

if __name__=="__main__":
    sample_payload = "__import__('os'). system('echo VULNERABILITY_EXPLOITED')"
    calculate_user_expression(sample_payload)