import datetime
import json
import boats
import loads

from flask import Flask, Blueprint, request, jsonify
from google.cloud import datastore

app = Flask(__name__)
client = datastore.Client()
app.register_blueprint(boats.bp)
app.register_blueprint(loads.bp)

# Index Page
@app.route('/')
def index():
    return "Please navigate to /boats to use this API"\

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)

