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

            reforge_option = generate_item_reforge_option(item, caps, weights, src=src, dst=dst)

            if include_gems:
                socket_options, used_gems = generate_item_socket_options(item, gems, filtered_gems, caps, weights)

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

            else:
                item_path = {
                    "slotID": item['slotID'],
                    "src": src,
                    "dst": dst,
                    "gems": [],
                    }

                item_paths.append(item_path)
                item_options.append(reforge_option)

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

        for cap_stat in caps_list:
            if not cap_stat in item_stats:
                result[stat].append(cap_stat)

    return result


def generate_item_reforge_option(item, caps, weights, src=None, dst=None):
    item_variant = {}

    caps_list = [d["name"] for d in caps if "name" in d]
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
        item_variant['score'] += floor(value * weights[stat])

    return item_variant

def generate_item_socket_options(item, gems, filtered_gems, caps, weights):
    # generate multi list of gems
    item_sockets = []
    for color in item['sockets']:
        item_sockets.append(filtered_gems[color])

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
            for stat, value in gems[gem]['stats'].items():
                for i, cap_stat in enumerate(caps):
                    if cap_stat['name'] == stat:
                        socket_variant[f"d{i+1}"] = value

                    socket_variant['score'] += floor(value * weights[stat])

        socket_variations.append(socket_variant)

    # filtered_variations, filtered_gems = remove_duplicate_socket_sums(socket_variations, socket_combinations)

    return socket_variations, socket_combinations

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

def generate_enchant_options(enchants, caps, weights):

    # template variant
    variant = {}
    for i, cap_stat in enumerate(caps):
        variant[f"d{i+1}"] = 0
    variant['score'] = 0

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

def apply_sockets(item_options, socket_options):
    return 0

def apply_enchants(item_options, enchant_options):
    return 0
