import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# ================= CONFIGURATION =================

CHANNELS = [
    "iProxyChannel",
    "filembad",
    "FreakConfig",
]

TARGET = 250
OUTPUT_FILE = "configs.txt"
REQUEST_DELAY = 1

# ==================================================

CONFIG_PATTERN = re.compile(
    r"(?:"
    r"vless://[^\s<>\"']+|"
    r"vmess://[^\s<>\"']+|"
    r"trojan://[^\s<>\"']+|"
    r"ss://[^\s<>\"']+"
    r")",
    re.IGNORECASE,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}


def clean_config(config):
    """Remove trailing punctuation from a configuration URL."""
    return config.rstrip(".,;:!?)\\]}").strip()


def fetch_page(channel, before=None):
    """Fetch a Telegram public channel page."""
    base_url = f"https://t.me/s/{quote(channel)}"
    params = {"before": before} if before else {}

    response = requests.get(
        base_url,
        params=params,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")


def collect_channel(channel, global_seen):
    """
    Collect up to TARGET unique configurations from one channel.
    Skip configurations already collected from other channels.
    """
    channel_configs = 0
    before = None
    pages = 0

    print(f"\n{'=' * 60}")
    print(f"Channel: {channel}")
    print(f"Target: {TARGET} unique configs")
    print(f"Output: {OUTPUT_FILE}")
    print(f"{'=' * 60}")

    with open(OUTPUT_FILE, "a", encoding="utf-8") as output:

        while channel_configs < TARGET:

            try:
                soup = fetch_page(channel, before)

            except requests.RequestException as exc:
                print(f"[ERROR] Failed to fetch {channel}: {exc}")
                break

            messages = soup.select(".tgme_widget_message")

            if not messages:
                print(f"[{channel}] No messages found. Stopping.")
                break

            # Process newest messages first.
            messages.reverse()

            oldest_id = None

            for message in messages:

                # Determine the oldest message ID on this page.
                post_id = message.get("data-post", "")

                if post_id:
                    try:
                        message_id = int(post_id.rsplit("/", 1)[1])

                        oldest_id = (
                            message_id
                            if oldest_id is None
                            else min(oldest_id, message_id)
                        )

                    except (ValueError, IndexError):
                        pass

                # Extract message text.
                text_element = message.select_one(
                    ".tgme_widget_message_text"
                )

                if not text_element:
                    continue

                text = text_element.get_text("\n", strip=True)

                # Find supported configurations.
                for match in CONFIG_PATTERN.findall(text):

                    config = clean_config(match)

                    if not config:
                        continue

                    # Skip duplicates across all channels.
                    if config in global_seen:
                        continue

                    global_seen.add(config)
                    channel_configs += 1

                    # Save configuration to the common output file.
                    output.write(config + "\n")
                    output.flush()

                    print(
                        f"[{channel}] "
                        f"[{channel_configs:03}/{TARGET}] "
                        f"{config[:65]}..."
                    )

                    if channel_configs >= TARGET:
                        break

                if channel_configs >= TARGET:
                    break

            pages += 1

            print(
                f"[{channel}] Page {pages} processed — "
                f"{channel_configs}/{TARGET} unique configs."
            )

            # Stop when the target is reached.
            if channel_configs >= TARGET:
                print(f"[{channel}] Target reached.")
                break

            # Stop if no message IDs were found.
            if oldest_id is None:
                print(
                    f"[{channel}] Could not determine the oldest "
                    "message ID. Stopping."
                )
                break

            # Prevent infinite pagination loops.
            if before is not None and oldest_id >= before:
                print(
                    f"[{channel}] Pagination made no progress. "
                    "Stopping."
                )
                break

            # Load older messages on the next request.
            before = oldest_id

            time.sleep(REQUEST_DELAY)

    print(
        f"\n[{channel}] Finished: "
        f"{channel_configs}/{TARGET} new unique configs collected."
    )

    return channel_configs


def remove_duplicates():
    """
    Remove duplicate lines from OUTPUT_FILE.
    Preserve the order of the first occurrence.
    """
    seen = set()
    unique_configs = []

    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
            for line in file:
                config = line.strip()

                if config and config not in seen:
                    seen.add(config)
                    unique_configs.append(config)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            for config in unique_configs:
                file.write(config + "\n")

        print("\n" + "=" * 60)
        print("DUPLICATE REMOVAL")
        print("=" * 60)
        print(f"Unique configurations: {len(unique_configs)}")
        print(f"Saved to: {OUTPUT_FILE}")

    except OSError as exc:
        print(f"[ERROR] Failed to remove duplicates: {exc}")


def main():
    # Global deduplication across all channels.
    global_seen = set()

    results = {}

    # Start each run with an empty output file.
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8"):
            pass
    except OSError as exc:
        print(f"[ERROR] Cannot create output file: {exc}")
        return

    print(f"Channels to process: {len(CHANNELS)}")
    print(f"Target per channel: {TARGET}")
    print(f"Output file: {OUTPUT_FILE}")

    for channel in CHANNELS:

        try:
            count = collect_channel(channel, global_seen)
            results[channel] = count

        except Exception as exc:
            print(
                f"[ERROR] Unexpected error while processing "
                f"{channel}: {exc}"
            )

            results[channel] = 0

        # Pause before starting the next channel.
        time.sleep(REQUEST_DELAY)

    # Final summary before cleanup.
    print(f"\n{'=' * 60}")
    print("FINAL SUMMARY")
    print(f"{'=' * 60}")

    for channel, count in results.items():
        print(f"{channel}: {count}/{TARGET} configs")

    print(f"Total unique configs collected: {len(global_seen)}")

    # Final deduplication pass.
    remove_duplicates()

    print("\nFinished.")


if __name__ == "__main__":
    main()
