"""Tests for the GM/ALLE/SPEZIFISCH visibility filtering.

These cover the enforcement boundary between GM and player, so they are worth
keeping strict: every assertion here is something a player must not be able to
see. Pure functions, no database needed.
"""

import json

from app.entities.visibility import (
    filter_entities_for_viewer,
    filter_entity_for_viewer,
    filter_gegenstaende_for_viewer,
    filter_gegenstand_for_viewer,
    filter_graph_edges_for_viewer,
    filter_graph_nodes_for_viewer,
    filter_verbindungen_for_viewer,
    is_visible_to,
    redact_rich_text,
)

KIRA = "person-kira"
BOSS = "person-boss"


def entity(**overrides) -> dict:
    base = {
        "id": "e1",
        "name": "Testeintrag",
        "description": "",
        "notes": "",
        "sichtbarkeit": "ALLE",
        "sichtbarFuer": [],
        "notizenSichtbarkeit": "GM",
        "notizenSichtbarFuer": [],
    }
    return {**base, **overrides}


def doc(*texts_and_secrets) -> str:
    """Builds a TipTap document; pass (text, is_secret) pairs."""
    return json.dumps(
        {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": text, **({"marks": [{"type": "gmSecret"}]} if secret else {})}
                        for text, secret in texts_and_secrets
                    ],
                }
            ],
        }
    )


def texts_of(raw: str) -> list[str]:
    return [n["text"] for n in json.loads(raw)["content"][0]["content"]]


class TestIsVisibleTo:
    def test_gm_sees_everything(self):
        assert is_visible_to("GM", [], "GM", None)
        assert is_visible_to("SPEZIFISCH", [], "GM", None)

    def test_alle_is_public(self):
        assert is_visible_to("ALLE", [], "PLAYER", KIRA)

    def test_gm_only_is_hidden_from_players(self):
        assert not is_visible_to("GM", [], "PLAYER", KIRA)

    def test_spezifisch_only_for_listed_players(self):
        assert is_visible_to("SPEZIFISCH", [KIRA], "PLAYER", KIRA)
        assert not is_visible_to("SPEZIFISCH", [BOSS], "PLAYER", KIRA)

    def test_spezifisch_without_a_character_is_hidden(self):
        assert not is_visible_to("SPEZIFISCH", [KIRA], "PLAYER", None)

    def test_unknown_mode_fails_closed(self):
        assert not is_visible_to("VOELLIG_NEUER_MODUS", [], "PLAYER", KIRA)


class TestRedactRichText:
    def test_gm_keeps_secret_spans(self):
        raw = doc(("offen ", False), ("geheim", True))
        assert redact_rich_text(raw, "GM") == raw

    def test_player_loses_secret_spans(self):
        raw = doc(("offen ", False), ("geheim", True))
        assert texts_of(redact_rich_text(raw, "PLAYER")) == ["offen "]

    def test_legacy_plain_text_passes_through(self):
        assert redact_rich_text("altes Klartextfeld", "PLAYER") == "altes Klartextfeld"

    def test_empty_stays_empty(self):
        assert redact_rich_text("", "PLAYER") == ""

    def test_secret_nested_in_a_table_is_also_removed(self):
        raw = json.dumps(
            {
                "type": "doc",
                "content": [
                    {
                        "type": "table",
                        "content": [
                            {
                                "type": "tableRow",
                                "content": [
                                    {
                                        "type": "tableCell",
                                        "content": [
                                            {
                                                "type": "paragraph",
                                                "content": [
                                                    {"type": "text", "text": "sichtbar"},
                                                    {
                                                        "type": "text",
                                                        "text": "Codewort",
                                                        "marks": [{"type": "gmSecret"}],
                                                    },
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )
        assert "Codewort" not in redact_rich_text(raw, "PLAYER")
        assert "sichtbar" in redact_rich_text(raw, "PLAYER")


class TestFilterEntity:
    def test_hidden_entity_becomes_none(self):
        assert filter_entity_for_viewer(entity(sichtbarkeit="GM"), "PLAYER", KIRA) is None

    def test_gm_sees_hidden_entity(self):
        assert filter_entity_for_viewer(entity(sichtbarkeit="GM"), "GM", None) is not None

    def test_notes_withheld_when_notes_visibility_is_gm(self):
        result = filter_entity_for_viewer(entity(notes="SL-Notiz"), "PLAYER", KIRA)
        assert result["notes"] == ""

    def test_notes_released_when_notes_visibility_allows(self):
        result = filter_entity_for_viewer(
            entity(notes="Für alle", notizenSichtbarkeit="ALLE"), "PLAYER", KIRA
        )
        assert result["notes"] == "Für alle"

    def test_notes_visibility_is_independent_of_entity_visibility(self):
        """An entity can be public while its notes stay GM-only."""
        result = filter_entity_for_viewer(
            entity(sichtbarkeit="ALLE", notes="geheim", notizenSichtbarkeit="GM"), "PLAYER", KIRA
        )
        assert result is not None
        assert result["notes"] == ""

    def test_secret_spans_stripped_from_description(self):
        result = filter_entity_for_viewer(
            entity(description=doc(("bekannt ", False), ("Hintergedanke", True))), "PLAYER", KIRA
        )
        assert texts_of(result["description"]) == ["bekannt "]

    def test_secret_spans_stripped_from_released_notes(self):
        result = filter_entity_for_viewer(
            entity(
                notes=doc(("harmlos ", False), ("brisant", True)),
                notizenSichtbarkeit="ALLE",
            ),
            "PLAYER",
            KIRA,
        )
        assert texts_of(result["notes"]) == ["harmlos "]

    def test_input_is_not_mutated(self):
        original = entity(notes="SL-Notiz")
        filter_entity_for_viewer(original, "PLAYER", KIRA)
        assert original["notes"] == "SL-Notiz"

    def test_legacy_node_without_visibility_fields_stays_hidden(self):
        """Nodes predating the visibility model must fail closed, not leak."""
        legacy = {"id": "old", "name": "Alteintrag", "description": "", "notes": ""}
        assert filter_entity_for_viewer(legacy, "PLAYER", KIRA) is None
        assert filter_entity_for_viewer(legacy, "GM", None) is not None

    def test_null_visibility_fields_stay_hidden(self):
        """Neo4j returns None for a property that was never written."""
        nulled = entity(sichtbarkeit=None, sichtbarFuer=None)
        assert filter_entity_for_viewer(nulled, "PLAYER", KIRA) is None

    def test_list_drops_hidden_entries(self):
        entities = [
            entity(id="a", sichtbarkeit="ALLE"),
            entity(id="b", sichtbarkeit="GM"),
            entity(id="c", sichtbarkeit="SPEZIFISCH", sichtbarFuer=[KIRA]),
            entity(id="d", sichtbarkeit="SPEZIFISCH", sichtbarFuer=[BOSS]),
        ]
        visible = filter_entities_for_viewer(entities, "PLAYER", KIRA)
        assert [e["id"] for e in visible] == ["a", "c"]


class TestFilterGegenstand:
    """Item notes are GM-only wholesale: items have no notizenSichtbarkeit."""

    def item(self, **overrides) -> dict:
        base = {
            "id": "i1",
            "name": "Pistole",
            "description": "",
            "notes": "",
            "sichtbarkeit": "SPEZIFISCH",
            "sichtbarFuer": [KIRA],
        }
        return {**base, **overrides}

    def test_owner_sees_their_item(self):
        assert filter_gegenstand_for_viewer(self.item(), "PLAYER", KIRA) is not None

    def test_other_player_does_not(self):
        assert filter_gegenstand_for_viewer(self.item(), "PLAYER", BOSS) is None

    def test_notes_are_withheld_from_players(self):
        result = filter_gegenstand_for_viewer(self.item(notes="Ist in Wahrheit verwanzt"), "PLAYER", KIRA)
        assert result["notes"] == ""

    def test_gm_keeps_item_notes(self):
        result = filter_gegenstand_for_viewer(self.item(notes="Ist in Wahrheit verwanzt"), "GM", None)
        assert result["notes"] == "Ist in Wahrheit verwanzt"

    def test_secret_spans_stripped_from_item_description(self):
        result = filter_gegenstand_for_viewer(
            self.item(description=doc(("eine Pistole ", False), ("mit Peilsender", True))), "PLAYER", KIRA
        )
        assert texts_of(result["description"]) == ["eine Pistole "]

    def test_template_without_owner_visibility_fails_closed(self):
        assert filter_gegenstaende_for_viewer([{"id": "t", "name": "Vorlage"}], "PLAYER", KIRA) == []


class TestFilterVerbindungen:
    def edge(self, **overrides) -> dict:
        base = {
            "id": "v1",
            "vonId": KIRA,
            "zuId": "ort-bar",
            "sichtbarkeit": "ALLE",
            "sichtbarFuer": [],
            "vonSichtbarkeit": "ALLE",
            "vonSichtbarFuer": [],
            "zuSichtbarkeit": "ALLE",
            "zuSichtbarFuer": [],
        }
        return {**base, **overrides}

    def test_public_edge_between_public_nodes_is_kept(self):
        assert filter_verbindungen_for_viewer([self.edge()], "PLAYER", KIRA) != []

    def test_hidden_edge_is_dropped(self):
        assert filter_verbindungen_for_viewer([self.edge(sichtbarkeit="GM")], "PLAYER", KIRA) == []

    def test_edge_to_hidden_target_is_dropped(self):
        """Otherwise a public connection announces the secret NPC behind it."""
        assert filter_verbindungen_for_viewer([self.edge(zuSichtbarkeit="GM")], "PLAYER", KIRA) == []

    def test_edge_from_hidden_source_is_dropped(self):
        assert filter_verbindungen_for_viewer([self.edge(vonSichtbarkeit="GM")], "PLAYER", KIRA) == []

    def test_edge_to_endpoint_specific_to_this_player_is_kept(self):
        edge = self.edge(zuSichtbarkeit="SPEZIFISCH", zuSichtbarFuer=[KIRA])
        assert filter_verbindungen_for_viewer([edge], "PLAYER", KIRA) != []

    def test_gm_keeps_everything(self):
        edges = [self.edge(sichtbarkeit="GM", zuSichtbarkeit="GM")]
        assert filter_verbindungen_for_viewer(edges, "GM", None) == edges


class TestFilterGraph:
    def test_hidden_nodes_are_dropped(self):
        nodes = [
            {"id": "a", "kind": "Person", "label": "Kira", "sichtbarkeit": "ALLE", "sichtbarFuer": []},
            {"id": "b", "kind": "Person", "label": "Mr. Chrome", "sichtbarkeit": "GM", "sichtbarFuer": []},
        ]
        assert [n["id"] for n in filter_graph_nodes_for_viewer(nodes, "PLAYER", KIRA)] == ["a"]

    def test_edges_to_dropped_nodes_are_dropped(self):
        edges = [{"id": "e", "source": "a", "target": "b", "sichtbarkeit": "ALLE", "sichtbarFuer": []}]
        assert filter_graph_edges_for_viewer(edges, {"a"}, "PLAYER", KIRA) == []

    def test_edges_between_surviving_nodes_are_kept(self):
        edges = [{"id": "e", "source": "a", "target": "b", "sichtbarkeit": "ALLE", "sichtbarFuer": []}]
        assert filter_graph_edges_for_viewer(edges, {"a", "b"}, "PLAYER", KIRA) != []

    def test_hidden_edge_between_visible_nodes_is_dropped(self):
        edges = [{"id": "e", "source": "a", "target": "b", "sichtbarkeit": "GM", "sichtbarFuer": []}]
        assert filter_graph_edges_for_viewer(edges, {"a", "b"}, "PLAYER", KIRA) == []
