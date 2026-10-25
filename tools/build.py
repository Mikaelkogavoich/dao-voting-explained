"""Builds index.html from tools/index.template.html, inlining the diagrams.

  python3 tools/build.py      then   node tools/render.js   (PNG diagrams and guide.pdf)
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "tools/data.json")))
e = html.escape

# Messages exactly as the platform shows them, what they mean, and what to do.
CANT = [
    ("nopanel", "No Cast your vote panel",
     "Voting is not open on this proposal. It has closed, or it has not opened yet.",
     "Open a proposal that is active. Closed proposals show Voting closed."),
    ("connect", "Connect your wallet to check eligibility",
     "No wallet is connected.",
     "Press Connect wallet."),
    ("switch", "Switch to Redbelly Network",
     "Your wallet is set to another network.",
     "Press it, then try again."),
    ("nocred", "This proposal is open to identity-verified wallets only. This address does not hold a Receptor credential on Redbelly.",
     "This wallet did not hold the credential at this proposal's snapshot block. You see this if it was never enabled, and also if it was enabled after the snapshot.",
     "Check the wallet at Redbelly Access. If it is enabled, it can vote on proposals whose snapshot comes after that."),
    ("notsnap", "This address was not identity-verified at the proposal snapshot.",
     "The same as the message above, in the panel's other wording.",
     "As above. This proposal is closed to this wallet; later ones are not."),
    ("wrong", "Not eligible, but you are sure you verified",
     "The connected address may not be the one you enabled.",
     "Compare the address in your wallet with the one at Redbelly Access, and connect the enabled one."),
    ("unavail", "Eligibility could not be checked. Please try again.",
     "The check did not finish.",
     "Reload the page and try again."),
    ("cancel", "Signature cancelled.",
     "The signature request was rejected in your wallet.",
     "Press Review and sign again and approve the request."),
    ("notrec", "The vote was not recorded.",
     "The signed ballot did not save.",
     "Check that voting is still open, then sign again."),
]

EVIDENCE = [
    ("Only verified wallets can vote on new proposals",
     ["CODE: identity registry set for chain 151", "API: require_verified on every proposal since 29 Aug"]),
    ("Eligibility is read once, at the snapshot block",
     ["UI TEXT: vote panel", "API: /api/power returns snapshotBlock"]),
    ("The snapshot block is %d to %d s before voting opens" % (data["gap_min_s"], data["gap_max_s"]),
     ["API: start time of all %d proposals" % data["native_proposals"], "CHAIN: snapshot block timestamps"]),
    ("A wallet enabled after the snapshot has 0 power, and sees the credential message",
     ["CHAIN: registry event 3 blocks after a snapshot", "API: identity verified, power 0"]),
    ("One vote per verified address; RBNT does not matter",
     ["UI TEXT: Verified identity setting", "API: power 1 for verified voters"]),
    ("Several wallets per identity count separately",
     ["ACCESS FAQ: more accounts linked to your identity", "UI TEXT: not unique people", "CODE: up to about %d" % data["addresses_per_credential"]]),
    ("A vote is a signature with no amount or recipient",
     ["UI TEXT: Wallet safety page", "CODE: signed message fields"]),
    ("Button and message names in the steps", ["UI TEXT: platform interface"]),
    ("A new ballot replaces the old one", ["UI TEXT: Change vote"]),
    ("Access: MetaMask and Coinbase Wallet, Averer, free", ["ACCESS FAQ"]),
]


def svg(name):
    s = open(os.path.join(ROOT, "diagrams", name), encoding="utf-8").read().strip()
    return re.sub(r'\s(width|height)="\d+"', "", s, count=2)  # let CSS size the inline copy


rows = "".join('<tr data-key="%s"><td><b>%s</b></td><td>%s</td><td>%s</td></tr>' % (k, e(a), e(b), e(c)) for k, a, b, c in CANT)
options = "".join('<option value="%s">%s</option>' % (k, e(a if len(a) < 70 else a[:67] + "...")) for k, a, _, _ in CANT)
evidence = "".join('<tr><td>%s</td><td>%s</td></tr>' % (e(r), "".join('<span class="tag">%s</span>' % e(t) for t in tags))
                   for r, tags in EVIDENCE)

tpl = open(os.path.join(ROOT, "tools/index.template.html"), encoding="utf-8").read()
main = re.search(r"<main.*?</main>", tpl, re.S).group(0)
words = len(re.findall(r"[A-Za-z0-9']+", re.sub(r"<[^>]+>|\{\{[A-Z0-9_]+\}\}", " ", main)))
words += sum(len(a.split()) + len(b.split()) + len(c.split()) for _, a, b, c in CANT)

report_path = os.path.join(ROOT, "verify/report.json")
check_line = "Run verify/check.py --live to check every rule against the live platform."
if os.path.exists(report_path):
    rep_ = json.load(open(report_path))
    if rep_.get("live"):
        ok = sum(r["ok"] for r in rep_["results"])
        check_line = "LAST LIVE CHECK %s: %d OF %d CHECKS PASSED" % (rep_["ran_at"].upper(), ok, len(rep_["results"]))

rep = {
    "D1": svg("01-path-to-vote.svg"), "D2": svg("02-snapshot-timeline.svg"), "D3": svg("03-wallets-and-votes.svg"),
    "ROWS": rows, "OPTIONS": options, "EVIDENCE": evidence,
    "VERIFIED": data["verified"], "VERIFIED_CAPS": data["verified_caps"],
    "N_NATIVE": str(data["native_proposals"]), "GAP_MIN": str(data["gap_min_s"]), "GAP_MAX": str(data["gap_max_s"]),
    "N_DIAGRAMS": "3", "CHECK_LINE": check_line, "READ_MIN": str(max(1, round(words / 220))),
}
for k, v in rep.items():
    tpl = tpl.replace("{{%s}}" % k, v)
left = re.findall(r"\{\{[A-Z0-9_]+\}\}", tpl)
assert not left, "unfilled placeholders: %s" % left
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(tpl)
print("index.html built: %d words in the guide, about %s min read" % (words, rep["READ_MIN"]))
