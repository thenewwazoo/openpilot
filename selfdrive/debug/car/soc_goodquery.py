#!/usr/bin/env python3
"""
Known-good GM firmware query — uses the exact same request/offset/bus as fingerprinting.
If this gets responses, the panda/bus/safety-mode setup is correct and the BECM is reachable.
If this also times out, the problem is below the SoC query level.

Run with openpilot stopped (tmux kill-server).

Usage: python soc_goodquery.py
"""
import time
from panda import Panda
from opendbc.car.can_definitions import CanData
from opendbc.car.isotp_parallel_query import IsoTpParallelQuery
from opendbc.car.gm.values import GM_RX_OFFSET
from opendbc.car.fw_query_definitions import StdQueries
from opendbc.car.structs import CarParams

BUS = 0

# Same request/response format used in FW_QUERY_CONFIG for every GM ECU
REQUEST  = [StdQueries.SHORT_TESTER_PRESENT_REQUEST, b'\x1a\xc1']  # software module 1 part number
RESPONSE = [StdQueries.SHORT_TESTER_PRESENT_RESPONSE, b'\x5a\xc1']

# A handful of ECUs that should be present on the Bolt
ECUS = {
  0x7E0: "ECM",
  0x7E1: "TCM/BECM-alt",
  0x7E4: "BECM",
}

p = Panda()
p.reset()
p.set_safety_mode(CarParams.SafetyModel.elm327, 1)
p.can_clear(BUS)
time.sleep(0.1)

def can_recv(wait_for_one: bool = False) -> list[list[CanData]]:
  recv = p.can_recv()
  while len(recv) == 0 and wait_for_one:
    recv = p.can_recv()
  return [[CanData(addr, dat, bus) for addr, dat, bus in recv]]

def can_send(msgs: list[CanData]) -> None:
  p.can_send_many([(m.address, m.dat, m.src) for m in msgs])

print(f"Querying ECUs with GM_RX_OFFSET={hex(GM_RX_OFFSET)}, bus={BUS}")
print(f"  request : {[r.hex() for r in REQUEST]}")
print(f"  response: {[r.hex() for r in RESPONSE]}")
print()

query = IsoTpParallelQuery(can_send, can_recv, bus=BUS, addrs=list(ECUS.keys()),
                           request=REQUEST, response=RESPONSE,
                           response_offset=GM_RX_OFFSET)
results = query.get_data(timeout=1.0, total_timeout=5.0)

for addr, name in ECUS.items():
  key = (addr, None)
  if key in results:
    print(f"  OK  {name} ({hex(addr)}+{hex(GM_RX_OFFSET)}={hex(addr+GM_RX_OFFSET)}): {results[key].hex()}")
  else:
    print(f"  --  {name} ({hex(addr)}): no response")

p.set_safety_mode(CarParams.SafetyModel.noOutput)
