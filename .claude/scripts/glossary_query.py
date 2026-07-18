#!/usr/bin/env python3
"""Build compact, current terminology context from docs/glossary.md.

The Markdown glossary is the canonical source.  This tool is intentionally
read-only: agents call it at task start instead of copying terminology into
their prompts or skills.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GLOSSARY = ROOT / "docs/glossary.md"

DOMAIN_MARKER = re.compile(r"^<!--\s*domain:([\w-]+)\s*-->$")
TABLE_SEPARATOR = re.compile(r"^:?-{3,}:?$")
SOURCE_HEADERS = {"en", "english", "en key", "词根"}
TARGET_HEADERS = {"zh", "中文", "译法"}

DOMAIN_HINTS = {
    "gods": r"\bgods?\b|神祇|神名|祭坛|altar|piety|penance|pray|godspeak|trog|zin|sif",
    "god-titles": r"god.?title|神祇称号|神称号",
    "magic": r"magic|school|法术学派|魔法学派|conjuration|summoning|necromancy|hex",
    # Do not use bare "cast" here: it is a high-frequency polysemous glossary
    # key and should select its exact entry, not every spell-name entry.
    "spells": r"\bspells?\b|法术|施法|memor",
    "items": r"item|weapon|armou?r|ring|amulet|scroll|potion|wand|artefact|talisman|物品|武器|护甲",
    "combat": r"combat|attack|damage|hit|block|dodge|fight|战斗|攻击|伤害|格挡|闪避",
    "dialogue": r"dialogue|speech|speak|say|whisper|taunt|对话|台词|说话|低语",
    "shouts": r"shout|yell|roar|喊叫|吼叫|叫声",
    "characters": r"character.?voice|speaker|角色语气|人物语气|口吻",
    "culture": r"culture|adaptation|文化适配|典故",
    "species": r"species|race|种族|物种",
    "skills": r"\bskills?\b|技能|evocations",
    "status": r"status|duration|effect|状态|效果",
    "backgrounds": r"background|job|职业|背景",
    "abilities": r"abilit|能力",
    "mutations": r"mutation|变异",
    "monsters": r"monster|creature|demon|undead|dragon|monspeak|怪物|恶魔|亡灵|龙",
    "unique-monsters": r"unique monster|独特怪物|唯一怪物",
    "monster-titles": r"monster.?title|怪物称号",
}


@dataclass(frozen=True)
class Term:
    domain: str
    source: str
    targets: tuple[str, ...]
    comment: str = ""


@dataclass(frozen=True)
class DomainSection:
    name: str
    title: str
    body: str
    terms: tuple[Term, ...]


def _clean_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def _split_variants(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in re.split(r"\s+/\s+", value) if part.strip())


def _parse_table(domain: str, lines: list[str]) -> list[Term]:
    rows = [
        [_clean_cell(cell) for cell in line.strip().strip("|").split("|")]
        for line in lines
    ]
    if len(rows) < 2 or len(rows[0]) < 2:
        return []

    header = rows[0]
    if header[0].casefold() not in SOURCE_HEADERS:
        return []
    if header[1].casefold() not in TARGET_HEADERS:
        return []
    if not all(TABLE_SEPARATOR.match(cell) for cell in rows[1][:2]):
        return []

    terms: list[Term] = []
    for row in rows[2:]:
        if len(row) < 2 or not row[0] or not row[1]:
            continue
        comments = []
        for index, value in enumerate(row[2:], start=2):
            if value and value != "—":
                label = header[index] if index < len(header) else f"column{index + 1}"
                comments.append(f"{label}={value}")
        targets = _split_variants(row[1]) or (row[1],)
        for source in _split_variants(row[0]) or (row[0],):
            terms.append(Term(domain, source, targets, "; ".join(comments)))
    return terms


def parse_glossary(path: Path = DEFAULT_GLOSSARY) -> dict[str, DomainSection]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    markers: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = DOMAIN_MARKER.match(line.strip())
        if match:
            markers.append((index, match.group(1)))

    if not markers:
        raise ValueError(f"no domain markers found in {path}")

    sections: dict[str, DomainSection] = {}
    for marker_index, (start, domain) in enumerate(markers):
        end = markers[marker_index + 1][0] if marker_index + 1 < len(markers) else len(lines)
        body_lines = lines[start + 1:end]
        while body_lines and body_lines[-1].strip() == "---":
            body_lines.pop()
        title = next((line.lstrip("# ") for line in body_lines if line.startswith("## ")), domain)

        terms: list[Term] = []
        index = 0
        while index < len(body_lines):
            if not body_lines[index].lstrip().startswith("|"):
                index += 1
                continue
            table: list[str] = []
            while index < len(body_lines) and body_lines[index].lstrip().startswith("|"):
                table.append(body_lines[index])
                index += 1
            terms.extend(_parse_table(domain, table))

        sections[domain] = DomainSection(
            name=domain,
            title=title,
            body="\n".join(body_lines).strip(),
            terms=tuple(terms),
        )
    return sections


def infer_domains(task: str, files: Iterable[str], explicit: Iterable[str] = ()) -> list[str]:
    combined = " ".join([task, *files]).casefold()
    domains = {"core", "rules", *explicit}
    for domain, pattern in DOMAIN_HINTS.items():
        if re.search(pattern, combined, flags=re.IGNORECASE):
            domains.add(domain)

    if "godspeak" in combined:
        domains.update({"gods", "dialogue", "characters"})
    if "monspeak" in combined or "monspell" in combined:
        domains.update({"monsters", "dialogue", "shouts", "characters"})
    if "dat/descript" in combined:
        domains.update({"core", "rules"})
    return sorted(domains)


def _file_haystack(files: Iterable[str], max_bytes: int) -> str:
    chunks: list[str] = []
    for filename in files:
        path = Path(filename)
        if not path.is_absolute():
            path = ROOT / path
        try:
            if path.is_file() and path.stat().st_size <= max_bytes:
                chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(chunks)


def _source_mentioned(source: str, text: str) -> bool:
    source = source.casefold().strip()
    text = text.casefold()
    if not source:
        return False
    if len(source) < 3:
        return source == text.strip()
    if re.fullmatch(r"[\w -]+", source, flags=re.UNICODE):
        return re.search(rf"(?<!\w){re.escape(source)}(?!\w)", text) is not None
    return source in text


def select_terms(
    sections: dict[str, DomainSection],
    domains: Iterable[str],
    haystack: str,
    requested_terms: Iterable[str],
    limit: int,
) -> tuple[list[Term], int]:
    requested = {term.casefold() for term in requested_terms}
    folded_haystack = haystack.casefold()
    candidates = [term for domain in domains for term in sections.get(domain, DomainSection(domain, domain, "", ())).terms]

    exact = [
        term for term in candidates
        if term.source.casefold() in requested or _source_mentioned(term.source, folded_haystack)
    ]
    ordered: list[Term] = []
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    for term in [*exact, *candidates]:
        key = (term.domain, term.source, term.targets)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(term)
    return ordered[:limit], max(0, len(ordered) - limit)


def build_context(
    glossary: Path,
    task: str,
    files: list[str],
    domains: list[str],
    terms: list[str],
    limit: int,
    scan_file_bytes: int,
) -> dict:
    sections = parse_glossary(glossary)
    selected_domains = infer_domains(task, files, domains)
    haystack = "\n".join([task, *terms, _file_haystack(files, scan_file_bytes)])
    folded_haystack = haystack.casefold()
    # Exact source-term mentions are stronger than domain keyword heuristics.
    # This lets a task such as "translate broad axe" discover domain:items
    # without requiring the prompt to also say "weapon".
    for domain, section in sections.items():
        if any(_source_mentioned(term.source, folded_haystack) for term in section.terms):
            selected_domains.append(domain)
    selected_domains = sorted(set(selected_domains))
    missing_domains = [domain for domain in selected_domains if domain not in sections]
    if missing_domains:
        raise ValueError(f"unknown glossary domains: {', '.join(missing_domains)}")

    selected_terms, omitted = select_terms(sections, selected_domains, haystack, terms, limit)
    guidance_domains = [
        domain for domain in selected_domains
        if domain in {"god-titles", "rules", "characters", "culture"}
    ]
    digest = hashlib.sha256(glossary.read_bytes()).hexdigest()
    try:
        glossary_reference = glossary.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        # A caller-supplied external glossary has no repository-relative name.
        glossary_reference = str(glossary)
    return {
        "glossary": glossary_reference,
        "sha256": digest,
        "domains": selected_domains,
        "terms": [
            {
                "domain": term.domain,
                "source": term.source,
                "targets": list(term.targets),
                "comment": term.comment,
            }
            for term in selected_terms
        ],
        "omitted_terms": omitted,
        "guidance": {domain: sections[domain].body for domain in guidance_domains},
    }


def render_markdown(context: dict) -> str:
    lines = [
        "## Terminology Context",
        "",
        f"- Source: `{context['glossary']}`",
        f"- SHA-256: `{context['sha256']}`",
        f"- Domains: {', '.join(context['domains'])}",
        "",
        "### Canonical terms",
        "",
        "| Domain | Source | Allowed target(s) | Comment |",
        "|---|---|---|---|",
    ]
    for term in context["terms"]:
        targets = " / ".join(term["targets"])
        comment = term["comment"].replace("|", "\\|")
        lines.append(f"| {term['domain']} | {term['source']} | {targets} | {comment} |")
    if not context["terms"]:
        lines.append("| — | No matching tabular terms | — | Query exact terms if needed |")
    if context["omitted_terms"]:
        lines.extend(["", f"> {context['omitted_terms']} additional terms omitted; query them explicitly with `--term`."])

    for domain, body in context["guidance"].items():
        lines.extend(["", f"### Guidance: {domain}", "", body])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glossary", type=Path, default=DEFAULT_GLOSSARY)
    parser.add_argument("--task", default="")
    parser.add_argument("--files", nargs="*", default=[])
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--term", action="append", default=[])
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--scan-file-bytes", type=int, default=500_000)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be positive")
    try:
        context = build_context(
            args.glossary,
            args.task,
            args.files,
            args.domain,
            args.term,
            args.limit,
            args.scan_file_bytes,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))

    if args.format == "json":
        print(json.dumps(context, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(context), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
