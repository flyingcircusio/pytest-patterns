import enum
import re
from typing import Iterable, List, Set, Tuple

import pytest


@pytest.fixture
def patterns():
    yield PatternsLib()


def pytest_assertrepr_compare(op, left, right):
    if op != "==":
        return
    if left.__class__.__name__ == "Pattern":
        return list(left._audit(right).report())
    elif right.__class__.__name__ == "Pattern":
        return list(right._audit(left).report())


class Status(enum.Enum):
    UNEXPECTED = 1
    OPTIONAL = 2
    EXPECTED = 3
    REFUSED = 4

    @property
    def symbol(self):
        return STATUS_SYMBOLS[self]


STATUS_SYMBOLS = {
    Status.UNEXPECTED: "🟡",
    Status.EXPECTED: "🟢",
    Status.OPTIONAL: "⚪️",
    Status.REFUSED: "🔴",
}

EMPTY_LINE_PATTERN = "<empty-line>"


def match(pattern, line):
    if pattern == EMPTY_LINE_PATTERN:
        if not line:
            return True
    pattern = pattern.replace("\t", " " * 8)
    line = line.replace("\t", " " * 8)
    pattern = re.escape(pattern)
    pattern = pattern.replace(r"\.\.\.", ".*?")
    pattern = re.compile("^" + pattern + "$")
    return pattern.match(line)


class Line:
    status: Status = Status.UNEXPECTED
    status_cause: str = ""

    def __init__(self, data: str):
        self.data = data

    def matches(self, expectation: str):
        return bool(match(expectation, self.data))

    def mark(self, status: Status, cause: str):
        if status.value <= self.status.value:
            # Stay in the current status
            return
        self.status = status
        self.status_cause = cause


class Audit:
    content: List[Line]
    unmatched_expectations: List[Tuple[str, str]]
    matched_refused: Set[Tuple[str, str]]

    def __init__(self, content: str):
        self.unmatched_expectations = []
        self.matched_refused = set()

        self.content = []
        for line in content.splitlines():
            self.content.append(Line(line))

    def cursor(self):
        return iter(self.content)

    def in_order(self, name: str, expected_lines: List[str]):
        """Expect all lines exist and come in order, but they
        may be interleaved with other lines."""
        cursor = self.cursor()
        for expected_line in expected_lines:
            for line in cursor:
                if line.matches(expected_line):
                    line.mark(Status.EXPECTED, name)
                    break
            else:
                self.unmatched_expectations.append((name, expected_line))
                # Reset the scan, maybe the other lines will match
                cursor = self.cursor()

    def optional(self, name: str, tolerated_lines: List[str]):
        """Those lines may exist and then they may appear anywhere
        a number of times, or they may not exist.
        """
        for tolerated_line in tolerated_lines:
            for line in self.cursor():
                if line.matches(tolerated_line):
                    line.mark(Status.OPTIONAL, name)

    def refused(self, name: str, refused_lines: List[str]):
        for refused_line in refused_lines:
            for line in self.cursor():
                if line.matches(refused_line):
                    line.mark(Status.REFUSED, name)
                    self.matched_refused.add((name, refused_line))

    def continuous(self, name: str, continuous_lines: List[str]):
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

    def report(self):
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
                line.status.symbol, line.status_cause, line.data
            )
        if self.unmatched_expectations:
            yield ""
            yield "These are the unmatched expected lines: "
            yield ""
            for name, line in self.unmatched_expectations:
                yield format_line_report(Status.REFUSED.symbol, name, line)
        if self.matched_refused:
            yield ""
            yield "These are the matched refused lines: "
            yield ""
            for name, line in self.matched_refused:
                yield format_line_report(Status.REFUSED.symbol, name, line)

    def is_ok(self):
        if self.unmatched_expectations:
            return False
        for line in self.content:
            if line.status not in [Status.EXPECTED, Status.OPTIONAL]:
                return False
        return True


def format_line_report(symbol, cause, line):
    return symbol + " " + cause.ljust(15)[:15] + " | " + line


def pattern_lines(lines: str) -> List[str]:
    # Remove leading whitespace, ignore empty lines.
    return list(filter(None, lines.splitlines()))


class Pattern:
    def __init__(self, library, name):
        self.name = name
        self.library = library
        self.ops = []
        self.inherited = set()

    # Modifiers (Verbs)

    def merge(self, *base_patterns):
        """Merge the rules from those patterns (recursively) into this pattern."""
        self.inherited.update(base_patterns)

    def normalize(self, mode: str):
        pass

    # Matches (Adjectives)

    def continuous(self, lines: str):
        """These lines must appear once and they must be continuous."""
        self.ops.append(("continuous", self.name, pattern_lines(lines)))

    def in_order(self, lines: str):
        """These lines must appear once and they must be in order."""
        self.ops.append(("in_order", self.name, pattern_lines(lines)))

    def optional(self, lines: str):
        """These lines are optional."""
        self.ops.append(("optional", self.name, pattern_lines(lines)))

    def refused(self, lines: str):
        """If those lines appear they are refused."""
        self.ops.append(("refused", self.name, pattern_lines(lines)))

    # Internal API

    def flat_ops(self):
        for inherited_pattern in self.inherited:
            yield from getattr(self.library, inherited_pattern).flat_ops()
        yield from self.ops

    def _audit(self, content):
        audit = Audit(content)
        for op, *args in self.flat_ops():
            getattr(audit, op)(*args)
        return audit

    def __eq__(self, other):
        assert isinstance(other, str)
        audit = self._audit(other)
        return audit.is_ok()


class PatternsLib:
    def __getattr__(self, name):
        self.__dict__[name] = Pattern(self, name)
        return self.__dict__[name]
