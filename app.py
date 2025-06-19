from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Donation, DonorRegistration
from utils.predict import predict_blood_group
import os

# Flask setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
basedir = os.path.abspath(os.path.dirname(__file__))

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'bloodmark.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
instance_dir = os.path.join(basedir, 'instance')
os.makedirs(instance_dir, exist_ok=True)

# Upload folder
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# DB + Login manager
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# Routes
@app.route('/')
@app.route('/land')
def land():
    return render_template('land.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('land'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or email already exists.')
            return redirect(url_for('login'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/detection', methods=['GET', 'POST'])
@login_required
def detection():
    predicted_class = None
    if request.method == 'POST':
        file = request.files.get('fingerprint')
        if not file or file.filename == '':
            flash('No file selected.')
            return redirect(url_for('detection'))

        if not allowed_file(file.filename):
            flash('Unsupported file format. Please upload PNG, JPG, JPEG, or BMP.')
            return redirect(url_for('detection'))

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            predicted_label, confidence = predict_blood_group(filepath)
            predicted_class = predicted_label
            # flash(f'Detected Blood Type: {predicted_label} (Confidence: {confidence:.2f}%)')

            new_donation = Donation(
                blood_type=predicted_label,
                location='Unknown',
                user_id=current_user.id
            )
            db.session.add(new_donation)
            db.session.commit()

        except Exception as e:
            flash(f'Prediction failed: {str(e)}')
            return redirect(url_for('detection'))

    return render_template('detection.html', result=predicted_class)


    
    
# Add your donation and registration routes here (unchanged)...
@app.route('/donation')
@login_required
def donation():
    return render_template('donation.html')

@app.route('/donation/volunteer', methods=['POST'])
@login_required
def donation_volunteer():
    new_donation = Donation(
        name=request.form['name'],
        phone=request.form['phone'],
        available_days=request.form['available_days'],
        user_id=current_user.id
    )
    db.session.add(new_donation)
    db.session.commit()
    flash('Volunteer registration successful!')
    return redirect(url_for('donation'))

@app.route('/donation/donor', methods=['POST'])
@login_required
def donation_donor():
    new_donation = Donation(
        location=request.form['location'],
        donors=request.form['donors'],
        donation_date=request.form['donation_date'],
        availability=request.form['availability'],
        user_id=current_user.id
    )
    db.session.add(new_donation)
    db.session.commit()
    flash('Donor registration successful!')
    return redirect(url_for('donation'))

@app.route('/donation/needy', methods=['POST'])
@login_required
def donation_needy():
    new_donation = Donation(
        patient_name=request.form['patient_name'],
        blood_type=request.form['blood_type'],
        location=request.form['location'],
        user_id=current_user.id
    )
    db.session.add(new_donation)
    db.session.commit()
    flash('Blood request submitted successfully!')
    return redirect(url_for('donation'))

@app.route('/submit_registration', methods=['GET', 'POST'])
@login_required
def submit_registration():
    if request.method == 'POST':
        if 'consent' not in request.form:
            flash('You must provide consent to register.')
            return redirect(url_for('submit_registration'))

        new_registration = DonorRegistration(
            full_name=request.form['fullName'],
            dob=request.form['dob'],
            gender=request.form['gender'],
            blood_group=request.form['bloodGroup'],
            weight=request.form['weight'],
            contact=request.form['contact'],
            email=request.form['email'],
            address=request.form['address'],
            recent_donation=request.form['recentDonation'],
            medical_conditions=request.form.get('medicalConditions', ''),
            consent=True,
            user_id=current_user.id
        )
        db.session.add(new_registration)
        db.session.commit()
        flash('Blood donation registration successful!')
        return redirect(url_for('land'))

    return render_template('form.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('land'))

if __name__ == '__main__':
    app.run(debug=True)
