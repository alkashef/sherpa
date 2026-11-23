import contextlib
import io
import os
import re
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

from src.cli import main as cli_main

CATEGORY_ERROR = "error: the category must be 1 to 20 lowercase letters\n"

INVALID_CATEGORIES = st.one_of(
    st.just(""),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=21, max_size=30),
    st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ ",
        min_size=1,
        max_size=25,
    ).filter(lambda s: not re.fullmatch(r"[a-z]{1,20}", s)),
)


@given(category=st.from_regex(r"[a-z]{1,20}", fullmatch=True))
@settings(max_examples=50)
def test_ledg_003_valid_categories_accepted_by_cli(category: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = Path(tmp) / "ledger.json"
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.dict(os.environ, {"LEDGER_DATA": str(ledger)}),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            code = cli_main(["add", "1", category])
        assert code == 0
        assert stderr.getvalue() == ""
        assert uuid.UUID(stdout.getvalue().strip()).version == 4


@given(category=INVALID_CATEGORIES)
@settings(max_examples=50)
def test_ledg_003_invalid_categories_refused_by_cli(category: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = Path(tmp) / "ledger.json"
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.dict(os.environ, {"LEDGER_DATA": str(ledger)}),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            code = cli_main(["add", "1", category])
        assert code == 2
        assert stdout.getvalue() == ""
        assert stderr.getvalue() == CATEGORY_ERROR
        assert not ledger.exists()
