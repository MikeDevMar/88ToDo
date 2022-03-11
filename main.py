from flask import Flask, jsonify, render_template, redirect, url_for,request, flash
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
import werkzeug.security
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
from functools import wraps
from flask_ckeditor import CKEditorField, CKEditor
from markupsafe import Markup


app = Flask(__name__)

app.config['SECRET_KEY'] = 'mahmoudismahmoud'
Bootstrap(app)
ckeditor = CKEditor(app)

gravatar = Gravatar( app,\
                     size=100,
                     rating='g',
                     default ='retro',
                     force_default=False,
                     force_lower=False,
                     use_ssl =False,
                     base_url=None
                     )

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users-data.db'
app.config['SQLALCHEMY_TRACK-MODIFICATIONS'] = False
db= SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Data.query.get(int(user_id))


class Data(UserMixin, db.Model):
    __tablename__ = 'users_data'
    id= db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable = False)
    email = db.Column( db.String(200), nullable= False)
    password = db.Column(db.String(200), nullable= False)
    tasks = relationship('UserTasks', back_populates='author')


class UserTasks(db.Model):
    __tablename__ = 'user_tasks'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users_data.id'))
    author = relationship('Data', back_populates ='tasks')

    title = db.Column(db.String(250), nullable = False)
    body = db.Column(db.Text, nullable = False)


tasks = db.session.query(UserTasks).all()


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField()


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Your password', validators=[DataRequired()])
    re_password = PasswordField('Re-enter your password', validators=[DataRequired()])
    submit = SubmitField('Register')


class TaskForm(FlaskForm):
    title= StringField('Title', validators=[DataRequired()])
    body= CKEditorField('Task', validators=[DataRequired()])
    submit = SubmitField('Add')


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/log-in', methods=['GET', 'POST'])
def log_in():
    log_in_form = LoginForm()
    if log_in_form.validate_on_submit():
        email = log_in_form.email.data
        password = log_in_form.password.data
        user = Data.query.filter_by(email=email).first()
        if not user:
            flash('You have entered a wrong email')
            return render_template('log-in.html', form=log_in_form)
        elif not check_password_hash(user.password, password):
            flash('invalid password')
            return redirect(url_for('log_in', form = log_in_form))
        else:
            logged_in = current_user.is_authenticated
            login_user(user)
            return redirect(url_for('my_profile',  logged_in = current_user.is_authenticated, user=user))

    return render_template('log-in.html' ,form=log_in_form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        if register_form.password.data == register_form.re_password.data:
            hashed_pass = werkzeug.security.generate_password_hash(
                password= register_form.password.data,
                method= 'pbkdf2:sha256',
                salt_length=8
            )
            new_user= Data(
                name = register_form.name.data,
                password = hashed_pass,
                email = register_form.email.data
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('my_profile', current_user=new_user))
    return render_template('register.html', form=register_form )



@app.route('/my-profile', methods=["GET", "POST"])
@login_required
def my_profile():
    user = current_user
    return render_template('my-profile.html', current_user=user)
@app.route('/add-new-tasks', methods=["GET", "POST"])
@login_required
def add_new_tasks():
    add_task_form = TaskForm()
    if add_task_form.validate_on_submit():
        new_task = UserTasks(
            author=current_user,
            title=add_task_form.title.data,
            body=add_task_form.body.data
        )
        db.session.add(new_task)
        db.session.commit()

        return redirect(url_for('show_all_tasks'))
    return render_template('add-new-tasks.html', form = add_task_form)



@app.route('/all-tasks', methods=['GET', 'POST'])
@login_required
def show_all_tasks():
    tasks = db.session.query(UserTasks).all()

    return render_template('all-tasks.html',logged_in = current_user.is_authenticated, current_user=current_user, tasks= tasks)

@app.route("/view-task/<int:taskid>", methods=['GET', 'POST'])
@login_required
def view_task(taskid):
    requested_task = UserTasks.query.get(taskid)
    return render_template('view-task.html', task= requested_task)


@app.route('/edit-task/<int:taskid>', methods=['GET', 'POST'])
@login_required
def edit_task(taskid):
    requested_task = UserTasks.query.get(taskid)
    edit_form = TaskForm(
        title = requested_task.title,
        body = requested_task.body,
        author_id = requested_task.author_id
    )
    if edit_form.validate_on_submit():
        requested_task.title = edit_form.title.data
        requested_task.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for('view_task', taskid =requested_task.id))
    return render_template('add-new-tasks.html', form = edit_form)

@app.route('/delete-task/<int:taskid>')
@login_required
def delete_task(taskid):
    requested_task = UserTasks.query.get(taskid)
    db.session.delete(requested_task)
    db.session.commit()
    return redirect(url_for("show_all_tasks"))

@app.route('/logout', methods =["GET", "POST"])
def log_out():
    logout_user()
    return redirect(url_for('home'))




if __name__=='__main__':
    app.run(debug=True)

