
def select_item_ids(items, list_1, list_2):
    socket_pairs = {
        "red": ["red", "orange", "purple"],
        "yellow": ["yellow", "orange", "green"],
        "blue": ["blue", "purple", "green"],
        "prismatic": ["red", "yellow", "blue", "orange", "green", "purple"]}

    filtered_gems = {}

    list2_index = {stat: i for i, stat in enumerate(list_2)}
    allowed_stats = set(list_1) | set(list_2)

    valid_items = {
        item_id: item
        for item_id, item in items.items()
        if set(item.get("stats", {}).keys()).issubset(allowed_stats)
    }

    for socket_color in socket_pairs:
        filtered_gems[socket_color] = set()

        # Step 1: Best item per stat in list_1
        for stat1 in list_1:
            best_item_id = None
            best_list2_index = float('inf')

            for item_id, item in valid_items.items():
                item_color = item['color']

                if item_color in socket_pairs[socket_color]:
                    stats = item.get("stats", {})
                    item_stats = set(stats.keys())

                    if stat1 in item_stats and any(s in list2_index for s in item_stats):
                        lowest_idx = min([list2_index[s] for s in item_stats if s in list2_index], default=float('inf'))
                        if lowest_idx < best_list2_index:
                            best_item_id = item_id
                            best_list2_index = lowest_idx

            if best_item_id:
                filtered_gems[socket_color].add(best_item_id)

        # Step 2: Best item that has only list_2 stats
        best_item_id = None
        best_index_sum = float('inf')

        for item_id, item in valid_items.items():
            item_color = item['color']

            if item_color in socket_pairs[socket_color]:
                stats = item.get("stats", {})
                item_stats = set(stats.keys())

                if all(stat in list_2 for stat in item_stats) and not any(stat in list_1 for stat in item_stats) and item_stats:
                    total_index = sum(list2_index[stat] for stat in item_stats)
                    if total_index < best_index_sum:
                        best_item_id = item_id
                        best_index_sum = total_index

        if best_item_id:
            filtered_gems[socket_color].add(best_item_id)

        # Step 3: All items with only stats from list_1
        for item_id, item in valid_items.items():
            item_color = item['color']

            if item_color in socket_pairs[socket_color]:
                stats = item.get("stats", {})
                item_stats = set(stats.keys())
                if item_stats and all(stat in list_1 for stat in item_stats):
                    filtered_gems[socket_color].add(item_id)

        filtered_gems[socket_color] = list(filtered_gems[socket_color])

    return filtered_gems
