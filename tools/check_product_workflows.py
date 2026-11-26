#!/usr/bin/env python3
"""Check all published links and onboarding invariants; optionally parse CLI examples.
Run: python3 tools/check_product_workflows.py --product-root /path/to/product
This parses commands only. It never executes a product mutation.
"""
from pathlib import Path
import argparse, importlib, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
def check(root, product_root=None):
    pages = sorted(root.rglob("*.mdx"))
    errors = []
    links = 0
    config = json.loads((root / "docs.json").read_text())
    nav = [page for lang in config["navigation"]["languages"] for group in lang["groups"] for page in group["pages"]]
    actual = {str(page.relative_to(root).with_suffix("")) for page in pages}
    if set(nav) != actual or len(nav) != len(actual):
        errors.append("Published pages and navigation must have a one-to-one mapping")
    seen_redirects = set()
    for redirect in config.get("redirects", []):
        source, destination = redirect["source"], redirect["destination"]
        if source in seen_redirects or source.lstrip("/") in actual or destination.lstrip("/") not in actual or source.startswith("/ko/") != destination.startswith("/ko/"):
            errors.append(f"Invalid or duplicate consolidation redirect: {source} -> {destination}")
        seen_redirects.add(source)
    retired_entry = re.compile(r'/i/<(?:handle|ticket|credential)>|22-character (?:handle|locator|filename)|(?:trusted public hostname or verified numeric|verified (?:numeric.IP/private.CA|Private CA fingerprint))|검증된 숫자 IP/Private CA|Private CA fingerprint와 인증서 IP SAN|generated one-time bootstrap|(?:command|launcher) (?:length|character) (?:limit|bound|budget)|drlink-bootstrap\.exe|sudo drlink enroll ', re.I)
    entry_examples = (
        'curl -kfsS https://remote.xdr.ooo/A3xK9mP2|sudo bash',
        'iex(curl.exe -kfsS https://remote.xdr.ooo/A3xK9mP2|Out-String)',
    )
    for page in pages:
        text = page.read_text()
        # Retired MCP setup nouns must never return to published instructions.
        if re.search(r"\bai-mcp\b|AI MCP Setup|Connect or manage AI service|MCP Bridge settings / diagnostics", text):
            errors.append(f"{page.relative_to(root)}: retired MCP setup workflow")
        for no, line in enumerate(text.splitlines(), 1):
            if retired_entry.search(line):
                errors.append(f"{page.relative_to(root)}:{no}: retired Zero-Touch entry guidance")
        if "doctor" in text.split("---", 2)[1].lower():
            errors.append(f"{page}: obsolete doctor command in page metadata")
        for target in re.findall(r'(?:href=["\']|\]\()(/[^\s"\')#]+)', text):
            links += 1
            path = root / target.lstrip("/")
            if not any(p.is_file() for p in (path, Path(str(path)+".mdx"), Path(str(path)+".md"))):
                errors.append(f"{page.relative_to(root)}: missing link {target}")
        # Closing fences must match the opening marker, not just have even totals.
        opened = None
        for line in text.splitlines():
            match = re.match(r"^(`{3}|~{3})(.*)$", line)
            if match:
                if opened is None:
                    opened = match[1]
                elif match[1] == opened and not match[2].strip():
                    opened = None
        if opened:
            errors.append(f"{page}: unclosed fence")
    for prefix in ("", "ko/"):
        entry = (root / (prefix+"guides/zero-touch.mdx")).read_text()
        labels = (("다운로드", "옵션", "프로토콜", "Server 주소", "Bootstrap 파일명", "실행", "8자리") if prefix else
                  ("Downloader", "Options", "Protocol", "Server authority", "Bootstrap filename", "Execution", "eight-character"))
        for token in (*labels, *entry_examples):
            if token not in entry:
                errors.append(f"{prefix}guides/zero-touch: missing canonical entry field {token}")
        required_flow = ("자동 등록", "추가 승인") if prefix else ("automatic registration", "No separate approval")
        if not all(token in entry for token in required_flow):
            errors.append(f"{prefix}guides/zero-touch: missing automatic registration contract")
        # Code examples are an exact template, not a length budget or alternate launcher.
        actual = [line for line in entry.splitlines() if line.startswith(("curl ", "iex(", "curl.exe ", "sudo drlink enroll "))]
        if actual != list(entry_examples):
            errors.append(f"{prefix}guides/zero-touch: unexpected entry example")
        for name in ("getting-started/quickstart", "getting-started/linux-client",
                     "getting-started/oci-drlink-install", "use-cases/remote-ssh"):
            text = (root / (prefix+name+".mdx")).read_text()
            if re.search(r"^set (?:service-object|remote-service) ", text, re.M):
                errors.append(f"{prefix+name}: onboarding must not recreate selected services")
            if "SSH only" not in text or "show remote-services" not in text:
                errors.append(f"{prefix+name}: missing selection or actual-service discovery")
        for name in ("guides/enrollment", "guides/zero-touch", "guides/services"):
            text = (root / (prefix+name+".mdx")).read_text()
            if not all(x in text for x in ("SSH only", "management-only", "set enrollment bulk")):
                errors.append(f"{prefix+name}: single/bulk service boundary missing")
        for name in ("use-cases/lan-relay", "use-cases/private-web"):
            text = (root / (prefix+name+".mdx")).read_text()
            if "Choose Remote Services" not in text:
                errors.append(f"{prefix+name}: missing automatic new-host path")
        for name in ("drlink/configuration-bundle", "use-cases/configuration-bundle"):
            if "sourceRevision" not in (root / (prefix+name+".mdx")).read_text():
                errors.append(f"{prefix+name}: missing reviewed revision guidance")
        text = (root / (prefix+"use-cases/ai-server-control.mdx")).read_text()
        if "set enrollment bulk" in text:
            errors.append(f"{prefix}server-self tutorial must not require Agent enrollment")
    command_count = 0
    if product_root:
        sys.path.insert(0, str(product_root / "lib"))
        grammar = importlib.import_module("frp_ctl_grammar")
        seen = set()
        for page in pages:
            fence = None
            for no, line in enumerate(page.read_text().splitlines(), 1):
                marker = re.match(r"^(`{3}|~{3})(\w*)", line)
                if marker:
                    fence = None if fence else marker[2]
                    continue
                if fence not in ("text", "bash"):
                    continue
                command = line.strip()
                # POSIX shell file-existence guard, not a DRLink CLI command.
                if fence == "bash" and command.startswith("test ! -e "):
                    continue
                if "drlink " in command:
                    command = command.split("drlink ", 1)[1]
                if command.startswith("drlink> "):
                    command = command[8:]
                if not re.match(r"^(show|set|unset|test|system|help|menu|exit)( |$)", command):
                    continue
                if command in ("show", "set", "unset", "test", "system"):
                    continue # command roots deliberately document discovery, not complete actions
                if command.endswith("\\") or " ..." in command or "→" in command or " is " in command or "는 " in command:
                    continue
                # Optional [] and <> forms in reference blocks are syntax templates.
                command = re.sub(r"\[[^\]]+\]", "", command)
                command = re.sub(r"<[^>]+>", "example", command).strip()
                if command in seen:
                    continue
                seen.add(command)
                command_count += 1
                try:
                    results = [grammar.match(grammar.tokenize(command), role)
                               for role in ("server", "client")]
                    if not any(r.get("status") == "ok" or r.get("action") in ("help", "discovery")
                               for r in results):
                        errors.append(f"{page}:{no}: CLI rejected {command}: {results}")
                except Exception as exc:
                    errors.append(f"{page}:{no}: CLI rejected {command}: {exc}")
    return {"pages": len(pages), "links": links, "unique_cli_forms": command_count,
            "errors": errors}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--product-root", type=Path)
    args = parser.parse_args()
    result = check(ROOT, args.product_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result["errors"]))
