"""Tests für die Wiki-Fachlogik.

Reine Unit-Tests ohne Datenbank — dieselbe Bauart wie test_visibility.py.
Alles, was hier geprüft wird, ist bewusst frei von Neo4j: Inhaltsverzeichnis,
Verknüpfungserkennung, Sichtbarkeit und die "bis hierher freigeben"-Reihenfolge
sind Fachregeln, keine Datenbankfragen.
"""

import json

import pytest

from app.wiki.logic import (
    baum_bauen,
    inhaltsverzeichnis,
    seiten_bis_einschliesslich,
    verweise_sammeln,
)
from app.wiki.visibility import filter_seite_for_viewer, filter_seiten_for_viewer


def doc(*bloecke):
    return json.dumps({"type": "doc", "content": list(bloecke)})


def h(stufe, text, anker=None):
    knoten = {
        "type": "heading",
        "attrs": {"level": stufe},
        "content": [{"type": "text", "text": text}],
    }
    if anker:
        knoten["attrs"]["id"] = anker
    return knoten


def p(*teile):
    return {"type": "paragraph", "content": list(teile)}


def text(t, marks=None):
    knoten = {"type": "text", "text": t}
    if marks:
        knoten["marks"] = marks
    return knoten


def verweis(ziel_id, typ, label):
    return {
        "type": "entitaetsverweis",
        "attrs": {"zielId": ziel_id, "zielTyp": typ, "label": label},
    }


class TestInhaltsverzeichnis:
    def test_leeres_dokument_hat_kein_verzeichnis(self):
        assert inhaltsverzeichnis(doc()) == []

    def test_ueberschriften_werden_in_reihenfolge_gesammelt(self):
        roh = doc(h(1, "Kapitel 1"), p(text("Fliesstext")), h(2, "Die Bar"), h(3, "Szene"))
        eintraege = inhaltsverzeichnis(roh)
        assert [e["text"] for e in eintraege] == ["Kapitel 1", "Die Bar", "Szene"]
        assert [e["stufe"] for e in eintraege] == [1, 2, 3]

    def test_jeder_eintrag_hat_einen_anker_zum_springen(self):
        eintraege = inhaltsverzeichnis(doc(h(1, "Der Deal geht schief")))
        assert eintraege[0]["anker"] == "der-deal-geht-schief"

    def test_gleiche_ueberschriften_bekommen_eindeutige_anker(self):
        eintraege = inhaltsverzeichnis(doc(h(2, "Vorgeschichte"), h(2, "Vorgeschichte")))
        anker = [e["anker"] for e in eintraege]
        assert anker == ["vorgeschichte", "vorgeschichte-2"]
        assert len(set(anker)) == 2

    def test_umlaute_werden_lesbar_uebersetzt(self):
        eintraege = inhaltsverzeichnis(doc(h(1, "Straße der Grüße")))
        assert eintraege[0]["anker"] == "strasse-der-gruesse"

    def test_geheime_ueberschrift_taucht_beim_spieler_nicht_auf(self):
        # Sonst verriete allein das Inhaltsverzeichnis den Plot.
        roh = doc(
            h(1, "Kapitel 1"),
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [text("Der Verräter", [{"type": "gmSecret"}])],
            },
        )
        assert [e["text"] for e in inhaltsverzeichnis(roh, viewer_role="GM")] == ["Kapitel 1", "Der Verräter"]
        assert [e["text"] for e in inhaltsverzeichnis(roh, viewer_role="PLAYER")] == ["Kapitel 1"]

    def test_kaputtes_json_wirft_nicht(self):
        assert inhaltsverzeichnis("kein json") == []
        assert inhaltsverzeichnis("") == []


class TestVerweise:
    def test_ohne_verweise_leer(self):
        assert verweise_sammeln(doc(p(text("nur Text")))) == []

    def test_verweis_wird_mit_ziel_und_typ_gefunden(self):
        roh = doc(p(text("Er trifft "), verweis("npc-1", "Person", "Mr. Chrome")))
        assert verweise_sammeln(roh) == [{"zielId": "npc-1", "zielTyp": "Person"}]

    def test_doppelter_verweis_zaehlt_einmal(self):
        # Eine Seite verweist auf einen NPC, egal wie oft er im Text steht.
        roh = doc(
            p(verweis("npc-1", "Person", "Mr. Chrome")),
            p(verweis("npc-1", "Person", "Chrome")),
        )
        assert verweise_sammeln(roh) == [{"zielId": "npc-1", "zielTyp": "Person"}]

    def test_verweise_in_tabellen_werden_gefunden(self):
        roh = doc(
            {
                "type": "table",
                "content": [
                    {
                        "type": "tableRow",
                        "content": [
                            {"type": "tableCell", "content": [p(verweis("ort-1", "Ort", "Neon Alley"))]}
                        ],
                    }
                ],
            }
        )
        assert verweise_sammeln(roh) == [{"zielId": "ort-1", "zielTyp": "Ort"}]

    def test_verweis_ohne_ziel_wird_ignoriert(self):
        roh = doc(p({"type": "entitaetsverweis", "attrs": {"label": "kaputt"}}))
        assert verweise_sammeln(roh) == []


class TestSeitenbaum:
    def test_flache_liste_wird_zu_baum(self):
        seiten = [
            {"id": "a", "parentId": None, "sortierung": 0, "titel": "Hauptgeschichte"},
            {"id": "b", "parentId": "a", "sortierung": 0, "titel": "Kapitel 1"},
            {"id": "c", "parentId": "a", "sortierung": 1, "titel": "Kapitel 2"},
            {"id": "d", "parentId": "b", "sortierung": 0, "titel": "Szene"},
        ]
        baum = baum_bauen(seiten)
        assert len(baum) == 1
        assert baum[0]["id"] == "a"
        assert [k["id"] for k in baum[0]["kinder"]] == ["b", "c"]
        assert [k["id"] for k in baum[0]["kinder"][0]["kinder"]] == ["d"]

    def test_sortierung_wird_beachtet(self):
        seiten = [
            {"id": "b", "parentId": None, "sortierung": 1, "titel": "Zweite"},
            {"id": "a", "parentId": None, "sortierung": 0, "titel": "Erste"},
        ]
        assert [s["id"] for s in baum_bauen(seiten)] == ["a", "b"]

    def test_verwaiste_seite_landet_nicht_im_nichts(self):
        # Elternseite gelöscht oder für diesen Betrachter unsichtbar: die Seite
        # darf nicht verschwinden, sonst ist sie unerreichbar.
        seiten = [{"id": "x", "parentId": "weg", "sortierung": 0, "titel": "Waise"}]
        baum = baum_bauen(seiten)
        assert [s["id"] for s in baum] == ["x"]

    def test_zyklus_bricht_nicht_endlos(self):
        seiten = [
            {"id": "a", "parentId": "b", "sortierung": 0, "titel": "A"},
            {"id": "b", "parentId": "a", "sortierung": 0, "titel": "B"},
        ]
        baum = baum_bauen(seiten)
        assert len(baum) >= 1


class TestBisHierherFreigeben:
    """Marks 'was bisher geschah' — nach Session 3 alles bis Kapitel 3 freigeben."""

    def test_liefert_seite_und_alle_vorherigen_in_lesereihenfolge(self):
        seiten = [
            {"id": "a", "parentId": None, "sortierung": 0, "titel": "Prolog"},
            {"id": "b", "parentId": None, "sortierung": 1, "titel": "Kapitel 1"},
            {"id": "b1", "parentId": "b", "sortierung": 0, "titel": "Szene A"},
            {"id": "c", "parentId": None, "sortierung": 2, "titel": "Kapitel 2"},
        ]
        assert seiten_bis_einschliesslich(seiten, "b1") == ["a", "b", "b1"]

    def test_die_zielseite_selbst_ist_enthalten(self):
        seiten = [{"id": "a", "parentId": None, "sortierung": 0, "titel": "Nur eine"}]
        assert seiten_bis_einschliesslich(seiten, "a") == ["a"]

    def test_spaetere_seiten_bleiben_aussen_vor(self):
        seiten = [
            {"id": "a", "parentId": None, "sortierung": 0, "titel": "Erste"},
            {"id": "b", "parentId": None, "sortierung": 1, "titel": "Zweite"},
        ]
        assert "b" not in seiten_bis_einschliesslich(seiten, "a")

    def test_unbekannte_seite_gibt_nichts_frei(self):
        seiten = [{"id": "a", "parentId": None, "sortierung": 0, "titel": "Erste"}]
        assert seiten_bis_einschliesslich(seiten, "gibtsnicht") == []


class TestSeitenSichtbarkeit:
    def basis(self, **ueber):
        seite = {
            "id": "s-1",
            "titel": "Kapitel 1",
            "inhalt": doc(p(text("Sichtbar"), text(" geheim", [{"type": "gmSecret"}]))),
            "sichtbarkeit": "GM",
            "sichtbarFuer": [],
            "parentId": None,
            "sortierung": 0,
        }
        seite.update(ueber)
        return seite

    def test_neue_seite_ist_nur_fuer_die_sl(self):
        assert filter_seite_for_viewer(self.basis(), "PLAYER", "pc-1") is None

    def test_sl_sieht_alles(self):
        ergebnis = filter_seite_for_viewer(self.basis(), "GM", None)
        assert ergebnis is not None
        assert "geheim" in ergebnis["inhalt"]

    def test_freigegebene_seite_erreicht_den_spieler(self):
        ergebnis = filter_seite_for_viewer(self.basis(sichtbarkeit="ALLE"), "PLAYER", "pc-1")
        assert ergebnis is not None
        assert ergebnis["titel"] == "Kapitel 1"

    def test_geheime_absaetze_werden_serverseitig_entfernt(self):
        ergebnis = filter_seite_for_viewer(self.basis(sichtbarkeit="ALLE"), "PLAYER", "pc-1")
        assert "Sichtbar" in ergebnis["inhalt"]
        assert "geheim" not in ergebnis["inhalt"]

    def test_spezifisch_nur_fuer_genannte_spieler(self):
        seite = self.basis(sichtbarkeit="SPEZIFISCH", sichtbarFuer=["pc-1"])
        assert filter_seite_for_viewer(seite, "PLAYER", "pc-1") is not None
        assert filter_seite_for_viewer(seite, "PLAYER", "pc-2") is None

    def test_fehlende_sichtbarkeit_gilt_als_geheim(self):
        seite = self.basis()
        del seite["sichtbarkeit"]
        assert filter_seite_for_viewer(seite, "PLAYER", "pc-1") is None

    def test_eingabe_wird_nicht_veraendert(self):
        seite = self.basis(sichtbarkeit="ALLE")
        original = json.dumps(seite, sort_keys=True)
        filter_seite_for_viewer(seite, "PLAYER", "pc-1")
        assert json.dumps(seite, sort_keys=True) == original

    def test_liste_filtert_unsichtbare_heraus(self):
        seiten = [
            self.basis(id="a", sichtbarkeit="ALLE"),
            self.basis(id="b", sichtbarkeit="GM"),
            self.basis(id="c", sichtbarkeit="SPEZIFISCH", sichtbarFuer=["pc-1"]),
        ]
        sichtbar = filter_seiten_for_viewer(seiten, "PLAYER", "pc-1")
        assert [s["id"] for s in sichtbar] == ["a", "c"]
