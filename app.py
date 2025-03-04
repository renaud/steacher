import json
import mimetypes
import traceback
from datetime import datetime

import tornado.ioloop
import tornado.web
import tornado.escape

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, send_file

# Initialize the Flask app
app = Flask(__name__)

def setup_logging(log_file_path):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) # general log level
    # Rotating file handler
    rotating_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=50)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    rotating_handler.setFormatter(formatter)
    logger.addHandler(rotating_handler)
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    # Suppress unnecessary logs from other libs
    for lib in ['tornado', 'asyncio', 'httpx', 'httpcore', 'openai']:
        logging.getLogger(lib).setLevel(logging.WARNING)


class QuestionHandler(tornado.web.RequestHandler):
    async def get(self, question_id):
        await self.render("code_editor.html", question_id=question_id)


class OkHandler(tornado.web.RequestHandler):
    ''' to ping service '''
    async def get(self):
        self.write(f"ok {datetime.now()}")


class InitialMessagesHandler(tornado.web.RequestHandler):

    async def post(self):
        try:
            request = tornado.escape.json_decode(self.request.body)
            student_id = request.get('student_id')
            question_id = request.get('question_id')
            language   = request.get('language')
            # check if there's already a message history for this student
            messages = db.get_messages(student_id, question_id)
            if messages:
                self.write({"student_id": student_id, "messages": messages})
            else:
                self.write({"student_id": student_id, "messages": init_conversation(student_id, question_id, language)})
        except Exception as e:
            print("exception InitialMessagesHandler", e, traceback.format_exc())
            self.set_status(500)
            self.write({"error": f"Internal server error: {str(e)}"})



class ExecuteHandler(tornado.web.RequestHandler):
    """
    Handles POST requests to the /api/execute endpoint.
    Expects a JSON payload with 'action', 'code', and 'student_id'.
    """
    async def post(self):
        try:
            # Parse JSON body
            request = tornado.escape.json_decode(self.request.body)
            student_id   = request.get('student_id')
            question_id  = request.get('question_id')
            student_code = request.get('code')
            question     = request.get('question')
            hint         = request.get('hint')
            messages     = request.get('messages')

            # check for student_id, question_id
            if not student_id or not question_id:
                self.set_status(400)
                self.write({"error": "Missing 'student_id' or 'question_id' in request."})
                return

            new_messages = run_conversation(student_id, question_id, messages, student_code, question, hint)
            self.write({'messages': new_messages})
            return

        except json.JSONDecodeError:
            self.set_status(400)
            self.write({"error": "Invalid JSON in request."})
        except Exception as e:
            logging.error(f"ExecuteHandler Exception: {e}, Stacktrace: {traceback.format_exc()}")
            self.set_status(500)
            self.write({"error": f"Internal server error: {str(e)}"})


class FileContentHandler(tornado.web.RequestHandler):
    # TODO not used yet
    async def get(self):
        """
        Serves the content of a specified file for a given student.
        Query Parameters:
            - student_id: Unique identifier for the student.
            - file: Relative path to the file within the student's directory.
        """
        try:
            # Retrieve query parameters
            student_id = self.get_query_argument('student_id', None)
            file_name = self.get_query_argument('file', None)

            # Validate query parameters
            if not student_id or not file_name:
                self.set_status(400)
                self.write({"error": "Missing 'student_id' or 'file' query parameter."})
                return

            # Prevent path traversal attacks by normalizing the path
            normalized_file_name = os.path.normpath(file_name)
            if os.path.isabs(normalized_file_name) or normalized_file_name.startswith(".."):
                self.set_status(400)
                self.write({"error": "Invalid file path."})
                return

            # Construct the full path to the file
            student_dir = os.path.join(BASE_STUDENTS_DIR, student_id)
            file_path = os.path.join(student_dir, normalized_file_name)

            # Check if the file exists and is indeed a file
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                self.set_status(404)
                self.write({"error": "File not found."})
                return

            # Determine the MIME type based on file extension
            mime_type = self.get_mime_type(file_path)

            # Read and serve the file content
            with open(file_path, 'rb') as f:
                content = f.read()

            self.set_header("Content-Type", mime_type)
            self.write(content)

        except Exception as e:
            print("FileContentHandler Exception:", e)
            self.set_status(500)
            self.write({"error": f"Internal server error: {str(e)}"})

    def get_mime_type(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return mime_type
        return 'application/octet-stream'


class AssessmentResultHandler(tornado.web.RequestHandler):
    async def post(self):
        try:
            request = tornado.escape.json_decode(self.request.body)
            code = request.get('code')
            created_at = request.get('createdAt')
            student_id = request.get('student_id')
            question_id = request.get('question_id')

            if not code or not created_at or not student_id or not question_id:
                self.set_status(400)
                self.write({"error": "Missing 'code', 'createdAt', 'student_id', or 'question_id' in request."})
                return

            # Compute the assessment score based on the provided code
            score, rubric_evaluated = grade(code, question_id)
            logging.info(f"Assessment score: {score}")

            if score is not None:
                # Save the grading result to the database
                db.save_grading_result(student_id, question_id, created_at, score, rubric_evaluated)
                self.write({'score': score})
            else:
                self.set_status(500)
                self.write({'error': 'Failed to compute assessment score.'})
        except Exception as e:
            logging.error(f"AssessmentResultHandler Exception: {e}, Stacktrace: {traceback.format_exc()}")
            self.set_status(500)
            self.write({"error": f"Internal server error: {str(e)}"})


class RootRedirectHandler(tornado.web.RequestHandler):
    async def get(self):
        self.redirect("/code_editor/5_csv_temperatures")


def make_app():
    return tornado.web.Application([
        (r"/code_editor/(.*)", QuestionHandler),
        (r"/ok", OkHandler),
        (r"/api/execute", ExecuteHandler),
        (r"/api/init", InitialMessagesHandler),
        # (r"/api/get_file", FileContentHandler),
        (r"/api/assessment", AssessmentResultHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': 'static'}),
        (r"/", RootRedirectHandler),
    ], debug=True)  # Enable debug mode here


@app.route('/download-db', methods=['GET'])
def download_db():
    db_path = 'history.db'  # Path to your SQLite database file
    if os.path.exists(db_path):
        return send_file(db_path, as_attachment=True, attachment_filename='history.db')
    else:
        return "Database file not found.", 404


if __name__ == "__main__":

    log_file = os.path.join(os.path.dirname(__file__), "app.log")
    setup_logging(log_file)

    # Import other modules after logging is configured
    import db
    from main import init_conversation, run_conversation
    from tools import BASE_STUDENTS_DIR
    from assess_code import grade


    db.initialize_db()  # create db if necessary
    app = make_app()
    port = 10000  # default render.com port
    logging.info(f"Starting server on http://localhost:{port}")
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
