"""Testet ob der istEntwurf-Filter in list_orte greift."""
import asyncio
import sys
sys.path.insert(0, ".")

from app.entities import routes, repository
from app.entities.visibility import filter_entities_for_viewer

CAMPAIGN_ID = "3690f69c-daa2-4964-a31f-8e8c907a1ec5"

async def test():
    # 1. Hole rohe Daten aus DB
    orte_roh = await repository.list_nodes('Ort', repository.ORT_FIELDS, CAMPAIGN_ID)
    print(f"1. Rohe Orte aus DB: {len(orte_roh)}")
    for o in orte_roh:
        print(f"   - {o.get('name')}: istEntwurf={o.get('istEntwurf')}")
    
    # 2. Simuliere was _aufbereiten macht
    class FakeViewer:
        role = 'gm'
        person_id = None
    
    viewer = FakeViewer()
    sichtbar = filter_entities_for_viewer(orte_roh, viewer.role, viewer.person_id)
    print(f"\n2. Nach Sichtbarkeits-Filter: {len(sichtbar)}")
    
    # 3. Der kritische Filter
    ohne_entwuerfe = [e for e in sichtbar if not e.get("istEntwurf", False)]
    print(f"\n3. Nach istEntwurf-Filter (ohne Entwürfe): {len(ohne_entwuerfe)}")
    for o in ohne_entwuerfe:
        print(f"   - {o.get('name')}")
    
    # 4. Check ob der Filter-Code in routes.py existiert
    import inspect
    source = inspect.getsource(routes._aufbereiten)
    if "istEntwurf" in source:
        print("\n4. ✓ istEntwurf-Filter ist im Code vorhanden")
    else:
        print("\n4. ✗ istEntwurf-Filter FEHLT im Code!")

asyncio.run(test())
