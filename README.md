# Config Collector

A Python script that collects unique proxy configurations from public Telegram channels.

## Features

- Collects VLESS, VMess, Trojan, and Shadowsocks configurations.
- Removes duplicate configurations.
- Saves results to `configs.txt`.
- Runs automatically using GitHub Actions.
- Updates `configs.txt` in the repository after each successful run.

## Requirements

- Python 3.12+
- requests
- beautifulsoup4

Dependencies are installed automatically by GitHub Actions.

## Automatic Schedule

The collector runs automatically every 5 hours using GitHub Actions.

You can also start it manually from the **Actions** tab.

## Output

Collected configurations are saved in:

`configs.txt`

## Disclaimer

Configurations are collected from publicly accessible Telegram channels. Their availability, security, and reliability are not guaranteed. Use them responsibly and follow applicable laws and service terms.
