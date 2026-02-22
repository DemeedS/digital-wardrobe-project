#!/usr/bin/env python3
"""Detect usernames exceeding a configured maximum length.

Run from the project root: `python3 scripts/check_usernames.py --limit 80`
"""
from app import create_app
from app.models import User
from sqlalchemy import func


def find_long_usernames(limit: int):
    app = create_app()
    with app.app_context():
        results = (
            User.query
            .filter(func.length(User.username) > limit)
            .all()
        )
        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Check for usernames longer than limit")
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()

    long_users = find_long_usernames(args.limit)
    if not long_users:
        print(f"No usernames longer than {args.limit} found.")
        return 0

    print(f"Found {len(long_users)} usernames longer than {args.limit}:")
    for u in long_users:
        print(f"- id={u.id} username='{u.username}' length={len(u.username)})")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
