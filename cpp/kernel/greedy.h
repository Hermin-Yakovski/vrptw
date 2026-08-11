#pragma once
#include <vector>
#include <utility>

using namespace std;

struct GreedyResult {
    vector<pair<int,int>> edges;   // travel edges (i,j)
    vector<int> unserved;          // customer indices that couldn't be served
};

GreedyResult greedy_solve(
    const vector<double>& x,
    const vector<double>& y,
    const vector<double>& demand,
    const vector<double>& earliest,
    const vector<double>& latest,
    const vector<double>& service_time,
    double capacity);
