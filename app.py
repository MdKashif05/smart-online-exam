import os
import logging
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, session, abort, jsonify
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create database base class
class Base(DeclarativeBase):
    pass

# Initialize Flask app and database
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/exam_app")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Import models after DB initialization to avoid circular imports
with app.app_context():
    from models import User, Exam, Question, Option, UserExam, UserResponse
    db.create_all()

# Import forms
from forms import LoginForm, RegisterForm, ExamForm, QuestionForm, OptionForm

# Load user for flask-login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter((User.username == form.username.data) | 
                                          (User.email == form.email.data)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('register.html', form=form)
        
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get available exams (that the user hasn't taken yet)
    available_exams = Exam.query.filter(
        ~Exam.user_exams.any(UserExam.user_id == current_user.id)
    ).all()
    
    # Get completed exams
    completed_exams = UserExam.query.filter_by(
        user_id=current_user.id,
        status='completed'
    ).all()
    
    return render_template('dashboard.html', 
                           available_exams=available_exams, 
                           completed_exams=completed_exams)

# Admin routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.filter_by(is_admin=False).count()
    total_exams = Exam.query.count()
    recent_exams = Exam.query.order_by(Exam.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', 
                          total_users=total_users,
                          total_exams=total_exams,
                          recent_exams=recent_exams)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot delete admin users', 'danger')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/exams')
@login_required
@admin_required
def admin_exams():
    exams = Exam.query.all()
    form = ExamForm()  # Create a form instance to pass to the template
    return render_template('admin/create_exam.html', exams=exams, form=form)

@app.route('/admin/exams/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_exam():
    form = ExamForm()
    if form.validate_on_submit():
        exam = Exam(
            title=form.title.data,
            description=form.description.data,
            duration_minutes=form.duration_minutes.data,
            created_by=current_user.id,
            created_at=datetime.now()
        )
        db.session.add(exam)
        db.session.commit()
        flash('Exam created successfully! Now add questions.', 'success')
        return redirect(url_for('edit_exam', exam_id=exam.id))
    
    return render_template('admin/create_exam.html', form=form)

@app.route('/admin/exams/<int:exam_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    form = ExamForm(obj=exam)
    question_form = QuestionForm()
    
    if form.validate_on_submit():
        exam.title = form.title.data
        exam.description = form.description.data
        exam.duration_minutes = form.duration_minutes.data
        db.session.commit()
        flash('Exam updated successfully!', 'success')
        return redirect(url_for('edit_exam', exam_id=exam.id))
    
    return render_template('admin/edit_exam.html', 
                          exam=exam, 
                          form=form, 
                          question_form=question_form)

@app.route('/admin/exams/<int:exam_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    flash('Exam deleted successfully', 'success')
    return redirect(url_for('admin_exams'))

@app.route('/admin/exams/<int:exam_id>/add_question', methods=['POST'])
@login_required
@admin_required
def add_question(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    form = QuestionForm()
    
    if form.validate_on_submit():
        question = Question(
            exam_id=exam.id,
            text=form.text.data,
            question_type=form.question_type.data,
            marks=form.marks.data
        )
        db.session.add(question)
        db.session.commit()
        
        # For multiple choice questions, add options
        if form.question_type.data in ['single_choice', 'multiple_choice']:
            options_text = request.form.getlist('options[]')
            correct_options = request.form.getlist('correct_options[]')
            
            for i, option_text in enumerate(options_text):
                if option_text.strip():  # Only add non-empty options
                    is_correct = str(i) in correct_options
                    option = Option(
                        question_id=question.id,
                        text=option_text,
                        is_correct=is_correct
                    )
                    db.session.add(option)
            
            db.session.commit()
            
        flash('Question added successfully', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'danger')
    
    return redirect(url_for('edit_exam', exam_id=exam.id))

@app.route('/admin/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    exam_id = question.exam_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully', 'success')
    return redirect(url_for('edit_exam', exam_id=exam_id))

@app.route('/admin/results')
@login_required
@admin_required
def view_results():
    user_exams = UserExam.query.filter_by(status='completed').all()
    return render_template('admin/results.html', user_exams=user_exams)

# Exam taking routes
@app.route('/exams/<int:exam_id>/instructions')
@login_required
def exam_instructions(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if user already took this exam
    existing_attempt = UserExam.query.filter_by(
        user_id=current_user.id,
        exam_id=exam.id
    ).first()
    
    if existing_attempt and existing_attempt.status == 'completed':
        flash('You have already completed this exam', 'info')
        return redirect(url_for('view_exam_result', user_exam_id=existing_attempt.id))
    
    if existing_attempt and existing_attempt.status == 'in_progress':
        # Resume exam
        return redirect(url_for('take_exam', exam_id=exam.id))
    
    return render_template('exam/instructions.html', exam=exam)

@app.route('/exams/<int:exam_id>/start', methods=['POST'])
@login_required
def start_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if user already took this exam
    existing_attempt = UserExam.query.filter_by(
        user_id=current_user.id,
        exam_id=exam.id
    ).first()
    
    if existing_attempt and existing_attempt.status == 'completed':
        flash('You have already completed this exam', 'info')
        return redirect(url_for('view_exam_result', user_exam_id=existing_attempt.id))
    
    if existing_attempt and existing_attempt.status == 'in_progress':
        # Resume exam
        return redirect(url_for('take_exam', exam_id=exam.id))
    
    # Create new user exam attempt
    user_exam = UserExam(
        user_id=current_user.id,
        exam_id=exam.id,
        start_time=datetime.now(),
        status='in_progress'
    )
    db.session.add(user_exam)
    db.session.commit()
    
    return redirect(url_for('take_exam', exam_id=exam.id))

@app.route('/exams/<int:exam_id>/take')
@login_required
def take_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # Get the user's exam attempt
    user_exam = UserExam.query.filter_by(
        user_id=current_user.id,
        exam_id=exam.id,
        status='in_progress'
    ).first_or_404()
    
    # Check if time is up
    if user_exam.is_time_up():
        return submit_exam(exam_id)
    
    # Get all questions for this exam
    questions = Question.query.filter_by(exam_id=exam.id).all()
    
    # Get existing responses
    user_responses = {
        resp.question_id: resp 
        for resp in UserResponse.query.filter_by(user_exam_id=user_exam.id).all()
    }
    
    return render_template('exam/take_exam.html', 
                          exam=exam, 
                          questions=questions, 
                          user_exam=user_exam,
                          user_responses=user_responses)

@app.route('/exams/<int:exam_id>/submit', methods=['POST'])
@login_required
def submit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # Get the user's exam attempt
    user_exam = UserExam.query.filter_by(
        user_id=current_user.id,
        exam_id=exam.id,
        status='in_progress'
    ).first_or_404()
    
    if request.method == 'POST':
        # Save all responses
        for key, value in request.form.items():
            if key.startswith('question_'):
                question_id = int(key.split('_')[1])
                
                # Check if response already exists
                existing_response = UserResponse.query.filter_by(
                    user_exam_id=user_exam.id,
                    question_id=question_id
                ).first()
                
                if existing_response:
                    existing_response.response = value
                else:
                    response = UserResponse(
                        user_exam_id=user_exam.id,
                        question_id=question_id,
                        response=value
                    )
                    db.session.add(response)
    
    # Calculate score
    total_marks = 0
    earned_marks = 0
    
    questions = Question.query.filter_by(exam_id=exam.id).all()
    for question in questions:
        total_marks += question.marks
        
        user_response = UserResponse.query.filter_by(
            user_exam_id=user_exam.id,
            question_id=question.id
        ).first()
        
        if user_response:
            if question.question_type == 'text':
                # For text questions, admin needs to grade manually
                pass
            elif question.question_type in ['single_choice', 'multiple_choice']:
                # For choice questions, check if answer is correct
                correct_options = [opt.id for opt in question.options if opt.is_correct]
                if question.question_type == 'single_choice':
                    if user_response.response and int(user_response.response) in correct_options:
                        earned_marks += question.marks
                else:  # multiple_choice
                    selected_options = [int(id) for id in user_response.response.split(',') if id]
                    if set(selected_options) == set(correct_options):
                        earned_marks += question.marks
    
    # Update user exam status
    user_exam.end_time = datetime.now()
    user_exam.status = 'completed'
    user_exam.score = earned_marks
    user_exam.total_marks = total_marks
    
    db.session.commit()
    
    flash('Exam submitted successfully!', 'success')
    return redirect(url_for('view_exam_result', user_exam_id=user_exam.id))

@app.route('/exams/response/<int:question_id>', methods=['POST'])
@login_required
def save_response(question_id):
    question = Question.query.get_or_404(question_id)
    
    # Get user exam
    user_exam = UserExam.query.filter_by(
        user_id=current_user.id,
        exam_id=question.exam_id,
        status='in_progress'
    ).first_or_404()
    
    if user_exam.is_time_up():
        return jsonify({'error': 'Time is up!', 'redirect': url_for('submit_exam', exam_id=question.exam_id)})
    
    response_data = request.get_json()
    response_value = response_data.get('response', '')
    
    # Check if response already exists
    existing_response = UserResponse.query.filter_by(
        user_exam_id=user_exam.id,
        question_id=question_id
    ).first()
    
    if existing_response:
        existing_response.response = response_value
    else:
        response = UserResponse(
            user_exam_id=user_exam.id,
            question_id=question_id,
            response=response_value
        )
        db.session.add(response)
    
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/results/<int:user_exam_id>')
@login_required
def view_exam_result(user_exam_id):
    user_exam = UserExam.query.get_or_404(user_exam_id)
    
    # Ensure the user can only view their own results (unless admin)
    if user_exam.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Get exam details
    exam = Exam.query.get(user_exam.exam_id)
    
    # Get questions and responses
    questions = Question.query.filter_by(exam_id=exam.id).all()
    responses = UserResponse.query.filter_by(user_exam_id=user_exam.id).all()
    
    # Create a dictionary of responses for easy access
    response_dict = {r.question_id: r for r in responses}
    
    return render_template('exam/results.html', 
                          user_exam=user_exam, 
                          exam=exam, 
                          questions=questions, 
                          responses=response_dict)

@app.route('/admin/manual-grading/<int:user_exam_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manual_grading(user_exam_id):
    user_exam = UserExam.query.get_or_404(user_exam_id)
    exam = Exam.query.get(user_exam.exam_id)
    
    if request.method == 'POST':
        # Update scores for text questions
        for key, value in request.form.items():
            if key.startswith('score_'):
                question_id = int(key.split('_')[1])
                score = float(value) if value else 0
                
                # Get the question
                question = Question.query.get(question_id)
                if not question:
                    continue
                
                # Ensure score is not greater than max marks
                if score > question.marks:
                    score = question.marks
                
                # Update score in the response
                response = UserResponse.query.filter_by(
                    user_exam_id=user_exam.id,
                    question_id=question_id
                ).first()
                
                if response:
                    response.awarded_marks = score
        
        # Recalculate total score
        total_score = 0
        for response in UserResponse.query.filter_by(user_exam_id=user_exam.id):
            if response.awarded_marks is not None:
                total_score += response.awarded_marks
            elif response.question.question_type in ['single_choice', 'multiple_choice']:
                # For choice questions, use automatic grading
                correct_options = [opt.id for opt in response.question.options if opt.is_correct]
                if response.question.question_type == 'single_choice':
                    if response.response and int(response.response) in correct_options:
                        total_score += response.question.marks
                else:  # multiple_choice
                    if response.response:
                        selected_options = [int(id) for id in response.response.split(',') if id]
                        if set(selected_options) == set(correct_options):
                            total_score += response.question.marks
        
        user_exam.score = total_score
        db.session.commit()
        
        flash('Grading updated successfully', 'success')
        return redirect(url_for('view_results'))
    
    # Get text questions that need manual grading
    text_questions = Question.query.filter_by(
        exam_id=exam.id,
        question_type='text'
    ).all()
    
    # Get responses
    responses = {r.question_id: r for r in UserResponse.query.filter_by(user_exam_id=user_exam.id)}
    
    return render_template('admin/manual_grading.html',
                          user_exam=user_exam,
                          exam=exam,
                          text_questions=text_questions,
                          responses=responses)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
