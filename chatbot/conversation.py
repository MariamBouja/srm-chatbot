"""Conversation-level orchestration in front of the RAG pipeline.

Currently handles one stateful flow: agency lookup by region. Everything
else is passed straight through to chatbot.rag.answer_question() unchanged,
so the existing RAG behavior is not touched by this module.
"""
from chatbot.agencies import (
    agencies_for_region,
    format_agency_list,
    format_region_options_message,
    is_agency_question,
    list_regions,
    match_region,
)
from chatbot.rag import answer_question

PENDING_AGENCY_REGION = "agency_region"


def new_state():
    """A fresh, empty conversation state. Callers (Streamlit session_state,
    the CLI loop) own this dict and pass it back in on every turn."""
    return {"pending": None}


def _result(answer, sources=None, fallback=False, options=None):
    return {"answer": answer, "sources": sources or [], "fallback": fallback, "options": options}


def _agency_result(region_label):
    agencies = agencies_for_region(region_label)
    return _result(format_agency_list(region_label, agencies))


def handle_message(question, state):
    """Route one user message through the agency-clarification state
    machine, falling back to the normal RAG pipeline otherwise.

    `state` is a plain dict (see new_state()) mutated in place to track
    whether we're mid-clarification. Keeping it caller-owned instead of a
    module-level global means it stays scoped to one conversation, so
    concurrent Streamlit sessions don't leak state into each other.
    """
    if state.get("pending") == PENDING_AGENCY_REGION:
        region = match_region(question)
        if region:
            state["pending"] = None
            return _agency_result(region)

        # Still no recognizable region — re-ask instead of silently
        # dropping the clarification and answering something unrelated.
        return _result(
            "Je n'ai pas reconnu cette région. " + format_region_options_message(),
            options=list_regions(),
        )

    if is_agency_question(question):
        region = match_region(question)
        if region:
            return _agency_result(region)

        state["pending"] = PENDING_AGENCY_REGION
        return _result(format_region_options_message(), options=list_regions())

    return answer_question(question)
