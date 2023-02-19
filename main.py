from flask import Flask,render_template,request,session,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user,logout_user,login_manager,LoginManager
from flask_login import login_required,current_user
from flask_mail import Mail
import json

# MY db connection
local_server=True
app = Flask(__name__)
app.secret_key='dbms'

# this is for getting unique user access
login_manager=LoginManager(app)
login_manager.login_view='login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# app.config['SQLALCHEMY_DATABASE_URL']='mysql://username:password@localhost/database_table_name'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@127.0.0.1/db_hms'
db=SQLAlchemy(app)

class User(UserMixin,db.Model):
    user_id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(50),unique=True)
    password=db.Column(db.String(1000))
    def get_id(self):
           return (self.user_id)
   

class Doctors(db.Model):
    did=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(50))
    doctorname=db.Column(db.String(50))
    phno=db.Column(db.Integer)
    deptid=db.Column(db.Integer)

class Departments(db.Model):
    deptid=db.Column(db.Integer,primary_key=True)
    deptname=db.Column(db.String(50))

class Appointments(db.Model):
    aid=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50),nullable=False)
    gender=db.Column(db.String(50),nullable=False)
    age=db.Column(db.Integer)
    disease=db.Column(db.String(50))
    date=db.Column(db.String(50),nullable=False)
    dept=db.Column(db.String(50),nullable=False)
    email=db.Column(db.String(50))




@app.route('/')
def index():
    return render_template('index.html')

# route to sigh up page
@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method == "POST":
        email=request.form.get('email')
        password=request.form.get('password')
        cpassword=request.form.get('cpassword')
        # print(email," ", password," ",cpassword)
        user=User.query.filter_by(email=email).first()
        if user:
            flash("Email Already Exist","warning")
            return render_template('/login.html')
        if cpassword!=password:
            flash("Password and Confirm Password don't match","warning")
            # print('not equal')
            return render_template('/signup.html')
        encpassword=generate_password_hash(password)

        new_user=db.engine.execute(f"INSERT INTO `user` (`email`,`password`) VALUES ('{email}','{encpassword}')")
        # new_user=db.engine.execute(f"INSERT INTO `user` (`username`,`usertype`,`email`,`password`) VALUES ('{email}','Patient','{email}','{encpassword}')")
        # this is method 2 to save data in db
        # newuser=User(username=username,email=email,password=encpassword)
        # db.session.add(newuser)
        # db.session.commit()
        flash("Signup Succes Please Login","success")
        return render_template('login.html')
    return render_template('signup.html')

# route to login page
@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == "POST":
        mail=request.form.get('email')
        password=request.form.get('password')
        print(mail,password)
        user=User.query.filter_by(email=mail).first()
        # if(check_password_hash(user.password,password)):
            # return 'yes';
        # return user.password;
        if user and check_password_hash(user.password,password):
            login_user(user)
            flash("Login Successful","primary")
            em=current_user.email
            user=Doctors.query.filter_by(email=em).first()
            if user:
                return redirect(url_for('doctor'))
            else:
                return redirect(url_for('patient'))
        else:
            flash("invalid credentials","danger")
        return render_template('login.html')
    return render_template('login.html')   

#take booking values from form and store in db
@app.route('/new-appointments',methods=['POST','GET'])
@login_required
def appoint_done():
    doct=db.engine.execute("SELECT * FROM `doctors`")

    if request.method=="POST":
        name=request.form.get('name')
        gender=request.form.get('gender')
        age=request.form.get('age')
        disease=request.form.get('disease')
        date=request.form.get('date')
        dept=request.form.get('dept')
        email=current_user.email
        subject="HOSPITAL MANAGEMENT SYSTEM"
        query=db.engine.execute(f"INSERT INTO `appointments` (`name`,`gender`,`age`,`disease`,`date`,`dept`,`email`) VALUES ('{name}','{gender}','{age}','{disease}','{date}','{dept}','{email}');")

# mail starts from here

        # mail.send_message(subject, sender=params['gmail-user'], recipients=[email],body=f"YOUR bOOKING IS CONFIRMED THANKS FOR CHOOSING US \nYour Entered Details are :\nName: {name}\nSlot: {slot}")



        flash("Booking Confirmed","info")


    return render_template('patient.html',doct=doct)
    # return '/appointments'

#route to display appointments
@app.route('/appoint-done')
@login_required
def appointments(): 
    em=current_user.email
    user=Doctors.query.filter_by(email=em).first();
    if user:
        dept=Departments.query.filter_by(deptid=user.deptid).first()
        print(dept.deptid);
        query=db.engine.execute(f"SELECT * FROM `appointments` WHERE dept='{dept.deptname}'")
        return render_template('appoint-done.html',query=query)
    else:
        print(em);
        query=db.engine.execute(f"SELECT * FROM `appointments` WHERE email='{em}'")
        return render_template('appoint-done.html',query=query)
    
#route to department and its doctors in hospital
@app.route('/department')
def department():
    return render_template('department.html')

#route to about page of hopital 
@app.route('/about')
def about():
    return render_template('about.html')

# route to appointment booking page
@app.route('/book')
def book():
    return render_template('book.html')

# route to doctor home page
@app.route('/doctor')
@login_required
def doctor():
    return render_template('doctors.html')

# route to patient home page
@app.route('/patient')
@login_required
def patient():
    return render_template('patient.html')

    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul","warning")
    return redirect(url_for('login'))

#delete an appointment
@app.route("/delete/<string:aid>",methods=['POST','GET'])
@login_required
def delete(aid):
    db.engine.execute(f"DELETE FROM `appointments` WHERE `appointments`.`aid`='{aid}'")
    flash("Slot Deleted Successful","danger")
    return redirect('/appoint-done')

#update an appointment
@app.route("/update/<string:aid>",methods=['POST','GET'])
@login_required
def update(aid):
    posts=Appointments.query.filter_by(aid=aid).first()
    if request.method=="POST":
        date=request.form.get('date')
        db.engine.execute(f"UPDATE `appointments` SET `date`='{date}' WHERE `aid` = {aid}")
        flash("Slot is Updates","success")
        return redirect('/appoint-done')
    return render_template('update.html',posts=posts)


@app.route('/privacy')
def privacy():
    # posts=Trigr.query.all()
    # posts=db.engine.execute("SELECT * FROM `trigr`")
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    # posts=Trigr.query.all()
    # posts=db.engine.execute("SELECT * FROM `trigr`")
    return render_template('terms.html')

@app.route('/test')
def test():
    try:
        User.query.all()
        email='aman@gmail.com'
        user=User.query.filter_by(email=email).first()
        if user:
            return f'{user.email} already exist';
        return 'blank'
    except:
        return 'My db is not Connected'

app.run(debug=False,host='0.0.0.0')
index()