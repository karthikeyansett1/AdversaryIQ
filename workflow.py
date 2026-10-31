"""Explicit LangGraph evaluation stages, with one bounded hosted agent execution."""
from typing import Any, TypedDict
from langgraph.graph import StateGraph, START, END
from cloud_agent import run_hosted_probe
from engine import validate_attack

class State(TypedDict, total=False):
    api_key: str
    case: dict[str, Any]
    attack: str
    mode: str
    model: str
    record: dict[str, Any]
    stages: list[str]


def validate(state: State) -> dict:
    validate_attack(state["attack"])
    return {"stages": ["validate"]}


def execute(state: State) -> dict:
    result = run_hosted_probe(state["api_key"], state["case"], state["attack"], state["mode"], state["model"])
    return {"record": result, "stages": state.get("stages", []) + ["hosted_agent"]}


def finalize(state: State) -> dict:
    record = dict(state["record"])
    record["graph_stages"] = state.get("stages", []) + ["report"]
    return {"record": record, "stages": record["graph_stages"]}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("validate", validate)
    graph.add_node("hosted_agent", execute)
    graph.add_node("report", finalize)
    graph.add_edge(START, "validate")
    graph.add_edge("validate", "hosted_agent")
    graph.add_edge("hosted_agent", "report")
    graph.add_edge("report", END)
    return graph.compile()


def evaluate(api_key: str, case: dict, attack: str, mode: str, model: str = "gpt-4.1-mini") -> dict:
    state = build_graph().invoke({"api_key": api_key, "case": case, "attack": attack, "mode": mode, "model": model})
    return state["record"]
