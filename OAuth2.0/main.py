#########################################################################################
import flask
import requests
import string
import random

from flask import Flask, request, redirect, render_template, jsonify


CLIENT_ID = '129750749498-uc629jr3t6gmcktnv69gl7pffqk8t8qg.apps.googleusercontent.com'
CLIENT_SECRET = 'PhkNW7uqNexQQYc85bxlncGT'
SCOPE = 'https://www.googleapis.com/auth/userinfo.profile'
#REDIRECT_URI = 'http://localhost:8080/oauth' # For local testing
REDIRECT_URI = 'https://barracln-oauth.wl.r.appspot.com/oauth' # For deploying to gcloud

def create_app():
	import uuid
	app = flask.Flask(__name__)
	app.secret_key = str(uuid.uuid4()) # Not sure why, but we need to set secret_key in order to access the session
	return app

app = create_app()


# Index
@app.route('/')
def index():
	return render_template("index.html") # Welcome page


# Auth
@app.route('/authenticate')
def auth_redirect():
	
    # Create a randomly generated state upon auth request and store
    char_string = string.ascii_letters + string.digits
    new_state = ''.join((random.choice(char_string) for i in range(8)))
    
    # Store the generated state in the session for later comparison
    flask.session['state'] = new_state
    
    auth_uri = ('https://accounts.google.com/o/oauth2/v2/auth?response_type=code&'
                    'client_id={}&redirect_uri={}&scope={}&state={}').format(CLIENT_ID, REDIRECT_URI, SCOPE, new_state)
    return redirect(auth_uri)

@app.route('/oauth')
def auth_callback():
    auth_code = request.args.get('code')
    data = {'code': auth_code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'}
    res = requests.post('https://oauth2.googleapis.com/token', data=data)
    response_data = res.json()
    tok = response_data['access_token'] # Retrieve access token as a string
    
    # Exchange token with google for user information
    cred_response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token={}'.format(tok))
    response_data = cred_response.json()
    
    state = request.args.get('state') # Retrieve state when we get the authorization code
    
    # Retrieve first name and last name and set up greeting message
    f_name = response_data['given_name']
    l_name = response_data['family_name']
    greetings = "Hello " + str(l_name) + ", " + str(f_name)
    
    # Compare session state and show greeting unless states don't match
    if state == flask.session['state']:
        return (greetings)
    else:
        error = "ERROR: State is was not equal to session state."
        return (error)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
