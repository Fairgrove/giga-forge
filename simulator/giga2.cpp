
#include <iostream>
#include <fstream>
#include <vector>
#include <unordered_map>
#include <string>
//#include <nlohmann/json.hpp>
#include "json.hpp"  // nlohmann/json

using json = nlohmann::json;

// Encode a vector<int> state into a string (simple comma-separated)
std::string encode(const std::vector<int>& state) {
    std::string s;
    for (size_t i = 0; i < state.size(); i++) {
        s += std::to_string(state[i]);
        if (i != state.size() - 1) s += ",";
    }
    return s;
}

// Decode a string into vector<int>
std::vector<int> decode(const std::string& s) {
    std::vector<int> state;
    size_t start = 0, end;
    while ((end = s.find(',', start)) != std::string::npos) {
        state.push_back(std::stoi(s.substr(start, end - start)));
        start = end + 1;
    }
    state.push_back(std::stoi(s.substr(start)));
    return state;
}

// Main compute_reforge_core function
void compute_reforge_core(const std::vector<int>& init_values, const std::vector<std::vector<std::vector<int>>>& reforge_options,
                          std::unordered_map<std::string, int>& out_scores,
                          std::unordered_map<std::string, std::string>& out_sequences) {

    size_t num_caps = init_values.size();
    std::unordered_map<std::string, int> scores;
    std::unordered_map<std::string, std::string> sequences;

    std::vector<int> init_state = init_values;
    std::string init_encoded_state = encode(init_state);
    scores[init_encoded_state] = 0;
    sequences[init_encoded_state] = "";

    for (const auto& item_opts : reforge_options) {
        std::unordered_map<std::string, int> new_scores;
        std::unordered_map<std::string, std::string> new_sequences;
        
        long total_inner = scores.size() * item_opts.size();
        long iterations = 0;

        for (const auto& pair : scores) {
            const std::string& encoded_state = pair.first;
            int score = pair.second;
            const std::string& sequence = sequences[encoded_state];
            std::vector<int> state = decode(encoded_state);

            for (size_t option_idx = 0; option_idx < item_opts.size(); ++option_idx) {
                const auto& option_data = item_opts[option_idx];
                std::vector<int> new_state(num_caps);

                for (size_t cap_idx = 0; cap_idx < num_caps; ++cap_idx) {
                    new_state[cap_idx] = state[cap_idx] + option_data[cap_idx];
                }

                std::string new_encoded_state = encode(new_state);
                int new_score = score + option_data.back();

                if (new_scores.find(new_encoded_state) == new_scores.end() || new_score > new_scores[new_encoded_state]) {
                    new_scores[new_encoded_state] = new_score;
                    new_sequences[new_encoded_state] = sequence + static_cast<char>('1' + option_idx);
                }
            }
            iterations = iterations + item_opts.size();
            //if (iterations % 1'000'000 == 0){
                std::cout << iterations << " / " << total_inner << std::endl;
            //}

        }

        scores = std::move(new_scores);
        sequences = std::move(new_sequences);
    }

    out_scores = std::move(scores);
    out_sequences = std::move(sequences);
}

int main() {
    // Load caps.json
    std::ifstream caps_file("output/caps.json");
    json caps_json;
    caps_file >> caps_json;

    std::vector<int> init_values;
    for (auto& item : caps_json) {
        init_values.push_back(item["init"].get<int>());
    }

    // Load options.json
    std::ifstream options_file("output/options.json");
    json options_json;
    options_file >> options_json;

    std::vector<std::vector<std::vector<int>>> reforge_options = options_json.get<std::vector<std::vector<std::vector<int>>>>();

    std::unordered_map<std::string, int> scores;
    std::unordered_map<std::string, std::string> sequences;

    compute_reforge_core(init_values, reforge_options, scores, sequences);

    // Example: print max score
    int max_score = 0;
    std::string best_seq;
    for (const auto& pair : scores) {
        if (pair.second > max_score) {
            max_score = pair.second;
            best_seq = sequences[pair.first];
        }
    }

    std::cout << "Max score: " << max_score << "\nBest sequence: " << best_seq << "\n";
}
