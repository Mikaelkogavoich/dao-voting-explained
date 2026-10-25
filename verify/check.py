"""Checks the guide against the brief and against the live platform.

  python3 verify/check.py          offline: files, brand voice, no outdated rules, no advice, no credit
  python3 verify/check.py --live   also re-checks every rule against the platform, its API, its code,
                                   Redbelly Network and Redbelly Access

Standard library only. A live run writes verify/report.json (shown in the guide); an offline run writes
verify/report-offline.json.
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "tools/data.json")))
PLATFORM = "https://redbelly-governance.vercel.app"
ACCESS = "https://access.redbelly.network"
RPC = "https://governors.mainnet.redbelly.network"
REGISTRY = "0xcb385cD90ca6b219798F57B4a7958897e91A9163"  # identity registry the platform uses on chain 151
APPROVED = "2026-09-22"

TEXT_EXT = (".html", ".svg", ".md", ".py", ".js", ".json", ".txt", ".css")
results = []


def check(group, name, ok, detail=""):
    results.append({"group": group, "check": name, "ok": bool(ok), "detail": detail})


def text_files():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        if ".git" in dp or "node_modules" in dp:
            continue
        out += [os.path.join(dp, f) for f in fn if f.endswith(TEXT_EXT)]
    return sorted(out)


def rel(p):
    return os.path.relpath(p, ROOT)


def visible(html):
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html.replace("&quot;", '"').replace("&#x27;", "'").replace("&amp;", "&"))


# ---------------------------------------------------------------- offline
def offline():
    need = ["index.html", "guide.pdf", "SOURCES.md", "README.md", "tools/data.json"]
    for n in ("01-path-to-vote", "02-snapshot-timeline", "03-wallets-and-votes"):
        need += ["diagrams/%s.svg" % n, "diagrams/%s.png" % n]
    missing = [n for n in need if not os.path.exists(os.path.join(ROOT, n))]
    check("Deliverables", "Guide, PDF, diagrams (SVG source and PNG) all present", not missing, ", ".join(missing))

    page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    svgs = sorted(f for f in os.listdir(os.path.join(ROOT, "diagrams")) if f.endswith(".svg"))
    placed = [f for f in svgs if 'href="diagrams/%s"' % f in page]
    check("Deliverables", "Every diagram is placed in the guide and linked", len(placed) == len(svgs) == 3,
          "%d of %d placed" % (len(placed), len(svgs)))
    for f in svgs:
        s = open(os.path.join(ROOT, "diagrams", f), encoding="utf-8").read()
        ok = "<title" in s and "<desc" in s and "LAST VERIFIED %s" % DATA["verified_caps"] in s and "http" not in s.replace("http://www.w3.org/2000/svg", "")
        check("Diagrams", "%s: title, description, dated last-verified line, no external files" % f, ok)

    files = text_files()
    dash_re = re.compile("[%s%s]" % (chr(0x2013), chr(0x2014)))  # en dash, em dash
    dash = [rel(p) for p in files if dash_re.search(open(p, encoding="utf-8").read())]
    check("Brand voice", "No em dashes or en dashes in any file", not dash, ", ".join(dash))
    # Emoji and pictographs. The board allows its check (U+2713) and cross (U+2715) glyphs only.
    emoji_re = re.compile("[%s-%s%s-%s%s-%s%s%s-%s%s]" % (chr(0x1F000), chr(0x1FAFF), chr(0x2600), chr(0x26FF), chr(0x2700),
                                                 chr(0x2712), chr(0x2714), chr(0x2716), chr(0x27BF), chr(0xFE0F)))
    emo = [rel(p) for p in files if emoji_re.search(open(p, encoding="utf-8").read())]
    check("Brand voice", "No emoji (only the board's check and cross glyphs)", not emo, ", ".join(emo))

    text = visible(page)
    svg_text = " ".join(visible(open(os.path.join(ROOT, "diagrams", f), encoding="utf-8").read()) for f in svgs)
    body = re.search(r"<main.*?</main>", page, re.S).group(0)
    body = re.sub(r"(?s)<svg.*?</svg>", " ", body)            # diagrams are counted as diagrams
    body = re.sub(r'(?s)<section id="sources">.*?</section>', " ", body)  # reference table, not guide text
    words = len(re.findall(r"[A-Za-z0-9']+", visible(body)))
    check("Brief", "Short: guide body under 1,800 words", words < 1800, "%d words" % words)

    # Snapshot (the old tool) may only appear to say it is gone or to label imported history.
    allowed = ("no longer used", "came from Snapshot", "Imported from Snapshot")
    sentences = re.split(r"(?<=[.!?])\s+", text + " " + svg_text)
    bad = [s for s in sentences if re.search(r"\bSnapshot\b(?! block)", s) and not any(a in s for a in allowed)]
    check("Failure criteria", "No rule described from Snapshot or older setups", not bad and "Constitution" not in text,
          " | ".join(b[:80] for b in bad))

    advice = [r"\bwe recommend\b", r"\bshould (?:be )?chang", r"\bought to\b", r"\bconsider chang", r"\bit would be better\b",
              r"\bpropos(?:e|ing) (?:that|a change|to change)\b", r"\bthe DAO should\b", r"\bneeds? to be fixed\b"]
    hits = [a for a in advice if re.search(a, text + svg_text, re.I)]
    check("Failure criteria", "No recommendations to change the voting rules", not hits, ", ".join(hits))

    credit = [r"@\w{2,}", r"\bmade by\b", r"\bcreated by\b", r"\bdesigned by\b", r"\bwritten by\b", chr(0xA9)]
    pdf_text = ""
    try:
        pdf_text = subprocess.run(["pdftotext", os.path.join(ROOT, "guide.pdf"), "-"], capture_output=True, text=True).stdout
    except FileNotFoundError:
        pass
    hits = [c for c in credit if re.search(c, text + svg_text + pdf_text, re.I)]
    check("Failure criteria", "No personal credit in the guide, diagrams or PDF", not hits, ", ".join(hits))

    nums = ["%d proposals published" % DATA["native_proposals"], "%d to %d seconds" % (DATA["gap_min_s"], DATA["gap_max_s"])]
    check("Consistency", "Measured numbers on the page match tools/data.json", all(n in text for n in nums), "; ".join(nums))


# ---------------------------------------------------------------- live
def fetch(url, data=None, headers=None):
    h = {"User-Agent": "Mozilla/5.0", **(headers or {})}
    try:
        req = urllib.request.Request(url, data=data, headers=h)
        return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    except Exception:  # some hosts redirect in ways urllib cannot follow behind a proxy; curl can
        cmd = ["curl", "-sSL", "--fail", "-m", "60", "-A", "Mozilla/5.0"]
        for k, v in h.items():
            cmd += ["-H", "%s: %s" % (k, v)]
        if data:
            cmd += ["--data-binary", data.decode()]
        return subprocess.run(cmd + [url], capture_output=True, check=True).stdout.decode("utf-8", "ignore")


def api(path):
    return json.loads(fetch(PLATFORM + path))


def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    return json.loads(fetch(RPC, body, {"content-type": "application/json"}))["result"]


def bundle(base, paths):
    code = ""
    seen = set()
    for p in paths:
        page = fetch(base + p)
        for c in re.findall(r'/_next/static/chunks/[^"]+?\.js', page):
            if c not in seen:
                seen.add(c)
                code += fetch(base + c)
    return code


def live():
    props = [p for p in api("/api/proposals")["proposals"] if p["source"] == "native"]
    props.sort(key=lambda p: p["start_at"])
    latest = props[-1]

    # Interface text and code on the platform
    code = bundle(PLATFORM, ["/", "/create", "/safety", "/proposal/" + latest["id"]])
    ui = [
        "Eligibility is based on the proposal snapshot. Changes after that snapshot do not add voting power.",
        "Every identity-verified address gets exactly one vote.",
        "Verified addresses are not necessarily unique people.",
        "Voting power equals the native RBNT held at the snapshot block.",
        "Only wallets holding a Receptor credential can vote",
        "This replaces the ballot you already cast on this proposal.",
        "IPFS receipt not available yet. Your vote is recorded.",
        "Cast your vote", "Eligible to vote", "Review and sign", "Change vote", "Confirm your vote", "Sign in wallet",
        "Vote recorded", "View IPFS receipt", "Reason (optional)", "Browser wallet", "WalletConnect", "Switch to ",
        "Connect your wallet to check eligibility", "Eligibility could not be checked. Please try again.", "Signature cancelled.",
        "The vote was not recorded.", "This address was not identity-verified at the proposal snapshot.",
        "a proposal cannot be edited once it is open", "Distinct verified voters who must take part",
        "Multiple addresses may belong to the same person", "The portal records your signed ballot.",
        "Every identity-verified address gets exactly one vote regardless of holdings.",
    ]
    missing = [u for u in ui if u not in code]
    check("Platform text", "All %d interface strings the guide quotes are in the live platform" % len(ui), not missing, " | ".join(missing))

    m = re.search(r"\{US:\(\)=>\w,Ve:\(\)=>(\w),mj:\(\)=>\w\}\);let \1=(\d+)", code)
    n = int(m.group(2)) if m else None
    check("Platform code", "One credential enables up to about %d addresses" % DATA["addresses_per_credential"],
          n == DATA["addresses_per_credential"] and "One credential currently enables up to about" in code, "constant = %s" % n)
    fields = re.search(r'Vote:\[\{name:"from",type:"address"\},\{name:"space",type:"string"\},\{name:"proposal",type:"string"\},'
                       r'\{name:"choice",type:"string"\},\{name:"reason",type:"string"\},\{name:"timestamp",type:"uint64"\}\]', code)
    check("Platform code", "A vote signs only from, space, proposal, choice, reason, timestamp", bool(fields))
    check("Platform code", "Identity registry is set for chain 151, so new proposals are verified-only",
          REGISTRY in code and "requireVerified:ec" in code)
    check("Platform code", "Voting opens at publication and runs for the set number of days",
          "start:BigInt(s)" in code and re.search(r"t=s\+86400\*Number\(\w+\)", code) is not None)

    # API
    check("API", "Native proposal count matches the guide", len(props) == DATA["native_proposals"],
          "%d native proposals now (guide says %d)" % (len(props), DATA["native_proposals"]))
    since = [p for p in props if p["start_at"][:10] >= "2026-08-29"]
    check("API", "Every proposal since 29 Aug 2026 is verified wallets only", all(p["require_verified"] for p in since),
          "%d proposals" % len(since))
    after = [p for p in props if p["start_at"][:10] >= APPROVED]
    check("API", "DAO votes since approval use Verified identity",
          after and all(p["strategy"] == "verified-identity" for p in after), ", ".join(p["title"] for p in after))

    gaps = []
    for p in props:
        t = int(rpc("eth_getBlockByNumber", [hex(p["snapshot_block"]), False])["timestamp"], 16)
        gaps.append(int(datetime.fromisoformat(p["start_at"]).timestamp() - t))
    check("Chain", "Snapshot block is %d to %d s before voting opens" % (DATA["gap_min_s"], DATA["gap_max_s"]),
          min(gaps) == DATA["gap_min_s"] and max(gaps) == DATA["gap_max_s"], "measured %d to %d s" % (min(gaps), max(gaps)))

    voter = api("/api/proposals/" + latest["id"])["votes"][0]["voter"]
    pw = api("/api/power?" + urllib.parse.urlencode({"proposal": latest["id"], "voter": voter}))
    check("API", "A verified voter has exactly 1 vote on the latest proposal",
          pw.get("power") == 1 and pw.get("strategy") == "verified-identity" and pw.get("snapshotBlock") == latest["snapshot_block"], json.dumps(pw))
    nobody = "0x000000000000000000000000000000000000dEaD"
    pw = api("/api/power?" + urllib.parse.urlencode({"proposal": latest["id"], "voter": nobody}))
    check("API", "An unverified wallet has 0 power and sees the credential message",
          pw.get("power") == 0 and pw.get("blocked") and "does not hold a Receptor credential" in pw.get("unavailable", ""), json.dumps(pw))

    # A wallet added to the identity registry just after a snapshot: verified now, 0 power on that proposal.
    verified_only = [p for p in props if p["require_verified"]]
    found = None
    for p in reversed(verified_only):
        lo = p["snapshot_block"] + 1
        for start in range(lo, lo + 4000, 100):  # the RPC refuses ranges much wider than 100 blocks
            for lg in rpc("eth_getLogs", [{"address": REGISTRY, "fromBlock": hex(start), "toBlock": hex(start + 99)}]):
                addr = "0x" + lg["data"][-40:]
                if api("/api/identity?address=" + addr).get("verified"):
                    found = (p, addr, int(lg["blockNumber"], 16))
                    break
            if found:
                break
        if found:
            break
    if found:
        p, addr, blk = found
        pw = api("/api/power?" + urllib.parse.urlencode({"proposal": p["id"], "voter": addr}))
        check("Chain + API", "A wallet enabled after a snapshot is verified today but has 0 power on that proposal",
              pw.get("power") == 0 and "does not hold a Receptor credential" in pw.get("unavailable", ""),
              "enabled %d blocks after the snapshot of %s" % (blk - p["snapshot_block"], p["title"]))
    else:
        check("Chain + API", "A wallet enabled after a snapshot is verified today but has 0 power on that proposal", False,
              "no registry event found in the 4,000 blocks after any snapshot")

    # Redbelly Access portal
    acc = bundle(ACCESS, ["/"])
    faq = ["MetaMask and Coinbase Wallet can be used to get access.",
           "add more accounts which will be connected to your identity.",
           "Your identity will be verified by an accredited issuer, Averer.",
           "will cover any associated fees required to grant your network access.",
           "Check your wallet to sign the transaction that will enable your account.",
           "Add another account"]
    missing = [f for f in faq if f not in acc]
    check("Redbelly Access", "Access portal text the guide relies on is live", not missing, " | ".join(missing))


if __name__ == "__main__":
    offline()
    if "--live" in sys.argv:
        try:
            live()
        except Exception as ex:  # report, never hide
            check("Live", "Live checks ran to the end", False, "%s: %s" % (type(ex).__name__, ex))
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    json.dump({"ran_at": stamp, "live": "--live" in sys.argv, "results": results},
              open(os.path.join(ROOT, "verify", "report.json" if "--live" in sys.argv else "report-offline.json"), "w"), indent=2)
    width = max(len(r["check"]) for r in results)
    for r in results:
        print("%s  %-*s  %s" % ("PASS" if r["ok"] else "FAIL", width, r["check"], r["detail"] if not r["ok"] or r["group"] in ("Chain", "Brief", "Chain + API") else ""))
    failed = sum(not r["ok"] for r in results)
    print("\n%s: %d of %d checks passed (%s)" % ("FAIL" if failed else "PASS", len(results) - failed, len(results), stamp))
    sys.exit(1 if failed else 0)
