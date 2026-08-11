#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "greedy.h"

namespace py = pybind11;

PYBIND11_MODULE(_greedy_cpp, m) {
    m.doc() = "C++ greedy nearest-neighbor VRPTW solver";

    py::class_<GreedyResult>(m, "GreedyResult")
        .def_readonly("edges", &GreedyResult::edges)
        .def_readonly("unserved", &GreedyResult::unserved);

    m.def("greedy_solve", &greedy_solve,
        "Run nearest-neighbor VRPTW heuristic.",
        py::arg("x"),
        py::arg("y"),
        py::arg("demand"),
        py::arg("earliest"),
        py::arg("latest"),
        py::arg("service_time"),
        py::arg("capacity"));
}
