"""NLE-style timeline spans: cases/sessions + L1/L2/L3 page tracks.

X axis is log line number. Hierarchy matching is hardcoded from
docs/page-hierarchy.md (not the spec business-order table).
"""
from __future__ import annotations

import re
from typing import Any

from parser import LOG_RE

UUID_RE = re.compile(
    r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)
LOADED_PLAN_RE = re.compile(
    r"loaded plan:\s*brand:\s*([^,]+),\s*series:\s*([^,]+)", re.I
)
SIDE_RE = re.compile(r"operation side\s+(left|right|l|r|左|右)", re.I)
VERSION_RE = re.compile(r"Titan vesrion\s+(\S+)")
VERSION_RE_ALT = re.compile(r"Titan version\s+(\S+)", re.I)
FEMUR_REG_ERR_RE = re.compile(r"femur register error\s+([0-9.]+)", re.I)
TIBIA_REG_ERR_RE = re.compile(r"tibia register error\s+([0-9.]+)", re.I)
VERIFY_ERR_RE = re.compile(
    r"probe verify (femur|tibia) point\s+(\d+)\s+error:\s*([0-9.]+)", re.I
)
NAIL_ERR_RE = re.compile(r"nail verify error\s+([0-9.]+)", re.I)
ERROR_LIMIT_MM = 1.0

ALL_LINES_LIMIT = 30_000
HUGE_LINES = 80_000
DEFAULT_WINDOW = 12_000

CASE_PALETTE = [
    "#3d8bff",
    "#ff8c42",
    "#e63956",
    "#2ec4b6",
    "#7b61ff",
    "#f4c430",
    "#ff5d8f",
    "#3ddc97",
    "#c77dff",
    "#ffb703",
]
UNKNOWN_CASE_COLOR = "#6b7684"

L1_LABELS = ("登录", "方案管理", "方案预览", "准备", "术中评估", "导航")


def _norm_side(token: str) -> str | None:
    s = (token or "").strip().lower()
    if s in ("left", "l", "左"):
        return "left"
    if s in ("right", "r", "右"):
        return "right"
    return None


def _side_zh(side: str | None) -> str:
    if side == "left":
        return "左"
    if side == "right":
        return "右"
    return ""


def _msg(ev: dict) -> str:
    return ev.get("message") or ev.get("raw") or ""


def match_l1(msg: str) -> tuple[str, str | None]:
    """Return (action, label). action: enter | end_if | end_all | none."""
    if "Titan Application Exit" in msg:
        return "end_all", None
    if "Titan Application Startup" in msg:
        return "enter", "登录"
    if "from login page switch to plan manage" in msg:
        return "enter", "方案管理"
    if "from home page switch to plan manage" in msg:
        return "enter", "方案管理"
    if "from plan manage page switch to home" in msg:
        return "end_if", "方案管理"
    if "take over planviewer" in msg:
        return "enter", "方案预览"
    if "take over prepare" in msg:
        return "enter", "准备"
    if "click start operation" in msg:
        return "enter", "准备"
    if "take over gapmeasure" in msg:
        return "enter", "术中评估"
    if "take over cutter navigation" in msg:
        return "enter", "导航"
    if "robot motion take over" in msg:
        return "enter", "导航"
    return "none", None


def match_l2(msg: str) -> tuple[str, str | None]:
    if "enter saw mode" in msg:
        return "enter", "摆锯可视化"
    if "exit saw mode" in msg:
        return "exit", "摆锯可视化"
    if "enter tibia draw line mode" in msg:
        return "enter", "胫骨中线绘制"
    if "exit tibia draw line mode" in msg:
        return "exit", "胫骨中线绘制"
    if "cutter before in gapmeasure" in msg:
        return "enter", "截骨前"
    if "cutter after in gapmeasure" in msg:
        return "enter", "截骨后"
    if "switch to femur register step" in msg:
        return "enter", "股骨注册"
    if "switch to femur check step" in msg:
        return "enter", "股骨验证"
    if "switch to tibia register step" in msg:
        return "enter", "胫骨注册"
    if "switch to tibia check step" in msg:
        return "enter", "胫骨验证"
    if "switch femur distal check step" in msg:
        return "enter", "股骨远端验证"
    if "switch femur poster check step" in msg:
        return "enter", "股骨后方验证"
    if "switch femur distal step" in msg:
        return "enter", "股骨远端截骨"
    if "switch femur poster step" in msg:
        return "enter", "股骨四合一"
    if "switch tibia check step" in msg:
        return "enter", "胫骨近端验证"
    if "switch tibia step" in msg:
        return "enter", "胫骨近端截骨"
    return "none", None


def match_l3(msg: str) -> tuple[str, str | None]:
    if "finish collect gap" in msg:
        return "exit", "采集间隙"
    if "start collect gap" in msg:
        return "enter", "采集间隙"
    if "marker nail wighet open" in msg or "marker nail wigdet" in msg:
        return "enter", "标记钉采集"
    if "ankle collect step" in msg or "hip collect step" in msg:
        return "enter", "髋/踝中心"
    return "none", None


def match_device(msg: str) -> tuple[str, str | None]:
    """Background / device-status events. Not surgical L1-L3."""
    low = msg.lower()
    if "write camera para" in low or "take over camera" in low:
        return "tick", "相机"
    if "robot maintenance" in low:
        return "tick", "机械臂维护"
    if "take over setting" in low:
        return "tick", "设置"
    if "take over emc" in low or low.startswith("emc ") or " emc " in f" {low} ":
        return "tick", "EMC"
    if "tracker" in low:
        return "tick", "示踪器"
    if "ndi" in low and (
        "disconnect" in low or "not connected" in low or "reconnect" in low
    ):
        return "tick", "示踪器"
    return "none", None


def _time_index(events: list[dict], line_count: int) -> list[str]:
    times = [""] * max(line_count, 0)
    for ev in events:
        t = ev.get("time") or ""
        if not t:
            continue
        a = int(ev.get("line") or 1)
        b = int(ev.get("line_end") or a)
        for i in range(max(1, a), min(line_count, b) + 1):
            if not times[i - 1]:
                times[i - 1] = t
    last = ""
    for i, t in enumerate(times):
        if t:
            last = t
        elif last:
            times[i] = last
    return times


def _mark_index(events: list[dict], line_count: int) -> tuple[list[str], list[bool]]:
    marks = ["none"] * max(line_count, 0)
    noise = [False] * max(line_count, 0)
    rank = {"none": 0, "key": 1, "anomaly": 2}
    for ev in events:
        a = int(ev.get("line") or 1)
        b = int(ev.get("line_end") or a)
        is_noise = ev.get("source") == "noise" or ev.get("category") == "noise"
        mk = ev.get("mark") or "none"
        for i in range(max(1, a), min(line_count, b) + 1):
            if is_noise:
                noise[i - 1] = True
            if mk in rank and rank[mk] > rank[marks[i - 1]]:
                marks[i - 1] = mk
    return marks, noise


def _span(
    sid: str,
    label: str,
    start: int,
    end: int,
    times: list[str],
    extra: dict | None = None,
) -> dict:
    n = len(times)
    s = max(1, start)
    e = max(s, min(end, n) if n else end)
    rec = {
        "id": sid,
        "label": label,
        "start": s,
        "end": e,
        "t0": times[s - 1] if n and s <= n else "",
        "t1": times[e - 1] if n and e <= n else "",
    }
    if extra:
        rec.update(extra)
    return rec


class _Open:
    __slots__ = ("label", "start", "extra")

    def __init__(self, label: str, start: int, extra: dict | None = None):
        self.label = label
        self.start = start
        self.extra = extra or {}


def _close(open_span: _Open | None, end: int, times: list[str], bucket: list, prefix: str) -> None:
    if open_span is None:
        return
    if end < open_span.start:
        end = open_span.start
    extra = dict(open_span.extra)
    extra.setdefault("level", {"l1": 1, "l2": 2, "l3": 3, "dev": 0}.get(prefix))
    bucket.append(
        _span(
            f"{prefix}-{len(bucket)}",
            open_span.label,
            open_span.start,
            end,
            times,
            extra,
        )
    )


def parse_error_event(msg: str) -> dict | None:
    m = FEMUR_REG_ERR_RE.search(msg)
    if m:
        return {"target": "股骨注册", "label": "RMS", "value": float(m.group(1))}
    m = TIBIA_REG_ERR_RE.search(msg)
    if m:
        return {"target": "胫骨注册", "label": "RMS", "value": float(m.group(1))}
    m = VERIFY_ERR_RE.search(msg)
    if m:
        bone = "股骨" if m.group(1).lower() == "femur" else "胫骨"
        pt = int(m.group(2))
        return {
            "target": f"{bone}验证",
            "label": f"点{pt}",
            "point": pt,
            "value": float(m.group(3)),
        }
    m = NAIL_ERR_RE.search(msg)
    if m:
        return {"target": "标记钉采集", "label": "验证", "value": float(m.group(1))}
    return None


def collect_errors(events: list[dict]) -> list[dict]:
    out = []
    for ev in events:
        rec = parse_error_event(_msg(ev))
        if not rec:
            continue
        rec["line"] = int(ev.get("line") or 1)
        rec["over"] = rec["value"] > ERROR_LIMIT_MM
        out.append(rec)
    return out


def attach_errors(spans: list[dict], errors: list[dict]) -> None:
    """Put error readings onto the matching page span (last value per label)."""
    for sp in spans:
        hit = [e for e in errors if e["target"] == sp.get("label")
               and int(sp["start"]) <= e["line"] <= int(sp["end"]) + 12]
        if not hit:
            continue
        by_key: dict = {}
        for e in hit:
            by_key[e["label"]] = e
        ordered = sorted(by_key.values(), key=lambda e: (e.get("point") or 0, e["line"]))
        sp["errors"] = [
            {
                "label": e["label"],
                "value": round(e["value"], 3),
                "over": bool(e["over"]),
                "line": e["line"],
            }
            for e in ordered
        ]
        mx = max(e["value"] for e in ordered)
        sp["error_max"] = round(mx, 3)


def build_page_tracks(events: list[dict], line_count: int, times: list[str]) -> dict:
    l1: list[dict] = []
    l2: list[dict] = []
    l3: list[dict] = []
    device: list[dict] = []
    l2_ticks: list[dict] = []
    o1: _Open | None = None
    o2: _Open | None = None
    o3: _Open | None = None

    def close_l3(end: int) -> None:
        nonlocal o3
        _close(o3, end, times, l3, "l3")
        o3 = None

    def close_l2(end: int) -> None:
        nonlocal o2
        close_l3(end)
        _close(o2, end, times, l2, "l2")
        o2 = None

    def close_l1(end: int) -> None:
        nonlocal o1
        close_l2(end)
        _close(o1, end, times, l1, "l1")
        o1 = None

    for ev in events:
        msg = _msg(ev)
        line = int(ev.get("line") or 1)
        prev = line - 1 if line > 1 else line

        a1, lab1 = match_l1(msg)
        if a1 == "end_all":
            close_l1(line)
            continue
        if a1 == "end_if":
            if o1 and o1.label == lab1:
                close_l1(prev if prev >= o1.start else line)
            continue
        if a1 == "enter" and lab1:
            if o1 and o1.label == lab1:
                pass  # same L1 (e.g. cutter nav + robot motion)
            else:
                close_l1(prev if o1 else prev)
                o1 = _Open(lab1, line)
            # L1 enter still falls through so same-line L2 can open
        a2, lab2 = match_l2(msg)
        if a2 == "exit":
            if o2 and (lab2 is None or o2.label == lab2):
                _close(o2, line, times, l2, "l2")
                o2 = None
                close_l3(line)
            elif lab2:
                last = l2_ticks[-1] if l2_ticks else None
                if not (last and last["label"] == lab2 and line - int(last["end"]) <= 2):
                    l2_ticks.append(
                        _span(f"l2-{len(l2)+len(l2_ticks)}", lab2, line, line, times, {"level": 2})
                    )
        elif a2 == "enter" and lab2:
            if o2 and o2.label == lab2:
                pass
            else:
                close_l3(prev)
                _close(o2, prev if o2 else prev, times, l2, "l2")
                o2 = _Open(lab2, line)

        a3, lab3 = match_l3(msg)
        if a3 == "exit":
            if o3 and (lab3 is None or o3.label == lab3):
                _close(o3, line, times, l3, "l3")
                o3 = None
        elif a3 == "enter" and lab3:
            if o3 and o3.label == lab3:
                pass
            else:
                _close(o3, prev if o3 else prev, times, l3, "l3")
                o3 = _Open(lab3, line)

        ad, labd = match_device(msg)
        if ad == "tick" and labd:
            last = device[-1] if device else None
            if last and last["label"] == labd and line - int(last["end"]) <= 2:
                last["end"] = line
            else:
                device.append(
                    _span(f"dev-{len(device)}", labd, line, line, times, {"level": 0})
                )

    close_l1(line_count)
    l2.extend(l2_ticks)
    errs = collect_errors(events)
    attach_errors(l2, errs)
    attach_errors(l3, errs)
    return {"l1": l1, "l2": l2, "l3": l3, "device": device}


def _extract_version(msg: str) -> str | None:
    m = VERSION_RE.search(msg) or VERSION_RE_ALT.search(msg)
    return m.group(1) if m else None


def _extract_uuid(msg: str) -> str | None:
    if "start load plan uuid" in msg or "load plan sucess" in msg or "create ctfree plan uuid" in msg:
        m = UUID_RE.search(msg)
        return m.group(1).lower() if m else None
    return None


def build_sessions_and_cases(events: list[dict], line_count: int, times: list[str]) -> dict:
    sessions_raw: list[dict] = []
    markers: list[dict] = []
    cur: dict | None = None

    def start_session(line: int, t: str) -> dict:
        return {
            "start": line,
            "end": line_count,
            "t0": t,
            "startups": [line],
            "exits": [],
            "uuid": None,
            "brand": None,
            "series": None,
            "side": None,
            "uuid_line": None,
            "plan_changes": [],  # (line, uuid)
            "version": None,
            "version_line": None,
        }

    for ev in events:
        msg = _msg(ev)
        line = int(ev.get("line") or 1)
        t = ev.get("time") or (times[line - 1] if times and line <= len(times) else "")

        if "Titan Application Startup" in msg:
            markers.append({"line": line, "kind": "startup", "t": t})
            if cur is not None:
                meaningful = (
                    cur["uuid"]
                    or cur["plan_changes"]
                    or (line - cur["start"] > 8)
                )
                last_startup = cur["startups"][-1] if cur["startups"] else cur["start"]
                if not meaningful and line - last_startup <= 8:
                    cur["startups"].append(line)
                else:
                    cur["end"] = max(cur["start"], line - 1)
                    sessions_raw.append(cur)
                    cur = start_session(line, t)
            else:
                cur = start_session(line, t)
            continue

        if "Titan Application Exit" in msg:
            markers.append({"line": line, "kind": "exit", "t": t})
            if cur is not None:
                cur["exits"].append(line)
                cur["end"] = line
                sessions_raw.append(cur)
                cur = None
            elif sessions_raw and not sessions_raw[-1]["exits"]:
                sessions_raw[-1]["exits"].append(line)
                sessions_raw[-1]["end"] = line
            elif sessions_raw:
                # extra exit shortly after a closed session — extend
                prev = sessions_raw[-1]
                if line - prev["end"] <= 30:
                    prev["exits"].append(line)
                    prev["end"] = line
            continue

        if cur is None:
            continue

        ver = _extract_version(msg)
        if ver:
            if not cur.get("version"):
                cur["version"] = ver
                cur["version_line"] = line
            for mk in markers:
                if mk["kind"] == "startup" and mk["line"] >= cur["start"] and mk["line"] <= line:
                    if not mk.get("version"):
                        mk["version"] = ver
                        mk["version_line"] = line

        uid = _extract_uuid(msg)
        if uid:
            if cur["uuid"] is None:
                cur["uuid"] = uid
                cur["uuid_line"] = line
            elif uid != cur["uuid"]:
                cur["plan_changes"].append((line, uid))
                cur["uuid"] = uid
                cur["uuid_line"] = line

        lm = LOADED_PLAN_RE.search(msg)
        if lm:
            cur["brand"] = (lm.group(1) or "").strip()
            cur["series"] = (lm.group(2) or "").strip()

        sm = SIDE_RE.search(msg)
        if sm:
            cur["side"] = _norm_side(sm.group(1))

    if cur is not None:
        cur["end"] = line_count
        sessions_raw.append(cur)

    # If file has events before the first startup, they belong to no session.
    # Assign case keys: first uuid paints the whole session; extra uuids split.
    case_order: list[str] = []
    case_meta: dict[str, dict] = {}

    def remember(uid: str, brand, series, side) -> None:
        if uid not in case_meta:
            case_order.append(uid)
            case_meta[uid] = {"brand": brand, "series": series, "side": side}
        else:
            meta = case_meta[uid]
            if brand and not meta["brand"]:
                meta["brand"] = brand
            if series and not meta["series"]:
                meta["series"] = series
            if side and not meta["side"]:
                meta["side"] = side

    pieces: list[dict] = []  # session pieces after uuid splits
    for idx, ses in enumerate(sessions_raw):
        changes = ses.get("plan_changes") or []
        if not changes:
            uid = ses.get("uuid")
            if uid:
                remember(uid, ses.get("brand"), ses.get("series"), ses.get("side"))
            pieces.append(
                {
                    **ses,
                    "session_i": idx,
                    "uuid": uid,
                }
            )
        else:
            # first uuid covers session start → first change-1; then each change
            first_uid = ses.get("uuid")
            # reconstruct ordered unique changes including the first uuid
            # plan_changes are subsequent uuids; first uuid was set earlier
            # We don't have the first uuid line stored as a change. uuid_line is last.
            # Walk with a simpler split: use changes as split points, prefix gets
            # the uuid that was current before the first change.
            # Rebuild: first uuid is whatever was set before first change.
            # Actually we overwrote ses["uuid"] to the last one. Recover first from
            # the fact that first uuid is NOT in changes as the initial.
            # Store initial uuid: the uuid before first plan_change.
            # We lost it. Re-scan this session's events.
            initial = None
            splits: list[tuple[int, str]] = []
            for ev in events:
                line = int(ev.get("line") or 1)
                if line < ses["start"] or line > ses["end"]:
                    continue
                uid = _extract_uuid(_msg(ev))
                if uid:
                    if initial is None:
                        initial = uid
                        remember(uid, None, None, None)
                    elif uid != (splits[-1][1] if splits else initial):
                        splits.append((line, uid))
                        remember(uid, None, None, None)
            cursor_uid = initial
            cursor_start = ses["start"]
            for sl, uid in splits:
                pieces.append(
                    {
                        **ses,
                        "session_i": idx,
                        "uuid": cursor_uid,
                        "start": cursor_start,
                        "end": max(cursor_start, sl - 1),
                    }
                )
                cursor_uid = uid
                cursor_start = sl
            pieces.append(
                {
                    **ses,
                    "session_i": idx,
                    "uuid": cursor_uid,
                    "start": cursor_start,
                    "end": ses["end"],
                }
            )

    # Number restarts per uuid (across pieces that share session_i collapse first)
    # Build display sessions (one per original session)
    restart_count: dict[str, int] = {}
    sessions_out: list[dict] = []
    for idx, ses in enumerate(sessions_raw):
        uid = None
        for p in pieces:
            if p["session_i"] == idx and p.get("uuid"):
                uid = p["uuid"]
                break
        if uid is None:
            uid = ses.get("uuid")
        key = uid or ""
        if uid:
            restart_count[uid] = restart_count.get(uid, 0) + 1
            n = restart_count[uid]
        else:
            n = 0
        extra = {
            "uuid": uid,
            "n": n,
            "restart": bool(uid and n > 1),
            "brand": ses.get("brand"),
            "series": ses.get("series"),
            "side": ses.get("side"),
            "version": ses.get("version"),
            "version_line": ses.get("version_line"),
        }
        if uid:
            remember(uid, ses.get("brand"), ses.get("series"), ses.get("side"))
            meta = case_meta[uid]
            nth = case_order.index(uid) + 1
            extra["case_n"] = nth
            extra["case_label"] = _case_label(nth, uid, meta)
            extra["color"] = CASE_PALETTE[(nth - 1) % len(CASE_PALETTE)]
            label = extra["case_label"] if n <= 1 else f"#{n} 重启"
        else:
            extra["case_n"] = 0
            extra["case_label"] = "未打开方案"
            extra["color"] = UNKNOWN_CASE_COLOR
            label = "未打开方案"
        sessions_out.append(
            _span(f"ses-{idx}", label, ses["start"], ses["end"], times, extra)
        )

    # Merge consecutive pieces with the same case key into 手术 clips
    cases_out: list[dict] = []
    run: dict | None = None

    def flush_run() -> None:
        nonlocal run
        if not run:
            return
        uid = run["uuid"]
        extra = {
            "uuid": uid,
            "n": run["n"],
            "color": run["color"],
            "brand": run.get("brand"),
            "series": run.get("series"),
            "side": run.get("side"),
            "session_ids": run["session_ids"],
        }
        cases_out.append(
            _span(f"case-{len(cases_out)}", run["label"], run["start"], run["end"], times, extra)
        )
        run = None

    for ses in sessions_out:
        uid = ses.get("uuid")
        if uid:
            nth = ses.get("case_n") or (case_order.index(uid) + 1)
            color = CASE_PALETTE[(nth - 1) % len(CASE_PALETTE)]
            label = ses.get("case_label") or _case_label(nth, uid, case_meta.get(uid) or {})
            n = nth
        else:
            color = UNKNOWN_CASE_COLOR
            label = "未打开方案"
            n = 0
        if run and run["uuid"] == uid and run["uuid"] is not None:
            run["end"] = ses["end"]
            run["session_ids"].append(ses["id"])
            continue
        if run and run["uuid"] is None and uid is None:
            run["end"] = ses["end"]
            run["session_ids"].append(ses["id"])
            continue
        flush_run()
        run = {
            "uuid": uid,
            "n": n,
            "color": color,
            "label": label,
            "start": ses["start"],
            "end": ses["end"],
            "brand": ses.get("brand"),
            "series": ses.get("series"),
            "side": ses.get("side"),
            "session_ids": [ses["id"]],
        }
    flush_run()

    return {"cases": cases_out, "sessions": sessions_out, "markers": markers}


def _case_label(nth: int, uid: str, meta: dict) -> str:
    brand = (meta.get("brand") or "").strip()
    series = (meta.get("series") or "").strip()
    side = _side_zh(meta.get("side"))
    bits = [f"手术{nth}"]
    if brand or series:
        bits.append(f"{brand}/{series}".strip("/"))
    if side:
        bits.append(side)
    return " · ".join(bits)


def annotate_hlevel(events: list[dict]) -> None:
    """Set ev['hlevel'] to 1/2/3/None from hierarchy matches. Does not touch log 'level'."""
    for ev in events:
        msg = _msg(ev)
        a1, _ = match_l1(msg)
        a2, _ = match_l2(msg)
        a3, _ = match_l3(msg)
        ad, _ = match_device(msg)
        if a1 == "enter" or a1 == "end_if":
            ev["hlevel"] = 1
        elif a2 != "none":
            ev["hlevel"] = 2
        elif a3 != "none":
            ev["hlevel"] = 3
        elif ad != "none":
            ev["hlevel"] = 0
        else:
            ev["hlevel"] = None


def _special_index(events: list[dict], markers: list[dict], line_count: int) -> list[str]:
    spec = [""] * max(line_count, 0)
    for mk in markers:
        ln = int(mk.get("line") or 0)
        if mk.get("kind") == "startup" and 1 <= ln <= line_count:
            spec[ln - 1] = "startup"
        vl = mk.get("version_line")
        if vl and 1 <= int(vl) <= line_count and spec[int(vl) - 1] != "startup":
            spec[int(vl) - 1] = "version"
    for ev in events:
        msg = _msg(ev)
        line = int(ev.get("line") or 1)
        if not (1 <= line <= line_count):
            continue
        if "Titan Application Startup" in msg:
            spec[line - 1] = "startup"
        elif _extract_version(msg) and spec[line - 1] != "startup":
            spec[line - 1] = "version"
    return spec


def build_lines(
    raw_lines: list[str],
    marks: list[str],
    noise: list[bool],
    specials: list[str] | None = None,
    center: int | None = None,
    window: int | None = None,
) -> tuple[list[dict], bool, int, int]:
    n = len(raw_lines)
    lo, hi = 1, n
    windowed = False
    if n > ALL_LINES_LIMIT:
        win = window or DEFAULT_WINDOW
        if n > HUGE_LINES and window is None:
            win = DEFAULT_WINDOW
        c = center or max(1, n // 2)
        half = max(1, win // 2)
        lo = max(1, c - half)
        hi = min(n, lo + win - 1)
        if hi - lo + 1 < win:
            lo = max(1, hi - win + 1)
        windowed = lo > 1 or hi < n
    out = []
    for i in range(lo, hi + 1):
        raw = raw_lines[i - 1].rstrip("\n\r")
        m = LOG_RE.match(raw)
        t = m.group(1) if m else ""
        lv = m.group(4) if m else ""
        out.append(
            {
                "n": i,
                "t": t,
                "lv": lv,
                "raw": raw,
                "mark": marks[i - 1] if i - 1 < len(marks) else "none",
                "noise": bool(noise[i - 1]) if i - 1 < len(noise) else False,
                "special": (specials[i - 1] if specials and i - 1 < len(specials) else "") or "",
            }
        )
    return out, windowed, lo, hi


def compact_ticks(marks: list[str]) -> dict:
    key: list[int] = []
    anomaly: list[int] = []
    for i, mk in enumerate(marks, 1):
        if mk == "anomaly":
            anomaly.append(i)
        elif mk == "key":
            key.append(i)
    return {"key": key, "anomaly": anomaly}


def build_nle(
    events: list[dict],
    raw_lines: list[str],
    center: int | None = None,
    window: int | None = None,
) -> dict:
    line_count = len(raw_lines)
    times = _time_index(events, line_count)
    marks, noise = _mark_index(events, line_count)
    annotate_hlevel(events)
    pages = build_page_tracks(events, line_count, times)
    sc = build_sessions_and_cases(events, line_count, times)
    specials = _special_index(events, sc["markers"], line_count)
    lines, windowed, lo, hi = build_lines(
        raw_lines, marks, noise, specials, center=center, window=window
    )
    tracks = {
        "cases": sc["cases"],
        "sessions": sc["sessions"],
        "l1": pages["l1"],
        "l2": pages["l2"],
        "l3": pages["l3"],
        "device": pages.get("device") or [],
        "markers": sc["markers"],
    }
    return {
        "line_count": line_count,
        "lines": lines,
        "lines_windowed": windowed,
        "lines_start": lo,
        "lines_end": hi,
        "ticks": compact_ticks(marks),
        "tracks": tracks,
    }
