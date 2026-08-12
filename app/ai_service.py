import json
import os


def demo_code(title: str, body: str) -> str:
    text = f'{title} {body}'.lower()
    if 'fibonacci' in text:
        return '''def fibonacci(n):\n    """Return the first n Fibonacci numbers."""\n    if n < 0:\n        raise ValueError("n must be non-negative")\n    sequence = []\n    a, b = 0, 1\n    for _ in range(n):\n        sequence.append(a)\n        a, b = b, a + b\n    return sequence\n'''
    if 'factorial' in text:
        return '''def factorial(n):\n    """Return n factorial."""\n    if n < 0:\n        raise ValueError("n must be non-negative")\n    result = 1\n    for value in range(2, n + 1):\n        result *= value\n    return result\n'''
    if 'email' in text:
        return '''import re\n\ndef is_valid_email(email):\n    """Return True when email has a basic valid format."""\n    return bool(re.fullmatch(r"[^@\\s]+@[^@\\s]+\\.[^@\\s]+", email))\n'''
    return f'''def implement_requirement():\n    """Initial implementation generated for: {title}."""\n    # Requirement: {body or title}\n    raise NotImplementedError("Complete the implementation for this requirement")\n'''


def generate_code(title: str, body: str, demo=False):
    if demo or not os.getenv('AWS_REGION'):
        return demo_code(title, body), 'Demo AI generator'

    import boto3
    client = boto3.client('bedrock-runtime', region_name=os.environ['AWS_REGION'])
    model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0')
    prompt = f"Generate clean production-ready Python code for this GitHub issue. Return code only.\nTitle: {title}\nDescription: {body}"
    payload = {'anthropic_version': 'bedrock-2023-05-31', 'max_tokens': 2000, 'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}]}
    response = client.invoke_model(modelId=model_id, body=json.dumps(payload), contentType='application/json', accept='application/json')
    data = json.loads(response['body'].read())
    return data['content'][0]['text'], f'Amazon Bedrock ({model_id})'
