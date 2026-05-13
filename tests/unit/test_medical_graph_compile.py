from backend.graph.builder import build_medical_evidence_graph


def test_medical_graph_compiles():
    g = build_medical_evidence_graph()
    assert g is not None
