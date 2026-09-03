"""Fachregeln für Kontaktwissen und automatische GESEHEN-Ermittlung."""

from app.kontakte.logic import (
    effektiver_alias,
    erreichbare_npcs,
    ist_mindestens_stufe,
    kontakt_anzeige,
    kann_kontakt_anfragen,
    normalisiere_nachrichteninhalt,
    standard_alias,
)

PC = "pc-1"
NPC = "npc-1"


def node(node_id: str, kind: str, **werte) -> dict:
    return {"id": node_id, "kind": kind, "sichtbarkeit": "ALLE", "sichtbarFuer": [], **werte}


def edge(edge_id: str, source: str, target: str, **werte) -> dict:
    return {"id": edge_id, "source": source, "target": target, "sichtbarkeit": "ALLE", "sichtbarFuer": [], **werte}


def test_standard_alias_kommt_aus_rasse_und_faellt_auf_person_zurueck():
    assert standard_alias("Ork") == "Unbekannter Ork"
    assert standard_alias("Mensch") == "Unbekannter Mensch"
    assert standard_alias("") == "Unbekannte Person"


def test_persoenlicher_alias_ueberschreibt_npc_standard():
    assert effektiver_alias("Unbekannter Ork", "Der Riese") == "Der Riese"
    assert effektiver_alias("Unbekannter Ork", "  ") == "Unbekannter Ork"
    assert effektiver_alias("", "") == "Unbekannte Person"


def test_stufen_koennen_nur_aufwaerts_verglichen_werden():
    assert ist_mindestens_stufe("GESPROCHEN", "GESEHEN")
    assert ist_mindestens_stufe("KONTAKT_AUSGETAUSCHT", "GESPROCHEN")
    assert not ist_mindestens_stufe("GESEHEN", "GESPROCHEN")


def test_graphweg_ist_ungerichtet_und_erreicht_npc():
    nodes = [node(PC, "Person", personType="PC"), node("ort", "Ort"), node(NPC, "Person", personType="NPC")]
    edges = [edge("e1", "ort", PC), edge("e2", NPC, "ort")]

    assert erreichbare_npcs(PC, nodes, edges) == {NPC}


def test_graphweg_endete_nach_sieben_kanten():
    nodes = [node(PC, "Person", personType="PC")]
    edges = []
    vorher = PC
    for i in range(1, 8):
        aktuell = f"knoten-{i}"
        nodes.append(node(aktuell, "Ort"))
        edges.append(edge(f"e-{i}", vorher, aktuell))
        vorher = aktuell
    nodes.append(node(NPC, "Person", personType="NPC"))
    edges.append(edge("e-8", vorher, NPC))

    assert erreichbare_npcs(PC, nodes, edges) == set()


def test_ort_oder_event_kann_die_weitergabe_stoppen():
    nodes = [
        node(PC, "Person", personType="PC"),
        node("ort", "Ort", kontaktwissenWeitergeben=False),
        node(NPC, "Person", personType="NPC"),
    ]
    edges = [edge("e1", PC, "ort"), edge("e2", "ort", NPC)]

    assert erreichbare_npcs(PC, nodes, edges) == set()


def test_unsichtbare_kante_zaehlt_nicht_als_kontaktweg():
    nodes = [node(PC, "Person", personType="PC"), node(NPC, "Person", personType="NPC")]
    edges = [edge("e1", PC, NPC, sichtbarkeit="GM")]

    assert erreichbare_npcs(PC, nodes, edges) == set()


def test_bereits_sichtbarer_npc_wird_auch_ueber_sieben_kanten_erreicht():
    nodes = [node(PC, "Person", personType="PC"), node(NPC, "Person", personType="NPC")]
    edges = [edge("e1", PC, NPC)]

    assert erreichbare_npcs(PC, nodes, edges, max_kanten=1) == {NPC}


def test_eigener_pc_startet_auch_bei_gm_sichtbarkeit_eine_suche():
    nodes = [
        node(PC, "Person", personType="PC", sichtbarkeit="GM"),
        node(NPC, "Person", personType="NPC", sichtbarkeit="ALLE"),
    ]
    edges = [edge("e1", PC, NPC, sichtbarkeit="ALLE")]

    assert erreichbare_npcs(PC, nodes, edges, viewer_person_id=PC) == {NPC}


def test_kontakt_anzeige_enthaelt_echten_namen_nur_nach_freigabe():
    unbekannt = kontakt_anzeige("Mara Voss", "Unbekannte Person", "Die Rote", False)
    bekannt = kontakt_anzeige("Mara Voss", "Unbekannte Person", "Die Rote", True)

    assert unbekannt["alias"] == "Die Rote"
    assert unbekannt["echterName"] is None
    assert bekannt["echterName"] == "Mara Voss"


def test_kontaktanfrage_erst_ab_gesprochen():
    assert not kann_kontakt_anfragen("GESEHEN", "KEINE")
    assert kann_kontakt_anfragen("GESPROCHEN", "KEINE")
    assert not kann_kontakt_anfragen("KONTAKT_AUSGETAUSCHT", "ANGENOMMEN")


def test_klartext_wird_emoji_erhaltend_als_tiptap_absatz_verpackt():
    inhalt = "Treffen wir uns? 👩🏽‍🚀"
    gespeichert = normalisiere_nachrichteninhalt(inhalt)

    assert "👩🏽‍🚀" in gespeichert
    assert '"type": "doc"' in gespeichert
    assert '"type": "paragraph"' in gespeichert


def test_tiptap_json_bleibt_unveraendert():
    inhalt = '{"type":"doc","content":[{"type":"paragraph"}]}'

    assert normalisiere_nachrichteninhalt(inhalt) == inhalt
