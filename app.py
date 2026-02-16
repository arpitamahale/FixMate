from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Supabase configuration
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route('/')
def index():
    return render_template('INDEX.HTML')

@app.route('/login/user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        try:
            response = supabase.table('users').select("*").eq('name', name).eq('password', password).execute()
            if response.data:
                session['user_id'] = response.data[0]['id']
                session['user_name'] = response.data[0]['name']
                return redirect(url_for('profile_user'))
            else:
                flash("Invalid credentials")
        except Exception as e:
            flash(f"Error: {str(e)}")
    return render_template('LOGIN_USER.HTML')

@app.route('/login/provider', methods=['GET', 'POST'])
def login_provider():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        try:
            response = supabase.table('providers').select("*").eq('name', name).eq('password', password).execute()
            if response.data:
                session['provider_id'] = response.data[0]['id']
                session['provider_name'] = response.data[0]['name']
                return redirect(url_for('profile_provider'))
            else:
                flash("Invalid credentials")
        except Exception as e:
            flash(f"Error: {str(e)}")
    return render_template('LOGIN_PROVIDER.HTML')

@app.route('/signup/user', methods=['GET', 'POST'])
def signup_user():
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'password': request.form.get('password')
        }
        try:
            supabase.table('users').insert(data).execute()
            flash("Signup successful! Please login.")
            return redirect(url_for('login_user'))
        except Exception as e:
            flash(f"Error: {str(e)}")
    return render_template('SIGNIN_USER.HTML')

@app.route('/signup/provider', methods=['GET', 'POST'])
def signup_provider():
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'work': request.form.get('work'),
            'password': request.form.get('password')
        }
        try:
            supabase.table('providers').insert(data).execute()
            flash("Registration successful! Please login.")
            return redirect(url_for('login_provider'))
        except Exception as e:
            flash(f"Error: {str(e)}")
    return render_template('SIGNIN_PROVIDER.HTML')

@app.route('/profile/user')
def profile_user():
    if 'user_id' not in session:
        return redirect(url_for('login_user'))
    
    # Fetch user history
    history = []
    try:
        response = supabase.table('requests').select("*, providers(name)").eq('user_id', session['user_id']).execute()
        history = response.data
    except:
        pass
    
    return render_template('PROFILE_USER.HTML', history=history)

@app.route('/profile/provider')
def profile_provider():
    if 'provider_id' not in session:
        return redirect(url_for('login_provider'))
    
    # Fetch available requests matching provider's work
    requests_data = []
    try:
        # Get provider's work type
        p_res = supabase.table('providers').select("work").eq('id', session['provider_id']).execute()
        work_type = p_res.data[0]['work']
        
        response = supabase.table('requests').select("*, users(name)").eq('service_type', work_type).eq('status', 'pending').execute()
        requests_data = response.data
    except:
        pass
        
    return render_template('PROFILE_PROVIDER.HTML', requests=requests_data)

@app.route('/submit_request', methods=['POST'])
def submit_request():
    if 'user_id' not in session:
        return redirect(url_for('login_user'))
    
    data = {
        'user_id': session['user_id'],
        'service_type': request.form.get('service'),
        'details': request.form.get('details'),
        'status': 'pending'
    }
    try:
        supabase.table('requests').insert(data).execute()
        return render_template('SUBMISSION.HTML')
    except Exception as e:
        flash(f"Error: {str(e)}")
        return redirect(url_for('profile_user'))

@app.route('/accept_job/<job_id>', methods=['POST'])
def accept_job(job_id):
    if 'provider_id' not in session:
        return redirect(url_for('login_provider'))
    
    try:
        supabase.table('requests').update({
            'status': 'assigned',
            'provider_id': session['provider_id']
        }).eq('id', job_id).execute()
        flash("Job accepted successfully!")
    except Exception as e:
        flash(f"Error: {str(e)}")
    
    return redirect(url_for('profile_provider'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
