from flask import Flask, render_template, json, jsonify, request, session, redirect, url_for, flash
from dbconnect import connection
from content_management import Content
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
import gc
from functools import wraps

TOPIC_DICT = Content()

app = Flask(__name__)

# MySQL configurations


@app.route('/')
def homepage():
    return render_template('main.html')

@app.route('/dashboard/')
def dashboard():
    return render_template('dashboard.html', TOPIC_DICT = TOPIC_DICT)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

@app.route('/login/',methods=['GET', 'POST'])
def login_page():
    print "login page"
    error = ''
    try:
        c, conn = connection()
        if request.method == "POST":
	    print "login POST"
            data = c.execute("SELECT * FROM users WHERE username = (%s)",
                             [thwart(request.form['username'])] )
	    
            if not data:
		flash('username does not exist')
            data = c.fetchone()[2]
	    print "data fetchone"
            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']

                flash('You are now logged in')
                return redirect(url_for("dashboard"))

            else:
		flash('incorrect password')
                e = "Invalid credentials, try again."

        gc.collect()

        return render_template("login.html", error=error)

    except Exception as e:
        print e
        error = "EXCEPTIONInvalid credentials, try again."
        return render_template("login.html", error = error)  
		

class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('password', [validators.DataRequired(),
					  validators.EqualTo('confirm', message="Passwords must match")])
    confirm = PasswordField('Repeat Password')

    accept_tos = BooleanField('I accept the Terms of Service and the Privacy NOtice')


@app.route('/register/',methods=['GET', 'POST'])
def register_page():
    print "on register"
    try:
	form = RegistrationForm(request.form)
	print "on form"
	#must check request.method=='POST', but NOT request.form=='POST'
	if request.method=='POST':
	    print "POST works"
	if form.validate():
	    print "validate works"
	if request.method=='POST' and form.validate():
	    username = form.username.data
	    email = form.email.data
	    password = sha256_crypt.encrypt((str(form.password.data)))
	    c, conn = connection()
	    x = c.execute("SELECT * FROM users WHERE username = (%s)", [thwart(username)])
	    print "enter username"
	    #check if the inputted username exists or not
	    if int(x)>0:
		flash('that username is already taken. Choose another')    
		return render_template('register.html', form=form)
	    else:
		#send user to "/introduction-to-python-programming/" after they register
		c.execute("INSERT INTO users (username, password, email, tracking) VALUES (%s, %s, %s, %s)", (thwart(username), thwart(password), thwart(email), thwart("/introduction-to-python-programming/")))
		conn.commit() #save changes to the MySQL database
		flash('thanks for registering!')
		c.close()
		conn.close()
		gc.collect() #garbage collectoradminw
		session['logged_in'] = True
		session['username'] = username

		return redirect(url_for("dashboard"))
	
	return render_template("register.html", form=form)


    except Exception as e:
	return str(e)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for("login_page"))

    return wrap

@app.route("/logout/")
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for("dashboard"))

@app.route('/interactive/')
def interactive():
	return render_template('interactive.html')


@app.route('/background_process')
def background_process():
	try:
		lang = request.args.get('proglang', 0, type=str)
		if lang.lower() == 'jerry':
			return jsonify(result='That is my name indeed!')
		else:
			return jsonify(result='Try again.')
	except Exception as e:
		return str(e)

@app.route('/github/')
def github():
    return redirect("http://github.com/jk34")

@app.route('/linkedin/')
def linkedin():
    return redirect("http://linkedin.com/in/jerrykim12")


if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True)

