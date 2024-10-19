from __future__ import annotations

import enum
import re
from typing import Any, Iterator

import pytest


@pytest.fixture
def patterns() -> PatternsLib:
    return PatternsLib()


def pytest_assertrepr_compare(
    op: str, left: Any, right: Any
) -> list[str] | None:
    if op != "==":
        return None
    if isinstance(left, Pattern):
        return list(left._audit(right).report())
    elif isinstance(right, Pattern):
        return list(right._audit(left).report())
    else:
        return None


class Status(enum.Enum):
    UNEXPECTED = 1
    OPTIONAL = 2
    EXPECTED = 3
    REFUSED = 4

    @property
    def symbol(self) -> str:
        return STATUS_SYMBOLS[self]


STATUS_SYMBOLS = {
    Status.UNEXPECTED: "🟡",
    Status.EXPECTED: "🟢",
    Status.OPTIONAL: "⚪️",
    Status.REFUSED: "🔴",
}

EMPTY_LINE_PATTERN = "<empty-line>"


def tab_replace(line: str) -> str:
    while (position := line.find("\t")) != -1:
        fill = " " * (8 - (position % 8))
        line = line.replace("\t", fill)
    return line


ascii_to_control_pictures = {
    0x00: "\u2400",  # NUL -> ␀
    0x01: "\u2401",  # SOH -> ␁
    0x02: "\u2402",  # STX -> ␂
    0x03: "\u2403",  # ETX -> ␃
    0x04: "\u2404",  # EOT -> ␄
    0x05: "\u2405",  # ENQ -> ␅
    0x06: "\u2406",  # ACK -> ␆
    0x07: "\u2407",  # BEL -> ␇
    0x08: "\u2408",  # BS  -> ␈
    0x09: "\u2409",  # HT  -> ␉
    0x0A: "\u240a",  # LF  -> ␊
    0x0B: "\u240b",  # VT  -> ␋
    0x0C: "\u240c",  # FF  -> ␌
    0x0D: "\u240d",  # CR  -> ␍
    0x0E: "\u240e",  # SO  -> ␎
    0x0F: "\u240f",  # SI  -> ␏
    0x10: "\u2410",  # DLE -> ␐
    0x11: "\u2411",  # DC1 -> ␑
    0x12: "\u2412",  # DC2 -> ␒
    0x13: "\u2413",  # DC3 -> ␓
    0x14: "\u2414",  # DC4 -> ␔
    0x15: "\u2415",  # NAK -> ␕
    0x16: "\u2416",  # SYN -> ␖
    0x17: "\u2417",  # ETB -> ␗
    0x18: "\u2418",  # CAN -> ␘
    0x19: "\u2419",  # EM  -> ␙
    0x1A: "\u241a",  # SUB -> ␚
    0x1B: "\u241b",  # ESC -> ␛
    0x1C: "\u241c",  # FS  -> ␜
    0x1D: "\u241d",  # GS  -> ␝
    0x1E: "\u241e",  # RS  -> ␞
    0x1F: "\u241f",  # US  -> ␟
    0x20: "\u2420",  # SPACE -> ␠
    0x7F: "\u2421",  # DEL -> ␡
}


def to_control_picture(char: str) -> str:
    return ascii_to_control_pictures.get(ord(char), char)


def line_to_control_pictures(line: str) -> str:
    return "".join(to_control_picture(char) for char in line)


def match(pattern: str, line: str) -> bool | re.Match[str] | None:
    if pattern == EMPTY_LINE_PATTERN:
        if not line:
            return True

    line = tab_replace(line)
    pattern = re.escape(pattern)
    pattern = pattern.replace(r"\.\.\.", ".*?")
    re_pattern = re.compile("^" + pattern + "$")
    return re_pattern.match(line)


class Line:
    status: Status = Status.UNEXPECTED
    status_cause: str = ""

    def __init__(self, data: str):
        self.data = data

    def matches(self, expectation: str) -> bool:
        return bool(match(expectation, self.data))

    def mark(self, status: Status, cause: str) -> None:
        if status.value <= self.status.value:
            # Stay in the current status
            return
        self.status = status
        self.status_cause = cause


class Audit:
    content: list[Line]
    unmatched_expectations: list[tuple[str, str]]
    matched_refused: set[tuple[str, str]]

    def __init__(self, content: str):
        self.unmatched_expectations = []
        self.matched_refused = set()

        self.content = []
        for line in content.splitlines():
            self.content.append(Line(line))

    def cursor(self) -> Iterator[Line]:
        return iter(self.content)

    def in_order(self, name: str, expected_lines: list[str]) -> None:
        """Expect all lines exist and come in order, but they
        may be interleaved with other lines."""
        cursor = self.cursor()
        have_some_match = False
        for expected_line in expected_lines:
            for line in cursor:
                if line.matches(expected_line):
                    line.mark(Status.EXPECTED, name)
                    have_some_match = True
                    break
            else:
                self.unmatched_expectations.append((name, expected_line))
                if not have_some_match:
                    # Reset the scan, if we didn't have any previous
                    # match - maybe a later line will produce a partial match.
                    # But do not reset if we already have something matching,
                    # because that would defeat the "in order" assumption.
                    cursor = self.cursor()

    def optional(self, name: str, tolerated_lines: list[str]) -> None:
        """Those lines may exist and then they may appear anywhere
        a number of times, or they may not exist.
        """
        for tolerated_line in tolerated_lines:
            for line in self.cursor():
                if line.matches(tolerated_line):
                    line.mark(Status.OPTIONAL, name)

    def refused(self, name: str, refused_lines: list[str]) -> None:
        for refused_line in refused_lines:
            for line in self.cursor():
                if line.matches(refused_line):
                    line.mark(Status.REFUSED, name)
                    self.matched_refused.add((name, refused_line))

    def continuous(self, name: str, continuous_lines: list[str]) -> None:
        continuous_cursor = enumerate(continuous_lines)
        continuous_index, continuous_line = next(continuous_cursor)
        for line in self.cursor():
            if continuous_index and not line.data:
                # Continuity still allows empty lines (after the first line) in
                # between as we filter them out from the pattern to make those
                # more readable.
                line.mark(Status.OPTIONAL, name)
                continue
            if line.matches(continuous_line):
                line.mark(Status.EXPECTED, name)
                try:
                    continuous_index, continuous_line = next(continuous_cursor)
                except StopIteration:
                    # We exhausted the pattern and are happy.
                    break
            elif continuous_index:
                # This is not the first focus line any more, it's not valid to
                # not match
                line.mark(Status.REFUSED, name)
                self.unmatched_expectations.append((name, continuous_line))
                self.unmatched_expectations.extend(
                    [(name, line) for i, line in continuous_cursor]
                )
                break
        else:
            self.unmatched_expectations.append((name, continuous_line))
            self.unmatched_expectations.extend(
                [(name, line) for i, line in continuous_cursor]
            )

    def report(self) -> Iterator[str]:
        yield "String did not meet the expectations."
        yield ""
        yield " | ".join(
            [
                Status.EXPECTED.symbol + "=EXPECTED",
                Status.OPTIONAL.symbol + "=OPTIONAL",
                Status.UNEXPECTED.symbol + "=UNEXPECTED",
                Status.REFUSED.symbol + "=REFUSED/UNMATCHED",
            ]
        )
        yield ""
        yield "Here is the string that was tested: "
        yield ""
        for line in self.content:
            yield format_line_report(
                line.status, line.status.symbol, line.status_cause, line.data
            )
        if self.unmatched_expectations:
            yield ""
            yield "These are the unmatched expected lines: "
            yield ""
            for name, line_str in self.unmatched_expectations:
                yield format_line_report(
                    Status.REFUSED, Status.REFUSED.symbol, name, line_str
                )
        if self.matched_refused:
            yield ""
            yield "These are the matched refused lines: "
            yield ""
            for name, line_str in self.matched_refused:
                yield format_line_report(
                    Status.REFUSED, Status.REFUSED.symbol, name, line_str
                )

    def is_ok(self) -> bool:
        if self.unmatched_expectations:
            return False
        for line in self.content:
            if line.status not in [Status.EXPECTED, Status.OPTIONAL]:
                return False
        return True


def format_line_report(
    status: Status,
    symbol: str,
    cause: str,
    line: str,
) -> str:
    if status not in [Status.EXPECTED, Status.OPTIONAL]:
        line = line_to_control_pictures(line)
    return symbol + " " + cause.ljust(15)[:15] + " | " + line


def pattern_lines(lines: str) -> list[str]:
    # Remove leading whitespace, ignore empty lines.
    return list(filter(None, lines.splitlines()))


class Pattern:
    name: str
    library: PatternsLib
    ops: list[tuple[str, str, Any]]
    inherited: set[str]

    def __init__(self, library: PatternsLib, name: str):
        self.name = name
        self.library = library
        self.ops = []
        self.inherited = set()

    # Modifiers (Verbs)

    def merge(self, *base_patterns: str) -> None:
        """Merge rules from base_patterns (recursively) into this pattern."""
        self.inherited.update(base_patterns)

    def normalize(self, mode: str) -> None:
        pass

    # Matches (Adjectives)

    def continuous(self, lines: str) -> None:
        """These lines must appear once and they must be continuous."""
        self.ops.append(("continuous", self.name, pattern_lines(lines)))

    def in_order(self, lines: str) -> None:
        """These lines must appear once and they must be in order."""
        self.ops.append(("in_order", self.name, pattern_lines(lines)))

    def optional(self, lines: str) -> None:
        """These lines are optional."""
        self.ops.append(("optional", self.name, pattern_lines(lines)))

    def refused(self, lines: str) -> None:
        """If those lines appear they are refused."""
        self.ops.append(("refused", self.name, pattern_lines(lines)))

    # Internal API

    def flat_ops(self) -> Iterator[tuple[str, str, Any]]:
        for inherited_pattern in self.inherited:
            yield from getattr(self.library, inherited_pattern).flat_ops()
        yield from self.ops

    def _audit(self, content: str) -> Audit:
        audit = Audit(content)
        for op, *args in self.flat_ops():
            getattr(audit, op)(*args)
        return audit

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, str)
        audit = self._audit(other)
        return audit.is_ok()


class PatternsLib:
    def __getattr__(self, name: str) -> Pattern:
        res = self.__dict__[name] = Pattern(self, name)
        return res
