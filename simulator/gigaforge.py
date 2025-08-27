import gc
from tqdm import tqdm
import time
import json
from itertools import product

# modules
from weighted_options import get_items_options as weighted_get_items_options
from weighted_gem_filtering import filter_gems as weighted_filter_gems
# from priority_options import get_items_options as priority_get_items_options
# from priority_gem_filtering import filter_gems as priority_filter_gems

slotID_translations = {
        0: 'ammo',
        1: 'head',
        2: 'neck',
        3: 'shoulder',
        4: 'shirt',
        5: 'chest',
        6: 'waist',
        7: 'legs',
        8: 'feet',
        9: 'wrist',
        10: 'hands',
        11: 'finger 1',
        12: 'finger 2',
        13: 'trinket 1',
        14: 'trinket 2',
        15: 'back',
        16: 'main hand',
        17: 'off hand',
        18: 'ranged',
        }

def load_data(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)

    return data

def encode_bitwise(numbers):
    result = 0
    for num in numbers:
        # Convert to two's complement form for negative numbers
        if num < 0:
            num = (1 << BITS) + num  # e.g., -1 → (2^18) - 1
        result = (result << BITS) | (num & MASK)
    return result

def decode_bitwise(encoded, n):
    numbers = []
    for _ in range(n):
        num = encoded & MASK
        # Convert from two's complement back to signed
        if num & SIGN_BIT:
            num -= (1 << BITS)
        numbers.append(num)
        encoded >>= BITS
    return numbers[::-1]


def compute_reforge_core(caps, reforge_options):
    diagnostics = {
            'total_time': 0,
            'total_iterations':0
            }

    num_caps = len(caps)
    scores = {}
    codes = {}
    init_state = []

    for i in range(num_caps):
        val = caps[i]['init'] # floor(caps[i]['init'] + random.random())
        init_state.append(val)

    init_key = encode_bitwise(init_state)
    scores[init_key] = 0
    codes[init_key] = ""
    outer_pbar = tqdm(total=len(reforge_options), desc="Processing items", position=0, leave=True, dynamic_ncols=True)

    start_time = time.perf_counter()
    for i, item_opts in enumerate(reforge_options):
        # New progress bar for inner options (est total = #states * #options)
        total_inner = len(scores) * len(item_opts)
        inner_pbar = tqdm(total=total_inner, desc=f"Item {i+1} options", position=1, leave=False, dynamic_ncols=True)
        newscores = {}
        newcodes = {}

        diagnostics['total_iterations'] += total_inner
        diagnostics[f'item{i}'] = {
                'iterations': total_inner,
                }

        item_start_time = time.perf_counter()

        num_item_opts = len(item_opts)
        for key, score in scores.items():
            code = codes[key]
            state = decode_bitwise(key, num_caps)

            for j, o in enumerate(item_opts, 1):
                new_state = []

                for cap_i in range(num_caps):
                    delta = o.get(f'd{cap_i+1}', 0)
                    new_val = state[cap_i] + delta # + floor(delta + random.random())
                    new_state.append(new_val)

                new_key = encode_bitwise(new_state)
                new_score = score + o['score']

                # print(f"new key: {new_key}")
                # print(f"new score: {new_score}")
                # print(f"new state: {new_state}")

                if new_key not in newscores or new_score > newscores[new_key]:
                    newscores[new_key] = new_score
                    newcodes[new_key] = code + chr(j)

            inner_pbar.update(num_item_opts)

        scores, codes = newscores, newcodes

        gc.collect()

        inner_pbar.close()
        outer_pbar.update(1)

        item_end_time = time.perf_counter()
        diagnostics[f'item{i}']['time'] = item_end_time - item_start_time

    outer_pbar.close()

    end_time = time.perf_counter()

    diagnostics['total_time'] = end_time - start_time

    return scores, codes, diagnostics

def enforce_cap_targets(scores, codes, caps):
    """
    Filter out solutions that do not meet all cap targets.
    """
    valid_solutions = {}
    valid_codes = {}

    for key in scores:
        state = decode_bitwise(key, len(caps))
        meets_all_caps = all(
            state[i] >= caps[i].get('target', 0) for i in range(len(caps))
        )
        if meets_all_caps:
            valid_solutions[key] = scores[key]
            valid_codes[key] = codes[key]

    return valid_solutions, valid_codes

def get_best_score(valid_scores, valid_codes):
    if valid_scores:
        best_key = max(valid_scores, key=lambda k: valid_scores[k])
        best_score = valid_scores[best_key]
        best_code = valid_codes[best_key]
        best_state = decode_bitwise(best_key, len(caps))

        print("\n=== BEST SOLUTION ===")
        for i, val in enumerate(best_state):
            print(f"{caps[i]['name']}: {val} (target {caps[i]['target']})")
        print(f"Total Score: {best_score}")
        print(f"Reforge Path: {list(map(ord, best_code))}")

        return {'key': best_key, 'score': best_score, 'code': best_code, 'state': best_state, 'path': list(map(ord, best_code))}
    else:
        print("No valid solutions found that meet all cap targets.")

        return False

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

def get_init_cap_values(items, caps):
    cap_stats = [d["name"] for d in caps if "name" in d]

    result = {}

    for cap_stat in cap_stats:
        result[cap_stat] = 0

        for item in items:
            if cap_stat in item['stats']:
                result[cap_stat] += item['stats'][cap_stat]

    return result

def set_init_cap_values(items, caps):
    init_values = get_init_cap_values(items, caps)

    caps_with_init_values = caps.copy()

    for init_stat, init_stat_value in init_values.items():
        for cap in caps_with_init_values:
            if cap['name'] == init_stat:
                cap['init'] = init_stat_value

    return caps_with_init_values

def generate_addon_output(item_paths, items):
    def is_reforge_valid(src, dst, item):
        if src == dst:
            return False

        if dst in item['stats'].keys():
            return False

        if src not in item['stats'].keys():
            return False

        return True

    statIds = [
                'ITEM_MOD_SPIRIT_SHORT',
                'ITEM_MOD_DODGE_RATING',
                'ITEM_MOD_PARRY_RATING',
                'ITEM_MOD_HIT_RATING',
                'ITEM_MOD_CRIT_RATING',
                'ITEM_MOD_HASTE_RATING',
                'ITEM_MOD_EXPERTISE_RATING',
                'ITEM_MOD_MASTERY_RATING_SHORT'
                ]

    all_possible_reforges = []
    for i, _ in enumerate(statIds):
        for j, _ in enumerate(statIds):
            all_possible_reforges.append({'src': statIds[i], 'dst':statIds[j]})

    result = []
    for item in items:
        if len(item['stats']) > 0:
            id = -1

            slotID = item['slotID']
            item_path = next((path for path in item_paths if path.get("slotID") == slotID), None)
            #print(slotID)
            #print(item_path)
            for reforge_option in all_possible_reforges:
                if item_path['dst'] == None:
                    result.append({slotID: -1})
                    break

                if is_reforge_valid(reforge_option['src'], reforge_option['dst'], item):
                    id += 1

                if reforge_option['src'] == item_path['src'] and reforge_option['dst'] == item_path['dst']:
                    result.append({slotID: id})

    return result

# =======GLOBALS=======
BITS = 18 # required bits for signed 99999
SIGN_BIT = 1 << (BITS - 1)
MASK = (1 << BITS) - 1
# =====================

if __name__ == "__main__":
    character_data = load_data('items.json')
    items_json = character_data['items']
    stats = load_data('stat_prio.json')
    gems_json = load_data('gems.json')
    enchants_json = load_data('enchants.json')

    pre_init_caps = stats['caps']
    stat_prio = stats['stat_prio']
    stat_weights = stats['stat_weights']

    caps = set_init_cap_values(items_json, pre_init_caps)
    caps_list = [d["name"] for d in caps if "name" in d]

    filtered_gems = weighted_filter_gems(items_json, gems_json, caps, stat_weights)
    options, item_paths = weighted_get_items_options(items_json, gems_json, filtered_gems, enchants_json, caps, stat_weights, include_gems=True)

    item_paths = sorted(item_paths, key=len, reverse=True)

    print('computing reforges')
    scores, codes, diagnostics = compute_reforge_core(caps, sorted(options, key=len, reverse=True))

    print('finding best combination')
    valid_scores, valid_codes = enforce_cap_targets(scores, codes, caps)

    print('finding best option from valid combinations')
    best_option = get_best_score(valid_scores, valid_codes)

    # === OUTPUT ===

    for key, value in diagnostics.items():
        print(key, value)

    result = []
    for i, option in enumerate(best_option['path']):
        item_path = item_paths[i][option-1]
        result.append(item_path)

        print(f"SLOT: {slotID_translations[item_path['slotID']]} ({item_path['slotID']})")
        print(f"from: {item_path['src']}\n  --> {item_path['dst']}")
        for gemID in item_path['gems']:
            print(f"   {gems_json[gemID]['name']}({gems_json[gemID]['color']}): {gems_json[gemID]['stats']}")
        print()

    addon_input = generate_addon_output(result, items_json)
    print(addon_input)
