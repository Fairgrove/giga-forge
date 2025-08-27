import json
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

if __name__ == "__main__":
    character_data = load_data('items.json')
    items_json = character_data['items']
    stats = load_data('stat_prio.json')
    gems_json = load_data('gems.json')
    enchants_json = load_data('enchants.json')

    item_paths = load_data('output/paths.json')
    options = load_data('output/result.json')

    result = []
    for i, option in enumerate(options['sequence']):
        item_path = item_paths[i][option-1]
        result.append(item_path)

        # print(f"SLOT: {slotID_translations[item_path['slotID']]} ({item_path['slotID']})")
        # print(f"from: {item_path['src']}\n  --> {item_path['dst']}")
        # for gemID in item_path['gems']:
            # print(f"   {gems_json[gemID]['name']}({gems_json[gemID]['color']}): {gems_json[gemID]['stats']}")
        # if item_path['enchant']:
            # enchant_name = enchants_json[str(item_path['slotID'])][item_path['enchant']]['name']
            # print(f"   {enchant_name}")
        # print()

    addon_input = generate_addon_output(result, items_json)
    print_item_table(result)
    print(addon_input)
