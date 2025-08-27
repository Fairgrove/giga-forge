import json
import gc
import time
import os
from tqdm import tqdm

BITS = 18 # required bits for signed 99999
SIGN_BIT = 1 << (BITS - 1)
MASK = (1 << BITS) - 1

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
                    delta = o[cap_i]
                    new_val = state[cap_i] + delta # + floor(delta + random.random())
                    new_state.append(new_val)

                new_key = encode_bitwise(new_state)
                new_score = score + o[-1]

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

        return {'score': best_score, 'state': best_state, 'sequence': list(map(ord, best_code))}
    else:
        print("No valid solutions found that meet all cap targets.")

        return False


if __name__ == "__main__":
    caps = load_data('output/caps.json')
    options = load_data('output/options.json')

    print('computing reforges')
    scores, codes, diagnostics = compute_reforge_core(caps, options)

    print('finding best combination')
    valid_scores, valid_codes = enforce_cap_targets(scores, codes, caps)

    print('finding best option from valid combinations')
    best_option = get_best_score(valid_scores, valid_codes)

    for key, value in diagnostics.items():
        print(key, value)

    # --- OUTPUT ---
    print('writing output')
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    path = os.path.join(output_dir, 'result.json')
    with open(path, 'w') as f:
        json.dump(best_option, f, indent=2)
