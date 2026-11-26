#!/usr/bin/env python3
"""Guard public OCI-to-retirement documentation against security regressions.

This is a source-text contract, not proof of a live OCI/Agent/MCP deployment.
English and Korean navigation/CLI parity is checked separately.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "getting-started/server-installation": (
        "SOURCE_SHA", "^[0-9a-f]{40}", "system diagnostics",
    ),
    "getting-started/oci-network-vm": (
        "Reserved Public", "WHITELIST", "6099", "7000",
    ),
    "guides/remote-access": (
        "ALLOW ALL", "WHITELIST", "test remote-access",
        "nonmatching-source-object",
    ),
    "guides/internet-access": (
        "WHITELIST", "DENY", "system diagnostics", "NO_PROXY",
        "90drlink-proxy", "NAT",
    ),
    "guides/mcp-clients": (
        "single443", "OAuth", "real owner/UI", "MCP Server Settings", "set mcp-server", "set ai-identity", "set ai-access", "Server execution", "Retry", "NOT TESTED", "exit 1",
    ),
    "guides/enrollment": ("unset enrollment <ENROLLMENT>", "16-hexadecimal-character", "one explicit confirmation", "default is No"),
    "guides/ai-access": (
        "managed-hosts:trusted", "managed-host-group:", "DENY", "server:self", "host-info,process-read",
        "command-exec",
    ),
    "operations/lifecycle": (
        "unset managed-host <HOST>", "system uninstall",
        "Reserved Public IPv4", "set ai-identity <IDENTITY> revoke", "ALLOW ALL",
    ),
    "getting-started/full-lifecycle": (
        "Reserved Public", "set enrollment zero-touch",
        "WHITELIST", "Internet Access", "Claude", "ChatGPT",
        "system uninstall", "OCI",
    ),
}

# Translated prose differs by language; retain machine-verifiable CLI,
# security boundaries and complete lifecycle objects in both locales.
KO_REQUIRED = {
    "getting-started/server-installation": (
        "SOURCE_SHA", "^[0-9a-f]{40}", "system diagnostics",
    ),
    "getting-started/oci-network-vm": ("Reserved Public", "WHITELIST", "6099", "7000"),
    "guides/remote-access": ("ALLOW ALL", "WHITELIST", "test remote-access", "nonmatching-source-object"),
    "guides/internet-access": ("WHITELIST", "DENY", "system diagnostics", "NO_PROXY", "90drlink-proxy", "NAT"),
    "guides/mcp-clients": ("single443", "OAuth", "Owner/UI", "MCP Server Settings", "set mcp-server", "set ai-identity", "set ai-access", "Server execution", "Retry", "NOT TESTED", "종료 코드 1"),
    "guides/enrollment": ("unset enrollment <ENROLLMENT>", "16자리 16진수", "한 번의 명시적 확인", "기본값은 No"),
    "guides/ai-access": ("managed-hosts:trusted", "managed-host-group:", "DENY", "server:self", "host-info,process-read", "command-exec"),
    "operations/lifecycle": ("unset managed-host <HOST>", "system uninstall", "Reserved Public IPv4", "set ai-identity <IDENTITY> revoke", "ALLOW ALL"),
    "getting-started/full-lifecycle": ("Reserved Public", "set enrollment zero-touch", "WHITELIST", "Internet Access", "Claude", "ChatGPT", "system uninstall", "OCI"),
}


def check(root: Path) -> list[str]:
    errors: list[str] = []
    nav = json.loads((root / "docs.json").read_text(encoding="utf-8"))
    languages = {item["language"]: item for item in nav["navigation"]["languages"]}
    for lang, rules in (("en", REQUIRED), ("ko", KO_REQUIRED)):
        lang_root = root / ("ko" if lang == "ko" else "")
        if lang not in languages:
            errors.append(f"{lang}: missing navigation language")
            continue
        nav_paths = {
            name for group in languages[lang]["groups"] for name in group["pages"]
        }
        for path, literals in rules.items():
            nav_path = f"ko/{path}" if lang == "ko" else path
            file = lang_root / (path + ".mdx")
            if nav_path not in nav_paths:
                errors.append(f"{lang}: {nav_path} not in public navigation")
            if not file.is_file():
                errors.append(f"{lang}: missing {file.relative_to(root)}")
                continue
            data = file.read_text(encoding="utf-8")
            for literal in literals:
                if literal not in data:
                    errors.append(f"{lang}: missing required {literal!r} in {path}")
            if path == "getting-started/server-installation":
                if re.search(r"raw\.githubusercontent\.com/[^ \n]+/main/dist/bootstrap-server\.sh", data):
                    errors.append(f"{lang}: mutable main server bootstrap URL")
                if "sudo bash ./bootstrap-server.sh" not in data:
                    errors.append(f"{lang}: missing Server install invocation")
    for page in root.rglob("*.mdx"):
        data = page.read_text(encoding="utf-8")
        if re.search(
            r"raw\.githubusercontent\.com/datarelay-labs/datarelay-link/main/",
            data,
        ):
            errors.append(f"mutable installer/source URL in {page.relative_to(root)}")
    return errors


if __name__ == "__main__":
    chosen = Path(sys.argv[1]) if len(sys.argv) == 2 else ROOT
    findings = check(chosen)
    for finding in findings:
        print("FAIL", finding)
    if findings:
        raise SystemExit(1)
    print(f"PASS full-lifecycle EN/KO invariants ({len(REQUIRED)} paired topics)")
