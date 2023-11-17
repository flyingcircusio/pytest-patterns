import pytest
import this

zen = "".join([this.d.get(c, c) for c in this.s])


def test_comprehensive_example(patterns):
    patterns.ordered_sample.in_order(
        """
This comes early on
This comes later

This comes even later
And this should come last - but it doesn't
"""
    )

    patterns.optional_sample.optional(
        """
This is a heartbeat that can appear almost anywhere...
"""
    )
    patterns.continous_sample.continuous(
        """
This comes first (...)
This comes second (...)
This comes third (...)
"""
    )
    patterns.refused_sample.refused(
        """
...error...
"""
    )

    full_pattern = patterns.full
    full_pattern.merge(
        "ordered_sample",
        "optional_sample",
        "continuous_sample",
        "refused_sample",
    )
    assert (
        full_pattern
        == """\
This comes early on
This is a heartbeat that can appear almost anywhere
This comes first (with variability)
This comes second (also with variability)
This comes third (more variability!)
This line is an error :(
This is a heartbeat that can appear almost anywhere (outside focus ranges)
This comes later
This comes even later
"""
    )


def test_zen_1(patterns):
    p = patterns.better_things
    p.optional("...better...")
    assert p == zen


def test_zen_2(patterns):
    p = patterns.better_things
    p.optional("...better...")

    p = patterns.conclusio
    p.continuous(
        """\
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
"""
    )
    full_pattern = patterns.full
    full_pattern.merge("better_things", "conclusio")

    assert full_pattern == zen


def test_zen_3(patterns):
    p = patterns.better_things
    p.optional("...better...")

    p = patterns.conclusio
    p.continuous(
        """\
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
"""
    )

    p = patterns.top_and_middle
    p.in_order(
        """
The Zen of Python, by Tim Peters

Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
"""
    )
    full_pattern = patterns.full
    full_pattern.merge("top_and_middle", "better_things", "conclusio")

    assert full_pattern == zen


def test_zen_4(patterns):
    p = patterns.better_things
    p.optional("...better...")

    p = patterns.conclusio
    p.continuous(
        """\
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
"""
    )

    p = patterns.top_and_middle
    p.in_order(
        """
The Zen of Python, by Tim Peters

Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
"""
    )
    full_pattern = patterns.full
    full_pattern.merge("top_and_middle", "better_things", "conclusio")

    assert full_pattern == zen


def test_zen_5(patterns):
    p = patterns.better_things
    p.optional("...better...")

    p = patterns.conclusio
    p.continuous(
        """\
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
"""
    )

    p = patterns.top_and_middle
    p.in_order(
        """
The Zen of Python, by Tim Peters

Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
"""
    )
    full_pattern = patterns.full
    full_pattern.merge("top_and_middle", "better_things", "conclusio")

    assert full_pattern == zen


def test_zen_5_1(patterns):
    p = patterns.better_things
    p.optional("...better...")

    p = patterns.conclusio
    p.continuous(
        """\
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
"""
    )

    p = patterns.top_and_middle
    p.optional("<empty-line>")
    p.in_order(
        """
The Zen of Python, by Tim Peters

Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
"""
    )
    full_pattern = patterns.full
    full_pattern.merge("top_and_middle", "better_things", "conclusio")

    assert full_pattern == zen


def test_zen_6(patterns):
    p = patterns.better_things
    p.optional("...better...")

    p = patterns.conclusio
    p.continuous(
        """\
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
"""
    )

    p = patterns.top_and_middle
    p.optional("<empty-line>")
    p.in_order(
        """
The Zen of Python, by Tim Peters

Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
"""
    )

    p = patterns.no_should
    p.refused("...should...")

    full_pattern = patterns.full
    full_pattern.merge(
        "no_should", "top_and_middle", "better_things", "conclusio"
    )

    assert full_pattern == zen


@pytest.fixture
def zen_patterns(patterns):
    p = patterns.better_things
    p.optional("...better...")

    p = patterns.conclusio
    p.continuous(
        """\
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
"""
    )

    p = patterns.top_and_middle
    p.optional("<empty-line>")
    p.in_order(
        """
The Zen of Python, by Tim Peters

Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
"""
    )
    full_pattern = patterns.full
    full_pattern.merge("top_and_middle", "better_things", "conclusio")


def test_zen_7(patterns, zen_patterns):
    full_pattern = patterns.full
    full_pattern.merge("better_things", "conclusio", "top_and_middle")

    assert full_pattern == zen
