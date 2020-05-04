from flask import render_template, redirect, url_for, flash, jsonify, abort, request
from bson import ObjectId
import datetime
from taskany.models.models import Task, TaskList, User, Role, Team
from taskany.forms.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required


@login_required
def task_list():
    print("Loading tasks for " + current_user.name)
    return render_template('index.html', user=current_user, sprint_info=datetime.date.today(), date=None)

@login_required
def update_task():
    submitted_task_data = request.get_json(force=True)
    task = Task.objects(id=ObjectId(submitted_task_data['id'])).first()

    if user_allowed_to_access_task(task):
        operation_success = task.update_from_json(submitted_task_data)
        if operation_success:
            return "Changes saved."
        else:
            return "Error occurred - the task wasn't modified."
    else:
        abort(403)

@login_required
def new_task(task_list_id: str):
    task_list = TaskList.objects(id=ObjectId(task_list_id)).first()

    if user_allowed_to_access_list(task_list):
        new_task = Task(assignee=current_user.id, owners=[current_user.id]).save()
        task_list.append(new_task)
        return str(new_task.id)
    else:
        abort(403)

@login_required
def move_task():
    data = request.get_json(force=True)
    print("Recieved data: ", data)

    task = Task.objects(id=ObjectId(data['task_id'])).first()
    origin_list = TaskList.objects(id=ObjectId(data['origin_list_id'])).first()
    destination_list = TaskList.objects(id=ObjectId(data['destination_list_id'])).first()

    operation_allowed = (
        user_allowed_to_access_list(origin_list) and
        user_allowed_to_access_list(destination_list) and
        user_allowed_to_access_task(task)
    )

    if operation_allowed:
        if destination_list.id != origin_list.id:
            destination_list.append(task)
            origin_list.remove(task)
            print("Move Task operation complete.")
            return "Moved task to list: " + destination_list.title
        else:
            return "Task already in list."
    else:
        abort(403)

@login_required
def delete_task(task_id: str):
    print("Deleting task: " + task_id)
    task = Task.objects(id=ObjectId(task_id)).first()
    operation_allowed = user_allowed_to_access_task(task)

    if operation_allowed:
        task.remove_task_from_current_user()
        task.delete()
        return "Task deleted: " + task_id
    else:
        abort(403)

@login_required
def set_incoming_list():
    requested_task_list_id = ObjectId(request.get_data().decode('ascii'))
    requested_task_list = TaskList.objects(id=requested_task_list_id).first()

    if user_allowed_to_access_list(requested_task_list):
        requested_task_list.set_incoming(True)

        for task_list in current_user.task_lists:
            if task_list.id != requested_task_list.id:
                task_list.set_incoming(False)

        return jsonify({'success': True})
    else:
        abort(403)

def index():
    return "Hello"

def reset_data():
    system_has_no_users = User.objects.count() == 0
    user_is_admin = current_user.is_authenticated and current_user.is_admin()

    if (system_has_no_users or user_is_admin):
        create_mock_data()
        return "DB sas been reset to demo data."
    else:
        abort(403)

def app_login():
    if current_user.is_authenticated:
        return redirect(url_for(task_list))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(name=form.username.data).first()
        if user is None or not user.check_password(password=form.password.data):
            return redirect(url_for('app_login'))
        else:
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('task_list'))

    return render_template('login.html', title="Sign In", form=form)

@login_required
def app_logout():
    logout_user()
    return redirect(url_for('app_login'))

@login_required
def get_list(list_id: str):
    task_list = TaskList.objects(id=ObjectId(list_id)).first()
    if user_allowed_to_access_list(task_list):
        return task_list.details_as_json()
    else:
        abort(403)

@login_required
def delete_list(list_id: str):
    task_list = TaskList.objects(id=ObjectId(list_id)).first()
    if user_allowed_to_access_list(task_list):
        task_list.delete_task_list()
        return "Task list deleted."
    else:
        abort(403)

@login_required
def new_list():
    task_list = TaskList.new_empty_task_list()
    current_user.add_task_list(task_list)
    return str(task_list.id)

@login_required
def update_list():
    submitted_list_data = request.get_json(force=True)
    list_id = submitted_list_data['id']
    list_title = submitted_list_data['title']

    task_list = TaskList.objects(id=ObjectId(list_id)).first()
    if user_allowed_to_access_list(task_list):
        task_list.set_title(list_title)
        return "List updated."
    else:
        abort(403)

@login_required
def get_task(task_id: str):
    task = Task.objects(id=ObjectId(task_id)).first()
    operation_allowed = user_allowed_to_access_task(task)

    if (operation_allowed):
        return task.as_json()
    else:
        abort(403)

def user_allowed_to_access_task(task):
    # Deny all requests
    operation_allowed = False

    # Accept owner request
    if task.assignee.id == current_user.id:
        operation_allowed = True

    # Accept Admin request
    if Role.ADMIN.string() in current_user.roles:
        operation_allowed = True

    return operation_allowed

def user_allowed_to_access_list(task_list):
    # Deny all requests
    operation_allowed = False

    # Accept owner request
    owners = task_list.owners
    for person in owners:
        if person.id == current_user.id:
            operation_allowed = True

    # Accept Admin request
    if Role.ADMIN.string() in current_user.roles:
        operation_allowed = True

    return operation_allowed


def sanitize_string(string):
    #Todo: Sanitize
    return string

@login_required
def user_change_name(new_name: str):
    new_name = sanitize_string(new_name)
    current_user.set_name(new_name)
    return redirect(url_for('task_list'))

@login_required
def user_panel():
    return render_template('user_panel.html', user=current_user)

@login_required
def user_change_password(new_password: str):
    new_password = sanitize_string(new_password)


######### Mock Data Reset ##########

def create_mock_data():
    Team.objects().delete()
    Task.objects().delete()
    User.objects.delete()
    TaskList.objects().delete()

    bender = User(name="Bender", roles=[Role.USER.string()])
    bender.set_password("shiny_metal")
    bender.save()

    leela = User(name="Turanga Leela", roles=[Role.USER.string()])
    leela.set_password("one_eyed_peas")
    leela.save()

    fry = User(name="Philip J. Fry", roles=[Role.USER.string()])
    fry.set_password("panuccis_pizza")
    fry.save()

    farnsworth = User(name="Hubert Farnsworth", roles=[Role.USER.string(), Role.ADMIN.string()])
    farnsworth.set_password("WernstromSucks")
    farnsworth.save()

    amy = User(name="Amy Wong", roles=[Role.USER.string()])
    amy.set_password("martian_money")
    amy.save()

    zoid = User(name="Zoidberd", roles=[Role.USER.string()])
    zoid.set_password("why_not_me")
    zoid.save()

    team1 = Team(name="Planet Express, Inc").save()
    team1.add_members([bender, leela, fry, farnsworth, amy, zoid])

    task1 = Task(
        assignee=bender,
        title="Destroy all humans",
        body="And crustacean humanoids",
        color="turquoise",
        due_date = "21/8/2020"
    ).save()

    task2 = Task(
        assignee=bender,
        title="Build Theme Park",
        body="I'm starting my own theme park, with games of chance and courtesans!",
        color="gold",
        due_date="1/7/2021"
    ).save()

    task3 = Task(
        assignee=bender,
        title="Stalk Calculon",
        body="",
        color="tomato",
        due_date="7/7/2020"
    ).save()

    list1 = TaskList(
        title="To Do",
        accepts_incoming_tasks=True,
        tasks=[task1],
        owners=[bender]
    ).save()

    list2 = TaskList(
        title="Currently",
        tasks=[task2, task3],
        owners=[bender]
    ).save()

    list3 = TaskList(
        title="Done",
        tasks=[],
        owners=[bender]
    ).save()

    bender.task_lists = [list1, list2, list3]
    bender.save()

    return bender