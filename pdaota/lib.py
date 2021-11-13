from pdaota import app, mongo
from pdaota.smtp import *
from flask import render_template, request, url_for, redirect, session, flash, Response
from functools import wraps
from bson.objectid import ObjectId
from datetime import datetime
import bcrypt   
from pymongo import ReturnDocument
import json
from bson.json_util import dumps, loads
from pymongo import MongoClient
from random import randint, randrange

TOTAL_ROUND_CHOICES = [('1', '1'),
('2','2'), 
('3','3'), 
('4','4'), 
('5','5'),
('6','6'),
('7','7'),
('8','8'),
('9','9'),
('10','10')]

# wrapper function that forces a logged-in user
# optionally can include a project ID
def require_user_login(function):
    @wraps(function)
    def wrapper(**kwargs):
        if "email" in session:
            return function(**kwargs)
        else:
            flash("Cannot access page: you must be logged in to access.")
            return redirect(url_for("login"))
    return wrapper

# Create project with a project name and number of total rounds
def create_project(project_name, total_rounds, collaborators, deadlines, model):
    join_code = int(randint(10000, 99999))
    proj_id = mongo.db.projects.insert({'name': project_name, 
                                        'collaborating_sites': collaborators, 
                                        'owner': ObjectId(session['site_id']), 
                                        'date_created': datetime.today().strftime('%Y-%m-%d'),
                                        'rounds_completed': int(0), 
                                        'uploaded': [],
                                        'total_rounds': int(total_rounds),
                                        'code': join_code,
                                        'deadlines': deadlines,
                                        'model': model})

    mongo.db.sites.update_one({'_id': ObjectId(session['site_id'])}, {'$push': {'owned_projects' : proj_id}}, upsert = True)

    send_template_email(subject="PDA-OTA Project " + project_name, 
                        recipients=[session['email']],
                        template="new_proj_lead.html",
                        name=session['user_name'],
                        project=project_name,
                        code=join_code)

# Kicks a site off of a project
@app.route('/kick_site/<string:project_id>/<string:site_id>', methods=['POST', 'GET'])
@require_user_login
def kick_site(project_id, site_id):
    # find the site associated with this project
    mongo.db.projects.update(
        { '_id': ObjectId(project_id) },
        { '$pull': { 'collaborating_sites': ObjectId(site_id), 
                     'uploaded': ObjectId(site_id) } }
        )

    # return them to the project page
    return redirect(url_for('project',
                            project_id=project_id))

# Delete a project with the given ID from the system
# Must also delete the project from all user's owned and joined arrays
@app.route('/delete_project/<string:project_id>', methods=['POST', 'GET'])
@require_user_login
def delete_project(project_id):
    # find all files associated with this project and delete them
    all_files = mongo.db.files.find({'project': ObjectId(project_id)})
    for file in all_files:
        mongo.db.json.delete_one({'_id': file['json_id']})
        mongo.db.files.delete_one({'_id': file['_id']})

    # delete the project itself from the projects database
    mongo.db.projects.delete_one({'_id': ObjectId(project_id)})

    # remove pointers to the project from the owner
    # as well as all collaborators
    mongo.db.sites.update(
    { },
    { '$pull': { 'owned_projects': ObjectId(project_id) , 'joined_projects': ObjectId(project_id) } }
    )

    return redirect(url_for('dashboard'))

# Delete a project with the given ID from the system
# Must also delete the project from all user's owned and joined arrays
@app.route('/delete_file/<string:file_id>/<string:owner_id>/<string:project_id>', methods=['POST', 'GET'])
@require_user_login
def delete_file(file_id, owner_id, project_id):
    # first, get a reference to the file in question
    the_file = mongo.db.files.find_one({'_id': ObjectId(file_id)})
    # delete the JSON associated with this file
    mongo.db.json.delete_one({'_id': the_file['json_id']})
    # then delete the file itself
    mongo.db.files.delete_one({'_id': ObjectId(file_id)})

    # return them to the site page
    return redirect(url_for('site',
                            owner_id=owner_id,
                            project_id=project_id))

@app.route('/next_round/<string:project_id>', methods=['POST', 'GET'])
@require_user_login
def next_round(project_id):
    # first, get a reference to the project in question
    project = mongo.db.projects.find_one({'_id': ObjectId(project_id)})
    # get the rounds completed data
    curr_round = project['rounds_completed'] + 1

    filter = {'_id': ObjectId(project_id)}
    newvalue = { "$set": { 'rounds_completed': curr_round } }

    # update rounds completed
    mongo.db.projects.update_one(filter,newvalue)
    mongo.db.projects.update_one({'_id': ObjectId(project_id)}, { '$set' : {'uploaded': []}})

    # return them to the project page
    return redirect(url_for('project',
                            project_id=project_id))

@app.route('/upload_control/<string:project_id>', methods=['POST', 'GET'])
@require_user_login
def upload_control(project_id):
    project = mongo.db.projects.find_one({'_id': ObjectId(project_id)})
    if request.method == "POST" and project['owner'] == ObjectId(session['site_id']):

        if 'inputFile' in request.files:
            inputFile = request.files['inputFile']
            print(inputFile)
            load = json.load(inputFile)
            if load['model'][0].lower() != project['model'].lower():
                # flash a warning message - your models don't match!
                flash('The uploaded control.json had "' + load['model'][0] + 
                        '" selected, but the project had "' 
                        + project['model'] + '" selected!')
                return redirect(url_for('project', project_id=project['_id']))
            json_id = mongo.db.json.insert(load)

            # We're now at the stage where we are uploading the control.json file
            # 1. Find out if we've already uploaded a control.json file this round
            already_uploaded = mongo.db.files.find_one({
                'project': project['_id'], 
                'round': project['rounds_completed'], 
                'control': True
                })

            # no previously uploaded control.json file this round
            if (already_uploaded is None):
                # just upload a new file
                mongo.db.files.insert({'uploader': ObjectId(session['site_id']), 
                                       'project': project['_id'], 
                                       'json_id': json_id, 
                                       'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                       'filename': inputFile.filename, 
                                       'control': True, 
                                       'round': project['rounds_completed']})

            # we've uploaded a control file already    
            else:
                # first delete associated json information
                mongo.db.json.delete_one({'_id' : already_uploaded['json_id']})
                # then delete the file
                mongo.db.files.delete_one({'_id' : already_uploaded['_id']})

                # then upload the new file
                mongo.db.files.insert({
                    'uploader': ObjectId(session['site_id']), 
                    'project': project['_id'], 
                    'json_id': json_id, 
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 
                    'filename': inputFile.filename, 
                    'control': True, 
                    'round': project['rounds_completed']
                    })

        return redirect(url_for('project',
                            project_id=project['_id']))
    else:
        return 'no post request'

# User upload files on behalf of group to specified project.
# Currently no security measures to limit who can upload to project
@app.route('/upload_file/<string:project_id>', methods=['POST', 'GET'])
@require_user_login
def upload_file(project_id):
    if request.method == "POST":
        project = mongo.db.projects.find_one({'_id': ObjectId(project_id)})
        mongo.db.files.delete_one({
            'project': project['_id'], 
            'round': project['rounds_completed'], 
            'uploader': ObjectId(session['site_id']), 
            'control': False
            })
        if 'inputFile' in request.files:
            # read in the JSON file from the form
            input_file = loads(request.files['inputFile'].read())
            # get the filename from the raw data
            file_name = request.files['inputFile'].filename
            # insert the JSON (as bytes) to MongoDB
            # NOTE: returned object is NOT the ID!  It is the inserted object
            mongo_json = mongo.db.json.insert_one(input_file)
            # grab the JSON's ObjectId from inserted object
            json_id = ObjectId(mongo_json.inserted_id)

            if (mongo.db.files.find_one({'filename': file_name, 'project': request.form.get('project')})):
                return 'file name already taken for this project'

            to_insert = {'uploader': ObjectId(session['site_id']), 
                         'project': project['_id'],
                         'round': project['rounds_completed'], 
                         'json_id': json_id, 
                         'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                         'filename': file_name,
                         'control': False} 
  
            mongo.db.files.insert(to_insert)

            project_id = ObjectId(request.form.get('project'))
            owner_id = ObjectId(request.form.get('owner'))
            files = mongo.db.files.find({"$and": [{'project': project_id }, {'uploader': owner_id}]})
            owner = mongo.db.sites.find_one({'_id': ObjectId(owner_id)})
            owner_name = owner['name']
            
            # Adds site to list of uploaded in that round
            uploaded_sites = project['uploaded']
            if owner_id not in uploaded_sites:
                mongo.db.projects.update_one({'_id': project_id}, {'$push': {'uploaded' : owner_id}}, upsert = True)

            return render_template('site.html', 
                files=files, 
                owner_name=owner_name, 
                owner_id=owner_id, 
                project = project,
                is_user = True)
    else:
        project_id = ObjectId(project_id)
        project = mongo.db.projects['_id':project_id]
        owner_id = session['site_id']
        files = mongo.db.files.find({"$and": [{'project': project_id }, {'uploader': ObjectId(owner_id)}]})
        owner = mongo.db.sites.find_one({'_id': owner_id})
        owner_name = owner['name']
        return render_template('site.html', 
            files=files, 
            owner_name=owner_name, 
            owner_id=owner_id, 
            project = project,
            is_user = True)

@app.route('/download/<string:project_id>/<string:file_id>', methods=['GET'])
#@require_user_login
def download(project_id, file_id):
    proj = mongo.db.projects.find_one({'_id': ObjectId(project_id)})
    doc = mongo.db.files.find_one({'_id': ObjectId(file_id)})
    # Assert that site either owns the project or is a collaborator
    if not (proj['owner'] == ObjectId(session['site_id']) or ObjectId(session['site_id']) in proj['collaborating_sites']):
        return 'access denied'
    if doc:
        json_file = mongo.db.json.find_one({'_id': doc['json_id']})
        json_file.pop('_id', None)

        return Response(
        dumps(json_file),
        mimetype="application/json",
        headers={"Content-disposition":
                 "attachment; filename="+doc['filename']})
    else:
        return 'file not found'

def get_random_string(length):
    # Random string with the combination of lower and upper case
    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str




