#!/usr/bin/env python3
"""
Raw CAN diagnostic for BECM SoC query. Bypasses IsoTpParallelQuery entirely.

Run with openpilot stopped (tmux kill-server).

Steps:
  1. Verify panda is receiving frames on bus 0 (car must be on)
  2. Send raw ISO-TP single-frame UDS request to 0x7E4
  3. Dump all frames received on bus 0 for 2 seconds after the send
"""
import time
from panda import Panda
from opendbc.car.structs import CarParams

BUS       = 0
BECM_ADDR = 0x7E4
# ISO-TP single frame: byte 0 = 0x03 (length), then UDS ReadDataByIdentifier 0x8334
REQUEST   = bytes([0x03, 0x22, 0x83, 0x34, 0x00, 0x00, 0x00, 0x00])

p = Panda()
p.reset()
p.set_safety_mode(CarParams.SafetyModel.elm327, 1)
p.can_clear(BUS)
time.sleep(0.1)

# --- Step 1: verify we're receiving frames ---
print("Step 1: listening for 2s to verify bus 0 is live...")
deadline = time.monotonic() + 2.0
seen = {}
while time.monotonic() < deadline:
  for addr, dat, bus in p.can_recv():
    if bus == BUS:
      seen[addr] = dat
if seen:
  print(f"  OK — {len(seen)} distinct addresses seen on bus 0")
  for addr in sorted(seen)[:10]:
    print(f"    {hex(addr):8s}  {seen[addr].hex()}")
  if len(seen) > 10:
    print(f"    ... and {len(seen) - 10} more")
else:
  print("  WARNING: no frames received on bus 0 — is the car on?")

# --- Step 2: send raw request and dump everything that comes back ---
print(f"\nStep 2: sending raw UDS request to {hex(BECM_ADDR)}: {REQUEST.hex()}")
p.can_clear(BUS)
p.can_send(BECM_ADDR, REQUEST, BUS)
send_time = time.monotonic()

print(f"  Listening for 2s...")
responses = []
deadline = time.monotonic() + 2.0
while time.monotonic() < deadline:
  for addr, dat, bus in p.can_recv():
    if bus == BUS:
      responses.append((time.monotonic() - send_time, addr, dat))

if responses:
  print(f"  Received {len(responses)} frames:")
  for dt, addr, dat in responses:
    print(f"    +{dt*1000:6.1f}ms  addr={hex(addr):8s}  data={dat.hex()}")
else:
  print("  No frames received after send")

p.set_safety_mode(CarParams.SafetyModel.noOutput)
