#!/usr/bin/env python3
"""Deterministic completeness inventory for the five standalone guides."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

GUIDES = (
    ("quickstart", "quickstart.md", "underlined", "quickstart.txt"),
    ("manual", "crawl_manual.rst", "manual", "crawl_manual.txt"),
    ("options", "options_guide.txt", "options", None),
    ("macros", "macros_guide.txt", "underlined", None),
    ("tiles", "tiles_help.txt", "underlined", None),
)

UNDERLINE_RE = re.compile(r"^([=\-+*#])\1{2,}\s*$")
OPTION_RE = re.compile(r"^(?P<id>[0-7](?:-[a-z])?)-?\s+.+\S\s*$")
MANUAL_RE = re.compile(r"^(?P<id>[A-N])\.\s+.+\S\s*$")
APPENDIX_RE = re.compile(r"^(?P<id>[1-6])\.\s+.+\S\s*$")

TOKEN_PATTERNS = (
    ("url", re.compile(r"https?://[^\s)>]+")),
    ("option", re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")),
    ("path", re.compile(r"(?<![\w.-])(?:\./|\.\./|~/|(?:docs|settings|dat|source|crawl-ref)/)(?:[\w.*-]+/)*(?:[\w.*-]+)?")),
    ("file", re.compile(r"(?<![\w.-])[\w.-]+\.(?:txt|rc|lua|des|lst|json|yaml|png|ttf)\b")),
    ("keycode", re.compile(r"\\\{\d+\}")),
    ("key", re.compile(r"\b(?:Ctrl|Shift|Alt|Meta)\s*-?\s*(?:[A-Z0-9]|F?\d+)\b|\bF\d+\b|(?<!\w)'[^'\n]{1,3}'")),
    ("format", re.compile(r"%(?:\d+\$)?[-+#0]*(?:\d+|\*)?(?:\.\d+)?[a-zA-Z%]")),
    ("number", re.compile(r"(?<![\w])\d+(?:\.\d+)*(?![\w])")),
    ("markup", re.compile(r"</?[a-z][^>\n]*>")),
)
OPTION_DECL_RE = re.compile(
    r"^[ \t]*([a-z][a-z0-9_]*(?:[ \t]*,[ \t]*[a-z][a-z0-9_]*)*)"
    r"[ \t]+(?:\+=|\^=|-=|:=|=)[ \t]*", re.MULTILINE)
MACRO_KEY_DECL_RE = re.compile(
    r"^#\s*((?:(?:Ctrl|Shift|Alt|Meta)-)*"
    r"(?:Tab|Return|Enter|Esc(?:ape)?|Space|Del(?:ete)?|Backspace|Home|End|"
    r"PgUp|PgDn|Ins(?:ert)?|F(?:[1-9]|1[0-2])|[A-Za-z0-9]))\s*:",
    re.MULTILINE)
CODE_IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
STRUCTURAL_LITERALS = ("{{", "}}", "%%%%", "```", "::")
TERMINAL_CONCLUSIONS = {
    "keep", "adjust", "retranslate",
    "defer terminology", "defer implementation",
}
EVIDENCE_HEADING = "## Evidence cards"
EVIDENCE_HEADER = (
    "| Identity | Conclusion | English title/range | Chinese title/range | "
    "Semantic consistency and terminology basis | Defect / re-entry trigger | "
    "Confidence |"
)
EVIDENCE_SEPARATOR = "|---|---|---|---|---|---|---|"
BACKTICK_FIELD_RE = re.compile(r"^`([^`]+)`$")
CONFIDENCE_LEVELS = {"high", "medium", "low"}


class InventoryError(RuntimeError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slug(heading: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
    if not slug:
        raise InventoryError(f"English heading has no stable slug: {heading!r}")
    return slug


def _underlined(text: str) -> list[tuple[str, int]]:
    lines = text.splitlines()
    found = []
    for index in range(len(lines) - 1):
        title = lines[index].strip()
        underline = lines[index + 1].strip()
        if title and UNDERLINE_RE.fullmatch(underline):
            found.append((title, index))
    return found


def _manual(text: str) -> list[tuple[str, str, int]]:
    lines = text.splitlines()
    found = []
    in_appendices = False
    for index, line in enumerate(lines):
        if line.strip() == "Appendices" or line.strip() == "附录":
            in_appendices = True
            continue
        match = (APPENDIX_RE if in_appendices else MANUAL_RE).fullmatch(line.strip())
        if match:
            identity = ("appendix-" if in_appendices else "chapter-") + match.group("id")
            found.append((identity, line.strip(), index))
    return found


def _options(text: str) -> list[tuple[str, str, int]]:
    lines = text.splitlines()
    found = []
    for index in range(len(lines) - 1):
        match = OPTION_RE.fullmatch(lines[index].strip())
        if match and UNDERLINE_RE.fullmatch(lines[index + 1].strip()):
            found.append(("section-" + match.group("id"), lines[index].strip(), index))
    return found


def sections(text: str, kind: str) -> list[tuple[str, str, int]]:
    if kind == "manual":
        return [("preamble", "Preamble", 0), *_manual(text)]
    if kind == "options":
        return [("preamble", "Preamble", 0), *_options(text)]
    return [(f"chapter-{index + 1:02d}", title, line)
            for index, (title, line) in enumerate(_underlined(text))]


def protected_tokens(text: str, *, option_lua: bool = False) -> dict[str, Counter[str]]:
    # Reflowed source documentation may split identifiers after an underscore.
    text = re.sub(r"(?<=_)\s+(?=[A-Za-z0-9])", "", text)
    tokens = {name: Counter(pattern.findall(text))
              for name, pattern in TOKEN_PATTERNS}
    tokens["url"] = Counter(token.rstrip(".,;:")
                            for token in tokens["url"].elements())
    tokens["structural"] = Counter({literal: text.count(literal)
                                     for literal in STRUCTURAL_LITERALS})
    option_declarations = []
    for match in OPTION_DECL_RE.finditer(text):
        option_declarations.extend(
            item.strip() for item in match.group(1).split(","))
    # Repeated examples may legitimately be paraphrased, but declaration
    # identities and their first-occurrence order are configuration syntax.
    tokens["option_declaration_order"] = _ordered_tokens(
        dict.fromkeys(option_declarations))
    tokens["macro_key_declaration_order"] = _ordered_tokens(
        match.group(1) for match in MACRO_KEY_DECL_RE.finditer(text))
    tokens["code_identifier_order"] = _ordered_tokens(
        _code_identifiers(text, option_lua=option_lua))
    return tokens


def _ordered_tokens(values) -> Counter[str]:
    return Counter(f"{index:06d}:{value}"
                   for index, value in enumerate(values))


def _code_identifiers(text: str, *, option_lua: bool) -> list[str]:
    """Return identifiers from standalone-guide Lua/code syntax in order."""
    snippets = re.findall(r"\{\{(.*?)\}\}", text, re.DOTALL)
    if not option_lua:
        return [identifier for snippet in snippets
                for identifier in CODE_IDENTIFIER_RE.findall(snippet)]

    block = []
    delimiter = None
    for line in text.splitlines():
        # Options-guide Lua blocks use delimiters in column zero. Indented
        # braces elsewhere are examples/data and must not consume prose.
        if delimiter is not None:
            if line == delimiter:
                snippets.append("\n".join(block))
                block = []
                delimiter = None
            else:
                block.append(line)
            continue
        if line in {"<", "{"}:
            delimiter = ">" if line == "<" else "}"
            continue
        inline = re.match(r"^:\s*(\S.*)$", line)
        if inline:
            snippets.append(inline.group(1))
    if delimiter is not None:
        raise InventoryError("unterminated guide code block")

    identifiers = []
    for snippet in snippets:
        code = re.sub(r"--[^\n]*", "", snippet)
        code = re.sub(r'"(?:\\.|[^"\\])*"', '""', code)
        code = re.sub(r"'(?:\\.|[^'\\])*'", "''", code)
        identifiers.extend(CODE_IDENTIFIER_RE.findall(code))
    return identifiers


def _section_bodies(text: str, parsed: list[tuple[str, str, int]]) -> list[str]:
    lines = text.splitlines(keepends=True)
    bodies = []
    for index, (_, _, start) in enumerate(parsed):
        stop = parsed[index + 1][2] if index + 1 < len(parsed) else len(lines)
        bodies.append("".join(lines[start:stop]))
    return bodies


def _compare_tokens(identity: str, english: str, chinese: str) -> dict:
    option_lua = identity in {
        "guide:options:section-6-b", "guide:options:section-6-c",
    }
    en_tokens = protected_tokens(english, option_lua=option_lua)
    zh_tokens = protected_tokens(chinese, option_lua=option_lua)
    mismatches = {}
    for kind in en_tokens:
        matches = en_tokens[kind] == zh_tokens[kind]
        if kind == "key":
            matches = all(zh_tokens[kind][token] >= count
                          for token, count in en_tokens[kind].items())
        if not matches:
            mismatches[kind] = {
                "english": dict(sorted(en_tokens[kind].items())),
                "chinese": dict(sorted(zh_tokens[kind].items())),
            }
    if mismatches:
        raise InventoryError(f"{identity}: protected token mismatch: "
                             + ", ".join(sorted(mismatches)))
    return {kind: sum(values.values()) for kind, values in en_tokens.items()}


def build_inventory(root: Path) -> dict:
    docs = root / "crawl-ref" / "docs"
    source = root / "crawl-ref" / "source"
    glossary_path = root / "docs" / "glossary.md"
    if not glossary_path.is_file():
        raise InventoryError(f"missing glossary: {glossary_path}")
    glossary_sha256 = sha(glossary_path)
    inputs = {str(glossary_path.relative_to(root)): glossary_sha256}
    cards = []
    for guide, filename, kind, generated in GUIDES:
        en_path = docs / filename
        zh_path = docs / "zh" / filename
        if not en_path.is_file() or not zh_path.is_file():
            raise InventoryError(f"missing guide pair: {filename}")
        en_text = en_path.read_text(encoding="utf-8")
        zh_text = zh_path.read_text(encoding="utf-8")
        en_sections = sections(en_text, kind)
        zh_sections = sections(zh_text, kind)
        if not en_sections or not zh_sections:
            raise InventoryError(f"{guide}: no sections parsed")
        en_ids = [item[0] for item in en_sections]
        zh_ids = [item[0] for item in zh_sections]
        if len(set(en_ids)) != len(en_ids) or len(set(zh_ids)) != len(zh_ids):
            raise InventoryError(f"{guide}: duplicate section identity")
        if kind in {"manual", "options"} and en_ids != zh_ids:
            raise InventoryError(f"{guide}: section identity/order mismatch")
        if len(en_sections) != len(zh_sections):
            raise InventoryError(f"{guide}: section count mismatch: "
                                 f"{len(en_sections)} != {len(zh_sections)}")
        en_bodies = _section_bodies(en_text, en_sections)
        zh_bodies = _section_bodies(zh_text, zh_sections)
        for index, ((section_id, heading, _), en_body, zh_body) in enumerate(
                zip(en_sections, en_bodies, zh_bodies)):
            stable_component = (section_id if kind in {"manual", "options"}
                                else "chapter-" + _slug(heading))
            stable_id = f"guide:{guide}:{stable_component}"
            token_counts = _compare_tokens(stable_id, en_body, zh_body)
            cards.append({
                "stable_id": stable_id,
                "english_heading": heading,
                "ordinal": index + 1,
                "token_counts": token_counts,
                "conclusion": "inventory-pass",
            })
        inputs[str(en_path.relative_to(root))] = sha(en_path)
        inputs[str(zh_path.relative_to(root))] = sha(zh_path)

        if generated:
            generated_path = docs / "zh" / generated
            if not generated_path.is_file():
                raise InventoryError(f"missing generated guide: {generated_path}")
            if generated == "quickstart.txt":
                expected = zh_path.read_bytes()
            else:
                process = subprocess.run(
                    ["perl", str(source / "util" / "unrest.pl")],
                    input=zh_path.read_bytes(), stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, check=False)
                if process.returncode:
                    raise InventoryError("unrest.pl failed: "
                                         + process.stderr.decode(errors="replace"))
                expected = process.stdout
            if generated_path.read_bytes() != expected:
                raise InventoryError(f"generated guide is stale: {generated_path}")
            inputs[str(generated_path.relative_to(root))] = sha(generated_path)

    identities = [card["stable_id"] for card in cards]
    if len(identities) != len(set(identities)):
        raise InventoryError("inventory contains duplicate stable identities")
    sorted_inputs = dict(sorted(inputs.items()))
    digest_material = {
        "cards": cards,
        "glossary_sha256": glossary_sha256,
        "inputs": sorted_inputs,
    }
    digest = hashlib.sha256(
        json.dumps(digest_material, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")).encode()).hexdigest()
    return {
        "schema_version": 1,
        "guide_set": [item[0] for item in GUIDES],
        "glossary_sha256": glossary_sha256,
        "inputs": sorted_inputs,
        "inventory_digest": digest,
        "coverage": {"expected": len(cards), "concluded": len(cards)},
        "cards": cards,
        "terminal_conclusion": "inventory-pass",
    }


def render_review_plan(payload: dict) -> str:
    common = [f"- Inventory digest: `{payload['inventory_digest']}`",
              f"- Glossary SHA-256: `{payload['glossary_sha256']}`",
              f"- Frozen identities: {payload['coverage']['expected']}"]
    plan = "# Standalone Guide Review Plan\n\n" + "\n".join(common) + (
        "\n\nThe boundary is the five canonical English/Chinese guide pairs. "
        "Each identity below requires one structural terminal conclusion; "
        "linguistic readiness remains reviewer-owned.\n\n" +
        "\n".join(f"- `{card['stable_id']}`" for card in payload["cards"]) + "\n")
    return plan


def _single_metadata_value(text: str, label: str, pattern: str) -> str:
    matches = re.findall(
        rf"^- {re.escape(label)}: {pattern}\s*$", text, re.MULTILINE)
    if len(matches) != 1:
        raise InventoryError(
            f"review results require exactly one {label} metadata value")
    return matches[0]


def validate_review_results(root: Path, payload: dict) -> dict:
    path = root / "docs" / "guide-review-results.md"
    if not path.is_file():
        raise InventoryError(f"review evidence is missing or stale: {path}")
    text = path.read_text(encoding="utf-8")
    digest = _single_metadata_value(
        text, "Inventory digest", r"`([0-9a-f]{64})`")
    glossary = _single_metadata_value(
        text, "Glossary SHA-256", r"`([0-9a-f]{64})`")
    count_text = _single_metadata_value(
        text, "Frozen identities", r"([0-9]+)")
    if digest != payload["inventory_digest"]:
        raise InventoryError("review results inventory digest is stale")
    if glossary != payload["glossary_sha256"]:
        raise InventoryError("review results glossary SHA-256 is stale")
    if int(count_text) != payload["coverage"]["expected"]:
        raise InventoryError("review results frozen identity count is stale")

    if text.count(EVIDENCE_HEADING) != 1:
        raise InventoryError("review results require one evidence-card section")
    section = text.split(EVIDENCE_HEADING, 1)[1]
    section = section.split("\n## ", 1)[0]
    lines = section.splitlines()
    try:
        header_index = lines.index(EVIDENCE_HEADER)
    except ValueError as error:
        raise InventoryError("review results evidence table header is invalid") from error
    if (header_index + 1 >= len(lines)
            or lines[header_index + 1] != EVIDENCE_SEPARATOR):
        raise InventoryError("review results evidence table separator is invalid")

    rows = []
    for line in lines[header_index + 2:]:
        if not line.strip():
            continue
        if not line.startswith("|"):
            raise InventoryError("unexpected content in review evidence table")
        if not line.endswith(" |"):
            raise InventoryError("malformed review evidence-card row")
        fields = line[2:-2].split(" | ")
        if len(fields) != 7:
            raise InventoryError("malformed review evidence-card row")
        identity_match = BACKTICK_FIELD_RE.fullmatch(fields[0])
        conclusion_match = BACKTICK_FIELD_RE.fullmatch(fields[1])
        if not identity_match or not conclusion_match:
            raise InventoryError("review evidence identity/conclusion field is invalid")
        if any(not field.strip() for field in fields[2:]):
            raise InventoryError("review evidence-card required field is empty")
        if fields[6] not in CONFIDENCE_LEVELS:
            raise InventoryError("review evidence-card confidence is invalid")
        rows.append((identity_match.group(1), conclusion_match.group(1)))

    review_ids = [identity for identity, _ in rows]
    duplicates = sorted(identity for identity, count in Counter(review_ids).items()
                        if count > 1)
    if duplicates:
        raise InventoryError("duplicate review identities: " + ", ".join(duplicates))
    expected_ids = [card["stable_id"] for card in payload["cards"]]
    missing = sorted(set(expected_ids) - set(review_ids))
    unexpected = sorted(set(review_ids) - set(expected_ids))
    if missing or unexpected:
        details = []
        if missing:
            details.append("missing review identities: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected review identities: " + ", ".join(unexpected))
        raise InventoryError("; ".join(details))
    if review_ids != expected_ids:
        raise InventoryError("review identity order differs from frozen inventory")
    invalid = sorted(identity for identity, conclusion in rows
                     if conclusion not in TERMINAL_CONCLUSIONS)
    if invalid:
        raise InventoryError("non-terminal review conclusions: "
                             + ", ".join(invalid))
    conclusions = Counter(conclusion for _, conclusion in rows)
    return {
        "expected": len(expected_ids),
        "concluded": len(rows),
        "terminal_conclusion_counts": dict(sorted(conclusions.items())),
    }


def validate_review_docs(root: Path, payload: dict) -> None:
    path = root / "docs" / "guide-review-plan.md"
    if not path.is_file() or path.read_text(encoding="utf-8") != render_review_plan(payload):
        raise InventoryError(f"review evidence is missing or stale: {path}")
    payload["review_coverage"] = validate_review_results(root, payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-review-plan", action="store_true")
    parser.add_argument("--skip-review-docs", action="store_true")
    args = parser.parse_args()
    try:
        payload = build_inventory(args.root.resolve())
        if args.write_review_plan:
            plan = render_review_plan(payload)
            (args.root / "docs" / "guide-review-plan.md").write_text(
                plan, encoding="utf-8")
        elif not args.skip_review_docs:
            validate_review_docs(args.root.resolve(), payload)
    except (InventoryError, OSError) as error:
        print(f"guide inventory: FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
