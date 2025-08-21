

def filter_gems(items, gems, caps, weights):
    caps_list = [d["name"] for d in caps if "name" in d]

    socket_pairs = {
        "red": ["red", "orange", "purple"],
        "yellow": ["yellow", "orange", "green"],
        "blue": ["blue", "purple", "green"],
        "prismatic": ["red", "yellow", "blue", "orange", "green", "purple"]}

    result = {}
    for socket_color, socket_pair in socket_pairs.items():
        result[socket_color] = []
        best_all_weights = {"score": 0, "gemID": None}

        best_both = {}
        for cap_stat in caps_list:
            best_both[cap_stat] = {"score": 0, "gemID": None}

        for gemID, gem_data in gems.items():
            gem_stats = gem_data['stats']
            gem_color = gem_data['color']

            if gem_color not in socket_pair:
                continue

            # finding best gem with only weighted stats
            if all_weights(gem_stats, weights):

                score = 0
                for stat, value in gem_stats.items():
                    score += value * weights[stat]

                if score > best_all_weights['score']:
                    best_all_weights['score'] = score
                    best_all_weights['gemID'] = gemID

                continue

            # finding all gems with only capping stats
            if all_caps(gem_stats, caps):
                result[socket_color].append(gemID)
                continue

            # finding best gem for each cap stat
            if one_cap_one_weight(gem_stats, caps,  weights):
                score = 0
                match = ''
                for stat, value in gem_stats.items():
                    score += value * weights[stat]
                    if stat in caps_list:
                        match = stat

                if score > best_both[match]['score']:
                    best_both[match]['score'] = score
                    best_both[match]['gemID'] = gemID

        if best_all_weights['gemID']:
            result[socket_color].append(best_all_weights['gemID'])

        for k, v in best_both.items():
            if v['gemID']:
                result[socket_color].append(v['gemID'])

    # for printing output >)
    # for i, j in result.items():
        # print(i)
        # for k in j:
            # print(gems[k])
        # print()

    return result


def all_weights(gem_stats, weights):
    for stat in gem_stats:
        if weights[stat] == 0:
            return False
    return True

def all_caps(gem_stats, caps):
    caps_list = [d["name"] for d in caps if "name" in d]

    for stat in gem_stats:
        if stat not in caps_list:
            return False

    return True

def one_cap_one_weight(gem_stats, caps, weights):
    caps_list = [d["name"] for d in caps if "name" in d]
    cap_stat, weight_stat = False, False

    for stat in gem_stats:
        if stat in caps_list:
            cap_stat = True

        if weights[stat] > 0:
            weight_stat = True

    if cap_stat and weight_stat:
        return True
    else:
        return False

