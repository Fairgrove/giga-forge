
#include <iostream>
#include <fstream>
#include <vector>
#include <unordered_map>
#include <string>
#include <limits>
#include "json.hpp"  // nlohmann/json

using json = nlohmann::json;
using U64 = uint64_t;

constexpr int NUM_BITS = 13; // adjust if caps can be bigger than ±32k
constexpr U64 MASK = (1ULL << NUM_BITS) - 1ULL;

// ---------------- Encode/Decode ----------------
U64 encode(const std::vector<int>& nums) {
    U64 result = 0;
    for (int num : nums) {
        U64 uval = static_cast<U64>(num) & MASK;
        result = (result << NUM_BITS) | uval;
    }
    return result;
}

std::vector<int> decode(U64 encoded, size_t n) {
    std::vector<int> nums(n);
    for (int i = static_cast<int>(n) - 1; i >= 0; --i) {
        U64 uval = encoded & MASK;
        encoded >>= NUM_BITS;
        if (uval & (1ULL << (NUM_BITS - 1))) {
            nums[i] = static_cast<int>(uval) - (1 << NUM_BITS);
        } else {
            nums[i] = static_cast<int>(uval);
        }
    }
    return nums;
}

// ---------------- Core Function ----------------
void compute_reforge_core(
    const std::vector<int>& init_values,
    const std::vector<std::vector<std::vector<int>>>& reforge_options,
    std::unordered_map<U64, int>& out_scores,
    std::unordered_map<U64, std::vector<int>>& out_sequences)
{
    size_t num_caps = init_values.size();
    size_t sequence_length = reforge_options.size();

    std::unordered_map<U64, int> scores;
    std::unordered_map<U64, std::vector<int>> sequences;

    U64 init_encoded_state = encode(init_values);
    scores[init_encoded_state] = 0;
    sequences[init_encoded_state] = std::vector<int>(sequence_length, 0); // preallocate
                                                                          //
    int item_num = 1;
    int total_iterations = 0;

    for (size_t step = 0; step < sequence_length; ++step) {
        const auto& item_opts = reforge_options[step];

        std::unordered_map<U64, int> new_scores;
        std::unordered_map<U64, std::vector<int>> new_sequences;

        long total_inner = scores.size() * item_opts.size();

        std::cout << "item_number: " << item_num << "  iterations: " << total_inner << std::endl;
        total_iterations = total_iterations + total_inner;


        for (const auto& [encoded_state, score] : scores) {
            const std::vector<int>& sequence = sequences[encoded_state];
            std::vector<int> state = decode(encoded_state, num_caps);

            for (size_t option_idx = 0; option_idx < item_opts.size(); ++option_idx) {
                const auto& option_data = item_opts[option_idx];
                std::vector<int> new_state(num_caps);

                for (size_t cap_idx = 0; cap_idx < num_caps; ++cap_idx) {
                    new_state[cap_idx] = state[cap_idx] + option_data[cap_idx];
                }

                U64 new_encoded_state = encode(new_state);
                int new_score = score + option_data.back();

                if (new_scores.find(new_encoded_state) == new_scores.end() ||
                    new_score > new_scores[new_encoded_state])
                {
                    new_scores[new_encoded_state] = new_score;

                    std::vector<int> new_sequence = sequence;
                    new_sequence[step] = static_cast<int>(option_idx + 1); // 1-based
                    new_sequences[new_encoded_state] = std::move(new_sequence);
                }
            }
        }

        scores.swap(new_scores);
        sequences.swap(new_sequences);

        item_num++;
    }

    out_scores = std::move(scores);
    out_sequences = std::move(sequences);
}

// ---------------- Main ----------------
int main() {
    // Load caps.json
    std::ifstream caps_file("output/caps.json");
    if (!caps_file) {
        std::cerr << "Error: could not open caps.json\n";
        return 1;
    }
    json caps_json;
    caps_file >> caps_json;

    std::vector<int> init_values;
    std::vector<int> targets;
    for (auto& item : caps_json) {
        init_values.push_back(item["init"].get<int>());
        targets.push_back(item["target"].get<int>());
    }

    // Load options.json
    std::ifstream options_file("output/options.json");
    if (!options_file) {
        std::cerr << "Error: could not open options.json\n";
        return 1;
    }
    json options_json;
    options_file >> options_json;

    std::vector<std::vector<std::vector<int>>> reforge_options =
        options_json.get<std::vector<std::vector<std::vector<int>>>>();

    // Compute
    std::unordered_map<U64, int> scores;
    std::unordered_map<U64, std::vector<int>> sequences;
    compute_reforge_core(init_values, reforge_options, scores, sequences);

    // Find best score meeting target caps
    int max_score = std::numeric_limits<int>::min();
    std::vector<int> best_sequence;

    for (const auto& [encoded_state, score] : scores) {
        std::vector<int> state = decode(encoded_state, init_values.size());

        bool meets_target = true;
        for (size_t i = 0; i < state.size(); ++i) {
            if (state[i] < targets[i]) {
                meets_target = false;
                break;
            }
        }

        if (meets_target && score > max_score) {
            max_score = score;
            best_sequence = sequences[encoded_state];
        }
    }

    if (max_score != std::numeric_limits<int>::min()) {
        std::cout << "Max score: " << max_score << "\nSequence: ";
        for (int opt : best_sequence) std::cout << opt << "/";
        std::cout << "\n";

        // Decode the state of the best score
        U64 best_encoded_state = 0;
        for (const auto& [encoded_state, score] : scores) {
            std::vector<int> state = decode(encoded_state, init_values.size());
            bool meets_target = true;
            for (size_t i = 0; i < state.size(); ++i) {
                if (state[i] < targets[i]) {
                    meets_target = false;
                    break;
                }
            }
            if (meets_target && score == max_score) {
                best_encoded_state = encoded_state;
                break;
            }
        }

        std::vector<int> best_state = decode(best_encoded_state, init_values.size());

        // Print state
        std::cout << "State of best score: ";
        for (int val : best_state) std::cout << val << " ";
        std::cout << "\n";

        // --- JSON export ---
        json output;
        output["score"] = max_score;
        output["sequence"] = best_sequence;
        output["state"] = best_state;

        std::ofstream out_file("output/result.json");
        out_file << output.dump(4); // pretty-print with 4 spaces
        out_file.close();

        std::cout << "Best result written to best_result.json\n";

    } else {
        std::cout << "No state meets the target values.\n";
    }

    return 0;
}
