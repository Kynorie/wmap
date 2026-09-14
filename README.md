# wmap

## About

wmap is a command line tool that finds websites, subdomains, and live hosts on a network. It works in two ways:

1. It checks certificate transparency logs (a public record of SSL certificates). This sends no traffic to the target at all.
2. If you turn on the `--active` flag, it also tries common subdomain names using DNS lookups. This does send traffic to the target.

wmap only scans public networks and domains by default. If you scan your own computer or local network (like `127.0.0.1` or `192.168.1.0/24`), it skips straight to results since you clearly have permission there.

wmap works on Linux only.

## Warning

Only use wmap on IP addresses and domains you own, or that you have clear permission to scan. Scanning something you do not have permission for may break the law, even if you did not mean any harm.

wmap will remind you of this before every scan of a public target. This reminder is not a security check. It cannot confirm you actually have permission. It exists so nobody can say they were not told the rule. The responsibility to follow it is yours.

You can turn off the reminder with `wmap --i-agree` once you understand this.

## Installation

wmap needs Python 3 and a few packages to run. Clone the repository first, either way:

```
git clone https://github.com/kynorie/wmap.git
cd wmap
```

### Option 1: install.sh (recommended)

This sets up a virtual environment for you and lets you run `wmap` as a normal command, instead of typing `python3 wmap.py` every time.

1. Make the script runnable, then run it:
   ```
   chmod +x install.sh
   ./install.sh
   ```

2. Run wmap:
   ```
   wmap <target>
   ```

   For example:
   ```
   wmap 127.0.0.1
   ```

If the script tells you to add something to your PATH, follow that instruction before running the command above.

### Option 2: pip

Use this if you would rather manage packages yourself, or install.sh does not work for you.

1. Install the required packages:
   ```
   pip install -r requirements.txt --break-system-packages
   ```

2. Run wmap:
   ```
   python3 wmap.py <target>
   ```

   For example:
   ```
   python3 wmap.py 127.0.0.1
   ```
