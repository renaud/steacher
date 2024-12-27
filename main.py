import os
from collections import defaultdict
from datetime import datetime

from openai import OpenAI

from tools import execute_code, copy_student_files, delete_student_files, list_student_files
from safe_eval import is_code_safe
import db


client = OpenAI()



def get_assistant_response(messages):
    ''' Call OpenAI's API with `messages`. '''
    try:
        response = client.chat.completions.create(model="gpt-4o",
        messages=messages,
        temperature=0.7,  # Adjust for creativity
        max_tokens=150)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error communicating with OpenAI API: {e}"



def init_conversation(student_id, language):
    ''' Initialize the conversation with the system prompt and assistant's initial message'''

    # init prompts
    with open("prompt.md", 'r', encoding='utf-8') as file:
        system_prompt = file.read()

    # add language at end of prompt
    lang_prompt = f'\n\nYou will **interact with S in {language}**. Code is in English.'
    messages = [
        {"role": "system", "content": system_prompt + lang_prompt},
    ]

    # fetch initial response
    assistant_response = get_assistant_response(messages)

    # Append assistant's response to the conversation
    messages.append({
            "role": "assistant",
            "content": assistant_response,
    })

    db.save_messages(student_id, messages)

    return messages



def run_conversation(student_id, messages, code, question, hint):

        #print('code', code)
        code_safe, explanation = is_code_safe(code)
        if not code_safe:
            print('code not safe to evaluate', explanation, code)




            print('code not safe to evaluate', explanation, code)

            # Create a user message for unsafe code
            unsafe_user_message = {
                "role": "user",
                "content": f'''User has explicitely asked for hint: {hint}

    # User Question:

    {question}

    # User Code:

    ```python
    {code.strip()}
    ```

    # Safety Issue:

    ```
    {explanation}
    ```
    ''',
                "question": question,
                "hint": hint,
                "code": code,
                "consoleOutput": "",  # No output since code is not executed
                "consoleError": explanation,  # Set consoleError with explanation
                "variables": {},
                "fileList": [],
                "createdAt": datetime.utcnow(),
            }

            # Append the user's message about the unsafe code to the conversation
            messages.append(unsafe_user_message)

            # Create an assistant message indicating the code is unsafe
            assistant_response = "The code provided is unsafe for execution. Please review and modify your code to ensure it doesn't contain any harmful instructions."

            # Append assistant's response about unsafe code to the conversation
            messages.append({
                "role": "assistant",
                "content": assistant_response,
            })

            # Save the messages to the database
            db.save_messages(student_id, messages)

            # Return the messages with empty code_output because execution didn't occur
            return messages, ""

        else:
            # Proceed with safe code execution
            delete_student_files(student_id)
            copy_student_files(student_id)

            code_output, error_msg, variables = execute_code(code, student_id)
            student_files = list_student_files(student_id)
            #print('code_output',code_output)

            # Append user message to the conversation. In str format in 'content', and json otherwise
            messages.append({
                "role": "user",
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
                "question": question,
                "hint": hint,
                "code": code,
                "consoleOutput":code_output,
                "consoleError": error_msg,
                "variables": variables,
                "fileList": student_files,
                "createdAt": str(datetime.utcnow().isoformat()),
            })

            #print(messages)

            assistant_response = get_assistant_response(messages)
            #print(assistant_response)

            # Append assistant's response to the conversation
            messages.append({
                "role": "assistant",
                "content": assistant_response,
            })

            db.save_messages(student_id, messages)

            return messages
