
A (yet unnamed) experiment for a pytest plugin to improve pattern matching for
complex/long outputs from CLIs, HTML and maybe textual documents like JSON,
YAML, etc.

Long outputs means strings with 10-1000 lines.

When writing tests, this should improve:

* tolerance for variability (`...` is used as a pattern)
* tolerance for optional output
* tolerance for output that may appear out of order
* mixing/matching of multiple rules
* writing assumptions in a readable/maintainable way

And **most importantly**: provide failure reports that are very easy
to read and allow pinpointing the cause of a failure quickly.

# Playground

I'm using a nix flake to toy around with this:


```shell
nix develop
$ pytest -vv test_audit.py
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

# DONE

* [x] differentiate between tolerated and expected in status reporting

* [x] add avoided lines that must not appear

* [x] allow patterns expectations/tolerations/... to have names and use those to mark up the report why things matched?

    * (T) DEBUG     | ....
    * (X) MIGRATION | 

* [x] how to deal with HTML boilerplate -> use `optional("...")`

* [x] add  lines that must appear in order without being interrupted

# Later


* [ ] API design for merge alternatives?

* [ ] structlog integration? (via normalization?)

* [ ] add line numbers

* [ ] report line numbers on matched avoidances


# Wording


Matches on patterns are adjectives:

* These lines must appear and they must be **continuous**.
* These lines must appear and they must be **in order**.
* These lines are **optional**.
* If those lines appear they are **refused**.

Modifiers to the pattern itself are verbs:

* *Merge* the rules from those patterns into this one.
* *Normalize* the input (and the rules) in this way.s
