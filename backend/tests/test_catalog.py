from app.data_access.catalog import load_catalog, lookup, query_sqlite, seed_sqlite


def test_catalog_loads():
    catalog = load_catalog()
    assert len(catalog) > 20
    assert all(e.platforms for e in catalog)


def test_lookup_case_insensitive():
    entry = lookup("black mirror")
    assert entry is not None and "netflix" in entry.platforms
    assert lookup("totally-not-a-show") is None


def test_sqlite_seed_and_query(tmp_path):
    db = tmp_path / "catalog.db"
    seed_sqlite(db, force=True)
    fleabag = query_sqlite("fleabag", db)  # case-insensitive
    assert fleabag is not None and fleabag.platforms == ["prime"]
    assert query_sqlite("missing show", db) is None
