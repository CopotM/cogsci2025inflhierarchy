import networkx as nx
import pandas as pd
import pickle
from collections import defaultdict
import json
import numpy as np
from itertools import combinations
from datetime import datetime
import glob

files = glob.glob("*_bipartite.pickle")
files = [f.replace("_bipartite.pickle", "") for f in files]


for file in files:

    with open(file + "_bipartite.pickle", 'rb') as pickle_file:
        B= pickle.load(pickle_file)

    resolutions = np.round(np.arange(0, 2.1, 0.1), 1)

    lexemes = {n for n, d in B.nodes(data=True) if d["bipartite"] == 0}

    communities = defaultdict(dict)
    for res in resolutions:
        print("started res ", res, "at ", datetime.now())
        communities[res] = nx.community.louvain_communities(B, resolution = res)

    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError


    new_comms = defaultdict()
    #get lexemes only
    for res in resolutions:
        new_comms[res] = [s & lexemes for s in communities[res] if s & lexemes]

    with open('community_detection_'+file+'.json', 'w', encoding='utf8') as fp:
        json.dump(new_comms, fp, default = set_default, ensure_ascii = False)

    #hierarchy in the resolution
    #for each pair of levels, get lower level - for each community in lower level, find all pairs of verbs,
    #for each pair check if they are still in the same community in the higher level. If so, +1. Then average
    resolutions.sort()
    tuples = [(resolutions[i], resolutions[i+1]) for i in range(len(resolutions) - 1)]

    def find_set_containing_string(list_of_sets, x):
        for s in list_of_sets:
            if x in s:
                return s

    hierarchy_ratings = defaultdict()

    for upper_res,lower_res in tuples:
        print("started comm pair", upper_res, lower_res, datetime.now())
        lower_comms = new_comms[lower_res]
        upper_comms = new_comms[upper_res]
        communities_ratings = []
        if all(len(s) == 1 for s in lower_comms):
            hierarchy_ratings[str(lower_res)+"_"+str(upper_res)] = "Every lexeme in its own community"
        else:
            for community in lower_comms:
                comm = list(community)
                if comm and len(comm) != 1:
                    verb_pairs = list(combinations(comm, 2))
                    count_same_set = 0
                    for v1, v2 in verb_pairs:
                        s = find_set_containing_string(upper_comms, v1)
                        if v2 in s:
                            count_same_set += 1
                    score = count_same_set/len(verb_pairs)
                    communities_ratings.append(score)
            hierarchy_ratings[str(lower_res)+"_"+str(upper_res)] = communities_ratings

    averages = {
        key: values if isinstance(values, str) else sum(values) / len(values)
        for key, values in hierarchy_ratings.items()
    }
    # Create DataFrame from dictionary
    df_hierarchy = pd.DataFrame(list(averages.items()), columns=['Keys', 'Averages'])
    ncomms_upper = [len(new_comms[x]) for x in resolutions[:-1]]
    ncomms_lower = [len(new_comms[x]) for x in resolutions[1:]]
    df_hierarchy['ncomms_upper'] = ncomms_upper
    df_hierarchy['ncomms_lower'] = ncomms_lower

    df_hierarchy.to_csv(file + '_hierarchy_average.csv', index=False)
