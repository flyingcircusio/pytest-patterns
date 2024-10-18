`pytest-patterns` is a plugin for pytest that provides a pattern matching
engine optimized for testing.

Benefits:

* provides easy to read reporting for complex patterns in long strings (1000+ lines)
* assists in reasoning which patterns have matched or not matched – and why
* can deal with ambiguity, optional and repetitive matches, intermingled
  output from non-deterministic concurrent processes
* helps writing patterns that are easy to read, easy to maintain and
  easy to adjust in the face of unstable outputs
* helps reusing patterns using pytest fixtures

Long term goals:

Support testing of CLI output, as well as HTML and potentially typical text/*
types like JSON, YAML, and others.

# Examples

Try and play around using the examples in the source repository. The
examples fail on purpose, because the failure reporting is the most important
and useful part – aside from making it easier to write the assertions.

```shell
$ nix develop
$ hatch run test examples -vv
```

# Basic API

## `optional` matches and variability with the ellipsis `...`

If you want to test a complex string, start by pulling in the `patterns` fixture
and create a named pattern that accepts any number of lines that contain
the word "better":

```python
import this

zen = "".join([this.d.get(c, c) for c in this.s])


def test_zen(patterns):
    p = patterns.better_things
    p.optional("...better...")
    assert p == zen
```

This will not give us a green bar, as the pattern does match some lines, but
some lines were not matched and thus considered **unexpected**:

```
  🟢=EXPECTED | ⚪️=OPTIONAL | 🟡=UNEXPECTED | 🔴=REFUSED/UNMATCHED

  Here is the string that was tested:

  🟡                 | The Zen of Python, by Tim Peters
  🟡                 |
  ⚪️ better_things   | Beautiful is better than ugly.
  ⚪️ better_things   | Explicit is better than implicit.
  ⚪️ better_things   | Simple is better than complex.
  ⚪️ better_things   | Complex is better than complicated.
  ⚪️ better_things   | Flat is better than nested.
  ⚪️ better_things   | Sparse is better than dense.
  🟡                 | Readability counts.
  🟡                 | Special cases aren't special enough to break the rules.
  🟡                 | Although practicality beats purity.
  🟡                 | Errors should never pass silently.
  🟡                 | Unless explicitly silenced.
  🟡                 | In the face of ambiguity, refuse the temptation to guess.
  🟡                 | There should be one-- and preferably only one --obvious way to do it.
  🟡                 | Although that way may not be obvious at first unless you're Dutch.
  ⚪️ better_things   | Now is better than never.
  ⚪️ better_things   | Although never is often better than *right* now.
  🟡                 | If the implementation is hard to explain, it's a bad idea.
  🟡                 | If the implementation is easy to explain, it may be a good idea.
  🟡                 | Namespaces are one honking great idea -- let's do more of those!
```

The report highlights which lines were matched (and which pattern caused the
match) and are fine the way they are. Optional matches are displayed with a
white circle (⚪️). The report also highlights those lines that weren't matched
and marked with a yellow circle (🟡).

We know the Zen is correct the way it is, so lets use more of the API to continue
completing the pattern.

## `continous` matches

Lets use the `continuous` match which requires lines to come both in a specific order
and must not be interrupted by other lines. We create a new named pattern and
`merge` it with the previous pattern:

```python
def test_zen(patterns):
    ...

    p = patterns.conclusio
    p.continous("""
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
""")
    full_pattern = patterns.full
    full_pattern.merge("better_things", "conclusio")

    assert full_pattern == zen
```

This gets us a bit further:

```
  🟢=EXPECTED | ⚪️=OPTIONAL | 🟡=UNEXPECTED | 🔴=REFUSED/UNMATCHED

  Here is the string that was tested:

  🟡                 | The Zen of Python, by Tim Peters
  🟡                 |
  ⚪️ better_things   | Beautiful is better than ugly.
  ⚪️ better_things   | Explicit is better than implicit.
  ⚪️ better_things   | Simple is better than complex.
  ⚪️ better_things   | Complex is better than complicated.
  ⚪️ better_things   | Flat is better than nested.
  ⚪️ better_things   | Sparse is better than dense.
  🟡                 | Readability counts.
  🟡                 | Special cases aren't special enough to break the rules.
  🟡                 | Although practicality beats purity.
  🟡                 | Errors should never pass silently.
  🟡                 | Unless explicitly silenced.
  🟡                 | In the face of ambiguity, refuse the temptation to guess.
  🟡                 | There should be one-- and preferably only one --obvious way to do it.
  🟡                 | Although that way may not be obvious at first unless you're Dutch.
  ⚪️ better_things   | Now is better than never.
  ⚪️ better_things   | Although never is often better than *right* now.
  🟢 conclusio       | If the implementation is hard to explain, it's a bad idea.
  🟢 conclusio       | If the implementation is easy to explain, it may be a good idea.
  🟢 conclusio       | Namespaces are one honking great idea -- let's do more of those!
```

Note, that lines matched by `continuous` are highlighted in green as they are
considered a stronger match than the `optional` ones.

## `in_order` matches

There is still stuff missing. Lets make the test green by creating a match for
all other lines using `in_order`, which expects the lines to come in the order
given, but might be mixed in with other lines.

```python
def test_zen(patterns):
    ...
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
```

Shouldn't that have given us a green bar? I can still see a yellow circle there!

```
  🟢=EXPECTED | ⚪️=OPTIONAL | 🟡=UNEXPECTED | 🔴=REFUSED/UNMATCHED

  Here is the string that was tested:

  🟢 top_and_middle  | The Zen of Python, by Tim Peters
  🟡                 |
  ⚪️ better_things   | Beautiful is better than ugly.
  ⚪️ better_things   | Explicit is better than implicit.
  ⚪️ better_things   | Simple is better than complex.
  ⚪️ better_things   | Complex is better than complicated.
  ⚪️ better_things   | Flat is better than nested.
  ⚪️ better_things   | Sparse is better than dense.
  🟢 top_and_middle  | Readability counts.
  🟢 top_and_middle  | Special cases aren't special enough to break the rules.
  🟢 top_and_middle  | Although practicality beats purity.
  🟢 top_and_middle  | Errors should never pass silently.
  🟢 top_and_middle  | Unless explicitly silenced.
  🟢 top_and_middle  | In the face of ambiguity, refuse the temptation to guess.
  🟢 top_and_middle  | There should be one-- and preferably only one --obvious way to do it.
  🟢 top_and_middle  | Although that way may not be obvious at first unless you're Dutch.
  ⚪️ better_things   | Now is better than never.
  ⚪️ better_things   | Although never is often better than *right* now.
  🟢 conclusio       | If the implementation is hard to explain, it's a bad idea.
  🟢 conclusio       | If the implementation is easy to explain, it may be a good idea.
  🟢 conclusio       | Namespaces are one honking great idea -- let's do more of those!
```

## Handling empty lines with the `<empty-line>` marker

The previous pattern is not quite perfect because `pytest-patterns` has a
special way to handle newlines both in patterns and in content.

1. In content that is tested we never implicitly accept any lines that were not
   specified, including empty lines.

2. However, in patterns empty lines are not significant to allow you to use them
   to make your patterns more readable by grouping lines visually.

We get out of this by using the special marker `<empty-line>` in our patterns
which will match both literally for lines containing `<empty-line>` and which
are empty lines:

```python
def test_zen(patterns):
    ...
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
    ...
    assert full_pattern == zen
```

And we finally get a green bar:

```
examples/test_examples.py::test_zen_5_1 PASSED
```

## `refused` matches

Up until now we only created matches that allowed us to write down
things that we expect. However, we can also explicitly refuse lines - for example any line
containing the word "should":

```python
def test_zen(patterns):
    ...
    p = patterns.no_should
    p.refused("...should...")

    full_pattern = patterns.full
    full_pattern.merge(
        "no_should", "top_and_middle", "better_things", "conclusio"
    )

    assert full_pattern == zen
```

This is were `pytest-patterns` really shines. We now can quickly see which parts
of our output is OK and which isn't and why:

```
  🟢=EXPECTED | ⚪️=OPTIONAL | 🟡=UNEXPECTED | 🔴=REFUSED/UNMATCHED

  Here is the string that was tested:

  🟢 top_and_middle  | The Zen of Python, by Tim Peters
  🟡                 |
  ⚪️ better_things   | Beautiful is better than ugly.
  ⚪️ better_things   | Explicit is better than implicit.
  ⚪️ better_things   | Simple is better than complex.
  ⚪️ better_things   | Complex is better than complicated.
  ⚪️ better_things   | Flat is better than nested.
  ⚪️ better_things   | Sparse is better than dense.
  🟢 top_and_middle  | Readability counts.
  🟢 top_and_middle  | Special cases aren't special enough to break the rules.
  🟢 top_and_middle  | Although practicality beats purity.
  🔴 no_should       | Errors should never pass silently.
  🟢 top_and_middle  | Unless explicitly silenced.
  🟢 top_and_middle  | In the face of ambiguity, refuse the temptation to guess.
  🔴 no_should       | There should be one-- and preferably only one --obvious way to do it.
  🟢 top_and_middle  | Although that way may not be obvious at first unless you're Dutch.
  ⚪️ better_things   | Now is better than never.
  ⚪️ better_things   | Although never is often better than *right* now.
  🟢 conclusio       | If the implementation is hard to explain, it's a bad idea.
  🟢 conclusio       | If the implementation is easy to explain, it may be a good idea.
  🟢 conclusio       | Namespaces are one honking great idea -- let's do more of those!`

  These are the matched refused lines:

  🔴 no_should       | ...should...
  🔴 no_should       | ...should...

```

## Re-using patterns with fixtures

Lastly, we'd like to re-use patterns in multiple tests. Let's refactor the
current patterns into a separate fixture that can be activated as needed:

```python
import pytest
import this

zen = "".join([this.d.get(c, c) for c in this.s])


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


def test_zen(patterns, zen_patterns):
    full_pattern = patterns.full
    full_pattern.merge("better_things", "conclusio", "top_and_middle")

    assert full_pattern == zen
```

## Handling tabs and whitespace

When copying and pasting output from commands its easy to turn tabs from an
original source into spaces and then accidentally not aligning things right.

As its more typical to not insert tabs in your code pytest-patterns converts
tabs to spaces (properly aligned to 8 character stops as terminals render them):

```python
def test_tabs_and_spaces(patterns):
    data = """
pre>\taligned text
prefix>\tmore aligned text
"""
    tabs = patterns.tabs
    tabs.in_order("""
pre>    aligned text
prefix> aligned text
""")
    assert tabs == data
```

# Development


```shell
$ pre-commit install
$ nix develop
$ hatch run test
```


# TODO

* [ ] normalization feature

    -> json (+whitespace)
        -> python object causes serialization
        -> json object causes deserialization + reserialization (mit readable oder so)
        -> whitespace normalization

    -> html (+whitespace)
        -> parse html, then serialize in a normalized way
        -> whitespace normalization for both pattern and tested content

    -> whitespace (pattern and tested content)
        -> strip whitespace at beginning and end
        -> fold multiple spaces into single spaces (makes it harder to diagnose things)

* [ ] proper release process with tagging, version updates, etc.

* [ ] Get coverage working correctly (https://pytest-cov.readthedocs.io/en/latest/plugins.html doesnt seem to help ...)

* [ ] Get the project fully set up to make sense for interested parties and
      potential contributors.

* [ ] optional reporting without colors

* [ ] matrix builds for multiple python versions / use tox locally and in github action?

* [ ] highlight whitespace (e.g. <TAB> <SPACE> ) when reporting unmatched expected lines. this can be confusing if you see an "empty" line because you typoed e.g.:

```
    outmigrate.optional(
        """
simplevm             waiting                        interval=3 remaining=...
simplevm             check-staging-config           result='none'
simplevm             query-migrate                  arguments={} id=None subsystem='qemu/qmp'
simplevm             migration-status               mbps=... remaining='...' status='active'
simplevm             vm-destroy-kill-vm             attempt=... subsystem='qemu'
    """
    )
```

Do you see it? There are four spaces on the last line which is now an expected line with four spaces ...

This could also be improved by ignoring whitespace only lines (optionally?)


# DONE


* [x] coding style template

* [x] Actual documentation

* [x] differentiate between tolerated and expected in status reporting

* [x] add avoided lines that must not appear

* [x] allow patterns expectations/tolerations/... to have names and use those to mark up the report why things matched?

    * [T] DEBUG     | ....
    * [X] MIGRATION |

* [x] how to deal with HTML boilerplate -> use `optional("...")`

* [x] add  lines that must appear in order without being interrupted

# Later

* [ ] html normalization might want to include a feature to suppress reporting
   of certain lines (and just add `...` in the reporting output, e.g. if something
   fails do not report the owrap lines

* [ ] add line numbers

* [ ] report line numbers on matched avoidances

* [ ] structlog integration

* [ ] more comprehensive docs

# Wording


Matches on patterns are adjectives:

* These lines must appear and they must be **continuous**.
* These lines must appear and they must be **in order**.
* These lines are **optional**.
* If those lines appear they are **refused**.

Modifiers to the pattern itself are verbs:

* *Merge* the rules from those patterns into this one.
* *Normalize* the input (and the rules) in this way.s
