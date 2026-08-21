from app.pipeline import process_digest

if __name__ == "__main__":
    created = process_digest.run()
    print(f"{len(created)} digest(s) created")
