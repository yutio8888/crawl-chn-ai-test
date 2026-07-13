#!/usr/bin/env python3
"""Project-aware terminology checker for DCSS bilingual XLIFF files.

Unlike Okapi's SimpleTB checker, a glossary row may provide several legal
target terms (separated by ``/``).  Rows can also be filtered by the glossary
``domain`` field or by an explicit ``context`` field.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

NS = {"x": "urn:oasis:names:tc:xliff:document:1.2"}


@dataclass
class TermRule:
    source: str
    targets: set[str] = field(default_factory=set)
    domains: set[str] = field(default_factory=set)
    contexts: set[str] = field(default_factory=set)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def parse_fields(comment: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in comment.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            fields[key.strip().casefold()] = value.strip()
    return fields


def values_from_field(value: str, prefix: str) -> set[str]:
    return {
        match.casefold()
        for match in re.findall(rf"{re.escape(prefix)}=([A-Za-z0-9_-]+)", value, re.I)
    }


def domain_values(value: str) -> set[str]:
    result = set()
    for item in re.split(r"\s*\|\s*", value):
        item = item.strip()
        match = re.fullmatch(r"domain=([A-Za-z0-9_-]+)", item, re.I)
        result.add((match.group(1) if match else item).casefold())
    return {item for item in result if item}


def target_alternatives(value: str) -> set[str]:
    # The project's glossary uses slash-separated alternatives. Parenthetical
    # labels such as "（通用）" describe the alternative and are not text to
    # require in a translation.
    result = set()
    for item in re.split(r"\s*/\s*", value):
        item = re.sub(r"\s*[（(][^（）()]*[）)]\s*$", "", item).strip()
        if item:
            result.add(item)
    return result


def load_glossary(path: Path, domain: str | None = None) -> list[TermRule]:
    merged: dict[tuple[str, tuple[str, ...], tuple[str, ...]], TermRule] = {}
    wanted_domain = domain.casefold() if domain else None
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        columns = line.split("\t", 2)
        if len(columns) < 2:
            raise ValueError(f"{path}:{line_number}: expected at least 2 TSV columns")
        source, target = (column.strip() for column in columns[:2])
        if not source or not target:
            continue
        fields = parse_fields(columns[2] if len(columns) == 3 else "")
        domains = domain_values(fields.get("domain", ""))
        contexts = values_from_field(fields.get("context", ""), "context")
        if wanted_domain and domains and wanted_domain not in domains:
            continue
        if wanted_domain and not domains:
            continue
        key = (normalize(source), tuple(sorted(domains)), tuple(sorted(contexts)))
        rule = merged.setdefault(key, TermRule(source, domains=domains, contexts=contexts))
        rule.targets.update(target_alternatives(target))
    return list(merged.values())


def source_present(text: str, term: str) -> bool:
    # English glossary terms should not match inside another identifier or
    # word; CJK terms and punctuation-heavy keys use ordinary substring match.
    if re.search(r"[A-Za-z0-9_]", term):
        pattern = rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])"
        return re.search(pattern, text, re.IGNORECASE) is not None
    return normalize(term) in normalize(text)


def target_present(text: str, term: str) -> bool:
    if re.search(r"[A-Za-z0-9_]", term):
        pattern = rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])"
        return re.search(pattern, text, re.IGNORECASE) is not None
    return normalize(term) in normalize(text)


def source_pattern(rules: list[TermRule]) -> re.Pattern[str]:
    """Compile one matcher instead of scanning every term in every unit."""
    terms = sorted({rule.source for rule in rules}, key=len, reverse=True)
    parts = []
    for term in terms:
        escaped = re.escape(term)
        if re.search(r"[A-Za-z0-9_]", term):
            parts.append(rf"(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_])")
        else:
            parts.append(escaped)
    # An empty glossary is valid and should produce an empty report.
    return re.compile("|".join(parts) if parts else r"(?!)", re.IGNORECASE)


def note_fields(note: str) -> dict[str, str]:
    fields = parse_fields(note)
    if "context" in note.casefold() and "context" not in fields:
        match = re.search(r"context=([^;]+)", note, re.I)
        if match:
            fields["context"] = match.group(1).strip()
    return fields


def context_matches(rule: TermRule, note: str) -> bool:
    if not rule.contexts:
        return True
    context = note_fields(note).get("context", "").casefold()
    return context in rule.contexts


def check(input_path: Path, glossary_path: Path, domain: str | None = None) -> dict:
    rules = load_glossary(glossary_path, domain)
    rules_by_source: dict[str, list[TermRule]] = defaultdict(list)
    for rule in rules:
        rules_by_source[normalize(rule.source)].append(rule)
    matcher = source_pattern(rules)
    root = ET.parse(input_path).getroot()
    issues = []
    for unit in root.findall(".//x:trans-unit", NS):
        source = unit.findtext("x:source", default="", namespaces=NS)
        target = unit.findtext("x:target", default="", namespaces=NS)
        note = unit.findtext("x:note", default="", namespaces=NS)
        # One issue per matched source term and unit, matching the useful
        # granularity of Okapi while avoiding duplicate reports for repeated
        # occurrences in one sentence.
        seen_terms: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
        for match in matcher.finditer(source):
            for rule in rules_by_source.get(normalize(match.group()), []):
                rule_key = (normalize(rule.source), tuple(sorted(rule.domains)), tuple(sorted(rule.contexts)))
                if rule_key in seen_terms or not context_matches(rule, note):
                    continue
                seen_terms.add(rule_key)
                if any(target_present(target, alternative) for alternative in rule.targets):
                    continue
                issues.append(
                    {
                        "type": "TERMINOLOGY",
                        "severity": 0,
                        "trans_unit": unit.get("id", ""),
                        "source": source,
                        "target": target,
                        "term": rule.source,
                        "allowed_targets": sorted(rule.targets),
                        "domains": sorted(rule.domains),
                        "contexts": sorted(rule.contexts),
                        "note": note,
                    }
                )
    return {
        "format": "dcss-terminology-report-1",
        "input": str(input_path),
        "glossary": str(glossary_path),
        "domain": domain,
        "rules": len(rules),
        "issue_count": len(issues),
        "issue_types": dict(Counter(issue["type"] for issue in issues)),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="bilingual XLIFF")
    parser.add_argument("glossary", type=Path, help="tab-delimited project glossary")
    parser.add_argument("output", type=Path, help="JSON report path")
    parser.add_argument("--domain", help="only use glossary rows for this domain")
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"input does not exist: {args.input}")
    if not args.glossary.is_file():
        parser.error(f"glossary does not exist: {args.glossary}")
    report = check(args.input, args.glossary, args.domain)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote project terminology report: {args.output} ({report['issue_count']} issues)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
