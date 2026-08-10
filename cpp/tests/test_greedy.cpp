#include <cassert>
#include <iostream>
#include "greedy.h"

int main() {
    // 5-node instance: depot (0) + 4 customers, capacity=10
    // Expected: Route 1: 0->1->3->4->0, Route 2: 0->2->0
    std::vector<double> x =      {0, 1, 0, 2, 0};
    std::vector<double> y =      {0, 0, 1, 0, 2};
    std::vector<double> demand = {0, 4, 7, 3, 3};
    std::vector<double> earliest = {0, 0, 0, 30, 0};
    std::vector<double> latest =   {1000, 100, 100, 100, 100};
    std::vector<double> service =  {0, 10, 10, 1, 1};

    auto result = greedy_solve(x, y, demand, earliest, latest, service, 10.0);

    // Verify 6 edges: (0,1), (1,3), (3,4), (4,0), (0,2), (2,0)
    assert(result.edges.size() == 6);
    assert(result.edges[0] == std::make_pair(0, 1));
    assert(result.edges[1] == std::make_pair(1, 3));
    assert(result.edges[2] == std::make_pair(3, 4));
    assert(result.edges[3] == std::make_pair(4, 0));
    assert(result.edges[4] == std::make_pair(0, 2));
    assert(result.edges[5] == std::make_pair(2, 0));
    assert(result.unserved.empty());

    std::cout << "All C++ kernel tests passed." << std::endl;
    return 0;
}
