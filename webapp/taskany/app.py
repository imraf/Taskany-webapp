from flask import Flask


app = Flask(__name__)
app.config.from_pyfile('config.py')

from flask_login import LoginManager
login = LoginManager(app)

from flask_mongoengine import MongoEngine
db = MongoEngine()
db.init_app(app)

from taskany.views.views import *

app.add_url_rule("/reset", view_func=reset_data)
app.add_url_rule("/", view_func=index)
app.add_url_rule("/tasks", view_func=task_list)
app.add_url_rule("/update/task", view_func=update_task, methods=['POST'])
app.add_url_rule("/update/list", view_func=update_list, methods=['POST'])
app.add_url_rule("/new/task/<string:task_list_id>", view_func=new_task, methods=['GET'])
app.add_url_rule("/new/list", view_func=new_list, methods=['GET'])
app.add_url_rule("/delete/task/<string:task_id>", view_func=delete_task, methods=['GET'])
app.add_url_rule("/delete/list/<string:list_id>", view_func=delete_list, methods=['GET'])
app.add_url_rule("/login", view_func=app_login, methods=['GET', 'POST'])
app.add_url_rule("/logout", view_func=app_logout)
app.add_url_rule("/task/<string:task_id>", view_func=get_task)
app.add_url_rule("/list/<string:list_id>", view_func=get_list)
app.add_url_rule("/set-incoming-list", view_func=set_incoming_list, methods=['POST'])
app.add_url_rule("/move-task", view_func=move_task, methods=['POST'])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)