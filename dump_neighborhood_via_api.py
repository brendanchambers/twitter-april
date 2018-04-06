__author__ = 'Brendan'


import json
import numpy as np
import tweepy as twee
import time

# twitter developer credentials
json_credentials_file = open('../local/credentials.json','r')
credentials = json.load(json_credentials_file)

auth = twee.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
api = twee.API(auth)

# get local neighborhood for this user
reference_user = 'societyoftrees'
json_target_string = 'my friend neighborhood_higher_cutoff.json' # json save file name

#  friends_ids , followers_ids  http://tweepy.readthedocs.io/en/v3.5.0/api.html#friendship-methods

def get_friends(user):
    time.sleep(60)
    print "sleeping..."
    return api.friends_ids(user)

def get_followers(user):
    time.sleep(60)
    print "sleeping..."
    return api.followers_ids(user)

def mergeLists(list1, list2): # isn't there an array method for this. use it
    result = []
    for item in list1:
        if ~(item in result):
            result.append(item)
    for item in list2:
        if not(item in result):
            result.append(item)
    return result

def screen_name_to_vertex_index(screen_name):
    for idx,v in enumerate(vertices):
        if v['screen_name'] == screen_name:
            return idx

def edge_exists(source_user,target_user):
    for e in edges:
        if e['source']==source_user.screen_name:
            if e['target']==target_user.screen_name:
                return True
    return False


# graph = { vertices = {name}, edges = {source, target, weight}

# find the node set
friends_ids = get_friends(reference_user)
#friends_ids = friends_ids[0:10] # was testing on small subset
followers_ids = get_followers(reference_user)
neighborhood_ids = mergeLists(friends_ids, followers_ids) # followers & friends
reference_id = api.get_user(reference_user).id
time.sleep(1) # 900 calls / 15 min allowed
neighborhood_ids = mergeLists([reference_id], neighborhood_ids) # # don't forget to include the reference user
vertices = [] # format for the json dump
for user_id in neighborhood_ids:
    username = api.get_user(user_id).screen_name
    time.sleep(1) # 900 calls / 15 min allowed
    vertices.append({"screen_name":username,"id":user_id}) # should probably use 'vertices' instead of 'vertex ids' below, sry

#print neighborhood_ids
N = len(neighborhood_ids)
print "number of nodes = " + str(N)

edges = [] # store as a list
adjmat = np.zeros((N,N)) # store as an adjacency matrix
visited = [] # process the nodes one by one

# GET THE FRIENDSHIP WHEEL
print "populating friendship wheel..."
items_per_request = 100 # b/c of the limit on api.lookup_friendships  # still need to monitor request rate, rewrite w cursor method
pages = int(np.ceil(N / items_per_request)) # total lookup_friendships requests that will be needed to check one node
for page in range(pages+1):
    request_startidx = items_per_request * page
    if page < pages:
        request_endidx = items_per_request * (page + 1) - 1
        relationships = api.lookup_friendships(neighborhood_ids[request_startidx:request_endidx])
        print "sleeping..."
        time.sleep(60)
    else:
        relationships = api.lookup_friendships(neighborhood_ids[request_startidx:])
        print "sleeping..."
        time.sleep(60)
    #print relationships[0]
    #print np.shape(relationships)
    for idx,r in enumerate(relationships):
        if r.is_following:
            weight = 1
            edges.append({"source":reference_user,"target":r.screen_name,"weight":weight})
            adjmat[0,idx+request_startidx] += weight  # todo figure out how to embed the node names with the rows
        if r.is_followed_by:
            weight = 1
            edges.append({"source":r.screen_name,"target":reference_user,"weight":weight})
            adjmat[idx+request_startidx,0] += weight  # todo figure out how to embed the node names with the rows
visited.append(reference_user);


MAX_DEGREE = 10000
def visit_node(vertex):
    
    friend_of_vertex_ids = []
    follower_of_vertex_ids = []

    print "current_user=" + vertex['screen_name']
    current_user = api.get_user(vertex['screen_name'])
    time.sleep(1)

    ## check friends:
    print "checking friends of current vertex...."
    if current_user.friends_count > MAX_DEGREE:
        vertex['gulper']=True # todo make sure this actually modifies the vertex object
        print "this user has too many friends"
    else:
        vertex['gulper']=False
        friends_of_current_user_and_neighbor_of_reference_node = []

        for page in twee.Cursor(api.friends_ids, screen_name=vertex['screen_name']).pages():
            # check for friends who are in the network
            friend_of_vertex_ids.extend(page)
            print "sleeping..."
            time.sleep(60)

        for id in friend_of_vertex_ids:
            if id in neighborhood_ids: # if the friend of vertex is also a neighbor of the reference node
                friends_of_current_user_and_neighbor_of_reference_node.append(id)

        current_node_idx = screen_name_to_vertex_index(current_user.screen_name)

        print "updating friend record keeping..."
        for friend in friends_of_current_user_and_neighbor_of_reference_node:
            friend_of_neighbor = api.get_user(friend)
            time.sleep(1)
            print friend_of_neighbor.screen_name + " is a friend of " + current_user.screen_name + " and " + reference_user

            if not(edge_exists(current_user, friend_of_neighbor)): # could call this earlier to cut a few api calls (~ factor 2)
                                                        # need a cleverer approach when number of edges gets big (e.g. just add edge and then trim duplicates in a later step)
                weight = 1
                edges.append({"source":current_user.screen_name,"target":friend_of_neighbor.screen_name,"weight":weight})
                friend_of_friend_idx = screen_name_to_vertex_index(friend_of_neighbor.screen_name)
                adjmat[current_node_idx, friend_of_friend_idx] += weight

    ## check followers
    print "checking followersof current vertex...."
    if current_user.followers_count > MAX_DEGREE:
        vertex['celebrity']=True # todo make sure this actually modifies the vertex object
        print "this user has too many followers"
    else:
        vertex['celebrity']=False
        followers_of_current_user_and_neighbor_of_reference_node = []

        for page in twee.Cursor(api.followers_ids, screen_name=vertex['screen_name']).pages():
            # check for friends who are in the network
            follower_of_vertex_ids.extend(page)
            print "sleeping..."
            time.sleep(60)

        for id in follower_of_vertex_ids:
            if id in neighborhood_ids: # if the follower of vertex is also a neighbor of the reference node
                followers_of_current_user_and_neighbor_of_reference_node.append(id)

        current_node_idx = screen_name_to_vertex_index(current_user.screen_name)

        print "updating follower record keeping..."
        for follower in followers_of_current_user_and_neighbor_of_reference_node:
            follower_of_neighbor = api.get_user(follower)
            print follower_of_neighbor.screen_name + " is a friend of " + current_user.screen_name + " and " + reference_user
            time.sleep(1)

            if not(edge_exists(current_user, follower_of_neighbor)): # could call this earlier to cut a few api calls (~ factor 2)
                                                        # need a cleverer approach when number of edges gets big (e.g. just add edge and then trim duplicates in a later step)
                weight = 1
                edges.append({"source":current_user.screen_name,"target":follower_of_neighbor.screen_name,"weight":weight})
                follower_of_neighbor_idx = screen_name_to_vertex_index(follower_of_neighbor.screen_name)
                adjmat[current_node_idx, follower_of_neighbor_idx] += weight

        print "finished processing v = " + current_user.screen_name
        visited.append(current_user.screen_name)

# FIND neighborhood interconnections
print "discovering neighborhood interconnections..."
for v in vertices:
    if not(v['screen_name'] in visited): # make sure we haven't processed this node yet # don't really need this
        visit_node(v)


num_edges = np.sum(adjmat.flatten())
print "there are " + str(num_edges) + " links in the network"
print np.shape(adjmat)

save_object = {"vertices":vertices,"edges":edges,"adjacency_matrix":adjmat.tolist(),"max_degree_cutoff":MAX_DEGREE}

json_target_file = open(json_target_string,'w')
json.dump(save_object, json_target_file, indent=2, sort_keys=True)






