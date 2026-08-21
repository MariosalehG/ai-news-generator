from app.pipeline import curate

if __name__ == "__main__":
    ranked = curate.run()
    for item in ranked:
        print(f"[{item['score']:>3}] {item['title']} ({item['url']})")
        print(f"      {item['reason']}")
