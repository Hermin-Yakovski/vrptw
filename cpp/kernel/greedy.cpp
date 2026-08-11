#include "greedy.h"
#include <cmath>
#include <set>
#include <limits>

GreedyResult greedy_solve(
    const vector<double>& x,
    const vector<double>& y,
    const vector<double>& demand,
    const vector<double>& earliest,
    const vector<double>& latest,
    const vector<double>& service_time,
    double capacity)
{
    int n = static_cast<int>(x.size());

    // Unvisited set: all customer indices except depot (index 0)
    set<int> unvisited;
    for (int c = 1; c < n; ++c)
        unvisited.insert(c);

    GreedyResult result;
    int current = 0;
    double load = 0.0;
    double time = earliest[0] + service_time[0];

    while (!unvisited.empty()) {
        int best = -1;
        double best_dist = numeric_limits<double>::infinity();

        for (int j : unvisited) {
            // Capacity check
            if (load + demand[j] > capacity) continue;

            // Manhattan distance
            double dist = abs(x[current] - x[j]) + abs(y[current] - y[j]);

            // Time window check
            double arrival = time + dist;
            if (arrival > latest[j]) continue;

            // Nearest so far
            if (dist < best_dist) {
                best = j;
                best_dist = dist;
            }
        }

        if (best >= 0) {
            // Visit customer best
            result.edges.emplace_back(current, best);
            double arrival = time + best_dist;
            time = max(arrival, earliest[best]) + service_time[best];
            load += demand[best];
            current = best;
            unvisited.erase(best);
        } else {
            // No feasible customer found
            if (current == 0) break;  // Already at depot — remaining are unservable
            result.edges.emplace_back(current, 0);
            current = 0;
            load = 0.0;
            time = earliest[0] + service_time[0];
        }
    }

    // Close last route
    if (current != 0)
        result.edges.emplace_back(current, 0);

    // Collect unserved customer indices
    for (int c : unvisited)
        result.unserved.push_back(c);

    return result;
}
