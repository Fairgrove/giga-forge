import copy
from itertools import product
from math import floor

unreforgable_stats = [
        'ITEM_MOD_STAMINA_SHORT',
        'ITEM_MOD_AGILITY_SHORT',
        'ITEM_MOD_INTELLECT_SHORT',
        'ITEM_MOD_STRENGTH_SHORT',
        'power',
        'resilience',
        ]

spell_haste_specs = {0,}

def get_cap_stat_index(caps, stat):
    caps_list = [d["name"] for d in caps if "name" in d]

    if not stat in caps_list:
        return None

    return caps_list.index(stat)

def generate_empty_item_variation(caps):
    caps_list = [d["name"] for d in caps if "name" in d]

    item_variant = []
    for cap_idx in caps_list:
        item_variant.append(0)
    item_variant.append(0)

    return item_variant

def combine_item_variations(variation1, variation2):
        return [stat1 + stat2 for stat1, stat2 in zip(variation1, variation2)]

def get_items_options(items, gems, filtered_gems, enchants, caps, weights, include_gems=True):
    items_variations = []
    items_paths = []

    # filtered_weights = filter_stat_weights(weights)
    weights = normalize_weights(weights)

    # for i,j in weights.items():
        # print(i,j)

    for item in items:
        if len(item['stats']) > 0 and not item['locked']:

            item_options, item_paths = get_item_options(item, gems, filtered_gems, enchants, caps, weights, include_gems)

            items_variations.append(item_options)
            items_paths.append(item_paths)

    return items_variations, items_paths

def get_item_options(item, gems, filtered_gems, enchants, caps, weights, include_gems):
    reforge_table = generate_reforge_table(item, caps, weights)

    item_options = []
    item_paths = []

    for src, dst_list in reforge_table.items():
        for dst in dst_list:

            variation_options, variation_paths = generate_item_reforge_option(item, caps, weights, src=src, dst=dst)

            variation_options, variation_paths = generate_item_socket_options(item, gems, filtered_gems, caps, weights, variation_options, variation_paths, include_gems)

            variation_options, variation_paths = generate_enchant_options(item, enchants, caps, weights, variation_options, variation_paths)

            for option, path in zip(variation_options, variation_paths):
                item_options.append(option)
                item_paths.append(path)

    filtered_item_options, filtered_item_paths = remove_duplicate_item_variations(item_options, item_paths)

    if len(item_options) > len(filtered_item_options):
        print(f"Removed {len(item_options) - len(filtered_item_options)} duplicates on item slot: {item['slotID']}\n  Before: {len(item_options)}\n  After:  {len(filtered_item_options)}")

    return filtered_item_options, filtered_item_paths
    # return item_options, item_paths

def generate_reforge_table(item, caps, weights):
    caps_list = [d["name"] for d in caps if "name" in d]
    item_stats = list(item['stats'].keys())

    result = {}

    first_stat = True
    for stat, value in item['stats'].items():
        result[stat] = []

        if first_stat:
            result[stat].append(None)
            first_stat = False

        #find the best dst for this src
        best_val = 0
        best_stat = None
        for weight_stat, weight_value in weights.items():
            if weight_stat in item_stats:
                continue

            if weight_value == weights[stat]:
                continue

            if weight_stat in unreforgable_stats:
                continue

            if weight_value < weights[stat] and weight_stat not in caps_list:
                continue

            if weight_value > best_val:
                best_val = weight_value
                best_stat = weight_stat

        if best_stat:
            result[stat].append(best_stat)

        for cap_stat in caps_list:
            if not cap_stat in item_stats:
                result[stat].append(cap_stat)

    return result

def generate_item_reforge_option(item, caps, weights, src=None, dst=None):
    caps_list = [d["name"] for d in caps if "name" in d]

    item_path = {
        "slotID": item['slotID'],
        "src": src,
        "dst": dst,
        "gems": [],
        "enchant": None,
        }

    item_variant = generate_empty_item_variation(caps)

    temp_item = copy.deepcopy(item)

    if src and dst:
        reforge_coeff = 0.4

        new_stat = floor(item['stats'][src] * reforge_coeff)
        temp_item['stats'][dst] = new_stat
        temp_item['stats'][src] -= new_stat

        for i, cap_stat in enumerate(caps_list):
            if src == cap_stat:
                item_variant[i] -= new_stat

            if dst == cap_stat:
                item_variant[i] += new_stat

    for stat, value in temp_item['stats'].items():
        item_variant[-1] += floor(value * weights[stat])

    return [item_variant], [item_path]

def generate_item_socket_options(item, gems, filtered_gems, caps, weights, variation_options, variation_paths, include_gems):
    if not include_gems:
        return variation_options, variation_paths

    item_sockets = []
    for color in item['sockets']:
        item_sockets.append(filtered_gems[color])

    if len(item_sockets) == 0:
        return variation_options, variation_paths

    # socket_combinations = unique_unordered_combinations(item_sockets)
    socket_combinations = cartesian_product(item_sockets)
    # print(item_sockets)

    socketed_item_variations = []
    socketed_item_paths = []

    for socket_combination in socket_combinations:
        socket_variation = generate_empty_item_variation(caps)

        socketed_item_path = copy.deepcopy(variation_paths[0])
        socketed_item_path['gems'] = socket_combination
        socketed_item_paths.append(socketed_item_path)

        for gem in socket_combination:
            for stat, value in gems[gem]['stats'].items():
                stat_idx = get_cap_stat_index(caps, stat)
                if get_cap_stat_index(caps, stat):
                    socket_variation[stat_idx] += value

                socket_variation[-1] += floor(value * weights[stat])

        # add item and sockets together
        socketed_item_variation = combine_item_variations(variation_options[0], socket_variation)
        #socketed_item_variation = [item_stat + socket_stat for item_stat, socket_stat in zip(variation_options[0], socket_variation)]

        socketed_item_variations.append(socketed_item_variation)

    return socketed_item_variations, socketed_item_paths

def unique_unordered_combinations(lists):
    seen = set()
    result = []

    # Generate all combinations (cartesian product)
    for combo in product(*lists):
        sorted_combo = tuple(sorted(combo))  # Make unordered by sorting

        if sorted_combo not in seen:
            seen.add(sorted_combo)
            result.append(list(sorted_combo))

    return result

def cartesian_product(socket_list):
    return [list(combo) for combo in product(*socket_list)]

def remove_duplicate_item_variations(variations, item_paths):
    unique_variations = []
    unique_item_paths = []

    for i, variation in enumerate(variations):
        if variation not in unique_variations:
            unique_variations.append(variation)
            unique_item_paths.append(item_paths[i])

    return unique_variations, unique_item_paths

def normalize_weights(weights):
    non_zero_weights = [v for v in weights.values() if v > 0]

    if not non_zero_weights:
        return weights

    min_non_zero = min(non_zero_weights)

    # Normalize, keeping 0 as 0.0
    return {
        k: (v / min_non_zero if v > 0 else 0.0)
        for k, v in weights.items()
    }

def generate_enchant_options(item, enchants, caps, weights, variation_options, variation_paths):
    # if there are no enchants for this slot
    if not str(item['slotID']) in enchants:
        return variation_options, variation_paths

    enchants = enchants[str(item['slotID'])]

    caps_list = [d["name"] for d in caps if "name" in d]

    # Find best scoring enchant + capping enchants
    enchant_variations = []
    enchants_used = []

    best_score = 0
    best_enchant_ID = None

    for enchant_ID, enchant_data in enchants.items():
        enchant_variant = []
        for i, cap_stat in enumerate(caps):
            enchant_variant.append(0)

        enchant_variant.append(0)

        enchant_stats = enchant_data['stats']

        enchant_score = 0
        for stat_name, stat_value in enchant_data['stats'].items():
            if stat_name in caps_list:
                stat_idx = caps_list.index(stat_name, 0)
                enchant_variant[stat_idx] += stat_value

            enchant_score += floor(stat_value * weights[stat_name])

        if not all(x==0 for x in enchant_variant):
            enchants_used.append(enchant_ID)
            enchant_variations.append(enchant_variant)


        if enchant_score > best_score:
            best_score = enchant_score
            best_enchant_ID = enchant_ID

    #append to temp variation
    if best_score > 0:
        enchant_variant = []
        for i, cap_stat in enumerate(caps):
            enchant_variant.append(0)

        enchant_variant.append(best_score)

        enchants_used.append(best_enchant_ID)
        enchant_variations.append(enchant_variant)

    item_variations = []
    item_paths = []

    if len(enchants_used) == 0:
        return variation_options, variation_paths

    for option, path in zip(variation_options, variation_paths):
        for enchant_variant, enchant_used in zip(enchant_variations, enchants_used):
            temp_option = copy.deepcopy(option)
            temp_path = copy.deepcopy(path)

            temp_option = [x + y for x, y in zip(temp_option, enchant_variant)]
            temp_path['enchant'] = enchant_used

            item_variations.append(temp_option)
            item_paths.append(temp_path)

    return item_variations, item_paths

def add_stat_equalities(item_stats, specID):

    return 1
