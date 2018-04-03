__author__ = 'Brendan'


import json
import numpy as np
import tweepy as twee

# twitter developer credentials
json_credentials_file = open('../local/credentials.json','r')
credentials = json.load(json_credentials_file)

auth = twee.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
api = twee.API(auth)

# get local neighborhood for this user
reference_user = 'societyoftrees'
json_target_string = 'my friendship wheel.json' # json save file name

#  friends_ids , followers_ids  http://tweepy.readthedocs.io/en/v3.5.0/api.html#friendship-methods

def get_friends(user):
    return api.friends_ids(user)

def get_followers(user):
    return api.followers_ids(user)

def mergeLists(list1, list2): # isn't there an array method for this. use it
    result = [];
    for item in list1:
        if ~(item in result):
            result.append(item)
    for item in list2:
        if not(item in result):
            result.append(item)
    return result

# graph = { vertices = {name}, edges = {source, target, weight}

# find the node set
friends_ids = get_friends(reference_user)
followers_ids = get_followers(reference_user)
neighborhood_ids = mergeLists(friends_ids, followers_ids) # followers & friends
reference_id = api.get_user(reference_user).id
neighborhood_ids = mergeLists([reference_id], neighborhood_ids) # # don't forget to include the reference user
vertices = [] # format for the json dump
for user_id in neighborhood_ids:
    username = api.get_user(user_id).screen_name
    vertices.append({"screen_name":username,"id":user_id}) # should probably use 'vertices' instead of 'vertex ids' below, sry

print neighborhood_ids
N = len(neighborhood_ids)
print N

edges = [] # store as a list
adjmat = np.zeros((N,N)) # store as an adjacency matrix

items_per_request = 100 # b/c of the limit on api.lookup_friendships  # still need to monitor request rate, rewrite w cursor method
pages = int(np.ceil(N / items_per_request)) # total lookup_friendships requests that will be needed to check one node
for page in range(pages+1):
    request_startidx = items_per_request * page
    if page < pages:
        request_endidx = items_per_request * (page + 1) - 1
        relationships = api.lookup_friendships(neighborhood_ids[request_startidx:request_endidx])
    else:
        relationships = api.lookup_friendships(neighborhood_ids[request_startidx:])
    print relationships[0]
    print np.shape(relationships)
    for idx,r in enumerate(relationships):
        if r.is_following:
            weight = 1
            edges.append({"source":reference_user,"target":r.screen_name,"weight":weight})
            adjmat[0,idx+request_startidx] += weight  # todo figure out how to embed the node names with the rows
        if r.is_followed_by:
            weight = 1
            edges.append({"source":r.screen_name,"target":reference_user,"weight":weight})
            adjmat[idx+request_startidx,0] += weight  # todo figure out how to embed the node names with the rows
#
# todo figure out the other neighborhood interconnections (except maybe for celebrities)
#
# # find the edge set
# for pre_idx,pre_id in enumerate(vertex_ids):
#     for post_idx,post_id in enumerate(vertex_ids):
#         if not(pre_idx==post_idx): # no self-loops
#                 print "friendship detected " + str(pre_id) + ', ' +  str(post_id)
#                 edges.append({"source":pre_id,"target":post_id,"weight":weight})
#                 adjmat[pre_idx,post_idx] += weight  # todo figure out how to embed the node names with the rows
#

num_edges = np.sum(adjmat.flatten())
print "there are " + str(num_edges) + " links in the network"
print np.shape(adjmat)

save_object = {"vertices":vertices,"edges":edges,"adjacency_matrix":adjmat.tolist()}

json_target_file = open(json_target_string,'w')
json.dump(save_object, json_target_file, indent=2, sort_keys=True)






