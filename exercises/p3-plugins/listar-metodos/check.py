from qiskit.transpiler.passes.synthesis.plugin import (
    high_level_synthesis_plugin_names,
    unitary_synthesis_plugin_names,
)
from qiskit.transpiler.preset_passmanagers.plugin import list_stage_plugins

from qgcheck import learner, visible


def names(value):
    return sorted(value) if isinstance(value, (list, tuple, set)) else value


@visible("`clifford_metodos` lista los métodos para sintetizar un Clifford")
def test_clifford():
    got = names(learner.clifford_metodos)
    assert got == sorted(high_level_synthesis_plugin_names("clifford")), f"`clifford_metodos` vale {got}."


def test_unitary():
    got = names(learner.unitaria_metodos)
    assert got == sorted(unitary_synthesis_plugin_names()), f"`unitaria_metodos` vale {got}."


def test_routing():
    got = names(learner.routing_metodos)
    assert got == sorted(list_stage_plugins("routing")), f"`routing_metodos` vale {got}."
