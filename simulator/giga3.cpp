
#include <iostream>
#include <fstream>
#include <vector>
#include <unordered_map>
#include <string>
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
    std::unordered_map<U64, std::string>& out_sequences) 
{
    size_t num_caps = init_values.size();

    std::unordered_map<U64, int> scores;
    std::unordered_map<U64, std::string> sequences;

    U64 init_encoded_state = encode(init_values);
    scores[init_encoded_state] = 0;
    sequences[init_encoded_state] = "";

    int item_num = 1;
    int total_iterations = 0;
    for (const auto& item_opts : reforge_options) {

        std::unordered_map<U64, int> new_scores;
        std::unordered_map<U64, std::string> new_sequences;

        long total_inner = scores.size() * item_opts.size();
        long iterations = 0;
        
        std::cout << "item_number: " << item_num << "  iterations: " << total_inner << std::endl;
        item_num++;
        total_iterations = total_iterations + total_inner;

        for (const auto& [encoded_state, score] : scores) {
            const std::string& sequence = sequences[encoded_state];
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
                    new_score > new_scores[new_encoded_state]) {
                    new_scores[new_encoded_state] = new_score;
                    new_sequences[new_encoded_state] = sequence + static_cast<char>('1' + option_idx);
                }
                //iterations++;
            }
            //iterations = iterations + item_opts.size();
            //if (iterations % 1'000'000 == 0){
            //std::cout << iterations << " / " << total_inner << std::endl;
            //}
        }

        // Swap instead of copying → avoids allocations
        scores.swap(new_scores);
        sequences.swap(new_sequences);
    }
    
    
    std::cout << "total iterations: " << total_iterations << std::endl;

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
    for (auto& item : caps_json) {
        init_values.push_back(item["init"].get<int>());
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
    std::unordered_map<U64, std::string> sequences;
    compute_reforge_core(init_values, reforge_options, scores, sequences);

    // Find best score
    int max_score = std::numeric_limits<int>::min();
    std::string best_seq;
    for (const auto& [state, score] : scores) {
        if (score > max_score) {
            max_score = score;
            best_seq = sequences[state];
        }
    }

    std::cout << "Max score: " << max_score << "\n";
    std::cout << "Best sequence: " << best_seq << "\n";

    return 0;
}
