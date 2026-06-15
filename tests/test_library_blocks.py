"""Tests for embedded library-block definitions (plcopen/library_blocks.py).

The editor embeds the signatures of every library block a project uses into a
project-level <addData> payload so xml2st can type the _TMP temporaries it
emits for FUNCTION outputs without bundling any library of its own.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plcopen.library_blocks import extract_library_blocks  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


# --- extractor unit tests -------------------------------------------------

def test_no_payload_returns_empty():
    blocks = extract_library_blocks(os.path.join(FIXTURES, "current_dt_baseline.xml"))
    assert blocks == []


def test_nullary_function_return_type():
    blocks = extract_library_blocks(
        os.path.join(FIXTURES, "current_dt_with_payload.xml")
    )
    by_name = {b["name"]: b for b in blocks}
    assert "CURRENT_DT" in by_name
    cdt = by_name["CURRENT_DT"]
    assert cdt["type"] == "function"
    assert cdt["inputs"] == []
    assert cdt["outputs"] == [("OUT", "DT", "none")]
    assert cdt["extensible"] is False


def test_variadic_function_flag_and_generics():
    blocks = extract_library_blocks(os.path.join(FIXTURES, "variadic_sumn.xml"))
    by_name = {b["name"]: b for b in blocks}
    assert "SUMN" in by_name
    sumn = by_name["SUMN"]
    assert sumn["extensible"] is True
    assert sumn["outputs"] == [("OUT", "ANY_NUM", "none")]
    assert [i[1] for i in sumn["inputs"]] == ["ANY_NUM", "ANY_NUM"]


def test_missing_file_is_tolerated():
    assert extract_library_blocks("/nonexistent/path.xml") == []


# --- end-to-end transpile tests ------------------------------------------

def _compile(path):
    from xml2st import compile_xml_to_st

    return compile_xml_to_st(path)


def test_e2e_nullary_typed_from_payload():
    """CURRENT_DT (nullary, dangling output) is typed DT from the payload,
    instead of falling back to the illegal ANY that strucpp rejects."""
    st = _compile(os.path.join(FIXTURES, "current_dt_with_payload.xml"))
    assert st is not None
    assert "_TMP_CURRENT_DT" in st
    # the temp is declared DT, never ANY
    decl = next(l for l in st.splitlines() if "_TMP_CURRENT_DT" in l and "OUT :" in l)
    assert ": DT;" in decl
    assert ": ANY;" not in st


def test_e2e_baseline_is_any_without_payload():
    """Sanity: without the payload, the same block falls back to ANY."""
    st = _compile(os.path.join(FIXTURES, "current_dt_baseline.xml"))
    assert st is not None
    assert "_TMP_CURRENT_DT" in st and ": ANY;" in st


def test_e2e_variadic_keeps_all_inputs_and_resolves_type():
    """An embedded extensible function emits ALL connected inputs, and its
    generic ANY_NUM output resolves to the concrete connected type (INT)."""
    st = _compile(os.path.join(FIXTURES, "variadic_sumn.xml"))
    assert st is not None
    assert "_TMP_SUMN9000_OUT : INT;" in st
    assert "SUMN(a, b, c)" in st


def test_e2e_connected_sink_type_wins_over_definition():
    """A connected variable's type takes precedence over the embedded block
    definition's nominal return type.  MK_PTR is defined as returning ULINT,
    but its output is wired to a `POINTER TO INT` variable, so the temp must
    adopt POINTER TO INT (regression: ADR was emitting ULINT and breaking the
    downstream pointer assignment)."""
    st = _compile(os.path.join(FIXTURES, "output_sink_precedence.xml"))
    assert st is not None
    assert "_TMP_MK_PTR8000_OUT : POINTER TO INT;" in st
    assert "_TMP_MK_PTR8000_OUT : ULINT;" not in st
