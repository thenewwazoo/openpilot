#!/usr/bin/env python3
"""
Directly query the BECM for SoC via UDS. Tries both response offsets so we
can see which one the BECM actually answers on.

Run with openpilot STOPPED (needs exclusive access to panda).

Usage: python soc_query.py
"""
from panda import Panda
from opendbc.car.can_definitions import CanData
from opendbc.car.isotp_parallel_query import IsoTpParallelQuery
from opendbc.car.structs import CarParams

BECM_ADDR = 0x7E4
SOC_DID   = b'\x22\x83\x34'
SOC_RESP  = b'\x62\x83\x34'
BUS       = 0

p = Panda()
p.set_safety_mode(CarParams.SafetyModel.elm327, 1)
p.can_clear(BUS)

def can_recv(wait_for_one: bool = False) -> list[list[CanData]]:
  recv = p.can_recv()
  while len(recv) == 0 and wait_for_one:
    recv = p.can_recv()
  return [[CanData(addr, dat, bus) for addr, dat, bus in recv]]

def can_send(msgs: list[CanData]) -> None:
  p.can_send_many([(m.address, m.dat, m.src) for m in msgs])

for offset_name, offset in [("standard (+0x8)", 0x8), ("GM (+0x400)", 0x400)]:
  p.can_clear(BUS)
  print(f"\n--- Trying response_offset={offset_name} (expects reply on {hex(BECM_ADDR + offset)}) ---")
  query = IsoTpParallelQuery(can_send, can_recv, bus=BUS, addrs=[BECM_ADDR],
                             request=[SOC_DID], response=[SOC_RESP],
                             response_offset=offset)
  results = query.get_data(timeout=1.0, total_timeout=2.0)
  if results:
    print(f"  Got response: {results}")
    raw = results.get((BECM_ADDR, None), b'')
    if raw:
      print(f"  Raw byte: {raw[0]}  =>  SoC = {(raw[0] * 39) / 99 / 100.0:.3f}")
  else:
    print("  No response (timed out)")

p.set_safety_mode(CarParams.SafetyModel.noOutput)
