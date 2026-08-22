"""The statement regex must not care which whitespace follows $a or $p.

set.mm writes the keyword at the end of a line 24 times -- `df-fi`, `df-scott`
and 22 proofs -- putting the typecode on the next line.  A pattern requiring a
space or tab there drops those statements from `kind` and, because `refs` keeps
only tokens already in `kind`, silently drops every citation of them as well.

Run with the stdlib runner, no test dependency:

    python -m unittest discover -s tests -v
"""

import tempfile
import unittest
from pathlib import Path

from mmforge import necessity as N

# A database in miniature.  `df-two` puts its typecode on the next line, the way
# set.mm writes df-fi and df-scott; `thm-b` does the same for a proof.
DATABASE = """\
$c |- wff ( ) -> $.
$v P Q $.
wp $f wff P $.
wq $f wff Q $.

ax-one $a |- P $.

df-two $a
    |- ( P -> Q ) $.

thm-a $p |- Q $= ( ax-one df-two ) ABC $.

thm-b $p
    |- ( P -> Q ) $= ( df-two thm-a ) ABC $.

thm-c $p |- P $= ( thm-b ) AB $.
"""


class TestStatementWhitespace(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.db = Path(self._dir.name) / "mini.mm"
        self.db.write_bytes(DATABASE.encode("utf-8"))

    def test_every_statement_is_registered(self):
        kind, _ = N.parse(self.db)
        self.assertEqual(
            sorted(kind),
            ["ax-one", "df-two", "thm-a", "thm-b", "thm-c"],
        )

    def test_a_keyword_at_end_of_line_still_gets_its_sort(self):
        kind, _ = N.parse(self.db)
        self.assertEqual(kind["df-two"], "a")
        self.assertEqual(kind["thm-b"], "p")

    def test_citations_of_such_a_statement_survive(self):
        _, refs = N.parse(self.db)
        self.assertIn("df-two", refs["thm-a"])
        self.assertEqual(refs["thm-c"], ["thm-b"])

    def test_a_proof_written_that_way_keeps_its_own_edges(self):
        _, refs = N.parse(self.db)
        self.assertEqual(sorted(refs["thm-b"]), ["df-two", "thm-a"])

    def test_reachability_passes_through_such_a_statement(self):
        """thm-c reaches ax-one only by way of thm-b, which was invisible."""
        kind, refs = N.parse(self.db)
        reach = N.closure(kind, refs, {"ax-one"})
        self.assertIn("thm-a", reach)
        self.assertIn("thm-b", reach)
        self.assertIn("thm-c", reach)

    def test_crlf_line_endings_parse_the_same(self):
        crlf = self.db.with_name("mini-crlf.mm")
        crlf.write_bytes(DATABASE.replace("\n", "\r\n").encode("utf-8"))
        self.assertEqual(N.parse(self.db)[0], N.parse(crlf)[0])
        self.assertEqual(N.parse(self.db)[1], N.parse(crlf)[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
