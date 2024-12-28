import os
from openai import OpenAI

client = OpenAI()

def is_code_safe(code: str) -> bool:
    """
    Evaluates whether the provided Python code is safe to run.

    Parameters:
        code (str): The Python code to evaluate.

    Returns:
        str: "True" if the code is safe to run, "False" otherwise.
    """

    # empty code is ok :-)
    if len(code.strip()) == 0:
        return True


    prompt = f"""
You are an AI assistant that evaluates whether a given piece of Python code is safe to execute. Follow these guidelines to determine safety:

1. **Allowed Operations:**
   - Writing comments.
   - Printing to the console.
   - Defining and using variables.
   - Writing and calling functions.
   - Importing modules from the following safe list:
     - `csv`
     - `math`
     - `random`
   - Reading from and writing to files **only within the current working directory**.

2. **Disallowed Operations:**
   - Importing any modules **not** in the allowed list.
   - Using functions or methods that execute system commands, modify system settings, or perform network operations, such as:
     - `os.system`
     - `subprocess.Popen`
     - `eval`, `exec`
     - Any functions from the `os`, `sys` modules that can alter the environment
   - Accessing or modifying environment variables.
   - Importing modules like `socket`, `threading`, `multiprocessing`, `shutil`, etc.

3. **File Operations:**
   - Ensure that file paths do not traverse directories (e.g., no `../` patterns).
   - Only allow reading from and writing to files within the current directory.
   - It's ok not to specify the mode, as reading (`r`) is the default mode.

4. **Code Structure:**
   - The code may have indentation issues or syntax errors; focus only on the safety of operations.

5. **Response Format:**
   - Reply **ONLY** with `"True"` if the code adheres to all safety guidelines.
   - Reply with `"False"` if the code violates any safety guidelines and **explain why** it violates any safety guidelines.

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
        #print(answer)
        if answer.lower().startswith("true"):
            return True, None
        else:
            return False, answer

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
        result, explanation = is_code_safe(test['code'])
        print(f" Expected: {test['expected']}, Got: {result}. Explanation: {explanation}")
        print("Result:", "PASS" if result == test['expected'] else "FAIL")
        print("-" * 50)

if __name__ == "__main__":
    main()
