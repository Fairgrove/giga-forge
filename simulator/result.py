import json
import math
from tabulate import tabulate

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

stat_name_translations = {
        "ITEM_MOD_EXPERTISE_RATING": "Expertise",
        "ITEM_MOD_HIT_RATING": "Hit",
        "ITEM_MOD_CRIT_RATING": "Crit",
        "ITEM_MOD_HASTE_RATING": "Haste",
        "ITEM_MOD_MASTERY_RATING_SHORT": "Mastery",
        "ITEM_MOD_DODGE_RATING": "Dodge",
        "ITEM_MOD_PARRY_RATING": "Parry",
        "ITEM_MOD_SPIRIT_SHORT": "Spirit",
        "ITEM_MOD_INTELLECT_SHORT": "Intellect",
        "ITEM_MOD_AGILITY_SHORT": "Agility",
        "ITEM_MOD_STRENGTH_SHORT": "Strength",
        "ITEM_MOD_STAMINA_SHORT": "Stamina",
        "power": "power",
        "resilience": "resil"
        }

def load_data(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)

    return data

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

def print_item_table(data):
    table = []
    for item in data:
        #gems = '\n'.join(item['gems']) if item['gems'] else '-'
        gems = ""
        for gemID in item['gems']:
            gems += f"{gems_json[gemID]['name']}({gems_json[gemID]['color']})\n"
        gems_stats  = ""
        for gemID in item['gems']:
            temp = ""
            for gem_stat_name, gem_stat_value in gems_json[gemID]['stats'].items():
                temp += f"{stat_name_translations[gem_stat_name]}  {gem_stat_value}, "

            gems_stats += temp + "\n"

        table.append([
            f"{slotID_translations[item['slotID']]} ({item['slotID']})",
            gems,
            gems_stats,
            enchants_json[str(item['slotID'])][item['enchant']]['name'] if item['enchant'] else '-',
            stat_name_translations[item['src']],
            stat_name_translations[item['dst']] if item['dst'] else '-',
        ])
    headers = ['Slot', 'Gem', 'Gem Stats', 'Enchant', 'Src', 'Dst']
    print(tabulate(table, headers=headers, tablefmt='grid'))

def generate_before_after(items, gems, enchants, paths):
    stats_before = {}

    for stat in stat_name_translations:
        stats_before[stat] = 0

    for item in items:
        for stat, value in item['stats'].items():
            stats_before[stat] += value

    stats_after = stats_before.copy()

    for path in paths:
        item = get_item_by_ID(items, path['slotID'])
        src = path['src']
        dst = path['dst']

        # reforging
        if dst:
            new_stat = math.floor(item['stats'][src] * 0.4)

            stats_after[src] -= new_stat
            stats_after[dst] += new_stat

        # gemming
        for gemID in path['gems']:
            for stat, value in gems[gemID]['stats'].items():
                stats_after[stat] += value

        # enchanting
        slotID_str = str(path['slotID'])
        if slotID_str in enchants:
            enchant_slot = enchants[slotID_str]
            enchant = enchant_slot[path['enchant']]['stats']

            for stat, value in enchant.items():
                stats_after[stat] += value

    headers = ["Stat", "Before","After","Delta"]
    table = []
    for stat in stats_before:
        if stats_after[stat] > 0:
            translated_stat = stat_name_translations[stat]
            table.append([translated_stat, stats_before[stat], stats_after[stat], stats_after[stat] - stats_before[stat]])
            # print(f"{translated_stat:<12} {stats_before[stat]:<4} -> {stats_after[stat]:<5} ({stats_after[stat] - stats_before[stat]})")

    print(tabulate(table, headers=headers, tablefmt='grid'))

def get_item_by_ID(items, slotID):
    for item in items:
        if item['slotID'] == slotID:
            return item

    return None

def print_items(result, items):
    for i in result:
        for j,v in i.items():
            print(j, v)

        for j, v in get_item_by_ID(items_json, i['slotID'])['stats'].items():
            print(f"   {j} {v}")
        print()

if __name__ == "__main__":
    character_data = load_data('items.json')
    items_json = character_data['items']
    stats = load_data('stat_prio.json')
    gems_json = load_data('gems.json')
    enchants_json = load_data('enchants.json')

    item_paths = load_data('output/paths.json')
    options = load_data('output/result.json')

    options_unfiltered = load_data('output/options.json')

    result = []
    for i, option in enumerate(options['sequence']):
        item_path = item_paths[i][option-1]
        result.append(item_path)

    generate_before_after(items_json, gems_json, enchants_json, result)
    print()
    addon_input = generate_addon_output(result, items_json)
    print_item_table(result)
    print("---:Paste this in the reforging window:---")
    print(addon_input)
