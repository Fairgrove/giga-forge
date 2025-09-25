import gc
from tqdm import tqdm
import time
import json
from itertools import product
import os

# modules
from weighted_options import get_items_options as weighted_get_items_options
from weighted_gem_filtering import filter_gems as weighted_filter_gems
# from priority_options import get_items_options as priority_get_items_options
# from priority_gem_filtering import filter_gems as priority_filter_gems

spell_haste_specs = {0,}

def load_data(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)

    return data

def get_init_cap_values(items, caps):
    cap_stats = [d["name"] for d in caps if "name" in d]

    result = {}

    for cap_stat in cap_stats:
        result[cap_stat] = 0

        for item in items:
            if cap_stat in item['stats']:
                result[cap_stat] += item['stats'][cap_stat]


    return result

def set_init_cap_values(items, caps, raid_buffs, specID):
    init_values = get_init_cap_values(items, caps)

    caps_with_init_values = caps.copy()

    for init_stat, init_stat_value in init_values.items():
        for cap in caps_with_init_values:
            if cap['name'] == init_stat:
                cap['init'] = init_stat_value

    return caps_with_init_values

def funii():
    for cap in caps_with_init_values:
        # is stat a raidbuff
        if not cap['name'] in raid_buffs:
            continue

        # is that raidbuff enabled
        if not raid_buffs[cap['name']]['enabled']:
            continue

        if not cap['name'] == 'ITEM_MOD_HASTE_RATING':
            cap['init'] += raid_buffs[cap['name']]['value']
            continue

        if cap['name'] == 'ITEM_MOD_HASTE_RATING' and specID in spell_haste_specs:
            cap['init'] += raid_buffs[cap['name']]['value']


if __name__ == "__main__":
    character_data = load_data('items.json')
    items_json = character_data['items']
    stats = load_data('stat_prio.json')
    gems_json = load_data('gems.json')
    enchants_json = load_data('enchants.json')

    pre_init_caps = stats['caps']
    raid_buffs = stats['raid_buffs']
    stat_prio = stats['stat_prio']
    stat_weights = stats['stat_weights']

    caps = set_init_cap_values(items_json, pre_init_caps, raid_buffs, character_data['specID'])
    caps_list = [d["name"] for d in caps if "name" in d]

    filtered_gems = weighted_filter_gems(items_json, gems_json, caps, stat_weights)
    options, item_paths = weighted_get_items_options(items_json, gems_json, filtered_gems, enchants_json, caps, stat_weights, include_gems=True)

    # sorting hightest to lowest
    item_paths = sorted(item_paths, key=len, reverse=True)
    options = sorted(options, key=len, reverse=True)
    print(caps)
    # --- OUTPUT ---
    print('writing output')
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    path = os.path.join(output_dir, 'options.json')
    with open(path, 'w') as f:
        json.dump(options, f, indent=2)

    path = os.path.join(output_dir, 'caps.json')
    with open(path, 'w') as f:
        json.dump(caps, f, indent=2)

    path = os.path.join(output_dir, 'paths.json')
    with open(path, 'w') as f:
        json.dump(item_paths, f, indent=2)

