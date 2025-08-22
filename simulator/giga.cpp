
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <tuple>
#include <cstdint>
#include <algorithm>

#include <chrono>
#include <iomanip>

#include "json.hpp"  // nlohmann/json

using json = nlohmann::json;
using U64 = uint64_t;

constexpr int NUM_BITS = 13;
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
    for (int i = n - 1; i >= 0; --i) {
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

// ---------------- Load JSON ----------------
std::vector<int> load_init_values(const std::string& filename, const std::string& key) {
    std::ifstream f(filename);
    if (!f.is_open()) throw std::runtime_error("Cannot open file: " + filename);

    json j;
    f >> j;

    std::vector<int> init_values;
    for (auto& cap : j) {
        init_values.push_back(cap[key].get<int>()); // or "init" if you prefer
    }
    return init_values;
}

std::vector<std::vector<std::vector<int>>> load_reforge_options(const std::string& filename) {
    std::ifstream f(filename);
    if (!f.is_open()) throw std::runtime_error("Cannot open file: " + filename);

    json j;
    f >> j;

    std::vector<std::vector<std::vector<int>>> reforge_options;
    for (auto& item_opts : j) {
        std::vector<std::vector<int>> options_for_item;
        for (auto& option : item_opts) {
            options_for_item.push_back(option.get<std::vector<int>>());
        }
        reforge_options.push_back(options_for_item);
    }
    return reforge_options;
}

// ---------------- BestResult struct ----------------
struct BestResult {
    std::vector<int> state;
    int score = INT32_MIN;
    std::string sequence;
};

// ---------------- Simulation ----------------
BestResult compute_reforge_core(const std::vector<int>& init_values,
                                const std::vector<std::vector<std::vector<int>>>& reforge_options)
{
    const size_t num_caps = init_values.size();
    BestResult best;

    std::vector<std::tuple<U64, int, std::string>> current_states;
    current_states.emplace_back(encode(init_values), 0, "");

    for (const auto& item_opts : reforge_options) {
        std::vector<std::tuple<U64, int, std::string>> new_states;
    
        long total_inner = current_states.size() * item_opts.size();
        long iterations = 0;

        for (auto& [encoded_state, score, sequence] : current_states) {
            std::vector<int> state = decode(encoded_state, num_caps);

            for (size_t option_idx = 0; option_idx < item_opts.size(); ++option_idx) {
                const auto& option_data = item_opts[option_idx];
                std::vector<int> new_state(num_caps);

                for (size_t i = 0; i < num_caps; ++i) {
                    new_state[i] = state[i] + option_data[i];
                }

                int new_score = score + option_data.back();
                std::string new_sequence = sequence + static_cast<char>('1' + option_idx);

                // Check caps
                bool meets_caps = true;
                for (size_t i = 0; i < num_caps; ++i) {
                    if (new_state[i] < init_values[i]) {
                        meets_caps = false;
                        break;
                    }
                }

                if (meets_caps && new_score > best.score) {
                    best.state = new_state;
                    best.score = new_score;
                    best.sequence = new_sequence;
                }

                U64 new_encoded = encode(new_state);
                new_states.emplace_back(new_encoded, new_score, new_sequence);
                iterations++;
            }
            //iterations = iterations + item_opts.size();
            if (iterations % 10'000'000 == 0){
                std::cout << iterations << " / " << total_inner << std::endl;
            }
        }

        current_states = std::move(new_states);
    }

    return best;
}

// ---------------- Main ----------------
int main() {
    try {
        std::vector<int> init_values = load_init_values("output/caps.json", "init");
        std::vector<int> cap_values = load_init_values("output/caps.json", "target");
        std::vector<std::vector<std::vector<int>>> reforge_options = load_reforge_options("output/options.json");

        for (int v : init_values) std::cout << v << "\n";

        BestResult result = compute_reforge_core(init_values, reforge_options);

        std::cout << "Best score: " << result.score << "\n";
        std::cout << "Best sequence: " << result.sequence << "\n";
        std::cout << "Best state: ";
        for (int v : result.state) std::cout << v << " ";
        std::cout << "\n";
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
}
