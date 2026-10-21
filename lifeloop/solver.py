"""Bounded native search; Python independently replays every returned route."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess

from .model import BUSINESSES, Action, ActionKind, Result, Scenario, StartingBonus, job_payment, replay


ROOT = Path(__file__).resolve().parents[1]
KINDS = (ActionKind.JOB_BOOST, ActionKind.BUSINESS_BOOST, ActionKind.BUY,
         ActionKind.SELL, ActionKind.REFUND_BOOST)


@dataclass(frozen=True)
class SearchResult:
    result: Result
    statistics: dict


def ensure_binary() -> Path:
    binary = ROOT / "build/lifeloop-search"
    sources = [*ROOT.joinpath("native").glob("*"), ROOT / "flake.nix",
               ROOT / "flake.lock", ROOT / "scripts/compile.sh"]
    if not binary.exists() or any(p.stat().st_mtime > binary.stat().st_mtime for p in sources):
        subprocess.run([str(ROOT / "scripts/build_safe.sh")], cwd=ROOT, check=True)
    return binary


def solve(scenario: Scenario, beam_width: int = 512, businesses=BUSINESSES, *,
          seconds: int = 30, memory_mb: int = 768, diversity: bool = True,
          income_weight: int = 100, incumbent: Result | None = None) -> SearchResult:
    if not 1 <= beam_width <= 50_000:
        raise ValueError("Beam width must be between 1 and 50000")
    if not 1 <= seconds <= 1700 or not 256 <= memory_mb <= 1024:
        raise ValueError("Require 1..1700 seconds and 256..1024 MB")
    if not 25 <= income_weight <= 200:
        raise ValueError("Income weight must be between 25 and 200 percent")
    if incumbent is not None and replay(scenario, incumbent.actions, businesses) != incumbent:
        raise ValueError("Incumbent does not replay")
    binary = ensure_binary()
    for line in Path("/proc/self/cgroup").read_text().splitlines():
        if line.startswith("0::"):
            value = (Path("/sys/fs/cgroup" + line[3:]) / "memory.max").read_text().strip()
            if value.isdecimal():
                memory_mb = min(memory_mb, int(value) // (1024 * 1024))
    address_space = resource.getrlimit(resource.RLIMIT_AS)[0]
    if address_space != resource.RLIM_INFINITY:
        memory_mb = min(memory_mb, address_space // (1024 * 1024))
    if memory_mb < 256:
        raise ValueError("At least 256 MB of bounded job memory is required")

    first = scenario.education.start_month
    # Preserve half-dollar payments while keeping the native core integer-only.
    scale = 2 if scenario.starting_bonus == StartingBonus.BUSINESS_50 else 1
    header = [first, scenario.end_month, scenario.max_businesses, beam_width, seconds,
              memory_mb * 3 // 4, int(diversity), income_weight, scenario.starting_cash * scale, len(businesses)]
    lines = ["LIFELOOP2 " + " ".join(map(str, header))]
    lines += [f"{b.cost * scale} {int(b.income * scenario.business_multiplier * scale)}" for b in businesses]
    lines.append(" ".join(str(job_payment(scenario.education, m) * scenario.job_multiplier * scale)
                          for m in range(scenario.end_month + 1)))
    actions = incumbent.actions if incumbent else ()
    lines.append(f"{int(incumbent.final_cash * scale) if incumbent else -1} {len(actions)}")
    lines += [f"{a.month} {KINDS.index(a.kind)} {a.business if a.business is not None else -1}"
              for a in actions]
    environment = {**os.environ, "LIMIT_MAX_MB": str(memory_mb), "LIMIT_MAX_SECONDS": str(seconds + 3)}
    completed = subprocess.run([str(ROOT / "scripts/run_limited.sh"), str(binary)],
                               cwd=ROOT, input="\n".join(lines) + "\n", text=True,
                               capture_output=True, env=environment, timeout=seconds + 15)
    if completed.returncode:
        raise RuntimeError(f"Bounded native search failed ({completed.returncode}): {completed.stderr.strip()}")
    payload = json.loads(completed.stdout)
    route = tuple(Action(month, KINDS[kind], None if business == -1 else business)
                  for month, kind, business in payload["actions"])
    result = replay(scenario, route, businesses)
    if result.final_cash * scale != payload["final_cash"]:
        raise RuntimeError("Native score disagrees with independent Python replay")
    if incumbent and result.final_cash < incumbent.final_cash:
        raise RuntimeError("Native search lost its verified incumbent")
    statistics = payload["statistics"] | {
        "beam_width": beam_width, "time_limit_seconds": seconds, "hard_memory_mb": memory_mb,
        "diversity": diversity, "income_weight": income_weight,
        "incumbent_cash": incumbent.final_cash if incumbent else None,
        "native_money_scale": scale,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    }
    source = hashlib.sha256()
    for name in ("native/search.cpp", "native/safety.hpp", "lifeloop/model.py", "lifeloop/solver.py",
                 "lifeloop/polish.py", "lifeloop/records.py", "main.py", "scripts/compile.sh",
                 "scripts/run_limited.sh", "scripts/run_safe.sh", "scripts/build_safe.sh",
                 "scripts/compiler_limiter.sh", "flake.nix", "flake.lock"):
        source.update(name.encode() + b"\0" + (ROOT / name).read_bytes())
    statistics["source_sha256"] = source.hexdigest()
    return SearchResult(result, statistics)
