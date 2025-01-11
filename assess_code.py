import json
import os
import openai
import sys
import argparse

from pydantic import BaseModel, Field
from typing import List

from openai import OpenAI

client = OpenAI()


class Criterion(BaseModel):
    title: str
    score: bool
    short_explanation: str

class Rubric(BaseModel):
    criteria: List[Criterion]



def load_rubric(rubric_path):
    with open(rubric_path, 'r') as file:
        return json.load(file)


def prepare_prompt(rubric, student_code):
    prompt = f"""
You are an automated grading assistant. Using the rubric below, evaluate the provided Python code by assessing each criterion separately and independently.

### **Rubric Criteria:**
"""
    for idx, criterion in enumerate(rubric['criteria'], 1):
        prompt += f"- **{criterion['title']}**: {criterion['description']}\n"
    prompt += f"""

---


**Student Code:**
```python
{student_code}
```

---

### **Evaluation Instructions:**

For each of the above criteria, provide:

- **Score**: `True` if the criterion is met, `False` otherwise.
- **Explanation**: A very brief explanation (one or two sentences) supporting the score.

---

**Important**: Evaluate each criterion **independently** of the others to ensure that the assessment of one does not affect the evaluation of another.

"""

    return prompt


def call_openai_api(prompt, model="gpt-4o-2024-11-20", temperature=0):
    try:

        completion = client.beta.chat.completions.parse(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for grading Python code."},
                {"role": "user", "content": prompt}          ],
            response_format=Rubric
        )
        rubric_response = completion.choices[0].message
        if rubric_response.parsed:
            return rubric_response.parsed
        elif rubric_response.refusal:
            # handle refusal
            print(rubric_response.refusal)

    except Exception as e:
        # Handle edge cases
        if type(e) == openai.LengthFinishReasonError:
            # Retry with a higher max tokens
            print("Too many tokens: ", e)
        else:
            # Handle other exceptions
            print("Exception asses_code", e)



def display_grading(rubric):
    for criterion in rubric.criteria:
        print(f"{criterion.score}\t{criterion.title}\n     \t{criterion.short_explanation}")


def check_keys_match(rubric, rubric_evaluated):
    rubric_titles = [criterion['title'] for criterion in rubric['criteria']]
    evaluated_titles = [criterion.title for criterion in rubric_evaluated.criteria]

    # Check if sizes and respective ordered titles are the same
    if len(rubric_titles) != len(evaluated_titles):
        print('rubric_titles not same size as evaluated_titles',len(rubric_titles),len(evaluated_titles))
        return False

    for r_title, e_title in zip(rubric_titles, evaluated_titles):
        if r_title != e_title:
            print('r_title != e_title', r_title,e_title)
            return False

    return True


def compute_score(rubric, rubric_evaluated):
    score = 0.0
    for rubric_criterion, evaluated_criterion in zip(rubric['criteria'], rubric_evaluated.criteria):
        if evaluated_criterion.score:  # If the score is True for this criterion
            score += rubric_criterion.get('weight', 0)  # Assuming 'weight' is in the rubric json structure
    return int(score)



def grade(student_code, rubric_json='rubric.json') -> (int, str):
    ''' @returns a score btw 0 and 100 and the rubric evaluation (a json string), 
        or None, None if error.'''
    try:
        rubric = load_rubric(rubric_json)
        prompt = prepare_prompt(rubric, student_code)

        rubric_evaluated = call_openai_api(prompt, model="gpt-4o-mini")

        if rubric_evaluated:
            keys_match = check_keys_match(rubric, rubric_evaluated)
            if keys_match:
                score = compute_score(rubric, rubric_evaluated)
                return score, rubric_evaluated.model_dump_json()
            else:
                print("Rubrics do not match in keys or order.")
                return None, None

            #display_grading(rubric_evaluated)
        else:
            print("Failed to evaluate rubric.")
            return None, None
    except Exception as e:
        print("Error evaluating rubric", e)
        return None, None



def main():
    student_code = '''
import csv

temps = {}

f = open('temperatures.csv')
r = csv.reader(f)
for row in r:
    date = row[0]
    temp = row[2]
    temps.date = temp
f.close()
'''
    print(grade(student_code))


if __name__ == "__main__":
    main()
