from scripts.retrievers import retrieve

if __name__ == "__main__":
    query = "Gen ed decisions after 2020"

    results = retrieve(
        query=query,
        k=5,
        alpha=0.6,
        use_mmr=True,
        lambda_param=0.7
    )

    print("==== Top Results ====")
    for i, r in enumerate(results):
        print(f"[{i+1}] {r.payload['text'][:300]}...\n")
