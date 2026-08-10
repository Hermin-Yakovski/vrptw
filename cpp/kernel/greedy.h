#pragma once
#include <vector>
#include <utility>

struct GreedyResult {
    std::vector<std::pair<int,int>> edges;   // travel edges (i,j)
    std::vector<int> unserved;               // customer indices that couldn't be served
};

GreedyResult greedy_solve(
    const std::vector<double>& x,
    const std::vector<double>& y,
    const std::vector<double>& demand,
    const std::vector<double>& earliest,
    const std::vector<double>& latest,
    const std::vector<double>& service_time,
    double capacity);
