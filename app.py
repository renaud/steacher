import json
import tornado.ioloop
import tornado.web
import tornado.escape

import db

from main import init_conversation, run_conversation



class MainHandler(tornado.web.RequestHandler):
    async def get(self):
        await self.render("index.html")



class InitialMessagesHandler(tornado.web.RequestHandler):

    async def post(self):
        try:
            request = tornado.escape.json_decode(self.request.body)
            student_id = request.get('student_id')
            language   = request.get('language')
            # check if there's already a message history for this student
            messages = db.get_messages(student_id)
            if messages:
                self.write({"student_id": student_id, "messages": messages})
            else:
                self.write({"student_id": student_id, "messages": init_conversation(student_id, language)})
        except Exception as e:
            print("exception InitialMessagesHandler", e)
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
            student_code = request.get('code')
            question     = request.get('question', "")
            hint         = request.get('hint')
            messages     = request.get('messages')
            print(hint, messages)

            new_messages, code_output = run_conversation(student_id, messages, student_code, question, hint)
            self.write({'messages': new_messages})
            return

        except json.JSONDecodeError:
            self.set_status(400)
            self.write({"error": "Invalid JSON in request."})
        except Exception as e:
            print(e)
            self.set_status(500)
            self.write({"error": f"Internal server error: {str(e)}"})


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/api/execute", ExecuteHandler),
        (r"/api/init", InitialMessagesHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': 'static'}),
    ], debug=True)  # Enable debug mode here


if __name__ == "__main__":
    db.initialize_db()  # create db if necessary
    app = make_app()
    port = 8123
    print(f"Starting server on http://localhost:{port}")
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
