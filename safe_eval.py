import os
from openai import OpenAI

import logging
LOG = logging.getLogger(__name__)


client = OpenAI()

def is_code_safe(code: str) -> bool:
    """
    Evaluates whether the provided Python code is unsafe to run.

    Parameters:
        code (str): The Python code to evaluate.

    Returns:
        str: "False" if the code is unsafe to run, "True" otherwise.
    """
    # allow empty code
    if len(code.strip()) == 0:
        return True


    prompt = f"""
You are an AI assistant that evaluates whether a given piece of Python code is UNSAFE to execute. Identify only genuinely dangerous patterns that could lead to security or stability issues:

1. **Truly Dangerous Operations:**
   - Importing modules that can execute system commands or access network interfaces, such as:
     - `os`, `subprocess`, `socket`, `threading`, `multiprocessing`, `shutil`, etc.
   - Using functions or methods that execute system commands or open network connections, including:
     - `os.system`, `subprocess.run`, `exec`, `eval`
   - Accessing, modifying, or deleting environment variables or dangerous file paths (e.g., with `../`).

2. **File Operations:**
   - Identify dangerous file operations that manipulate files outside the current directory.

3. **Response Format:**
   - Reply **ONLY** with `"False"` if the code meets any of the dangerous criteria above.
   - Reply with `"True"` if no dangerous actions are identified.

**Here is the code to evaluate:**

```python
{code}
```

"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a code safety evaluator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # Set temperature to 0 for deterministic responses
            max_tokens=100, # Limit the response length
        )

        answer = completion.choices[0].message.content.strip()
        if answer.lower().startswith("true"):
            return True
        else:
            return False

    except Exception as e:
        print(f"An error occurred: {e}")
        return False, f"An error occurred: {e}"

def main():
    # Define test cases
    test_cases = [
        {
            "description": "Safe code with allowed import and file operations in CWD",
            "code": """
import csv

def read_csv(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        return list(reader)
""",
            "expected": True
        },
        {
            "description": "Safe code without any imports",
            "code": """
def greet(name):
    return f"Hello, {name}!"
""",
            "expected": True
        },
        {
            "description": "Unsafe code with disallowed import (os module)",
            "code": """
import os

def list_dir():
    return os.listdir('.')
""",
            "expected": False
        },
        {
            "description": "Unsafe code attempting to execute shell commands",
            "code": """
import subprocess

def execute_command(cmd):
    subprocess.run(cmd, shell=True)
""",
            "expected": False
        },
        {
            "description": "Hello world",
            "code": """
# Write your python code here
print('hello')
""",
            "expected": True
        }
    ]

    # Run tests
    for idx, test in enumerate(test_cases, 1):
        print(f"Test Case {idx}: {test['description']}")
        result = is_code_safe(test['code'])
        print(f" Expected: {test['expected']}, Got: {result}")
        print("Result:", "PASS" if result == test['expected'] else "FAIL")
        print("-" * 50)

if __name__ == "__main__":
    main()
