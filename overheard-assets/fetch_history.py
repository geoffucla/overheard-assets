#!/usr/bin/env python3
"""Fetch earlier editions verbatim from the public site repo geoffucla/overheard-site.

Usage: fetch_history.py bay|texas OUTDIR [--days 60] [--end YYYY-MM-DD]
Saves every edition found in the last DAYS calendar days (ending the day before --end, default
today UTC) as OUTDIR/SCUTTLEBUTT_YYYY-MM-DD.md, writes OUTDIR/MANIFEST.txt, and prints a summary.
Weekends and missing days (404) are skipped silently. The publishing job posts an edition
some hours after it is sent, so today's edition and sometimes yesterday's may be missing; fall
back to Resend get-broadcast for any weekday in the last 3 days that is missing here.
"""
import sys, os, datetime, urllib.request, urllib.error
BASE = "https://raw.githubusercontent.com/geoffucla/overheard-site/main/"
DIRS = {"bay": "output/", "texas": "output-texas/"}

def main(a):
    if len(a) < 3 or a[1] not in DIRS:
        print(__doc__); return 1
    ed, out = a[1], a[2]
    days = int(a[a.index("--days") + 1]) if "--days" in a else 60
    end = datetime.date.fromisoformat(a[a.index("--end") + 1]) if "--end" in a else datetime.datetime.utcnow().date()
    os.makedirs(out, exist_ok=True)
    got, missing = [], []
    for i in range(1, days + 1):
        d = end - datetime.timedelta(days=i)
        if d.weekday() >= 5:
            continue
        url = "%s%sSCUTTLEBUTT_%s.md" % (BASE, DIRS[ed], d.isoformat())
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ed"}), timeout=20) as r:
                txt = r.read().decode("utf-8", "replace")
            open(os.path.join(out, "SCUTTLEBUTT_%s.md" % d.isoformat()), "w", encoding="utf-8").write(txt)
            got.append((d, len(txt.split())))
        except urllib.error.HTTPError as e:
            missing.append((d, e.code))
        except Exception as e:
            missing.append((d, str(e)[:40]))
    with open(os.path.join(out, "MANIFEST.txt"), "w") as f:
        for d, w in sorted(got):
            f.write("%s  %d words\n" % (d, w))
        for d, c in sorted(missing):
            f.write("%s  MISSING (%s)\n" % (d, c))
    print("%s: fetched %d editions (%s to %s), %d weekdays missing" % (ed, len(got), min(got)[0] if got else "-", max(got)[0] if got else "-", len(missing)))
    print("missing weekdays:", ", ".join(str(d) for d, c in sorted(missing)[-6:]) or "none")
    return 0 if got else 2
if __name__ == "__main__":
    sys.exit(main(sys.argv))
