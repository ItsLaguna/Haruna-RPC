import sys
import time
import json
import socket
import os
import re
import threading
from datetime import datetime
from pypresence import Presence

# --- Configuration ---
MPV_SOCKET_PATH = "/tmp/mpvsocket"
DISCORD_CLIENT_ID = "1440522994320408728"  # <<< REPLACE WITH YOUR APP ID IF YOU DON'T WANT TO USE THIS ONE

LARGE_IMAGE_KEY = "haruna_logo"
LARGE_TEXT = "Haruna"
SMALL_IMAGE_PLAY = "play"
SMALL_IMAGE_PAUSE = "pause"

# --- FILE EXTENSION FILTER ---
TRACKED_EXTENSIONS = ["mkv"]  # Only tracks .mkv files by default, for more follow this pattern inside the []: ["mkv", "mp4", "mov"]

# Polling intervals
POLL_INTERVAL_PLAYING = 0.2
POLL_INTERVAL_PAUSED = 0.5
POLL_INTERVAL_IDLE = 0.5

class HarunaDiscordPresence:
    def __init__(self, socket_path=MPV_SOCKET_PATH, client_id=DISCORD_CLIENT_ID):
        self.socket_path = socket_path
        self.client_id = client_id
        self.ipc_request_id = 0
        self.discord_client: Presence | None = None
        self.is_connected = False
        self.last_update_state = {}
        self._last_time_pos = 0.0
        self._last_poll_time = 0.0
        self._is_paused = True

    # -------------------- Filename Parsing --------------------
    def _parse_filename_metadata(self, filename: str) -> tuple[str, str, bool]:
        base_name = os.path.splitext(filename)[0].strip()
        base_name_clean = re.sub(r'[._\-\[\]\(\)]', ' ', base_name)

        match = re.search(
            r"([sS]\s*(\d+)\s*[eE]\s*(\d+))"  # S01E03
            r"|(\s*(\d+)\s*[xX]\s*(\d+))"     # 1x03
            r"|([eE]0*(\d+))",                # E03 only (standalone E)
            base_name_clean
        )

        default_series_name = base_name
        default_episode_info = "Watching"

        if not match:
            return default_series_name, default_episode_info, False

        is_series_format = True

        # SxxExx
        if match.group(2) and match.group(3):
            s_num, e_num = match.group(2), match.group(3)
            series_name = base_name[:match.start(1)].strip() or default_series_name
            episode_info = f"Season {int(s_num)} | Episode {int(e_num)}"

        # XXxYY
        elif match.group(5) and match.group(6):
            s_num, e_num = match.group(5), match.group(6)
            series_name = base_name[:match.start(4)].strip() or default_series_name
            episode_info = f"Season {int(s_num)} | Episode {int(e_num)}"

        # E0X only
        elif match.group(8):
            e_num = match.group(8)
            # Slice up to start of full E0X match to avoid including it in the title
            series_name = base_name[:match.start(0)].strip() or default_series_name
            episode_info = f"Episode {int(e_num)}"

        else:
            return default_series_name, default_episode_info, False

        return series_name, episode_info, is_series_format

    # -------------------- MPV IPC --------------------
    def _send_command(self, command: list, property_name: str = None):
        self.ipc_request_id += 1
        payload = {"command": command, "request_id": self.ipc_request_id}
        message = json.dumps(payload) + "\n"

        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(self.socket_path)
            s.settimeout(0.05)
            s.sendall(message.encode("utf-8"))

            response_data = b""
            while True:
                try:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk
                except socket.timeout:
                    break
            s.close()

            for line in response_data.decode("utf-8", errors="ignore").strip().split("\n"):
                try:
                    res = json.loads(line)
                    if res.get("request_id") == self.ipc_request_id and res.get("error") == "success":
                        if property_name:
                            return res.get("data")
                        return True
                except Exception:
                    continue
            return None
        except Exception:
            return None

    def get_player_status(self) -> dict:
        filename = self._send_command(["get_property", "filename"], "filename")
        title = os.path.basename(filename) if filename else None

        return {
            "title": title,
            "time_pos": self._send_command(["get_property", "playback-time"], "playback-time"),
            "duration": self._send_command(["get_property", "duration"], "duration"),
            "paused": self._send_command(["get_property", "pause"], "pause"),
        }

    # -------------------- Discord --------------------
    def connect_to_discord(self):
        if self.is_connected:
            return
        try:
            self.discord_client = Presence(self.client_id)
            self.discord_client.connect()
            self.is_connected = True
        except Exception:
            self.discord_client = None
            self.is_connected = False

    def disconnect_discord(self):
        """
        Instantly clears Rich Presence in a separate thread for fast close/skip handling.
        """
        if self.discord_client:
            def safe_clear(client):
                try:
                    client.clear()
                except Exception:
                    pass  # ignore pipe errors

            threading.Thread(target=safe_clear, args=(self.discord_client,), daemon=True).start()

        self.discord_client = None
        self.is_connected = False
        self.last_update_state = {}
        self._last_time_pos = 0.0
        self._last_poll_time = 0.0
        self._is_paused = True

    # -------------------- Update Presence --------------------
    def update_presence(self, status: dict):
        if not self.is_connected or not status.get("title"):
            return

        title = status.get("title")

        # --- File Extension Filter ---
        ext = os.path.splitext(title)[1].lower().lstrip(".")
        if ext not in TRACKED_EXTENSIONS:
            if self.last_update_state:
                self.disconnect_discord()
            return

        paused = status.get("paused") or False
        duration = status.get("duration") or 0.0
        mpv_time_pos = status.get("time_pos") or 0.0
        current_time = time.time()

        # ----------------- Accurate elapsed time tracking -----------------
        seek_threshold = 0.2
        if not paused:
            if self._is_paused:
                self._last_poll_time = current_time
                self._last_time_pos = mpv_time_pos
                self._is_paused = False
            else:
                if abs(mpv_time_pos - self._last_time_pos) > seek_threshold:
                    self._last_time_pos = mpv_time_pos
                    self._last_poll_time = current_time
                else:
                    elapsed = current_time - self._last_poll_time
                    self._last_time_pos += elapsed
                    self._last_poll_time = current_time
        else:
            self._is_paused = True
            self._last_time_pos = mpv_time_pos
            self._last_poll_time = current_time

        time_pos = self._last_time_pos

        # ----------------- Parse title -----------------
        series_name, episode_info, is_series = self._parse_filename_metadata(title)
        details = series_name

        # Paused always shows "Paused"
        if paused:
            state = "Paused"
        else:
            state = episode_info if is_series else "Watching"

        # Timestamps only if not paused and duration exists
        start_time = int(current_time - time_pos) if not paused else None
        end_time = int(start_time + duration) if start_time and duration else None

        activity = {
            "details": details,
            "state": state,
            "large_image": LARGE_IMAGE_KEY,
            "large_text": LARGE_TEXT,
            "small_image": SMALL_IMAGE_PAUSE if paused else SMALL_IMAGE_PLAY,
            "small_text": "Paused" if paused else "Playing",
            "start": start_time,
            "end": end_time,
        }

        if activity != self.last_update_state:
            try:
                self.discord_client.update(**activity)
                self.last_update_state = activity
            except Exception:
                self.disconnect_discord()
                self.connect_to_discord()

    # -------------------- Main Loop --------------------
    def run(self):
        while True:
            if not self.is_connected:
                self.connect_to_discord()

            status = self.get_player_status()

            # Clear instantly on no media or untracked file
            if not status["title"] or os.path.splitext(status["title"])[1].lower().lstrip(".") not in TRACKED_EXTENSIONS:
                if self.last_update_state:
                    self.disconnect_discord()
                time.sleep(POLL_INTERVAL_IDLE)
            else:
                self.update_presence(status)
                time.sleep(POLL_INTERVAL_PLAYING if not status["paused"] else POLL_INTERVAL_PAUSED)


# -------------------- Entry Point --------------------
if __name__ == "__main__":
    if DISCORD_CLIENT_ID == "YOUR_DISCORD_APP_ID_HERE":
        print("CRITICAL: Replace 'YOUR_DISCORD_APP_ID_HERE' with your Discord Application ID.", file=sys.stderr)
        sys.exit(1)

    rpc_controller = HarunaDiscordPresence()
    try:
        rpc_controller.run()
    except KeyboardInterrupt:
        pass
    finally:
        rpc_controller.disconnect_discord()
