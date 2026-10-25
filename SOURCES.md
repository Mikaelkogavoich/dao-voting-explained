# Sources and evidence

Every rule in the guide was checked against the live platform on 25 October 2026. Run `python3 verify/check.py --live` to repeat every check below. It needs only Python 3 and network access.

Evidence types:

- **UI TEXT**: words the platform shows, read from its published front-end code at redbelly-governance.vercel.app.
- **API**: the platform's own public endpoints (`/api/proposals`, `/api/power`, `/api/identity`).
- **CODE**: logic in the platform's published front-end code.
- **CHAIN**: Redbelly Network mainnet (chain 151), read through `https://governors.mainnet.redbelly.network`.
- **ACCESS**: text in the Redbelly Access portal at access.redbelly.network.

## Sources

| | Source | Used for |
|---|---|---|
| S1 | DAO governance platform: https://redbelly-governance.vercel.app/ | Every voting rule, button and message |
| S2 | Wallet safety page: https://redbelly-governance.vercel.app/safety | What a vote signs, no gas |
| S3 | Platform API: `/api/proposals`, `/api/power`, `/api/identity` | Proposal settings, voting power, verification |
| S4 | Redbelly Network mainnet RPC: https://governors.mainnet.redbelly.network | Snapshot block times, identity registry events |
| S5 | Redbelly Access: https://access.redbelly.network/ | Getting verified, wallets, linked accounts |
| S6 | Redbelly docs, Receptor: https://docs.redbelly.network/pages/receptor/ | What Receptor is |
| S7 | Task Board brand kit: https://taskboard.redbellydao.network/brand | Colours, type, logo, voice |
| S8 | DAO task brief | The platform was approved for continued use on 22 September 2026 |

## Rules and their evidence

**1. Only wallets holding the access credential can vote.**
UI TEXT: "Only wallets holding a Receptor credential can vote, as Redbelly requires one for network access."
CODE: the identity registry `0xcb385cD90ca6b219798F57B4a7958897e91A9163` is set for chain 151, and new proposals are sent with `requireVerified` on when it is set.
API: `require_verified` is true on every proposal since 29 August 2026.

**2. Receptor is Redbelly's identity and credential system; Averer verifies identity; access is free.**
S6: "Receptor is Redbelly's native digital identity and verifiable credential protocol."
ACCESS: "Your identity will be verified by an accredited issuer, Averer." and "the accredited issuer that verifies your identity will cover any associated fees required to grant your network access."
ACCESS: "MetaMask and Coinbase Wallet can be used to get access." and "Check your wallet to sign the transaction that will enable your account."

**3. Eligibility is read once per proposal, at its snapshot block.**
UI TEXT: "Eligibility is based on the proposal snapshot. Changes after that snapshot do not add voting power."
API: `/api/power?proposal=<id>&voter=<address>` returns the `snapshotBlock` it used.

**4. Voting opens at publication and runs for the number of days its author set.**
CODE: the proposal's start is the time it is signed, and its end is start + 86,400 seconds × the number of days entered.

**5. The snapshot block is 15 to 162 seconds before voting opens.**
API + CHAIN: for each of the 10 proposals published on the platform, the snapshot block's timestamp was compared with the proposal's start time. Smallest gap 15 s, largest 162 s.

**6. A wallet enabled after the snapshot cannot vote on that proposal, and sees the credential message.**
CHAIN: the identity registry logged a new address 3 blocks after the snapshot block of the "Proposal Resubmission Policy" vote.
API: `/api/identity` reports that address as verified today. `/api/power` for that proposal returns power 0 and: "This proposal is open to identity-verified wallets only. This address does not hold a Receptor credential on Redbelly."
The check script finds such an address on its own each time it runs, so no address is listed here.

**7. One vote per verified address, regardless of RBNT.**
UI TEXT: "Every identity-verified address gets exactly one vote." and "Every identity-verified address gets exactly one vote regardless of holdings."
API: power is 1 for a verified voter on the latest proposal. Both votes since 22 September 2026 use the Verified identity strategy.

**8. With RBNT balance, power is the RBNT held at the snapshot block.**
UI TEXT: "Voting power equals the native RBNT held at the snapshot block."

**9. Several wallets under one verification each count as a separate verified address.**
ACCESS: "you will be offered the option to add more accounts which will be connected to your identity." and the button "Add another account".
UI TEXT: "Verified addresses are not necessarily unique people." and "Multiple addresses may belong to the same person."
CODE: "One credential currently enables up to about" followed by the constant 10. The Voters count and identity quorum count distinct addresses.

**10. The voting steps, buttons and messages.**
UI TEXT: "Connect wallet", "Browser wallet", "WalletConnect", "Switch to Redbelly Network", "Cast your vote", "Eligible to vote", "Reason (optional)", "Review and sign", "Confirm your vote", "Sign in wallet", "Vote recorded", "View IPFS receipt", "IPFS receipt not available yet. Your vote is recorded."

**11. Changing a vote.**
UI TEXT: "Change vote", "This replaces the ballot you already cast on this proposal." and "Voting again before the deadline replaces this ballot."

**12. What a vote signs.**
S2 and CODE: the signed message has the fields `from`, `space`, `proposal`, `choice`, `reason`, `timestamp`, under the domain "Redbelly Governance", version 1, chain 151. S2: "There is no amount, no recipient, and no spender in that structure." and "If something asks you to pay a fee to vote, it is not this site."

**13. Ballots are stored by the platform with IPFS receipts.**
UI TEXT: "The portal records your signed ballot. When its IPFS receipt is published, a link lets you inspect the signed payload independently. An unavailable receipt does not mean your vote failed."

**14. Settings vary by proposal and cannot be edited once open.**
UI TEXT (New proposal page): voting system, voting power, voting period, quorum and identity quorum are set by the author. "a proposal cannot be edited once it is open".

**15. Older proposals were imported from Snapshot.**
API: those proposals have `source: "snapshot"`. The platform labels them "Imported from Snapshot". The guide does not describe their rules.

## The troubleshooting table

Every message in section 06 is quoted from the platform's interface text, except two rows that describe situations rather than messages: "No Cast your vote panel" (the panel is only shown while a proposal is active, CODE) and "Not eligible, but you are sure you verified".
