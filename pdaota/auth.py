# Flask imports for basic HTML stuff
from flask import render_template, request, url_for, redirect, session

# bcrypt to encrypt the passwords, don't wanna save that cleartext!!!
import bcrypt

# date/time manipulation
import datetime

# to respond a document from pymongo
from pymongo import ReturnDocument

# json manipulation
import json

# manipulation of html text is important for emails (which are written in HTML)
import urllib.request

# we need to get the HTML files of emails to manipulate them!
import os

from pdaota import app, mongo
from pdaota.lib import *
from pdaota.smtp import *

# All authorization/authentication/login/logout stuff here

@app.route("/login", methods=["POST", "GET"])
def login():
    if "email" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        #check if email exists in database
        email_found = mongo.db.sites.find_one({"email": email})
        
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            #encode the password and check if it matches
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = email_val
                session["user_name"] = email_found['name']
                session["site_name"] = email_found['org_name']
                session['site_id'] = str(email_found['_id'])
                return redirect(url_for('dashboard'))
            else:
                if "email" in session:
                    return redirect(url_for("dashboard"))

                # NOTE: possibly change this to "email or password incorrect"
                #       for security reasons    
                flash("Password was incorrect, please try again.")
                return render_template('login.html')
        else:
            flash('This email was not found in our system.  Please click "register" to register for PDA!')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logged_in', methods=['GET', 'POST'])
def logged_in():
    if "email" in session:
        email = session["email"]
        return render_template('logged_in.html', email=email)
    else:
        return redirect(url_for("login"))

@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "email" in session:
        session.pop("email", None)
        session.pop("user_name", None)
        session.pop("site_name", None)
        session.pop("site_id", None)
        return render_template("signout.html")
    else:
        return render_template('login.html')

@app.route("/register", methods=["POST", "GET"])
def register():
    message = ''
    #if method post in index
    if "email" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        records = mongo.db.sites

        user = request.form.get("fullname")
        org = request.form.get("orgname")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        #if found in database showcase that it's found 
        email_found = records.find_one({"email": email})
        
        if email_found:
            message = 'This user already exists in database'
            return render_template('register.html', message=message)
        if password1 != password2:
            message = 'Passwords should match!'
            return render_template('register.html', message=message)
        else:
            #hash the password and encode it
            hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())
            #passing them in a dictionary in key value pairs
            user_input = {'name': user,
                          'org_name': org,
                          'email': email, 
                          'password': hashed, 
                          'owned_projects': [], 
                          'joined_projects': []}
            #insert it in the record collection
            records.insert_one(user_input)
            
            #find the new created account and its email
            user_data = records.find_one({"email": email})
            new_email = user_data['email']

            ##############################################
            # Welcome them to PDA with a friendly email! #
            ##############################################

            send_template_email(subject="Welcome to PDA!", 
                                recipients=[new_email],
                                template="welcome.html",
                                first_name=user)

            #if registered redirect to login page
            return redirect(url_for("login"))
    return render_template('register.html')

def get_auth_token(site_email, expires_sec=3600):
    s = Serializer(app.config['SECRET_KEY'], expires_sec)
    return s.dumps({'site_id': site_email}).decode('UTF-8')

def verify_auth_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        site_id = s.loads(token)['site_id']
    except:
        return None

    key = {"email" : site_id}
    site = mongo.db.sites.find_one(key)
    return site

app.route("/verify_user/<token>")
def verify_user(token):
    if "email" in session:
        session.pop("email", None)
        session.pop("site_name", None)
        session.pop("site_id", None)

    user = verify_auth_token(token)
    if user is None:
        # flash warning msg
        return redirect(url_for('login'))
    else:
        key = {"email" : user["email"]}
        mongo.db.users.update_one(key, { "$set": { "authenticated": True } })

    # flash success message
    return redirect(url_for('login'))

@app.route("/forgot_password/", methods=["POST", "GET"])
def forgot_password():
    form = ForgotPassword()

    if "email" in session:
        return redirect(url_for('dashboard'))

    # valid entry
    if form.validate_on_submit():
        # get email from forgot password page
        entered_email = request.form["email"]
        # check there exists a user with this email
        key = {"email" : entered_email}
        already_exists = mongo.db.users.find_one(key)

        # this user exists
        if (already_exists):
            # generate a random 8-digit password
            new_pw = get_random_string(8).encode("UTF-8")

            # generate a salt
            salt = bcrypt.gensalt()
            new_hashed_pw = bcrypt.hashpw(new_pw, salt)

            # set this user's password to this new password
            mongo.db.users.update_one(key, { "$set": { "hashed_pw": new_hashed_pw } })

            # create a reset pw validation token with email
            send_pw_email(entered_email, new_pw)

            # redirect page to login
            return redirect(url_for('login'))
        else:
            # User does not exist
            return render_template('forgotpassword.html', form=form)

    # invalid entry
    return render_template('forgotpassword.html', form=form)

@app.route("/reset_password/<token>", methods=["POST", "GET"])
def reset_password(token):
    form = ResetPassword()

    if "email" in session:
        session.pop("email", None)
        session.pop("site_name", None)
        session.pop("site_id", None)

    user = verify_auth_token(token)
    if user is None:
        # flash warning msg
        return redirect(url_for('login'))
    else:
        # valid entry
        if form.validate_on_submit():
            key = {"email" : user["email"]}

            entered_pw = request.form["cur_pw"].encode("UTF-8")
            hashed_pw = user["hashed_pw"]
            is_auth = user["authenticated"]

            # entered password matches user's temporary password
            if bcrypt.checkpw(entered_pw, hashed_pw) and is_auth:
                # set the password to the new password
                # generate a salt
                salt = bcrypt.gensalt()
                new_hashed_pw = bcrypt.hashpw(request.form["new_pw"].encode("UTF-8"), salt)
                mongo.db.users.update_one(key, { "$set": { "hashed_pw": new_hashed_pw } })
                # flash success message
                return redirect(url_for('login'))

    return render_template('resetpassword.html', form=form)





