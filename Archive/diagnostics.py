def test_year_filter(db, year=2024, keyword="CAPP", k=5):
    print(f"Testing for docs with year={year}, keyword='{keyword}'")
    results = db.similarity_search(keyword, k=k, filter={"year": year})
    for i, d in enumerate(results, 1):
        print(f"{i}. {d.metadata.get('source', 'unknown')}  (year={d.metadata.get('year')})")
