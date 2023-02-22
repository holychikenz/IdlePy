#include <random>
#include <iostream>
#include <string>
#include <functional>
#include <fstream>
#include <vector>

extern "C" {
std::default_random_engine engine;
std::uniform_int_distribution<int> fish_dist(0, 10);
std::uniform_int_distribution<int> low_bases(1, 5);
std::uniform_int_distribution<int> base_delta(0, 11);
std::uniform_int_distribution<int> zones(0,4);
std::vector<int> zone_values{1, 20, 50, 65, 85};
std::uniform_real_distribution<double> reals(0, 1);

auto randy = std::bind(reals, engine);
auto base = std::bind(low_bases, engine);
auto base_up = std::bind(base_delta, engine);
auto zone = std::bind(zones, engine);
auto fishy = std::bind(fish_dist, engine);

double calc_resources(int zone_level, int min_base, int max_base, double fishing_level, double bait_power, int trials){
    // zone_levels: N(1:100)
    // min_base: N(1:10)
    // max_base: N(2:20)
    // fishing_level: U(1:500)
    // bait_power: U(1:500)
    double total_resources = 0;
    for(int i=0; i<trials; i++){
        double max_node = floor(max_base + (randy() * (fishing_level-zone_level)/8) + floor(randy()*bait_power/20));
        double min_node = floor(min_base + (randy() * (fishing_level-zone_level)/6) + floor(randy()*bait_power/10));

        double lucky_chance = 0.05 + (bait_power / 2000);
        if( randy() <= lucky_chance ){
            min_node *= 1.5;
            max_node *= 3.0;
        }

        double delta = abs(min_node - max_node);
        double small = std::min(min_node, max_node);
        total_resources += floor(randy()*(delta + 1) + small);
    }
    return total_resources / trials;
}

double average_trials(double base_chance, int zone_level, int min_base, int max_base, double fishing_level,
                      double bait_power, int fishing, int nodes) {
    double total_tries = 0;
    for(int i=0; i<nodes; i++){
        double node_resources = calc_resources(zone_level, min_base, max_base, fishing_level, bait_power, 1);
        while(node_resources > 0){
            total_tries++;
            if(randy() < (base_chance + fishing*0.025 + node_resources/48)){
                node_resources--;
            }
        }
    }
    return total_tries / nodes;
}
}
