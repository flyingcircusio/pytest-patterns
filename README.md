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
nix develop
$ pytest -vv examples
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
		-> replace tabs with spaces
		-> fold multiple spaces into single spaces

* [ ] Get the project fully set up to make sense for interested parties and
      potential contributors.

* [ ] github actions integration

* [ ] coding style template

* [ ] Actual documentation

# DONE

* [x] differentiate between tolerated and expected in status reporting

* [x] add avoided lines that must not appear

* [x] allow patterns expectations/tolerations/... to have names and use those to mark up the report why things matched?

    * (T) DEBUG     | ....
    * (X) MIGRATION |

* [x] how to deal with HTML boilerplate -> use `optional("...")`

* [x] add  lines that must appear in order without being interrupted

# Later

* [ ] add line numbers

* [ ] report line numbers on matched avoidances

* [ ] structlog integration


# Wording


Matches on patterns are adjectives:

* These lines must appear and they must be **continuous**.
* These lines must appear and they must be **in order**.
* These lines are **optional**.
* If those lines appear they are **refused**.

Modifiers to the pattern itself are verbs:

* *Merge* the rules from those patterns into this one.
* *Normalize* the input (and the rules) in this way.s
