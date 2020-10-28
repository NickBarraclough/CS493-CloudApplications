import datetime
import json
import boats

from flask import Flask, Blueprint, request, jsonify
from google.cloud import datastore

client = datastore.Client()

bp = Blueprint('loads', __name__, url_prefix='/loads')

@bp.route('', methods=['GET', 'POST'])
def loads_get_post():
    if request.method == 'POST':
        content = request.get_json() # Retreive content from request body
        if len(content) == 4: # Correct amount of attributes
            # Build new load and assign attributes
            new_load = datastore.entity.Entity(key=client.key("loads"))
            new_load.update({"weight": content["weight"], "carrier": None,
          "content": content["content"], "delivery_date": content["delivery_date"]})
            client.put(new_load)
            success = {"id": new_load.key.id, "weight": content["weight"], "content": content["content"],
          "delivery_date": content["delivery_date"], "self": (request.url + '/' + str(new_load.key.id)), "carrier": None}
            return (success, 201)
        else: # Incorrect amount of attributes
            failure = {"Error": "The request object is missing at least one of the required attributes"}
            return (failure, 400)
        
#    if request.method == 'GET': # Get all loads
#        query = client.query(kind="loads") # Query datastore for all loads
#        results = list(query.fetch())
#        for e in results:
#            e["id"] = e.key.id
#            e["self"] = request.url + '/' + str(e.key.id)
#        return (jsonify(results), 200)
#
#    else:
#        failure = {"Error": "Could not get loads"}
#        return (failure, 404)
    elif request.method == 'GET':
        query = client.query(kind="loads")
        q_limit = int(request.args.get('limit', '3'))
        q_offset = int(request.args.get('offset', '0'))
        g_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = g_iterator.pages
        results = list(next(pages))
        if g_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
            e["self"] = request.url_root + "loads/" + str(e.key.id)
            if e["carrier"] != None:
                e['carrier']['self'] = request.url_root + "boats/" + str(e['carrier']['id'])
        output = {"loads": results}
        if next_url:
            output["next"] = next_url
        return (jsonify(output), 200)
        
# LOADS request handler - GET(Specified)
@bp.route('/<load_id>', methods=['GET', 'DELETE'])
def loads_id_get_delete(load_id):
    if request.method == 'GET':
        load_key = client.key("loads", int(load_id))
        load = client.get(key=load_key)
        if load == None: # Load not found
            failure = {"Error": "No load with this load_id exists"}
            return (failure, 404)
        # Load found, set id and self
        load["id"] = load_id
        load["self"] = request.url
        return (load, 200)

    elif request.method == 'DELETE':
        load_key = client.key("loads", int(load_id))
        load = client.get(key=load_key)
        if load == None:
            failure = {"Error": "No load with this load_id exists"}
            return (failure, 404)

        if load["carrier"] != None:
            boat_key = client.key("boats", int(load["carrier"]["id"]))
            boat = client.get(key=boat_key)
            for _ in boat["loads"]:
                if _["id"] == load.key.id:
                    boat["loads"].remove({"id": load.key.id})
            client.put(boat)
        
        client.delete(load_key)
        return('', 204)
    
    else:
        return 'Method not recogonized'
