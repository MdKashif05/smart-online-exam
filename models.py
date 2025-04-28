from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    exams_created = db.relationship('Exam', backref='creator', lazy='dynamic', foreign_keys='Exam.created_by')
    user_exams = db.relationship('UserExam', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Exam(db.Model):
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    questions = db.relationship('Question', backref='exam', lazy='dynamic', cascade='all, delete-orphan')
    user_exams = db.relationship('UserExam', backref='exam', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Exam {self.title}>'
    
    def get_total_marks(self):
        return sum(question.marks for question in self.questions)

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # 'text', 'single_choice', 'multiple_choice'
    marks = db.Column(db.Float, nullable=False, default=1.0)
    
    # Relationships
    options = db.relationship('Option', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    responses = db.relationship('UserResponse', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Question {self.id}: {self.text[:30]}...>'

class Option(db.Model):
    __tablename__ = 'options'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Option {self.id}: {self.text[:30]}...>'

class UserExam(db.Model):
    __tablename__ = 'user_exams'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default='in_progress')  # 'in_progress', 'completed'
    score = db.Column(db.Float)
    total_marks = db.Column(db.Float)
    
    # Relationships
    responses = db.relationship('UserResponse', backref='user_exam', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<UserExam {self.user_id}:{self.exam_id}>'
    
    def is_time_up(self):
        if not self.exam or not self.start_time:
            return False
        
        duration = timedelta(minutes=self.exam.duration_minutes)
        end_time = self.start_time + duration
        
        return datetime.now() > end_time
    
    def get_remaining_time(self):
        if not self.exam or not self.start_time:
            return 0
        
        if self.status == 'completed':
            return 0
        
        duration = timedelta(minutes=self.exam.duration_minutes)
        end_time = self.start_time + duration
        
        remaining = end_time - datetime.now()
        
        # If time is up, return 0
        if remaining.total_seconds() <= 0:
            return 0
        
        return int(remaining.total_seconds())
    
    def get_score_percentage(self):
        if self.score is None or self.total_marks is None or self.total_marks == 0:
            return 0
        return (self.score / self.total_marks) * 100

class UserResponse(db.Model):
    __tablename__ = 'user_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_exam_id = db.Column(db.Integer, db.ForeignKey('user_exams.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    response = db.Column(db.Text)
    awarded_marks = db.Column(db.Float)  # For manual grading of text questions
    
    def __repr__(self):
        return f'<UserResponse {self.id}>'
