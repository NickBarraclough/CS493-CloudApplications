#---------------------------------------------------------------------
# Assigment 4: Intermediate REST API
#   \__loads.py
# Datastore request handlers for /loads/*. 
#---------------------------------------------------------------------

import json
import boats

from flask import Flask, Blueprint, request, jsonify
from google.cloud import datastore

client = datastore.Client()

bp = Blueprint('loads', __name__, url_prefix='/loads')

# LOADS request handler - GET (All loads) and POST (Add new load)
@bp.route('', methods=['GET', 'POST'])
def loads_get_post():
    if request.method == 'POST':
        
        content = request.get_json() # Retreive content from request body
        
        # Build new load and assign request attributes
        if len(content) == 4: # Correct amount of attributes
            new_load = datastore.entity.Entity(key=client.key("loads")) # Grab a loads entity from Datastore
            new_load.update({"weight": content["weight"], "carrier": None, "content": content["content"], "delivery_date": content["delivery_date"]})
            client.put(new_load) # Update Datastore entity
            success = {"id": new_load.key.id, "weight": content["weight"], "content": content["content"], "delivery_date": content["delivery_date"], "self": (request.url + '/' + str(new_load.key.id)), "carrier": None}
            return (success, 201)
        else: # Incorrect amount of attributes
            failure = {"Error": "The request object is missing at least one of the required attributes"}
            return (failure, 400)
        
    # Paginated list of all loads (Max 3)
    elif request.method == 'GET':
        query = client.query(kind="loads") # Query datastore for all loads
        q_limit = int(request.args.get('limit', '3')) # Query has a list limit of 3
        q_offset = int(request.args.get('offset', '0')) # Set offset
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
    # GET load
    if request.method == 'GET':
        
        load_key = client.key("loads", int(load_id))
        load = client.get(key=load_key)
        
        # Load not found
        if load == None:
            failure = {"Error": "No load with this load_id exists"}
            return (failure, 404)
        
        # Load found, set id and self
        load["id"] = load_id
        load["self"] = request.url
        return (load, 200)

    # DELETE load
    elif request.method == 'DELETE':
        
        load_key = client.key("loads", int(load_id))
        load = client.get(key=load_key)
        
        # Load not found
        if load == None:
            failure = {"Error": "No load with this load_id exists"}
            return (failure, 404)

        # Carrier boat must remove this load before it is deleted
        if load["carrier"] != None:
            boat_key = client.key("boats", int(load["carrier"]["id"]))
            boat = client.get(key=boat_key)
            for _ in boat["loads"]: # Search each load on boat
                if _["id"] == load.key.id: # Find matching load
                    boat["loads"].remove({"id": load.key.id}) # Remove from boat's loads list
            client.put(boat) # Update boat in Datastore
        
        client.delete(load_key)
        
        return('', 204)
    
    else:
        return 'Method not recogonized'
