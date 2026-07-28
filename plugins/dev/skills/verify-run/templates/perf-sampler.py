#!/usr/bin/env python3
"""성능 지표 수집기 (검증용) — 서비스 단위 CPU/메모리 시계열 + 시나리오별 집계.

설계: 측정값은 "되는 것만" 원칙으로 native 도구에서 수집한다(이 머신서 실측 검증).
  백엔드/서비스:
  - 컨테이너(=서비스): `docker stats --no-stream --format '{{json .}}'`
  - pm2 프로세스(=서비스): `pm2 jlist` (monit.cpu / monit.memory)
  프론트(UI 검증 드라이버 런타임별 — Docker 제한 비대상, 절대값 기준):
  - 네이티브 iOS(시뮬레이터)·macOS(호스트 앱): `ps -o %cpu=,rss= -p <pid>` (RSS·CPU%)
  - 네이티브 Android(에뮬레이터/기기): `adb shell top -o PID,%CPU,RES -p <pid>` (RES=RSS·%CPU)
  - 웹(브라우저 클라이언트): CDP `Performance.getMetrics` → JSHeapUsedSize(메모리) + TaskDuration 증분(main-thread CPU%). stdlib WebSocket으로 직접 통신(zero-dep).
의존성: 표준 라이브러리만 (pip 설치 불필요). docker/pm2/ps/adb 는 PATH 전제.
  웹(--cdp)은 브라우저를 `--remote-debugging-port=<P> --remote-allow-origins=* --enable-precise-memory-info`로 띄워야 함.

정확도 caveat(실측 확인):
  - 샘플링 방식 → avg/peak·추이·시나리오 비교에 신뢰 가능. 간격(기본 1s) 미만 스파이크는 누락 가능.
  - macOS Docker Desktop: docker 절대 사용량·CPU코어%는 정확하나 MEM%의 분모는 Docker VM(호스트 전체 아님).
    → 보고는 절대 사용량(MB) + CPU%(코어환산) 기준. pm2/ps 값은 호스트 기준.

사용:
  # 1) 검증 시작 직후 백그라운드로 샘플링 시작
  python3 perf-sampler.py sample --out trace.jsonl --interval 1 \
      --pm2 --pid app=12345 --adb-pkg mobile=com.example.app --cdp web=9222 &
  SAMPLER=$!
  # 2) 각 시나리오 경계에 마커
  python3 perf-sampler.py mark --markers markers.jsonl --scenario SC-005 --event start
  #   ...시나리오 구동...
  python3 perf-sampler.py mark --markers markers.jsonl --scenario SC-005 --event end
  # 3) 검증 종료 시 샘플러 정지 후 보고서 생성
  kill -TERM $SAMPLER
  python3 perf-sampler.py report --trace trace.jsonl --markers markers.jsonl --out perf-report.md
"""
import argparse
import base64
import csv as _csv
import datetime
import json
import os
import re
import signal
import socket
import struct
import subprocess
import sys
import time
import urllib.request

BARS = "▁▂▃▄▅▆▇█"

# ---------- 공통 파서 ----------

_UNIT_MB = {"B": 1 / 1024 / 1024, "KIB": 1 / 1024, "MIB": 1.0, "GIB": 1024.0,
            "KB": 1 / 1024, "MB": 1.0, "GB": 1024.0, "K": 1 / 1024, "M": 1.0, "G": 1024.0}


def _to_mb(s):
    """'221.7MiB' / '1.913GiB' / '512kB' → MB(float). 실패 시 None."""
    if not s:
        return None
    m = re.match(r"\s*([0-9.]+)\s*([A-Za-z]+)\s*$", s)
    if not m:
        return None
    val, unit = float(m.group(1)), m.group(2).upper()
    return round(val * _UNIT_MB.get(unit, 1.0), 2)


def _pct(s):
    """'100.59%' → 100.59. 실패 시 None."""
    if s is None:
        return None
    try:
        return round(float(str(s).replace("%", "").strip()), 2)
    except ValueError:
        return None


def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""

# ---------- 수집원별 한 틱 ----------


def sample_docker(names=None):
    out = _run(["docker", "stats", "--no-stream", "--format", "{{json .}}"])
    recs = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = d.get("Name") or d.get("Container")
        if names and name not in names:
            continue
        mem_used = (d.get("MemUsage") or "").split("/")[0].strip()
        recs.append({"src": "docker", "service": name,
                     "cpu_pct": _pct(d.get("CPUPerc")), "mem_mb": _to_mb(mem_used)})
    return recs


def sample_pm2():
    out = _run(["pm2", "jlist"])
    recs = []
    start = out.find("[")
    if start < 0:
        return recs
    try:
        arr = json.loads(out[start:])
    except json.JSONDecodeError:
        return recs
    for p in arr:
        monit = p.get("monit", {})
        mem = monit.get("memory")
        recs.append({"src": "pm2", "service": p.get("name"),
                     "cpu_pct": _pct(monit.get("cpu")),
                     "mem_mb": round(mem / 1048576, 2) if mem else None})
    return recs


def sample_pids(pid_map):
    """pid_map: {service_name: pid}. ps 로 %cpu, rss(KB)."""
    recs = []
    for name, pid in pid_map.items():
        out = _run(["ps", "-o", "%cpu=,rss=", "-p", str(pid)])
        line = out.strip()
        if not line:
            recs.append({"src": "pid", "service": name, "cpu_pct": None, "mem_mb": None, "note": "no-process"})
            continue
        parts = line.split()
        cpu = _pct(parts[0]) if parts else None
        mem_mb = round(int(parts[1]) / 1024, 2) if len(parts) > 1 and parts[1].isdigit() else None
        recs.append({"src": "pid", "service": name, "cpu_pct": cpu, "mem_mb": mem_mb})
    return recs


def sample_adb(pkg_map, serial=None):
    """pkg_map: {service_name: android_package}. `top`으로 %CPU + RES(RSS) 한 번에.

    주의: dumpsys cpuinfo는 유휴 앱을 목록에 안 띄워(실측) CPU가 비므로 top을 쓴다.
    top %CPU는 단발 샘플이라 지속 부하엔 신뢰, 순간 스파이크는 누락 가능(best-effort).
    """
    base = ["adb"] + (["-s", serial] if serial else [])
    recs = []
    for name, pkg in pkg_map.items():
        cpu = mem_mb = None
        pid = (_run(base + ["shell", "pidof", pkg]).strip().split() or [""])[0]
        if not pid:
            recs.append({"src": "adb", "service": name, "cpu_pct": None, "mem_mb": None, "note": "no-process"})
            continue
        out = _run(base + ["shell", "top", "-b", "-n", "1", "-o", "PID,%CPU,RES", "-p", pid])
        for line in out.splitlines():
            parts = line.split()
            if parts and parts[0] == pid and len(parts) >= 3:
                cpu = _pct(parts[1])
                mem_mb = _to_mb(parts[2])  # '70M' / '1.2G'
                break
        recs.append({"src": "adb", "service": name, "cpu_pct": cpu, "mem_mb": mem_mb})
    return recs


# ---------- 웹 클라이언트(CDP, stdlib WS) ----------
# 브라우저 탭의 JS heap(메모리) + main-thread CPU(=TaskDuration 증분).
# pip 의존성 없이 표준 라이브러리만으로 CDP WebSocket을 직접 말한다(실측 검증됨).
# 전제: 브라우저를 `--remote-debugging-port=<P> --remote-allow-origins=* --enable-precise-memory-info`로 띄움.

class _Cdp:
    def __init__(self, port, url_substr=None):
        self.port = port
        self.url_substr = url_substr
        self.sock = None
        self.mid = 0
        self.prev_task = None
        self.prev_ts = None

    def _connect(self):
        targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json", timeout=5))
        page = None
        for t in targets:
            if t.get("type") != "page" or not t.get("webSocketDebuggerUrl"):
                continue
            if self.url_substr and self.url_substr not in (t.get("url") or ""):
                continue
            page = t
            break
        if not page:
            raise ConnectionError("no page target")
        url = page["webSocketDebuggerUrl"]
        hostport, _, path = url[5:].partition("/")
        host, _, p = hostport.partition(":")
        s = socket.create_connection((host, int(p)), timeout=5)
        key = base64.b64encode(os.urandom(16)).decode()
        s.sendall((f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\n"
                   f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                   f"Sec-WebSocket-Version: 13\r\nOrigin: http://{hostport}\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += s.recv(4096)
        self.sock = s
        self._cmd("Performance.enable")

    def _send(self, text):
        data = text.encode()
        n = len(data); mask = os.urandom(4)
        hdr = bytearray([0x81])
        if n < 126:
            hdr.append(0x80 | n)
        elif n < 65536:
            hdr.append(0x80 | 126); hdr += struct.pack(">H", n)
        else:
            hdr.append(0x80 | 127); hdr += struct.pack(">Q", n)
        hdr += mask
        self.sock.sendall(bytes(hdr) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _recv(self):
        def rd(n):
            b = b""
            while len(b) < n:
                c = self.sock.recv(n - len(b))
                if not c:
                    raise ConnectionError("closed")
                b += c
            return b
        payload = b""
        while True:
            h = rd(2); fin = h[0] & 0x80; op = h[0] & 0x0f; ln = h[1] & 0x7f; masked = h[1] & 0x80
            if ln == 126:
                ln = struct.unpack(">H", rd(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", rd(8))[0]
            mk = rd(4) if masked else b""
            pl = rd(ln)
            if masked:
                pl = bytes(b ^ mk[i % 4] for i, b in enumerate(pl))
            if op == 0x8:
                raise ConnectionError("close")
            if op in (0x0, 0x1, 0x2):
                payload += pl
                if fin:
                    return payload.decode("utf-8", "replace")

    def _cmd(self, method, params=None):
        self.mid += 1; i = self.mid
        self._send(json.dumps({"id": i, "method": method, "params": params or {}}))
        for _ in range(50):
            m = json.loads(self._recv())
            if m.get("id") == i:
                return m
        raise ConnectionError("no response")

    def sample(self, ts):
        if self.sock is None:
            self._connect()
        m = {x["name"]: x["value"] for x in self._cmd("Performance.getMetrics")["result"]["metrics"]}
        mem_mb = round(m.get("JSHeapUsedSize", 0) / 1048576, 2)
        cpu = None
        task = m.get("TaskDuration")
        if task is not None and self.prev_task is not None and ts > self.prev_ts:
            cpu = round((task - self.prev_task) / (ts - self.prev_ts) * 100, 2)  # main-thread %
        self.prev_task, self.prev_ts = task, ts
        return mem_mb, cpu

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass


def sample_cdp(clients, ts):
    """clients: {service_name: _Cdp}. 브라우저 JS heap + main-thread CPU."""
    recs = []
    for name, c in clients.items():
        try:
            mem_mb, cpu = c.sample(ts)
            recs.append({"src": "cdp", "service": name, "cpu_pct": cpu, "mem_mb": mem_mb})
        except (ConnectionError, OSError, ValueError, KeyError):
            c.sock = None  # 다음 틱에 재연결 시도
            recs.append({"src": "cdp", "service": name, "cpu_pct": None, "mem_mb": None, "note": "cdp-unavailable"})
    return recs

# ---------- 서브커맨드 ----------


def cmd_sample(a):
    pid_map = dict(kv.split("=", 1) for kv in a.pid) if a.pid else {}
    pkg_map = dict(kv.split("=", 1) for kv in a.adb_pkg) if a.adb_pkg else {}
    cdp_clients = {}
    for kv in (a.cdp or []):
        name, _, rest = kv.partition("=")
        port, _, url_substr = rest.partition(",")
        cdp_clients[name] = _Cdp(int(port), url_substr or None)
    stop = {"v": False}
    signal.signal(signal.SIGTERM, lambda *_: stop.update(v=True))
    signal.signal(signal.SIGINT, lambda *_: stop.update(v=True))
    t0 = time.time()
    with open(a.out, "a", buffering=1) as f:
        # 코어수 메타(보고서의 CPU% 해석용): 호스트 코어 + Docker VM 코어
        docker_ncpu = None
        di = _run(["docker", "info", "--format", "{{.NCPU}}"])
        try:
            docker_ncpu = int(di.strip())
        except (ValueError, AttributeError):
            pass
        f.write(json.dumps({"_meta": True, "host_ncpu": os.cpu_count(),
                            "docker_ncpu": docker_ncpu, "interval": a.interval},
                           ensure_ascii=False) + "\n")
        while not stop["v"]:
            ts = round(time.time(), 3)
            recs = []
            if not a.no_docker:
                recs += sample_docker(set(a.container) if a.container else None)
            if a.pm2:
                recs += sample_pm2()
            if pid_map:
                recs += sample_pids(pid_map)
            if pkg_map:
                recs += sample_adb(pkg_map, a.adb_serial)
            if cdp_clients:
                recs += sample_cdp(cdp_clients, ts)
            for r in recs:
                r["ts"] = ts
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            if a.duration and (time.time() - t0) >= a.duration:
                break
            # 인터럽트 반응 위해 잘게 sleep
            slept = 0.0
            while slept < a.interval and not stop["v"]:
                time.sleep(min(0.2, a.interval - slept))
                slept += 0.2
    for c in cdp_clients.values():
        c.close()
    return 0


def cmd_mark(a):
    with open(a.markers, "a", buffering=1) as f:
        f.write(json.dumps({"ts": round(time.time(), 3), "scenario": a.scenario,
                            "event": a.event}, ensure_ascii=False) + "\n")
    return 0


def _agg(samples):
    cpu = [s["cpu_pct"] for s in samples if s.get("cpu_pct") is not None]
    mem = [s["mem_mb"] for s in samples if s.get("mem_mb") is not None]
    return {
        "n": len(samples),
        "cpu_avg": round(sum(cpu) / len(cpu), 1) if cpu else None,
        "cpu_peak": round(max(cpu), 1) if cpu else None,
        "mem_avg": round(sum(mem) / len(mem), 1) if mem else None,
        "mem_peak": round(max(mem), 1) if mem else None,
    }


def _table(by_service):
    # CPU%는 100%=1코어. '≈코어peak' = cpu_peak/100 (1코어 환산).
    lines = ["| 서비스 | 출처 | 샘플 | CPU% avg | CPU% peak | ≈코어peak | MEM(MB) avg | MEM(MB) peak |",
             "|--------|------|------|----------|-----------|-----------|-------------|--------------|"]
    for (svc, src), agg in sorted(by_service.items()):
        cores = round(agg["cpu_peak"] / 100, 2) if agg["cpu_peak"] is not None else None
        lines.append(f"| {svc} | {src} | {agg['n']} | {agg['cpu_avg']} | {agg['cpu_peak']} | {cores} | {agg['mem_avg']} | {agg['mem_peak']} |")
    return "\n".join(lines)


def _spark(vals, vmax=None):
    vals = [v for v in vals if v is not None]
    if not vals:
        return ""
    vmax = vmax or max(vals) or 1
    return "".join(BARS[min(len(BARS) - 1, int(v / vmax * (len(BARS) - 1)))] for v in vals)


def _series_by_service(samples):
    """{(service,src): [(ts,cpu,mem)...]} ts 정렬."""
    g = {}
    for s in samples:
        g.setdefault((s.get("service"), s.get("src")), []).append((s["ts"], s.get("cpu_pct"), s.get("mem_mb")))
    for k in g:
        g[k].sort(key=lambda x: x[0])
    return g


def _write_csv(path, samples):
    """wide CSV: ts,iso + 서비스별 cpu/mem (스프레드시트 차트용)."""
    services = sorted({(s.get("service"), s.get("src")) for s in samples})
    by_ts = {}
    for s in samples:
        by_ts.setdefault(s["ts"], {})[(s.get("service"), s.get("src"))] = s
    cols = ["ts", "iso"]
    for svc, src in services:
        cols += [f"{svc}[{src}].cpu%", f"{svc}[{src}].mem_mb"]
    with open(path, "w", newline="") as f:
        w = _csv.writer(f)
        w.writerow(cols)
        for ts in sorted(by_ts):
            row = [ts, datetime.datetime.fromtimestamp(ts).isoformat(timespec="seconds")]
            for svc, src in services:
                rec = by_ts[ts].get((svc, src), {})
                row += [rec.get("cpu_pct", ""), rec.get("mem_mb", "")]
            w.writerow(row)


def cmd_report(a):
    meta = {}
    samples = []
    with open(a.trace) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("_meta"):
                meta = rec
            else:
                samples.append(rec)
    markers = []
    if a.markers:
        try:
            with open(a.markers) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        markers.append(json.loads(line))
        except FileNotFoundError:
            pass

    def group(rows):
        g = {}
        for r in rows:
            g.setdefault((r.get("service"), r.get("src")), []).append(r)
        return {k: _agg(v) for k, v in g.items()}

    host_n = meta.get("host_ncpu")
    docker_n = meta.get("docker_ncpu")
    interval = meta.get("interval", a.interval)

    out = ["# 성능 보고 (검증)", ""]
    if samples:
        ts_all = [s["ts"] for s in samples]
        out += [f"- 측정 구간: {round(max(ts_all) - min(ts_all), 1)}s, 총 샘플 {len(samples)}, 간격≈{interval}s"]
    out += [
        f"- **CPU% 읽는 법: 100% = CPU 1코어 풀가동** (머신 전체 아님). 호스트 {host_n}코어"
        + (f" / Docker VM {docker_n}코어" if docker_n else "") + ". `≈코어peak`=peak/100(1코어 환산).",
        f"  - `docker` 값은 **Docker VM 코어 기준**(최대 {docker_n * 100 if docker_n else '?'}%), `pm2`/`pid`/`adb` 값은 **호스트 {host_n}코어 기준**. 둘 다 100%=1코어이나 전체 대비 분모가 다름.",
        "- 샘플링 기반(추이·peak 신뢰, 간격 미만 스파이크 누락 가능). docker MEM은 절대 사용량(MB) 기준 — MEM%의 분모는 Docker VM.",
        "",
    ]
    out += ["## 전구간 서비스별 (full-run)", "", _table(group(samples)), ""]

    # 시계열(스파크라인) — 활동 있는 서비스 위주(peak CPU 또는 MEM 변동)
    series = _series_by_service(samples)
    out += ["## 시계열 (time-series)",
            "_CPU% 추이. 스파크라인은 각 서비스 자기 peak 기준 정규화(▁최소~█peak). 전체 수치는 CSV 참조._", ""]
    rows = []
    for (svc, src), pts in series.items():
        cpus = [c for _, c, _ in pts]
        mems = [m for _, _, m in pts]
        cpu_peak = max([c for c in cpus if c is not None], default=0)
        mem_peak = max([m for m in mems if m is not None], default=0)
        rows.append((cpu_peak, svc, src, cpus, mems, mem_peak))
    rows.sort(reverse=True)  # peak CPU 큰 순
    out += ["| 서비스 | 출처 | CPU 추이 (peak) | MEM 추이 (peak MB) |",
            "|--------|------|-----------------|--------------------|"]
    for cpu_peak, svc, src, cpus, mems, mem_peak in rows:
        out.append(f"| {svc} | {src} | `{_spark(cpus)}` ({cpu_peak}%) | `{_spark(mems)}` ({mem_peak}) |")
    out.append("")

    # 시나리오 윈도우 (start/end 짝)
    starts = {}
    windows = []
    for m in sorted(markers, key=lambda x: x["ts"]):
        key = m.get("scenario")
        if m.get("event") == "start":
            starts[key] = m["ts"]
        elif m.get("event") == "end" and key in starts:
            windows.append((key, starts.pop(key), m["ts"]))
    if windows:
        out += ["## 시나리오별 (per-scenario)", ""]
        for name, s, e in windows:
            win = [r for r in samples if s <= r["ts"] <= e]
            out += [f"### {name}  ({round(e - s, 2)}s, 샘플 {len(win)})", "", _table(group(win)), ""]
    else:
        out += ["## 시나리오별 (per-scenario)", "", "_시나리오 마커 없음 — `mark` 서브커맨드로 start/end 기록 필요._", ""]

    text = "\n".join(out)
    csv_path = None
    if a.out:
        with open(a.out, "w") as f:
            f.write(text)
        csv_path = (a.out[:-3] if a.out.endswith(".md") else a.out) + "-timeseries.csv"
        _write_csv(csv_path, samples)
        out.append(f"_전체 시계열(샘플 단위) CSV: `{csv_path}`_")
        with open(a.out, "w") as f:
            f.write("\n".join(out))
        print(f"wrote {a.out}")
        print(f"wrote {csv_path}")
    else:
        print(text)
    return 0


def main():
    p = argparse.ArgumentParser(description="검증용 성능 지표 수집기(서비스 단위 CPU/메모리 시계열).")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sample", help="시계열 샘플링(SIGTERM까지 또는 --duration).")
    s.add_argument("--out", required=True)
    s.add_argument("--interval", type=float, default=1.0)
    s.add_argument("--duration", type=float, default=0.0, help="0이면 SIGTERM까지")
    s.add_argument("--no-docker", action="store_true")
    s.add_argument("--container", action="append", help="특정 컨테이너만(반복). 미지정 시 전체")
    s.add_argument("--pm2", action="store_true")
    s.add_argument("--pid", action="append", help="name=pid (반복)")
    s.add_argument("--adb-pkg", action="append", help="name=package (반복)")
    s.add_argument("--adb-serial", default=None)
    s.add_argument("--cdp", action="append",
                   help="웹 클라이언트: name=port 또는 name=port,url부분문자열 (반복). "
                        "브라우저를 --remote-debugging-port=<port> --remote-allow-origins=* "
                        "--enable-precise-memory-info 로 띄워야 함")
    s.set_defaults(fn=cmd_sample)

    m = sub.add_parser("mark", help="시나리오 경계 마커 기록.")
    m.add_argument("--markers", required=True)
    m.add_argument("--scenario", required=True)
    m.add_argument("--event", required=True, choices=["start", "end"])
    m.set_defaults(fn=cmd_mark)

    r = sub.add_parser("report", help="시계열+마커 → 서비스별/시나리오별 보고서.")
    r.add_argument("--trace", required=True)
    r.add_argument("--markers", default=None)
    r.add_argument("--out", default=None)
    r.add_argument("--interval", type=float, default=1.0, help="보고서 표기용")
    r.set_defaults(fn=cmd_report)

    a = p.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
