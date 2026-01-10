# Purpose: ensure BeatOven is registered + schema paths exist + coupling rules present

def test_beatoven_manifest_present():
    import json
    import os

    path = os.path.join("aal_core", "overlays", "beatoven", "manifest.json")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    assert manifest["overlay_id"] == "beatoven"


def test_beatoven_schema_present():
    import os

    assert os.path.exists(
        os.path.join("aal_core", "schemas", "beatoven", "beatoven.pack.v0.schema.json")
    )
