"""CLI: python -m beatoven.output_module {compile,simulate,replay-check,vectors,ports,send}

Only ``send`` can drive a device, and it refuses without an operator grant
file. Everything else uses the simulated Output Module.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import LoopbackTransport, OutputModuleDriver, OutputStream, SimulatedOutputModule, VirtualClock, from_pack


def _simulate(stream: OutputStream, offset: int = 0, record: list = None):
    clock = VirtualClock(1_000_000)
    device = SimulatedOutputModule(clock_offset_us=offset)
    transport = LoopbackTransport(device, clock)
    if record is not None:
        send = transport.send
        transport.send = lambda data: (record.append((clock.now_us(), data)), send(data))[1]
    driver = OutputModuleDriver(transport, clock)
    driver.connect()
    report = driver.play(stream)
    return report, device


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="beatoven.output_module")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compile", help="BeatOven Pack JSON -> Output Stream JSON")
    c.add_argument("pack")
    c.add_argument("--time-unit", default="bars", choices=["beats", "bars", "seconds"])
    c.add_argument("--clock-ppqn", type=int, default=24, help="pulses per quarter note; 0 for no clock")
    c.add_argument("-o", "--out")
    s = sub.add_parser("simulate", help="play an Output Stream on the simulated device; print the jack trace")
    s.add_argument("stream")
    s.add_argument("-o", "--out")
    r = sub.add_parser("replay-check", help="play twice on separately clocked devices and diff the jack traces")
    r.add_argument("stream")
    v = sub.add_parser("vectors", help="write golden vectors for firmware tests")
    v.add_argument("stream")
    v.add_argument("outdir")
    sub.add_parser("ports", help="list the MIDI ports the OS exposes")
    p = sub.add_parser("send", help="play an Output Stream to a real MIDI port (needs an operator grant)")
    p.add_argument("stream")
    p.add_argument("--out", required=True, help="substring of the output port name")
    p.add_argument("--in", dest="inp", required=True, help="substring of the input port name")
    p.add_argument("--grant", required=True, help="path to a Hardware Lane Grant file")
    p.add_argument("--lookahead-ms", type=int, default=100)
    a = ap.parse_args(argv)

    if a.cmd == "ports":
        from .midi_port import list_ports
        print(json.dumps(list_ports(), indent=2))
        return 0
    if a.cmd == "send":
        from .authority import HardwareLaneGrant
        from .midi_port import MidiPortTransport
        from .authority import HardwareLaneDenied
        try:
            grant = HardwareLaneGrant.load(Path(a.grant))
            grant.check()
        except HardwareLaneDenied as exc:
            print(f"hardware lane denied: {exc}", file=sys.stderr)
            return 1
        stream = OutputStream.from_dict(json.loads(Path(a.stream).read_text()))
        driver = OutputModuleDriver(MidiPortTransport(a.out, a.inp), grant=grant,
                                    lookahead_us=a.lookahead_ms * 1000, lead_us=a.lookahead_ms * 1000)
        state = driver.connect()
        if state.value != "SYNCED":
            print(f"not connected: {state.value}: {driver.reject_reason}", file=sys.stderr)
            return 1
        report = driver.play(stream)
        driver.close()
        print(f"ok={report.ok} state={report.final_state.value} played={report.played} "
              f"played_hash_ok={report.played_hash_ok} loss={report.loss_reason} {report.detail}")
        return 0 if report.ok else 1

    if a.cmd == "compile":
        stream = from_pack(json.loads(Path(a.pack).read_text()), time_unit=a.time_unit, clock_ppqn=a.clock_ppqn or None)
        text = json.dumps(stream.to_dict(), indent=2) + "\n"
        Path(a.out).write_text(text) if a.out else sys.stdout.write(text)
        return 0

    stream = OutputStream.from_dict(json.loads(Path(a.stream).read_text()))
    if a.cmd == "simulate":
        report, device = _simulate(stream)
        Path(a.out).write_text(device.trace_csv()) if a.out else sys.stdout.write(device.trace_csv())
        print(f"ok={report.ok} state={report.final_state.value} trace_sha256={device.trace_hash()}", file=sys.stderr)
        return 0 if report.ok else 1
    if a.cmd == "replay-check":
        (r1, d1), (r2, d2) = _simulate(stream, 0), _simulate(stream, 987_654_321)
        same = r1.ok and r2.ok and d1.trace_csv() == d2.trace_csv()
        print(f"stream_id={stream.stream_id}\nrun1={d1.trace_hash()}\nrun2={d2.trace_hash()}\nidentical={same}")
        return 0 if same else 1
    if a.cmd == "vectors":
        sent: list = []
        report, device = _simulate(stream, 0, sent)
        out = Path(a.outdir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "stream.json").write_text(json.dumps(stream.to_dict(), indent=2) + "\n")
        (out / "host_frames.hex").write_text("".join(f.hex() + "\n" for _t, f in sent))
        (out / "host_frame_times.csv").write_text(
            "frame,t_host_us\n" + "".join(f"{i},{t}\n" for i, (t, _f) in enumerate(sent)))
        (out / "expected_trace.csv").write_text(device.trace_csv())
        (out / "manifest.json").write_text(json.dumps({
            "stream_id": stream.stream_id, "trace_sha256": device.trace_hash(), "frames": len(sent),
            "events": len(stream.events), "host_clock_start_us": 1_000_000, "device_clock_offset_us": 0,
            "note": "host_frames.hex: one host->device SysEx frame per line, in send order. "
                    "host_frame_times.csv gives the host time each was sent and received.",
        }, indent=2) + "\n")
        return 0 if report.ok else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
