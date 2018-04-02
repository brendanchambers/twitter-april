__author__ = 'Brendan'


from bs4 import BeautifulSoup
import requests
import json
import numpy as np
import tweepy as twee
import time

# tweepy credentials

json_credentials_file = open('../local/credentials.json','r')
credentials = json.load(json_credentials_file)

auth = twee.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
api = twee.API(auth)

# get local neighborhood
reference_user = 'societyoftrees'
json_target_string = 'SoT neighborhood'

# (1) exists_friendship (2) show_friendship (3) friends_ids (4) followers_ids  http://tweepy.readthedocs.io/en/v3.5.0/api.html#friendship-methods

def get_friends(user):
    return api.friends_ids(user)

def get_followers(user):
    return api.followers_ids(user)

def mergeLists(list1, list2):
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
friends_ids = get_friends(reference_user)  # todo store these in a more verbose way to make the loading step easier
followers_ids = get_followers(reference_user)
vertex_ids = mergeLists(friends_ids, followers_ids) # followers & friends
reference_id = api.get_user(reference_user).id
vertex_ids = mergeLists([reference_id], vertex_ids) # # don't forget to include the reference user
print vertex_ids
N = len(vertex_ids)
print N

# find the edge set
edges = [] # store as a list
adjmat = np.zeros((N,N)) # store as an adjacency matrix
for pre_idx,pre_id in enumerate(vertex_ids):
    for post_idx,post_id in enumerate(vertex_ids):
        if not(pre_idx==post_idx): # no self-loops
            weight = 1
            edges.append({"source":pre_id,"target":post_id,"weight":weight})
            adjmat[pre_idx,post_idx] += weight  # todo figure out how to embed the node names with the rows

num_edges = np.sum(adjmat.flatten())
print "there are " + str(num_edges) + " links in the network"
print np.shape(adjmat)

save_object = {"vertex_ids":vertex_ids,"edges":edges,"adjacency_matrix":adjmat.tolist()}

json_target_file = open(json_target_string,'w')
json.dump(save_object, json_target_file, indent=2, sort_keys=True)






