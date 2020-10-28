#---------------------------------------------------------------------
# Assigment 4: Intermediate REST API
#   \__boats.py
# Datastore request handlers for /boats/*. 
#---------------------------------------------------------------------

import json
import loads

from flask import Flask, Blueprint, request, jsonify
from google.cloud import datastore

client = datastore.Client()

bp = Blueprint('boats', __name__, url_prefix='/boats')

# BOATS request handler - GET and POST (Add boat)
@bp.route('', methods=['GET', 'POST'])
def boats_get_post():
    if request.method == 'POST':
        content = request.get_json() # Retreive content from request body
        if len(content) == 3: # Correct amount of attributes
            # Build new boat and assign attributes
            new_boat = datastore.entity.Entity(key=client.key("boats")) # Grab boats entity from Datastore
            new_boat.update({"name": content["name"], "type": content["type"], "length": content["length"], "loads": None}) # Set attributes using request content
            client.put(new_boat) # Update Datastore entity
            success = {"id": new_boat.key.id, "name": content["name"], "type": content["type"], "length": content["length"], "self": (request.url + '/' + str(new_boat.key.id)), "loads": None}
            return (success, 201) # Return successfully made boat with 201 status code
        else: # Incorrect amount of attributes
            failure = {"Error": "The request object is missing at least one of the required attributes"}
            return (failure, 400)

    # Paginated list of all boats (Max 3)
    elif request.method == 'GET':
        query = client.query(kind="boats") # Query datastore for all boats
        query_lim = int(request.args.get('limit', '3')) # Query has a list limit of 3
        query_off = int(request.args.get('offset', '0')) # Start at first object
        l_iterator = query.fetch(limit= query_lim, offset=query_off)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = query_off + query_lim
            next_url = request.base_url + "?limit=" + str(query_lim) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
            e["self"] = request.url + "/" + str(e.key.id)
            if e["loads"]:
                if len(e["loads"]) > 0:
                    for l in e["loads"]:
                        l["self"] = request.url_root + "loads/" + str(l["id"])
        output = {"boats": results}
        if next_url:
            output["next"] = next_url
        return (jsonify(output), 200)
    else:
        failure = {"Error": "Could not get boats"}
        return (failure, 404)
   
# BOATS request handler - GET (Loads)
@bp.route('/<boat_id>/loads', methods=['GET'])
def boats_get_loads(boat_id):
    if request.method == 'GET': # Get all of a specified boat's loads
        
        boat_key = client.key("boats", int(boat_id))
        boat = client.get(key=boat_key)
        
        # Boat not found
        if boat == None:
            failure = {"Error": "No boat with this boat_id exists"}
            return (failure, 404)
        
        # Build list of the boat's loads (including only id and self)
        boat_loads = []
        if boat["loads"] != None:
            for l in boat["loads"]:
                load_key = client.key("loads", int(l["id"]))
                load = client.get(key=load_key)
                load["id"] = load.key.id
                load["self"] = request.url_root + "loads/" + str(load.key.id)
                boat_loads.append(load)  
            return (jsonify(boat_loads), 200) # Return list of boats in JSON with 200 status code
    else:
        return 'Method not recogonized'

# BOATS request handler - GET and DELETE(Specified)
@bp.route('/<boat_id>', methods=['GET', 'DELETE'])
def boats_id_get(boat_id):
    if request.method == 'GET':
        
        boat_key = client.key("boats", int(boat_id))
        boat = client.get(key=boat_key)
        
        # Boat not found
        if boat == None:
            failure = {"Error": "No boat with this boat_id exists"}
            return (failure, 404)
        
        # Boat found, set id and self and all loads' "self" attributes
        boat["id"] = boat_id
        boat["self"] = request.url
        if boat["loads"] != None:
            for ld in boat["loads"]:
                ld.update({"self": request.url_root + "loads/" + str(ld["id"])})
                
        return (boat, 200)
    
    elif request.method == 'DELETE':
        
        boat_key = client.key("boats", int(boat_id))
        boat = client.get(key=boat_key)
        
        # Boat not found
        if boat == None:
            failure = {"Error": "No boat with this boat_id exists"}
            return (failure, 404)
        
        # Remove "carrier" from all this boat's loads
        if boat["loads"] != None or boat["loads"] == []:
            if len(boat["loads"]) > 0:
                for load in boat["loads"]:
                    load_object = client.get(key=client.key("loads", load["id"]))
                    load_object["carrier"] = None
                    client.put(load_object)
        
        client.delete(boat_key)
        return('', 204)
    
    else:
        return 'Method not recogonized'

# BOATS request handlers - PUT
@bp.route('/<boat_id>/loads/<load_id>', methods=['PUT'])
def boats_put_load(boat_id, load_id):
    if request.method == 'PUT':
        
        boat_key = client.key("boats", int(boat_id))
        boat = client.get(key=boat_key)
        load_key = client.key("loads", int(load_id))
        load = client.get(key=load_key)

        # Boat/Load not found
        if boat == None and load == None:
            failure = {"Error": "Not a valid boat_id nor a valid load_id."}
            return (failure, 404)
        if boat == None:
            failure = {"Error": "No boat with this boat_id exists"}
            return (failure, 404)
        if load == None:
            failure = {"Error": "No load with this load_id exists"}
            return (failure, 404)
            
        # Assign load to carrier
        if load["carrier"] == None:
            boat_self = str(request.url_root) + "boats/" + str(boat.key.id)
            load.update({"carrier": {"id": str(boat.key.id), "name": boat["name"], "self": boat_self}})
        else: # Load already assigned
            failure = {"Error": "This load is already assigned to a carrier."}
            return (failure, 403)
            
        add_load = {"id": load.key.id} # Load to be added

        # Update boat's loads list
        if boat["loads"] != None: # Boat has current loads
            loads_list = boat["loads"]
            loads_list.append(add_load)
            boat.update({"loads": loads_list})
        else: # Boat has no current loads
            loads_list = []
            loads_list.append(add_load)
            boat.update({"loads": loads_list})
        
        client.put(boat)
        client.put(load)
        
        return ('', 204)
   
    else:
        return 'Method not recogonized'

# BOATS request handlers - DELETE (Remove load from boat's loads list)
@bp.route('/<boat_id>/loads/<load_id>', methods=['DELETE'])
def boats_remove_load(boat_id, load_id):
    if request.method == 'DELETE':
        
        boat_key = client.key("boats", int(boat_id))
        boat = client.get(key=boat_key)
        load_key = client.key("loads", int(load_id))
        load = client.get(key=load_key)

        # Boat/Load not found
        if boat == None and load == None:
            failure = {"Error": "Not a valid boat_id nor a valid load_id."}
            return (failure, 404)
        if boat == None:
            failure = {"Error": "No boat with this boat_id exists"}
            return (failure, 404)
        if load == None:
            failure = {"Error": "No load with this load_id exists"}
            return (failure, 404)
        
        # Remove load from boat's loads list and remove carrier data from load
        if load["carrier"] != None:
            if load["carrier"]["id"] == boat_id: # Match carrier to specified boat
                loads_list = boat["loads"]
                loads_list.remove({"id": load.key.id})
                boat.update({"loads": loads_list})
                load.update({"carrier": None})
            else:
                failure = {"Error": "The load is not on this boat."}
                return (failure, 404)
        else:
            failure = {"Error": "The load does not have a carrier."}
            return (failure, 404)
            
        client.put(boat)
        client.put(load)
        
        return('', 204)
