import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, OperationalError
from dotenv import load_dotenv
from urllib.parse import quote_plus
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# --- Supabase / PostgreSQL Configuration (SQLAlchemy) ---
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PORT = os.getenv('DB_PORT')
DB_PASS = os.getenv('DB_PASS')

# Construct Database URI with URL-encoded password and NO SPACE before @
encoded_pass = quote_plus(DB_PASS) if DB_PASS else ""
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Models ---

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    address = db.Column(db.String)
    phone = db.Column(db.String)

class Provider(db.Model):
    __tablename__ = 'providers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    work = db.Column(db.String, nullable=False) # Changed from service_type to match DB
    address = db.Column(db.String)
    phone = db.Column(db.String)

class ServiceRequest(db.Model):
    __tablename__ = 'requests' # Matches DATABASE_SETUP.sql
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
    service_type = db.Column(db.String, nullable=False)
    details = db.Column(db.String)
    status = db.Column(db.String, default='pending')
    cost = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    user = db.relationship('User', backref='requests')
    provider = db.relationship('Provider', backref='requests')

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, default='pending')
    transaction_id = db.Column(db.String)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    request = db.relationship('ServiceRequest', backref='transactions')
    provider = db.relationship('Provider', backref='transactions')

# --- Routes ---

@app.route('/')
def index():
    return render_template('INDEX.HTML')

@app.route('/login/user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user = User.query.filter_by(email=email).first()
            if user and (check_password_hash(user.password, password) or user.password == password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                return redirect(url_for('profile_user'))
            else:
                flash('Invalid credentials. Please try again.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('LOGIN_USER.HTML')

@app.route('/signup/user', methods=['GET', 'POST'])
def signup_user():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password, phone=phone, address=address)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Signup successful! Please login.', 'success')
            return redirect(url_for('login_user'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('SIGNIN_USER.HTML')

@app.route('/login/provider', methods=['GET', 'POST'])
def login_provider():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            provider = Provider.query.filter_by(email=email).first()
            if provider and (check_password_hash(provider.password, password) or provider.password == password):
                session['provider_id'] = provider.id
                session['provider_name'] = provider.name
                return redirect(url_for('profile_provider'))
            else:
                flash('Invalid credentials. Please try again.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('LOGIN_PROVIDER.HTML')

@app.route('/signup/provider', methods=['GET', 'POST'])
def signup_provider():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        work = request.form.get('work')
        
        hashed_password = generate_password_hash(password)
        new_provider = Provider(name=name, email=email, password=hashed_password, phone=phone, address=address, work=work)
        try:
            db.session.add(new_provider)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login_provider'))
        except IntegrityError:
            db.session.rollback()
            flash('Email already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('SIGNIN_PROVIDER.HTML')

@app.route('/profile/user')
def profile_user():
    if 'user_id' not in session:
        return redirect(url_for('login_user'))
    
    user_id = session['user_id']
    history = ServiceRequest.query.filter_by(user_id=user_id).order_by(ServiceRequest.id.desc()).all()
    
    # Check for unpaid services and redirect if necessary (optional logic from user)
    for service in history:
        if service.status == 'ACCEPTED_UNPAID':
            return redirect(url_for('payment', service_id=service.id))
            
    return render_template('PROFILE_USER.HTML', history=history)

@app.route('/profile/provider')
def profile_provider():
    if 'provider_id' not in session:
        return redirect(url_for('login_provider'))
    
    provider_id = session['provider_id']
    provider = Provider.query.get(provider_id)
    
    # Find matching services based on work type and roughly by address
    # In a real app, we'd use better matching, but here we match service type
    available_jobs = ServiceRequest.query.filter_by(
        service_type=provider.work,
        status='pending'
    ).all()
    
    return render_template('PROFILE_PROVIDER.HTML', provider=provider, requests=available_jobs)

@app.route('/submit_request', methods=['POST'])
def submit_request():
    if 'user_id' not in session:
        return redirect(url_for('login_user'))
    
    user_id = session['user_id']
    service_type = request.form.get('service')
    details = request.form.get('details')
    
    new_request = ServiceRequest(
        user_id=user_id,
        service_type=service_type,
        details=details,
        status='pending'
    )
    try:
        db.session.add(new_request)
        db.session.commit()
        return render_template('SUBMISSION.HTML')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('profile_user'))

@app.route('/accept_job/<int:job_id>', methods=['POST'])
def accept_job(job_id):
    if 'provider_id' not in session:
        return redirect(url_for('login_provider'))
    
    provider_id = session['provider_id']
    try:
        job = ServiceRequest.query.get(job_id)
        if job:
            job.status = 'assigned' # or 'ACCEPTED_UNPAID' based on user's logic
            job.provider_id = provider_id
            job.cost = 500.00
            
            # Create transaction
            new_tx = Transaction(request_id=job.id, provider_id=provider_id, amount=job.cost, status='pending')
            db.session.add(new_tx)
            db.session.commit()
            flash("Job accepted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
    
    return redirect(url_for('profile_provider'))

@app.route('/payment/<int:service_id>')
def payment(service_id):
    if 'user_id' not in session:
        return redirect(url_for('login_user'))
    service = ServiceRequest.query.get_or_404(service_id)
    if service.user_id != session['user_id']:
        return "Unauthorized", 403
    return render_template('SUBMISSION.HTML', message="Payment page placeholder") # You can create a real PAYMENT.HTML

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':

    # Create tables if they don't exist

    with app.app_context():

        db.create_all()

    app.run(debug=True)
