import unittest

from anki_normalize import VERBATIM, clean_field


class NormalizeTests(unittest.TestCase):
    def assert_clean(self, source, expected, *, include_verbatim=False):
        actual, decisions = clean_field(source, include_verbatim)
        self.assertEqual(actual, expected)
        self.assertTrue(all(match is not None for _, match in decisions))

    def test_normal_text_whitespace(self):
        cases = {
            "one space": "one space",
            "two  spaces": "two spaces",
            "many     spaces": "many spaces",
            "a&nbsp;b": "a b",
            "a&#160;b": "a b",
            "a&#xA0;b": "a b",
            "a\u00a0b": "a b",
            "a &nbsp;  &#160; b": "a b",
            "a  \n  b\t\tb": "a \n b\t\tb",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assert_clean(source, expected)

    def test_latex_preserves_spaces_but_replaces_nbsp(self):
        cases = {
            r"\(a   b\)": r"\(a   b\)",
            r"\[a   b\]": r"\[a   b\]",
            r"outside  \(inside   spaces\)  text": (
                r"outside \(inside   spaces\) text"
            ),
            r"\(a&nbsp;&nbsp;b\)": "\\(a  b\\)",
            r"\[a &nbsp;  b\]": "\\[a    b\\]",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assert_clean(source, expected)

    def test_verbatim_elements_are_untouched(self):
        for tag in VERBATIM:
            source = f"<{tag}>a  &nbsp;b</{tag}>"
            with self.subTest(tag=tag):
                self.assert_clean(source, source)

    def test_all_includes_verbatim_but_respects_latex(self):
        self.assert_clean(
            r"<pre>a  \(b  &nbsp;c\)  d</pre>",
            "<pre>a \\(b   c\\) d</pre>",
            include_verbatim=True,
        )

    def test_attributes_are_never_normalized(self):
        cases = {
            '<span title="a  &nbsp; b">a  &nbsp; b</span>': (
                '<span title="a  &nbsp; b">a b</span>'
            ),
            '<span title="1 >  0 &nbsp;">a  b</span>': (
                '<span title="1 >  0 &nbsp;">a b</span>'
            ),
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assert_clean(source, expected)

    def test_bare_divs_become_minimal_line_boundaries(self):
        cases = {
            "<div>only</div>": "only",
            "<div>A</div><div>B</div>": "A<br>B",
            "before<div>middle</div>after": "before<br>middle<br>after",
            "<div></div>": "",
            "<div>   </div>": "",
            "<div>A</div><div></div><div>B</div>": "A<br>B",
            "<div><div>A</div></div>": "A",
            "<p>A</p><div>B</div><p>C</p>": "<p>A</p>B<p>C</p>",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assert_clean(source, expected)

    def test_attributed_divs_are_preserved(self):
        cases = {
            '<div class="x">A</div>': '<div class="x">A</div>',
            '<div style="color:red">A</div>': (
                '<div style="color:red">A</div>'
            ),
            '<div dir="rtl">A</div>': '<div dir="rtl">A</div>',
            '<div class="x"><div>A</div></div>': (
                '<div class="x">A</div>'
            ),
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assert_clean(source, expected)

    def test_divs_inside_protected_regions_are_preserved(self):
        self.assert_clean(r"\(<div>A</div>\)", r"\(<div>A</div>\)")
        self.assert_clean(
            "<code><div>A</div></code>",
            "<code><div>A</div></code>",
        )

    def test_unmatched_closing_div_is_preserved(self):
        self.assert_clean("A</div>", "A</div>")


if __name__ == "__main__":
    unittest.main()
