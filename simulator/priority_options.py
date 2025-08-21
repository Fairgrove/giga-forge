



def get_item_options(items: list, caps: dict, gems: dict):

    item_variations = []

    for item in items:
        if len(item['stats']) > 0 and not item['locked']:
            item_options, item_paths = get_item_options_from_prio(item, gems)
            item_variations.append(item_options)
            ITEM_PATHS.append(item_paths)

    return item_variations



def get_item_options_from_prio(item: dict, gems: dict):

    reforge_stats = filter_prio_list_to_reforge_stats(stats['stat_prio'], caps, item)
    print (reforge_stats)
    item_options = []
    item_paths = []
    for item_stat in item['stats']:
        for priority_stat in reforge_stats:
            src = item_stat
            #src_value = item['stats'][src]
            dst = priority_stat

            dst_value = stats['stat_prio'].index(dst) if dst in stats['stat_prio'] else len(stats['stat_prio'])

            src_value = stats['stat_prio'].index(src) if src in stats['stat_prio'] else len(stats['stat_prio'])

            # if src_value >= dst_value or dst not in caps_list:
                # continue
            # print(src_value, dst_value)
            if dst not in item['stats'] and (dst_value < src_value or dst in caps_list):
                print(f"{src} -> {dst}  |  {src_value} {dst_value} ")
                item_path = {
                        "slotID": item['slotID'],
                        "src": src,
                        "dst": dst,
                        "gems": [],
                        }

                reforge_option = generate_item_reforge_option_from_prio(item, src=src, dst=dst)

                socket_options, used_gems = generate_item_socket_options(item, gems)
                if socket_options:
                    for i, socket_option in enumerate(socket_options):
                        item_option = {}
                        for key, value in reforge_option.items():
                            item_option[key] = reforge_option[key] + socket_option[key]

                        item_path = {
                                "slotID": item['slotID'],
                                "src": src,
                                "dst": dst,
                                "gems": used_gems[i],
                                }
                        item_options.append(item_option)
                        item_paths.append(item_path)
                else:
                    item_path = {
                            "slotID": item['slotID'],
                            "src": src,
                            "dst": dst,
                            "gems": [],
                            }

                    item_options.append(reforge_option)
                    item_paths.append(item_path)

    # adding un reforged option for every item
    item_path = {
            "slotID": item['slotID'],
            "src": None,
            "dst": None,
            "gems": [],
            }

    item_variant = generate_item_reforge_option_from_prio(item)
    socket_options, used_gems = generate_item_socket_options(item, gems)
    if socket_options:
        for i, socket_option in enumerate(socket_options):
            item_option = {}
            for key, value in reforge_option.items():
                item_option[key] = item_variant[key] + socket_option[key]

            item_path = {
                    "slotID": item['slotID'],
                    "src": None,
                    "dst": None,
                    "gems": used_gems[i],
                    }
            item_options.append(item_option)
            item_paths.append(item_path)
    else:
        item_path = {
                "slotID": item['slotID'],
                "src": None,
                "dst": None,
                "gems": [],
                }

        item_options.append(item_variant)
        item_paths.append(item_path)

    filtered_item_options, filtered_item_paths = remove_duplicate_item_variations(item_options, item_paths)
    # print(filtered_item_options)

    print(f"item slot:{item['slotID']}\n   before: {len(item_options)}\n   after: {len(filtered_item_options)}")

    return filtered_item_options, filtered_item_paths

def filter_prio_list_to_reforge_stats(priority_list: list, caps: dict, item):
    unreforgable_stats = [
            'ITEM_MOD_STAMINA_SHORT',
            'ITEM_MOD_AGILITY_SHORT',
            'ITEM_MOD_INTELLECT_SHORT',
            'ITEM_MOD_STRENGTH_SHORT',
            'power',
            'resilience',
            ]

    result = []

    # find best possible stat from priority_list
    best_stat_index = 1000
    for i, stat in enumerate(priority_list):
        # pvp power and resilience might be in stats
        if not stat in item['stats'] and not stat in unreforgable_stats:
            if i < best_stat_index:
                best_stat_index = i

    if not best_stat_index == 1000:
        result.append(priority_list[best_stat_index])

    result += [d["name"] for d in caps if "name" in d]
    return result

def generate_item_reforge_option_from_prio(item, src=None, dst=None):
    item_variant = {}

    temp_item = copy.deepcopy(item)

    if src and dst:
        reforge_coeff = 0.4

        new_stat = floor(item['stats'][src] * reforge_coeff)
        temp_item['stats'][dst] = new_stat
        temp_item['stats'][src] -= new_stat

        for i, cap_stat in enumerate(caps_list):
            if src == cap_stat:
                item_variant[f"d{i+1}"] = new_stat * -1

            elif dst == cap_stat:
                item_variant[f"d{i+1}"] = new_stat

            else:
                item_variant[f"d{i+1}"] = 0

    else:
        for i, cap_stat in enumerate(caps):
            item_variant[f"d{i+1}"] = 0

    item_variant['score'] = 0

    for stat, value in temp_item['stats'].items():
        if stat in stat_prio:
            stat_placement = len(stat_prio) - stat_prio.index(stat)

            item_variant['score'] += floor(value * (stat_placement/len(stat_prio)))

    return item_variant

def generate_item_socket_options(item: dict, gems: dict):
    # generate multi list of gems
    item_sockets = []
    for color in item['sockets']:
        item_sockets.append(gems[color])


    if len(item_sockets) == 0:
        return False, False

    socket_combinations = unique_unordered_combinations(item_sockets)

    socket_variations = []
    for socket_combination in socket_combinations:
        socket_variant = {}
        for i, cap_stat in enumerate(caps):
            socket_variant[f"d{i+1}"] = 0

        socket_variant['score'] = 0

        for gem in socket_combination:
            for stat, value in gems_json[gem]['stats'].items():
                for i, cap_stat in enumerate(caps):
                    if cap_stat['name'] == stat:
                        socket_variant[f"d{i+1}"] = value
                if stat in stats['stat_prio']:
                    socket_variant['score'] += floor(value * ((len(stats['stat_prio']) - stats['stat_prio'].index(stat))/len(stats['stat_prio'])))

        socket_variations.append(socket_variant)

    # filtered_variations, filtered_gems = remove_duplicate_socket_sums(socket_variations, socket_combinations)

    return socket_variations, socket_combinations

def remove_duplicate_item_variations(variations, item_paths):
    unique_variations = []
    unique_item_paths = []

    for i, variation in enumerate(variations):
        if variation not in unique_variations:
            unique_variations.append(variation)
            unique_item_paths.append(item_paths[i])

    return unique_variations, unique_item_paths

