from flask_mongoengine import Document
from flask import jsonify
import hashlib
import os
from flask_login import UserMixin, current_user
from mongoengine import StringField, BooleanField, ListField, DateTimeField, ReferenceField, BinaryField
from enum import Enum, auto
import datetime
from bson import ObjectId
from webapp.taskany.app import login


class Role(Enum):
    ADMIN = auto()
    USER = auto()

    def string(self):
        return self.name

class TaskStatus(Enum):
    NEW = auto()
    STARTED = auto()
    DEFERRED = auto()
    BACKLOG = auto()
    IN_PROGRESS = auto()
    DONE = auto()

    def string(self):
        return self.name

class User(UserMixin, Document):
    TODO_LIST_NAME = "To Do"

    name = StringField(max_length=64)
    roles = ListField(StringField())
    task_lists = ListField(ReferenceField('models.TaskList'))
    key_hash = BinaryField()
    salt = BinaryField()
    messages = ListField(StringField)
    team = ReferenceField('models.Team')

    def add_task_list(self, task_list):
        task_list.owners.append(self)
        task_list.save()
        self.task_lists.append(task_list)
        self.save()

    def remove_task_list(self, task_list):
        if task_list in self.task_lists:
            self.task_lists.remove(task_list)
            self.save()

    def set_password(self, password: str):
        self.salt = os.urandom(32)
        self.key_hash = hashlib.pbkdf2_hmac(hash_name='sha256',
                                       password=password.encode('utf-8'),
                                       salt=self.salt,
                                       iterations=10000)

    def check_password(self, password: str):
        result = False
        if (self.salt is not None) and (self.key_hash is not None):
            hash = hashlib.pbkdf2_hmac(hash_name='sha256',
                                       password=password.encode('utf-8'),
                                       salt=self.salt,
                                       iterations=10000)
            if hash == self.key_hash:
                result = True
        return result

    def is_admin(self):
        is_admin = Role.ADMIN.string() in self.roles
        return is_admin

    @staticmethod
    @login.user_loader
    def load_user(id: str):
        object_id = ObjectId(id)
        return User.objects(id=object_id).first()

    def get_incoming_task_list(self):
        for task_list in self.task_lists:
            if task_list.accepts_incoming_tasks:
                return task_list
        #If no list was found
        return self.create_default_incoming_task_list()

    def create_default_incoming_task_list(self):
        task_list = TaskList(
            title="Incoming Tasks",
            owners=[self],
            accepts_incoming_tasks=True,
            tasks = []
        ).save()

        self.task_lists.append(task_list)
        self.save()

        return task_list


class Task(Document):
    title = StringField(max_length=128, default="New Task")
    body = StringField(default="")
    done = BooleanField(default=False)
    status = StringField(default = TaskStatus.NEW.string())
    creation_date = DateTimeField(default=datetime.datetime.now)
    due_date = StringField(default="")
    owners = ListField(ReferenceField('models.User'))
    assignee = ReferenceField('models.User')
    color = StringField(default="limegreen")

    def as_json(self):
        dict = {
            "id" : str(self.id),
            "body" : self.body,
            "title" : self.title,
            "status" : str(self.status),
            "creation_date" : str(self.creation_date),
            "due_date" : str(self.due_date),
            "assignee" : self.assignee.name,
            "color" : self.color
        }
        return jsonify(dict)

    def update_from_json(self, json: dict):
        update_successful = True
        try:
            #Todo: Sanitize and verify
            self.body = json['body']
            self.title = json['title']
            self.due_date = json['due_date']
            self.color = json['color']
            submitted_assignee = User.objects(id=ObjectId(json['assignee'])).first()
            if submitted_assignee is None:
                update_successful = False
            else:
                if submitted_assignee.id != current_user.id:
                    self.remove_task_from_current_user()
                    self.send_task_to_user(submitted_assignee)
                    self.assignee = submitted_assignee
                    print(current_user.name + " no longer owns task " + str(self.id))
        except Exception:
            update_successful = False

        if update_successful:
            self.save()

        return update_successful

    def set_assignee(self, user: User):
        self.assignee = user
        self.save()

    def append_owner(self, new_owner: User):
        update_required = True
        for owner in self.owners:
            if owner.id == new_owner.id:
                update_required = False

        if update_required:
            self.owners.append(new_owner)
            self.save()

    def remove_task_from_current_user(self):
        print("Removing task from " + str(current_user.name))
        task_list = self.find_in_user_task_lists(current_user)
        task_list.tasks.remove(self)
        task_list.save()

    def send_task_to_user(self, submitted_assignee: User):
        print("Sending task to " + submitted_assignee.name)
        task_list = submitted_assignee.get_incoming_task_list()
        task_list.tasks.append(self)
        task_list.save()

    def find_in_user_task_lists(self, user: User):
        result = None
        for task_list in user.task_lists:
            for task in task_list.tasks:
                if task.id == self.id:
                    print("Task found in list: " + task_list.title + ", id: " + str(task_list.id))
                    result = task_list
        return result

class TaskList(Document):
    title = StringField(max_length=128)
    tasks = ListField(ReferenceField('models.Task'))
    owners = ListField(ReferenceField('models.User'))
    accepts_incoming_tasks = BooleanField(default=False)

    @staticmethod
    def new_empty_task_list():
        task_list = TaskList(
            title="New Task List",
            owners=[],
            tasks=[],
            accepts_incoming_tasks=False
        ).save()
        return task_list

    def details_as_json(self):
        details = {
            "title" : self.title,
            "accepts_incoming_tasks" : self.accepts_incoming_tasks
        }
        return jsonify(details)

    def set_incoming(self, boolean: bool):
        self.accepts_incoming_tasks = boolean
        self.save()

    def append(self, task: Task):
        print("adding task " + str(task.id) + "to list: " + self.title)
        self.tasks.append(task)
        self.save()

    def remove(self, task: Task):
        print("removing task " + str(task.id) + "from list: " + self.title)
        self.tasks.remove(task)
        self.save()

    def delete_task_list(self):
        print("Removing task list " + self.title + " from " + current_user.name)
        if self in current_user.task_lists:

            print("Task list found in current user lists. Removing tasks.")
            for task in self.tasks:
                task.delete()

            print("Removing task list reference from user.")
            current_user.task_lists.remove(self)
            current_user.save()

            print("Deleting task list.")
            self.delete()

    def set_title(self, new_title):
        self.title = new_title
        self.save()

class Team(Document):
    members = ListField(ReferenceField('models.User'))
    name = StringField(max_length=128)

    def add_member(self, user: User):
        self.members.append(user)
        self.save()
        user.team = self
        user.save()

    def add_members(self, users: list):
        for user in users:
            self.add_member(user)