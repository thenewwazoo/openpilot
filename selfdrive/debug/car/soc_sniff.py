#!/usr/bin/env python3
"""
Sniff bus 0 for any frames in the UDS diagnostic address range.
Run while openpilot is running to see what the BECM actually responds with.

Usage: python soc_sniff.py
"""
import time
import cereal.messaging as messaging

BECM_TX = 0x7E4
# possible response addresses
ADDRS_OF_INTEREST = {
  BECM_TX,
  BECM_TX + 0x8,    # standard OBD-II offset
  BECM_TX + 0x400,  # GM offset
}

logcan = messaging.sub_sock('can')

print(f"Listening on bus 0. Watching for frames near BECM (tx={hex(BECM_TX)})...")
print(f"  Standard response addr : {hex(BECM_TX + 0x8)}")
print(f"  GM response addr       : {hex(BECM_TX + 0x400)}")
print()

while True:
  for pkt in messaging.drain_sock(logcan, wait_for_one=True):
    for msg in pkt.can:
      if msg.src == 0 and msg.address in ADDRS_OF_INTEREST:
        print(f"{time.monotonic():.3f}  addr={hex(msg.address)}  data={msg.dat.hex()}")
