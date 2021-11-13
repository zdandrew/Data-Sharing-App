from flask import render_template, request, url_for, redirect, session, flash
import bcrypt
import datetime
from pymongo import ReturnDocument
import json
import sys
from bson.objectid import ObjectId
from bson.json_util import dumps, loads
from pymongo import MongoClient

from pdaota import app, mongo
from pdaota.auth import *
from pdaota.crypto import *
from pdaota.forms import *
from pdaota.lib import *
from pdaota.smtp import *

#assign URLs to have a particular route 

@app.route("/", methods=['GET', 'POST'])
def landing():
    return redirect(url_for("login"))

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

# Site join project, currently no socurity measures in place
# Later the project_name can be changed to id, currently name for simplicity and testing.
@app.route("/join_project", methods=['GET', 'POST'])
@require_user_login
def join_project():
    if request.method == "POST":
        project_name = request.form.get('project_name')
        project_code = request.form.get('project_code')

        proj = mongo.db.projects.find_one({'name': project_name})

        if not proj:
            flash('No project with name "' + project_name + '" was found.')
            return redirect(url_for("dashboard"))
        elif proj['code'] != int(project_code):
            flash('Project code "' + project_code + '" is incorrect.')
            return redirect(url_for("dashboard"))

        mongo.db.projects.update_one({
            'name': project_name}, 
            {'$push': {
                'collaborating_sites' : ObjectId(session['site_id'])
                }}, upsert = True)

        mongo.db.sites.update_one({
            '_id': ObjectId(session['site_id'])}, 
            {'$push': {
            'joined_projects' : proj['_id']
            }}, upsert = True)

        return redirect(url_for("dashboard"))
    return render_template('join_project.html')
    

@app.route("/new_project", methods=['GET', 'POST'])
@require_user_login
def new_project():
    form = NewProjectForm(request.form)
    if request.method == "POST":
        project_name = request.form.get('project_name')
        total_rounds = request.form.get('num_rounds')
        collabs_id_list = []
        deadlines = []
        if total_rounds == "1":
            deadlines.append(request.form.get('deadline11'))
        elif total_rounds == "2":
            deadlines.append(request.form.get('deadline21'))
            deadlines.append(request.form.get('deadline22'))
        elif total_rounds == "3":
            deadlines.append(request.form.get('deadline31'))
            deadlines.append(request.form.get('deadline32'))
            deadlines.append(request.form.get('deadline33'))
        elif total_rounds == "4":
            deadlines.append(request.form.get('deadline41'))
            deadlines.append(request.form.get('deadline42'))
            deadlines.append(request.form.get('deadline43'))
            deadlines.append(request.form.get('deadline44'))
        elif total_rounds == "5":
            deadlines.append(request.form.get('deadline51'))
            deadlines.append(request.form.get('deadline52'))
            deadlines.append(request.form.get('deadline53'))
            deadlines.append(request.form.get('deadline54'))
            deadlines.append(request.form.get('deadline55'))
        elif total_rounds == "6":
            deadlines.append(request.form.get('deadline61'))
            deadlines.append(request.form.get('deadline62'))
            deadlines.append(request.form.get('deadline63'))
            deadlines.append(request.form.get('deadline64'))
            deadlines.append(request.form.get('deadline65'))
            deadlines.append(request.form.get('deadline66'))
        elif total_rounds == "7":
            deadlines.append(request.form.get('deadline71'))
            deadlines.append(request.form.get('deadline72'))
            deadlines.append(request.form.get('deadline73'))
            deadlines.append(request.form.get('deadline74'))
            deadlines.append(request.form.get('deadline75'))
            deadlines.append(request.form.get('deadline76'))
            deadlines.append(request.form.get('deadline77'))
        elif total_rounds == "8":
            deadlines.append(request.form.get('deadline81'))
            deadlines.append(request.form.get('deadline82'))
            deadlines.append(request.form.get('deadline83'))
            deadlines.append(request.form.get('deadline84'))
            deadlines.append(request.form.get('deadline85'))
            deadlines.append(request.form.get('deadline86'))
            deadlines.append(request.form.get('deadline87'))
            deadlines.append(request.form.get('deadline88'))
        elif total_rounds == "9":
            deadlines.append(request.form.get('deadline91'))
            deadlines.append(request.form.get('deadline92'))
            deadlines.append(request.form.get('deadline93'))
            deadlines.append(request.form.get('deadline94'))
            deadlines.append(request.form.get('deadline95'))
            deadlines.append(request.form.get('deadline96'))
            deadlines.append(request.form.get('deadline97'))
            deadlines.append(request.form.get('deadline98'))
            deadlines.append(request.form.get('deadline99'))
        elif total_rounds == "10":
            deadlines.append(request.form.get('deadline101'))
            deadlines.append(request.form.get('deadline102'))
            deadlines.append(request.form.get('deadline103'))
            deadlines.append(request.form.get('deadline104'))
            deadlines.append(request.form.get('deadline105'))
            deadlines.append(request.form.get('deadline106'))
            deadlines.append(request.form.get('deadline107'))
            deadlines.append(request.form.get('deadline108'))
            deadlines.append(request.form.get('deadline109'))
            deadlines.append(request.form.get('deadline1010'))
        
        # create a new project in mongoDB with data
        create_project(project_name, total_rounds, collabs_id_list, deadlines, request.form.get('model'))

        # Return to dashboard
        return redirect(url_for("dashboard"))
    return render_template('new_project.html', form=form)

        

    # if form.validate_on_submit():
    #     # gather data from submitted form
    #     project_name = form.project_name.data
    #     total_rounds = form.total_rounds.data
    #     collabs = form.possible_collabs.data

    #     collabs_id_list = []
    #     for idstr in collabs:
    #         collabs_id_list.append(ObjectId(idstr))

    #     # create a new project in mongoDB with data
    #     create_project(project_name, total_rounds, collabs_id_list)

    #     # Return to dashboard
    #     return redirect(url_for("dashboard"))

    # display the new_project.html page
    

# Todo after rest working
@app.route("/dashboard", methods=['GET', 'POST'])
@require_user_login
def dashboard():
    site = mongo.db.sites.find_one({'_id': ObjectId(session['site_id'])})
    owned_id = site['owned_projects']
    joined_id = site['joined_projects']

    owned = []
    joined = []

    for i in owned_id:
        proj = mongo.db.projects.find_one({'_id': i})
        # first, check to see if this project actually exists (sanity check)
        if (proj):
            proj_owner = mongo.db.sites.find_one({'_id': proj["owner"]})
            owner_name = proj_owner['org_name']
            proj['owner_name'] = owner_name

            owned.append(proj)

    for i in joined_id:
        proj = mongo.db.projects.find_one({'_id': i})
        # first, check to see if this project actually exists (sanity check)
        if (proj):
            proj_owner = mongo.db.sites.find_one({'_id': proj["owner"]})
            owner_name = proj_owner['org_name']
            proj['owner_name'] = owner_name

            joined.append(proj)

    return render_template('dashboard.html', joined=joined, owned=owned)

@app.route("/project/<string:project_id>", methods=['GET', 'POST'])
@require_user_login
def project(project_id):
    _id = ObjectId(project_id)
    project = mongo.db.projects.find_one({"_id": _id})

    # project['uploaded'] = [str(x) for x in project['uploaded']]

    leading_site_id = project['owner']
    leading_site = mongo.db.sites.find_one({"_id": leading_site_id})

    is_owner = project['owner']==ObjectId(session['site_id'])

    collabs_ids = project['collaborating_sites']
    collabs = []
    for site_id in collabs_ids:
        collabs.append(mongo.db.sites.find_one({'_id': site_id}))

    deadlines = project['deadlines']
    next_deadline = ""
    if project['rounds_completed'] < project['total_rounds']:
        next_deadline = deadlines[project['rounds_completed']].replace("T", ", ")
        
    files = mongo.db.files.find({"project": ObjectId(project_id), 'control': True})
    num_cntl_files = mongo.db.files.count_documents({"project": ObjectId(project_id), 'control': True})
    rounds_completed = project["rounds_completed"]

    current_control_json = None

    # We only want to set the current control.json file if one actually exists
    # Here are the following scenarios:
    # 1. rounds completed: 0 no file uploaded
    # 2. rounds completed: 0 but a file uploaded this round
    # 3. rounds completed: 1+ no file uploaded
    # 4. rounds completed: 1+ file uploaded this round
    # we should only assign a value to current control.json in 2 & 4

    if (num_cntl_files != 0 and num_cntl_files > rounds_completed):
        curr_cntl_json_id = files[num_cntl_files - 1]["json_id"]
        current_control_json = mongo.db.json.find({"_id": curr_cntl_json_id})

    return render_template('project.html', 
                           project=project, 
                           owner=leading_site, 
                           collabs=collabs, 
                           is_owner=is_owner, 
                           files=files, 
                           cntl_json=current_control_json,
                           next_deadline=next_deadline)

@app.route("/site/<string:project_id>/<string:owner_id>", methods=["POST", "GET"])
@require_user_login
def site(owner_id, project_id):
    files = mongo.db.files.find({"$and": [{'project': ObjectId(project_id) }, # belongs to this project
                                          {'uploader': ObjectId(owner_id)},   # was uploaded by this person
                                          {'control': False}]})               # is not a control.json file
    owner = mongo.db.sites.find_one({'_id': ObjectId(owner_id)})
    owner_name = owner['name']
    project = mongo.db.projects.find_one({'_id': ObjectId(project_id) })
    is_user = owner_id == session['site_id']
    is_leading = project['owner'] == ObjectId(session['site_id'])

    deadlines = project['deadlines']
    next_deadline = ""
    if project['rounds_completed'] < project['total_rounds']:
        next_deadline = deadlines[project['rounds_completed']].replace("T", ", ")

    return render_template('site.html', 
                            files = files, 
                            owner_name = owner_name, 
                            owner_id = owner_id, 
                            project = project, 
                            is_user = is_user, 
                            is_leading = is_leading, 
                            next_deadline = next_deadline)


