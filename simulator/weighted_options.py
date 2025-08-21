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

def get_items_options(items, gems, filtered_gems, enchants, caps, weights, include_gems=True):
    items_variations = []
    items_paths = []

    # filtered_weights = filter_stat_weights(weights)
    weights = normalize_weights(weights)

    # for i,j in weights.items():
        # print(i,j)

    for item in items:
        if len(item['stats']) > 0 and not item['locked']:
            item_options, item_paths = get_item_options(item, gems, filtered_gems, enchants,  caps, weights, include_gems)

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

    return filtered_item_options, filtered_item_paths
    # return item_options, item_paths

def generate_reforge_table(item, caps, weights):
    caps_list = [d["name"] for d in caps if "name" in d]

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
            if weight_stat in item['stats']:
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

        result[stat] += caps_list

    return result

def generate_item_reforge_option(item, caps, weights, src=None, dst=None):
    item_path = {
        "slotID": item['slotID'],
        "src": src,
        "dst": dst,
        "gems": [],
        "enchant": None,
        }

    item_variant = []

    caps_list = [d["name"] for d in caps if "name" in d]
    temp_item = copy.deepcopy(item)

    if src and dst:
        reforge_coeff = 0.4

        new_stat = floor(item['stats'][src] * reforge_coeff)
        temp_item['stats'][dst] = new_stat
        temp_item['stats'][src] -= new_stat

        for i, cap_stat in enumerate(caps_list):
            if src == cap_stat:
                item_variant.append(new_stat * -1)

            elif dst == cap_stat:
                item_variant.append(new_stat)

            else:
                item_variant.append(0)

    else:
        for i, cap_stat in enumerate(caps):
            item_variant.append(0)

    item_variant.append(0)

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
        return False, False

    socket_combinations = unique_unordered_combinations(item_sockets)

    socket_variations = []
    socket_paths = []
    for socket_combination in socket_combinations:
        socket_variant = []
        for i, cap_stat in enumerate(caps):
            socket_variant.append(0)

        socket_variant.append(0)

        temp_item_path = copy.deepcopy(variation_paths[0])
        temp_item_path['gems'] = socket_combination
        socket_paths.append(temp_item_path)

        for gem in socket_combination:
            for stat, value in gems[gem]['stats'].items():
                for i, cap_stat in enumerate(caps):
                    if cap_stat['name'] == stat:
                        socket_variant.append(value + variation_options[0][i])

                    socket_variant[-1] += floor(value * weights[stat]) + variation_options[0][-1]

        socket_variations.append(socket_variant)

    return socket_variations, socket_paths

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

def generate_enchant_options(enchants, caps, weights, variation_options, variation_paths):
    # if there are no enchants for this slot
    if not item['slotID'] in enchants:
        return variation_options, variation_paths

    enchants = enchants[item['slotID']]

    caps_list = [d["name"] for d in caps if "name" in d]

    # Find best scoring enchant
    # find the capping enchants

    for enchant, enchant_data in enchants.items():
        enchant_stats = enchant_data['stats']
        best_score = 0
        for stat_name, stat_value in enchant_stats:
            if stat_name in caps_list:
                stat_idx = stat_name.index(caps_list, 0)











    # template variant
    variant = []
    for i, cap_stat in enumerate(caps):
        variant.append(0)
    variant.append(0)

    enchant_variations = []
    enchants_used = []

    # temp_variant = copy.deepcopy(variant)

    best_enchant = copy.deepcopy(variant)
    for enchant, enchant_data in enchants.items():
        enchant_stats = enchant_data['stats']

        cap_enchant = False
        for i, cap_stat in enumerate(caps):
            if cap_stat in enchant_stats:
                cap_enchant = True


        if cap_enchant:

            continue












    for enchant, enchant_data in enchants.items():
        temp_variant = copy.deepcopy(variant)
        for i, cap_stat in enumerate(caps):
            enchant_variant[f"d{i+1}"] = 0

        enchant_variant['score'] = 0

        for stat, value in enchant_data['stats'].items():
            for i, cap_stat in enumerate(caps):
                if cap_stat['name'] == stat:
                    enchant_variant[f"d{i+1}"] = value
                    cap_enchant = True

                enchant_variant['score'] += floor(value * weights[stat])

    return enchant_variations, enchants_used


def combine_options(item, src, dst, reforge_option, socket_options, used_gems, enchant_options, used_enchants):
    item_path = {
        "slotID": item['slotID'],
        "src": src,
        "dst": dst,
        "gems": [],
        "enchant": None,
        }

    item_variations = []
    item_paths = []

    # this does not work because what if there are no enchants
    for socket_option, gems in zip(socket_options, used_gems):
        for enchant_option, enchant in zip(enchant_options, used_enchants):
            item_variation = reforge_option + socket_option + enchant_option

            temp_item_path = copy.deepcopy(item_path)

            temp_item_path['gems'] = gems
            temp_item_path['enchant'] = enchant

            item_variations.append(item_variation)
            item_paths.append(temp_item_path)

    return item_variations, item_paths
