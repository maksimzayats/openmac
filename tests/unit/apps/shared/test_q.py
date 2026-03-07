from __future__ import annotations

import pytest

from openmac.apps.shared.filterer import Q


def test_q_defaults_to_an_empty_and_node() -> None:
    query = Q()

    assert not query
    assert len(query) == 0
    assert list(query) == []
    assert query.connector == Q.AND
    assert query.negated is False


def test_q_sorts_keyword_children_and_tracks_referenced_fields() -> None:
    query = Q(z__exact=3, a=1, m__contains="x")

    assert query.children == [("a", 1), ("m__contains", "x"), ("z__exact", 3)]
    assert query.referenced_base_fields == {"a", "m", "z"}
    assert repr(query) == "Q(('a', 1), ('m__contains', 'x'), ('z__exact', 3))"


def test_q_combines_with_and_and_flattens_same_connector() -> None:
    combined = Q(a=1) & (Q(b=2) & Q(c=3))

    assert combined.connector == Q.AND
    assert combined.negated is False
    assert combined.children == [("a", 1), ("b", 2), ("c", 3)]


def test_q_keeps_nested_node_when_connector_changes() -> None:
    combined = Q(a=1) | (Q(b=2) & Q(c=3))

    assert combined.connector == Q.OR
    assert combined.children[0] == ("a", 1)
    assert combined.children[1] == (Q(b=2) & Q(c=3))


def test_q_supports_xor_connector() -> None:
    combined = Q(a=1) ^ Q(b=2)

    assert combined.connector == Q.XOR
    assert combined.children == [("a", 1), ("b", 2)]
    assert repr(combined) == "Q(('a', 1), ('b', 2), _connector='XOR')"


def test_q_combining_with_empty_query_returns_a_copy() -> None:
    original = Q(a=1)

    left = Q() & original
    right = original | Q()

    assert left == original
    assert right == original
    assert left is not original
    assert right is not original

    left.add(("b", 2), Q.AND)

    assert original.children == [("a", 1)]
    assert left.children == [("a", 1), ("b", 2)]


def test_q_invert_returns_a_negated_copy() -> None:
    original = Q(a=1)

    negated = ~original

    assert original.negated is False
    assert negated.negated is True
    assert negated.children == [("a", 1)]
    assert negated.deconstruct() == (
        "openmac.apps.shared.filterer.Q",
        (("a", 1),),
        {"_negated": True},
    )


def test_q_add_wraps_existing_children_when_switching_connector() -> None:
    query = Q(a=1)

    query.add(Q(b=2), Q.OR)

    assert query.connector == Q.OR
    assert query.children == [Q(a=1), Q(b=2)]


def test_q_flatten_yields_nested_queries_and_values_depth_first() -> None:
    inner = Q(a=1)
    outer = Q(inner, payload={"ids": [1, 2]})

    flattened = list(outer.flatten())

    assert flattened == [outer, inner, 1, {"ids": [1, 2]}]


def test_q_identity_normalizes_hashable_values() -> None:
    first = Q(meta={"ids": [1, 2]}, tags={"b", "a"})
    second = Q(meta={"ids": [1, 2]}, tags={"a", "b"})

    assert first == second
    assert hash(first) == hash(second)


def test_q_referenced_base_fields_include_nested_queries() -> None:
    query = Q(Q(user__id=1), status__in={"open", "closed"})

    assert query.referenced_base_fields == {"user", "status"}


def test_q_create_supports_non_default_state() -> None:
    query = Q.create(connector=Q.OR, negated=True)

    assert query.connector == Q.OR
    assert query.negated is True
    assert query.deconstruct() == (
        "openmac.apps.shared.filterer.Q",
        (),
        {"_connector": Q.OR, "_negated": True},
    )


def test_q_rejects_unknown_connector() -> None:
    with pytest.raises(ValueError, match="Unsupported Q connector: NAND"):
        Q(_connector="NAND")


def test_q_rejects_non_q_binary_operations() -> None:
    query = Q(a=1)

    with pytest.raises(TypeError):
        _ = query & 1

    with pytest.raises(TypeError):
        _ = query | 1

    with pytest.raises(TypeError):
        _ = query ^ 1


def test_q_internal_combine_requires_a_conditional_operand() -> None:
    class NonConditional:
        conditional = False

    with pytest.raises(TypeError):
        Q(a=1)._combine(NonConditional(), Q.AND)  # type: ignore[arg-type]


def test_q_non_q_equality_returns_false() -> None:
    assert (Q(a=1) == 1) is False


def test_q_hash_raises_for_unhashable_leaf_values() -> None:
    class UnhashableValue:
        __hash__ = None  # type: ignore[assignment]

    with pytest.raises(TypeError, match="Unhashable Q value"):
        hash(Q(value=UnhashableValue()))
