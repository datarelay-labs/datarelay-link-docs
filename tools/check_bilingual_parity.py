#!/usr/bin/env python3
"""Verify EN/KO DataRelay Link pages remain equivalent after translation.

Compares public navigation by semantic page pairs, literal CLI commands in
code fences, internal link targets and image asset references. Human language
is deliberately not compared as literal text.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

# Historical URL differences are intentional: these pages cover the same topic.
KO_ALIASES = {
    "operations/maintenance": "operations/overview",
    "troubleshooting/overview": "operations/troubleshooting",
}


def _commands(text: str) -> Counter[str]:
    result: Counter[str] = Counter()
    for _, _, body in re.findall(
        r"(?ms)^(`{3}|~{3})(text|bash)\s*\n(.*?)^\1\s*$", text
    ):
        for raw in body.splitlines():
            line = raw.strip()
            if not re.match(
                r"^(?:sudo\s+)?(?:drlink\s+)?"
                r"(?:show|set|test|unset|system|curl|git|ssh|nc|python3|apt-get|grep|sudo)"
                r"(?:\s|$)",
                line,
            ):
                continue
            # Arguments are intentionally translated in prose but executable
            # command verbs, selectors, flags and values must be identical.
            line = re.sub(r"<[^>]+>", "<ARG>", line)
            if line.endswith(" \\"):
                line = line[:-2].strip()
            result[line] += 1
    return result


def _links(text: str) -> set[str]:
    found = re.findall(r"(?:\]\(|href=[\"'])(/[^\s#)\"']+)", text)
    normalized = set()
    for href in found:
        if href.startswith("/ko/"):
            href = href[3:]
        href = "/" + KO_ALIASES.get(href.lstrip("/"), href.lstrip("/"))
        if not href.startswith("/images/"):
            normalized.add(href)
    return normalized


def _images(text: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\((/images/[^)]+)\)", text)


def check(root: Path = ROOT) -> dict:
    errors: list[str] = []
    nav = json.loads((root / "docs.json").read_text())
    languages = {item["language"]: item for item in nav["navigation"]["languages"]}
    if set(languages) != {"en", "ko"}:
        return {"pairs": 0, "commands": 0, "links": 0, "errors": ["Missing EN or KO language navigation"]}
    en_pages = [name for group in languages["en"]["groups"] for name in group["pages"]]
    ko_pages = [name.removeprefix("ko/") for group in languages["ko"]["groups"] for name in group["pages"]]
    expected_ko = [KO_ALIASES.get(p, p) for p in en_pages]
    if Counter(expected_ko) != Counter(ko_pages):
        errors.append(
            "EN/KO public navigation is not semantically paired: "
            f"EN-only={list((Counter(expected_ko)-Counter(ko_pages)).elements())}, "
            f"KO-only={list((Counter(ko_pages)-Counter(expected_ko)).elements())}"
        )
    checked_commands = 0
    checked_links = 0
    for enpath in en_pages:
        kopath = KO_ALIASES.get(enpath, enpath)
        a = root / (enpath + ".mdx")
        b = root / ("ko/" + kopath + ".mdx")
        if not a.is_file() or not b.is_file():
            errors.append(f"Missing EN/KO pair: {enpath} -> ko/{kopath}")
            continue
        entext, kotext = a.read_text(), b.read_text()
        a_cmd, b_cmd = _commands(entext), _commands(kotext)
        checked_commands += sum(a_cmd.values())
        if a_cmd != b_cmd:
            errors.append(
                f"CLI examples differ: {enpath}: EN-only={list((a_cmd-b_cmd).elements())}, "
                f"KO-only={list((b_cmd-a_cmd).elements())}"
            )
        a_links, b_links = _links(entext), _links(kotext)
        checked_links += len(a_links)
        if a_links != b_links:
            errors.append(
                f"Internal links differ: {enpath}: EN-only={sorted(a_links-b_links)}, "
                f"KO-only={sorted(b_links-a_links)}"
            )
        if _images(entext) != _images(kotext):
            errors.append(f"Actual image references differ: {enpath}")

    # These safety-critical workflows must be complete independently in each language.
    critical = {
        "use-cases/ai-full-access": (
            "OAuth", "server:self", "host-info", "process-read", "file-read",
            "file-write", "file-upload", "file-download", "command-exec",
            "set ai-access", "unset ai-access", "show ai-access-log",
        ),
        "use-cases/ai-readonly": ("OAuth", "DENY", "command-exec", "set ai-access"),
        "guides/mcp-clients": ("single443", "OAuth", "Managed Host", "server:self"),
        "guides/remote-access": ("WHITELIST", "BLACKLIST", "ALLOW ALL"),
        "guides/internet-access": ("WHITELIST", "DENY ALL"),
        "getting-started/choose-workflow": ("Remote Access", "Internet Access", "AI Access"),
        "guides/enrollment": ("SSH only", "set enrollment bulk", "show remote-services"),
    }
    for page, tokens in critical.items():
        for lang in ("en", "ko"):
            name = ("" if lang == "en" else "ko/") + page + ".mdx"
            text = (root / name).read_text()
            for token in tokens:
                if token not in text:
                    errors.append(f"Safety-critical content missing: {name} -> {token}")
    return {
        "pairs": len(en_pages),
        "commands": checked_commands,
        "links": checked_links,
        "errors": errors,
    }


if __name__ == "__main__":
    result = check()
    if result["errors"]:
        print(f"FAILED EN/KO parity: {len(result['errors'])} issues")
        for error in result["errors"]:
            print(error)
        sys.exit(2)
    print(
        f"PASS {result['pairs']} EN/KO page pairs, "
        f"{result['commands']} matching CLI example lines and "
        f"{result['links']} matching internal link targets"
    )
