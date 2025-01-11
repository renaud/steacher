import os
from collections import defaultdict
from datetime import datetime

from openai import OpenAI

import logging
LOG = logging.getLogger(__name__)

from tools import execute_code, copy_student_files, delete_student_files, list_student_files
from safe_eval import is_code_safe
import db


client = OpenAI()

model = "gpt-4o"



def get_assistant_response(messages):
    ''' Call OpenAI's API with `messages`. '''
    try:
        response = client.chat.completions.create(model=model,
        messages=messages,
        temperature=0.7,  # Adjust for creativity
        max_tokens=150)
        return response.choices[0].message.content.strip()
    except Exception as e:
        LOG.warn(f"Error communicating with OpenAI API: {e}, {messages}")
        return f"Error communicating with OpenAI API: {e}"



def init_conversation(student_id, language):
    ''' Initialize the conversation with the system prompt and assistant's initial message'''

    # init prompts
    with open("prompt.md", 'r', encoding='utf-8') as file:
        system_prompt = file.read()
    with open("initial_instruction.md", 'r', encoding='utf-8') as file:
        initial_instructions = file.read()

    # add language at end of prompt
    lang_prompt = f'\n\nYou will **interact with me (student) in {language}**. Python code is always in English.'
    messages = [
        {"role": "system", "content": system_prompt + lang_prompt},
        {"role": "assistant", "content": initial_instructions}
    ]
    LOG.debug(messages)

    db.save_messages(student_id, messages)
    return messages



def run_conversation(student_id, messages, code, question, hint):
    code_safe = is_code_safe(code)
    if not code_safe:
        LOG.error(f'SAFETY ERROR: code not safe to evaluate, {code}')
        code_output = ""
        error_msg = ""  # there's no error message, it's just not safe to evaluate
        variables = []

    else:
        # Proceed with safe code execution
        delete_student_files(student_id)
        copy_student_files(student_id)

        code_output, error_msg, variables = execute_code(code, student_id)
        LOG.debug(f'code_output: {code_output}')

    student_files = list_student_files(student_id)
    
    # Append a new user message to the conversation. In str format in 'content', and json otherwise
    messages.append({
        "role": "user",
        "question": question,
        "hint": hint,
        "code": code,
        "codeIsSafe": code_safe,
        "consoleOutput": code_output,
        "consoleError": error_msg if code_safe else "",  # Only set error_msg if code is safe
        "variables": variables,
        "fileList": student_files,
        "createdAt": str(datetime.utcnow().isoformat()),
        "content": f'''Hint requested: {hint}

# Student Message:

{question}

# Student Code:

```python
{code.strip()}
```

# Code Output:

```
{code_output}
```

# Execution Errors:

```
{error_msg}
```

''',
    })

    # Ask assistant for feedback?
    if hint or len(question) > 0 or (not code_safe):
        assistant_response = get_assistant_response(messages)

        # Append assistant's response to the conversation
        messages.append({
            "role": "assistant",
            "creator": "gpt-4o",
            "content": assistant_response,
        })

    db.save_messages(student_id, messages)
    return messages
