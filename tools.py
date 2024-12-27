import os
import contextlib
import io
import traceback
import shutil
import json


ORIGINAL_DIR = "original_code"
# Define the base directory for all students
BASE_STUDENTS_DIR = "students_code"
# Create the base directory if it doesn't exist
os.makedirs(BASE_STUDENTS_DIR, exist_ok=True)



def delete_student_files(student_id: str) -> str:
    student_dir = os.path.join(BASE_STUDENTS_DIR, student_id)
    if os.path.exists(student_dir):
        shutil.rmtree(student_dir)



def copy_student_files(student_id: str, original_dir: str=ORIGINAL_DIR) -> str:
    """
    Copies files from the original directory to the student's unique directory.

    Args:
        student_id (str): Unique identifier for the student.
        original_dir (str): Path to the original directory containing the files to copy.

    Returns:
        str: Success or error message.
    """
    try:
        # Define the student's directory path
        student_dir = os.path.join(BASE_STUDENTS_DIR, student_id)

        # Create the student's directory if it doesn't exist
        os.makedirs(student_dir, exist_ok=True)

        # Copy all files and subdirectories from original_dir to student_dir
        if os.path.isdir(original_dir):
            shutil.copytree(original_dir, student_dir, dirs_exist_ok=True)
        else:
            return f"Error: The original directory '{original_dir}' does not exist."

        return f"Files successfully copied to {student_dir}."

    except Exception as e:
        return f"Error copying files: {str(e)}"




def list_student_files(student_id: str) -> list:
    """
    Lists all files in the student's directory.

    Args:
        student_id (str): Unique identifier for the student.

    Returns:
        list: A list of file paths relative to the student's directory.
    """
    student_dir = os.path.join(BASE_STUDENTS_DIR, student_id)
    file_list = []

    if os.path.exists(student_dir) and os.path.isdir(student_dir):
        for root, _, files in os.walk(student_dir):
            for file in files:
                # Join the root and file then make it relative to the student's directory
                relative_path = os.path.relpath(os.path.join(root, file), student_dir)
                file_list.append(relative_path)

    return file_list





def execute_code(code: str, student_id: str) -> str:
    """
    Execute Python code passed as a string in a specified working directory.

    Args:
        code (str): The Python code to execute.
        student_dir (str): The directory to change to before executing the code.

    Returns:
        str: The standard output and standard error produced by the executed code.
    """

    student_dir = os.path.join(BASE_STUDENTS_DIR, student_id)
    # Save the current working directory to restore later
    original_directory = os.getcwd()
    output = io.StringIO()
    error_msg = None

    # Dictionary to serve as the execution namespace
    exec_globals = {"__name__": "__main__"}

    try:
        # Change to the specified student_dir
        os.chdir(student_dir)

        # Redirect stdout and stderr to capture outputs
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            exec(code, exec_globals)

    except Exception as e:
        # Capture the full stack trace
        stack_trace = traceback.format_exc()
        # only keep the relevant part for us
        err = stack_trace.split("exec(code, exec_globals)")[1]
        error_msg = f"Error:{err}"

    finally:
        # Restore the original working directory
        os.chdir(original_directory)


    # Capture variables after execution
    # Exclude built-in variables and modules
    captured_vars = {
        key: repr(value)
        for key, value in exec_globals.items()
        if not key.startswith("__") and not isinstance(value, type(os))
    }

    # Serialize captured variables to a JSON-compatible string
    try:
        variables_json = json.dumps(captured_vars, indent=4)
    except TypeError:
        # If some variables are not JSON serializable, fall back to string representation
        variables_json = json.dumps(
            {k: str(v) for k, v in captured_vars.items()}, indent=4
        )



    return output.getvalue(), error_msg, variables_json




# from RestrictedPython import compile_restricted_exec
# from RestrictedPython.Guards import safe_builtins, guarded_iter_unpack_sequence, guarded_unpack_sequence
# from io import StringIO
# import os

# from RestrictedPython.PrintCollector import PrintCollector





# def execute_restricted_python(student_id: str, code: str, base_students_dir: str = BASE_STUDENTS_DIR) -> str:
#     """
#     Executes Python code in a restricted environment within the student's directory.

#     Args:
#         student_id (str): Unique identifier for the student
#         code (str): The Python code to execute
#         base_students_dir (str): Base directory for student folders

#     Returns:
#         str: The output of the executed code or an error message
#     """
#     # Define the student's directory path
#     student_dir = os.path.join(base_students_dir, student_id)
#     if not os.path.isdir(student_dir):
#         return f"Error: Student directory '{student_dir}' does not exist. Please copy files first."

#     # Change the current working directory to the student's directory
#     original_cwd = os.getcwd()
#     try:
#         os.chdir(student_dir)

#         # Create output capture and print hook
#         output = StringIO()
#         print_hook = PrintHook(output)

#         # Compile the code using RestrictedPython
#         compiled_code = compile_restricted_exec(code)
#         if compiled_code.errors:
#             print(compiled_code.errors)

#         # Prepare restricted built-ins
#         restricted_globals = {
#             '__builtins__': safe_builtins,
#             '_print_': PrintCollector
#             '_getiter_': iter,
#             '_getattr_': getattr,
#             '_getitem_': lambda obj, key: obj[key],
#             '_unpack_sequence_': guarded_unpack_sequence,
#             '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
#         }

#         # Execute the compiled code
#         exec(compiled_code.code, restricted_globals, {})

#         # Get the captured output
#         result = output.getvalue()
#         return result if result else "Code executed successfully with no output."

#     except Exception as e:
#         import traceback
#         print(traceback.format_exc())
#         return f"Error during code execution: {str(e)}"

#     finally:
#         # Always restore the original working directory
#         os.chdir(original_cwd)

# # Example usage
# if __name__ == "__main__":
#     test_code = """print("Hello from restricted environment!")
# for i in range(3):
#     print(f"Count: {i}")
#     """

#     result = execute_restricted_python("test_student", test_code)
#     print("Execution result:")
#     print(result)
