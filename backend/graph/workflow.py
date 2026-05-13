from langgraph.graph import StateGraph, END
from backend.graph.state import GroundedGraphState
from backend.graph.nodes import retrieve_node, validate_node, generate_node, citation_node

def route_validation(state: GroundedGraphState) -> str:
    """Routes based on evidence validation."""
    if state.get("is_valid"):
        return "generate"
    else:
        return "fallback"

def build_grounded_workflow() -> StateGraph:
    """Builds the Phase 4 linear grounded workflow."""
    workflow = StateGraph(GroundedGraphState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("cite", citation_node)
    
    def fallback_node(state: GroundedGraphState):
        return {
            "generation": "I don't know based on the available evidence.",
            "citations": []
        }
        
    workflow.add_node("fallback", fallback_node)
    
    # Wire the edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "validate")
    
    workflow.add_conditional_edges(
        "validate",
        route_validation,
        {
            "generate": "generate",
            "fallback": "fallback"
        }
    )
    
    workflow.add_edge("generate", "cite")
    workflow.add_edge("cite", END)
    workflow.add_edge("fallback", END)
    
    return workflow.compile()
