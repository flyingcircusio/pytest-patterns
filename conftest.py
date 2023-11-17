import pytest

pytest.register_assert_rewrite("audit")

from audit import PatternsLib  # noqa: need to import after rewrite statement


def pytest_assertrepr_compare(op, left, right):
    if op != "==":
        return
    if left.__class__.__name__ == "Pattern":
        return left._audit(right).report()
    elif right.__class__.__name__ == "Pattern":
        return right._audit(left).report()


@pytest.fixture
def patterns():
    yield PatternsLib()
