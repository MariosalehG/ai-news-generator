from app.pipeline import build_email

if __name__ == "__main__":
    digest = build_email.run()
    print(digest.to_markdown())
