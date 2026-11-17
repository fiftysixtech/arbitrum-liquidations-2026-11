#!/usr/bin/env python3
"""Check any transaction in this dataset straight from an Arbitrum node. Python 3, standard library only.

    python3 check_tx.py 0x7ed7...e53 0x1c76...ea5                 # full 66-character transaction hashes
    RPC=https://your-arbitrum-rpc python3 check_tx.py <hash> ...  # RPC defaults to http://127.0.0.1:8547,
                                                                  # a local Arbitrum (Nitro) node

For each transaction it prints status, block, UTC time and recipient; every Atlas solver operation (bid,
executed, success); the Chainlink update events; and every token transfer, summed per token / from / to.
Read-only: eth_getTransactionByHash, eth_getTransactionReceipt, eth_getBlockByNumber, eth_call.
"""
import json
import os
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

RPC = os.environ.get("RPC", "http://127.0.0.1:8547")
T_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
T_ORACLE_2026 = "0x8d530b9ddc4b318d28fdd4c3a21fcfecece54c1a72a824f262985b99afef009b"
_id = 0


def rpc(method, params):
    global _id
    _id += 1
    req = urllib.request.Request(RPC, json.dumps({"jsonrpc": "2.0", "id": _id, "method": method, "params": params}).encode(),
                                 {"content-type": "application/json"})
    out = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if "error" in out:
        raise RuntimeError(f"{method}: {out['error']}")
    return out["result"]


def keccak_topic(sig: str) -> str:
    """Topic of an event signature, asked of the node itself (web3_sha3), so no crypto library is needed."""
    return rpc("web3_sha3", ["0x" + sig.encode().hex()])


meta = {}


def token(addr):
    if addr not in meta:
        def call(sel):
            try:
                return rpc("eth_call", [{"to": addr, "data": sel}, "latest"])
            except Exception:
                return "0x"
        d = call("0x313ce567")  # decimals()
        s = call("0x95d89b41")  # symbol()
        dec = int(d, 16) if d and d != "0x" else 18
        sym = "?"
        try:
            raw = bytes.fromhex(s[2:])
            n = int.from_bytes(raw[32:64], "big")
            sym = raw[64:64 + n].decode("utf-8", "replace") or "?"
        except Exception:
            pass
        meta[addr] = (dec, sym)
    return meta[addr]


def addr(word: str) -> str:
    return "0x" + word[-40:]


def short(a: str) -> str:
    return a[:8] + "…" + a[-4:]


def main(hashes):
    t_solver = keccak_topic("SolverTxResult(address,address,address,address,uint256,bool,bool,uint256)")
    for h in hashes:
        print("=" * 100)
        tx = rpc("eth_getTransactionByHash", [h])
        rc = rpc("eth_getTransactionReceipt", [h])
        if not tx or not rc:
            print(f"{h}: not found on this node")
            continue
        blk = int(rc["blockNumber"], 16)
        b = rpc("eth_getBlockByNumber", [hex(blk), False])
        when = datetime.fromtimestamp(int(b["timestamp"], 16), timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"{h}\n  status {'SUCCESS' if rc['status'] == '0x1' else 'FAILED'}  block {blk:,}  {when}  "
              f"from {tx['from']} to {tx['to']}  logs {len(rc['logs'])}")
        flows = defaultdict(int)
        for lg in rc["logs"]:
            t = lg["topics"]
            if not t:
                continue
            if t[0] == t_solver and len(t) >= 3:
                d = lg["data"][2:]
                w = [d[i:i + 64] for i in range(0, len(d), 64)]
                bid = int(w[1], 16) / 1e18
                print(f"  atlas op: solver {addr(t[1])} bid {bid:.6f} ETH executed {int(w[2], 16) == 1} success {int(w[3], 16) == 1}")
            elif t[0] == T_ORACLE_2026 and len(t) >= 2:
                print(f"  chainlink update: aggregator {lg['address']} round {int(t[1], 16)}")
            elif t[0] == T_TRANSFER and len(t) == 3:
                flows[(lg["address"].lower(), addr(t[1]), addr(t[2]))] += int(lg["data"], 16) if lg["data"] != "0x" else 0
        rows = []
        for (tok, f, to), amt in flows.items():
            dec, sym = token(tok)
            rows.append((sym, amt / 10 ** dec, f, to))
        rows.sort(key=lambda r: (r[0], -r[1]))
        print("  token transfers (summed per token, from, to):")
        for sym, amt, f, to in rows:
            print(f"    {sym[:8]:<8} {amt:>20,.6f}   {short(f)} -> {short(to)}")


if __name__ == "__main__":
    hs = [a for a in sys.argv[1:] if a.startswith("0x")]
    if not hs or any(len(a) != 66 for a in hs):
        sys.exit(__doc__)
    main(hs)
