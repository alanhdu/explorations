# Dataselect

Dataselect is a way to execute query strings on arbitrary data safely.
The data I use are stored with pandas dataframes, but any object where
`__getitem__` returns a NumPy compatible object should also work.

Dataselect is primarily powered by NumPy (for execution) and SymPy (to
store expressions). Unlike SymPy though:

* query strings are parsed via PyParsing, not via `eval`. That means it
  is much harder (impossible?) to hide unsafe code within the queries.
* Dataselect supports any symbol/column name, including those with
  punctuation and whitespace.
* Dataselect lets you easily include custom functions, without asking
  about derivatives or things like that.
* Dataselect supports operations on data columns (pandas Series if the
  selectee is a pandas DataFrame). That let's us write N -> 1 functions
  like mean, among other things.

## Query Syntax

String queries should be written like Sympy expressions, although all
data columns should be written in quotes (e.g. `log("Column 1") + 3`).
Quotes can be escaped with `\"`.

## Quick Tutorial

The function that will be used most is `dataselect.select`, which takes
a string query and an optional data selectee. If no data is provided,
`select` returns a `Selector` object, which can be called on any object.
If data is provided, `select` uses the `Selector` on the data selectee.

## Example Usage

```Python
>>> import dataselect as ds
>>> import pandas as pd
>>> df = pd.DataFrame("test/iris.csv")

>>> ds.select('"SepalLength"', df)

>>> def mean(xs):
...     return sum(x) / len(x)
>>> f = ds.select('"SepalWidth" - mean("SepalWidth")', custom_funcs={"mean": mean})
>>> f(df)
```

## Dependencies

* numpy
* toolz
* sympy
* pyparsing
