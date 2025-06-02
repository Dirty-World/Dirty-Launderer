#!/usr/bin/env python3
import os
import sys
from bot.utils.secret_manager import create_secret

def main():
    """Create Codecov token secret in GCP Secret Manager."""
    if len(sys.argv) != 2:
        print("Usage: python create_codecov_secret.py <codecov_token>")
        sys.exit(1)

    token = sys.argv[1]
    try:
        create_secret("CODECOV_TOKEN", token)
        print("Successfully created CODECOV_TOKEN secret")
    except Exception as e:
        print(f"Error creating secret: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 