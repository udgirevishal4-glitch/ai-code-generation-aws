from lambda_function import clean_code_response


def test_clean_python_fence():
    assert clean_code_response("```python\nprint('hello')\n```") == "print('hello')\n"


def test_clean_plain_code():
    assert clean_code_response("print('hello')") == "print('hello')\n"
