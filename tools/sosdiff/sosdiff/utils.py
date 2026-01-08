"""
utils.py: utilities for formatting output
"""
import io
import os
import re
import sys
from difflib import SequenceMatcher
from typing import Any
from typing import IO
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple


COLOR = os.isatty(sys.stdout.fileno())
_ESCAPE = re.compile("\033\[[^m]*m")


def bold(s: str) -> str:
    """Return s, but bolded (if color is enabled)"""
    if COLOR:
        return "\033[1m" + s + "\033[0m"
    else:
        return s

def compare_multiline_strings(a: str, b: str) -> Tuple[str, str]:
    """
    Compare two strings character-by-character and return new strings where the
    differences are bolded.

    Notes:
    - Uses ANSI escapes, which may not be supported on all terminals, and which
      require proper handling for string alignment.
    - This is for single-line strings. Multi-line strings can use the standard
      difflib tools.
    """
    m = SequenceMatcher(a=a, b=b)
    i, j = 0, 0
    sa, sb = "", ""
    common = ""
    blocks = m.get_matching_blocks()
    current_block = 0

    for new_i, new_j, n in blocks:
        current_block = current_block + 1
        if new_i > i:
            sa += bold(a[i:new_i])
            i = new_i
        if new_j > j:
            sb += bold(b[j:new_j])
            j = new_j
        if n == 0:
            continue
        common = a[i:i+n]
        if "\n" in common:
            if i == 0:
                common = common.split("\n").pop()
            else:
                common_sections = common.split("\n")
                if len(common_sections) > 1 and current_block < len(blocks):
                    common = common_sections[0] + "\n" + common_sections.pop()
                else:
                    common = common_sections[0] + "\n"

        sa += common
        sb += common
        i = new_i + n
        j = new_j + n

    return sa, sb

def compare_strings(a: str, b: str) -> Tuple[str, str]:
    """
    Compare two strings character-by-character and return new strings where the
    differences are bolded.

    Notes:
    - Uses ANSI escapes, which may not be supported on all terminals, and which
      require proper handling for string alignment.
    - This is for single-line strings. Multi-line strings can use the standard
      difflib tools.
    """
    m = SequenceMatcher(a=a, b=b)
    i, j = 0, 0
    sa, sb = "", ""
    for new_i, new_j, n in m.get_matching_blocks():
        if new_i > i:
            sa += bold(a[i:new_i])
            i = new_i
        if new_j > j:
            sb += bold(b[j:new_j])
            j = new_j
        if n == 0:
            continue
        common = a[i:i+n]
        sa += common
        sb += common
        i = new_i + n
        j = new_j + n
    return sa, sb


def _ljust(s: str, width: int, fillchar: str = ' ') -> str:
    """Left-justify, taking into account ANSI escape sequences."""
    escapelen = sum(m.span()[1] - m.span()[0] for m in _ESCAPE.finditer(s))
    return s.ljust(width + escapelen, fillchar)


def _rjust(s: str, width: int, fillchar: str = ' ') -> str:
    """Left-justify, taking into account ANSI escape sequences."""
    escapelen = sum(m.span()[1] - m.span()[0] for m in _ESCAPE.finditer(s))
    return s.rjust(width + escapelen, fillchar)


class Table:
    """
    Create an aligned, formatted table

    This helper makes it simple to create a text table which is aligned to your
    requirements, and whose values are formatted with whatever string formatter
    you'd like. The table will be written to stdout by default, but can be
    written to a custom output file if you prefer.

    To create the table, you need to specify all the columns. Each column is
    specified by a string which contains the column name, and optionally a colon
    (":") followed by a format string. You can prefix the format string with a
    "<" or ">" to control the justification of the column (it is stripped from
    the format string). By default, columns are left justified and formatted
    using ``format(value, '')`` which is typically the same as ``str()``. Here
    are some example column specifiers:

    1. "TIME:>.3f" - a column named "TIME", right justified
    2. "NAME" - a column named "NAME", left justified, formatted by str()
    3. "PTR:016x" - a 16-digit hexadecimal value, 0-filled

    Please note that this function will store all rows until ``write()`` is
    called. This way, it can determine the expected column widths for all rows,
    and align them accordingly. If you'd like your table rows to be printed as
    they are created (e.g. if producing the output takes a long time, and you'd
    like the user to see output as it becomes available), then you could use
    :class:`FixedTable`.

    :param header: a list of column specifiers, see above for details
    :param outfile: optional output file name (default is stdout)
    :param report: when true, outfile is opened in append mode
    """

    def __init__(
        self,
        header: List[str],
        outfile: Optional[str] = None,
        report: bool = False,
    ):
        # Name of each header
        self.header = []
        # Function (str, int) -> str to justify each column entry
        self.justifier = []
        # Format string for column
        self.formats = []
        for h in header:
            just = _ljust
            if ":" in h:
                name, fmt = h.rsplit(":", 1)
            else:
                name, fmt = h, ""
            if len(fmt) > 0 and fmt[0] in ("<", ">"):
                if fmt[0] == ">":
                    just = _rjust
                fmt = fmt[1:]
            self.header.append(name)
            self.justifier.append(just)
            self.formats.append(fmt)
        self.widths = [len(h) for h in header]
        self.rows: List[List[str]] = []
        self.out = sys.stdout
        self.close_output = bool(outfile)
        if outfile and report:
            self.out = open(outfile, "a")
            self.out.write("\n\n")
        elif outfile:
            self.out = open(outfile, "w")

    def _build_row(
        self, fields: Iterable[Any], update_widths: bool = True
    ) -> List[str]:
        row = []
        for i, data in enumerate(fields):
            if i < len(self.header):
                string = format(data, self.formats[i])
            else:
                string = str(data)
            row.append(string)
            strlen = len(string) - sum(
                m.span()[1] - m.span()[0] for m in _ESCAPE.finditer(string)
            )
            if update_widths and strlen > self.widths[i]:
                self.widths[i] = strlen
        return row

    def add_row(self, fields: Iterable[Any]) -> None:
        """Add a row to the table (values expressed as a list)"""
        self.rows.append(self._build_row(fields))

    def row(self, *fields: Any) -> None:
        """Add a row to the table (values expressed as positional args)"""
        self.add_row(fields)

    def _row_str(self, row: List[str]) -> str:
        return "  ".join(
            j(s, w) for j, s, w in zip(self.justifier, row, self.widths)
        ).rstrip()

    def write(self) -> None:
        """Print the table to the output file"""
        print(self._row_str(self.header), file=self.out)
        for row in self.rows:
            print(self._row_str(row), file=self.out)


def perror(e, verb = None, **kwds):
    """
    Standard error handler for dealing with file errors.
    Author: Ronan Pigott
    """
    *_prefix, prog = os.path.split(sys.argv[0])
    if verb and e.filename:
        filename = os.fsencode(e.filename).decode(errors='backslashreplace')
        context = f"cannot {verb} {filename!r}: "
    else:
        context = ""
    print(f"ERROR: {context}{e.strerror}", file=sys.stderr, **kwds)

def open_package_data(
    name: str, mode: str, encoding: Optional[str] = None
) -> IO:
    """Opens a data file distributed alongside sosdiff"""
    try:
        # The preferred way starting from Python 3.9
        from importlib.resources import files

        container = files("sosdiff")
        return (container / name).open(mode, encoding=encoding)

    except (ImportError, ModuleNotFoundError):
        # Deprecated starting from Python 3.9, removed in 3.12
        from pkg_resources import resource_stream

        stream = resource_stream("sosdiff", name)
        if "b" not in mode or encoding is not None:
            stream = io.TextIOWrapper(stream, encoding=encoding)
        return stream
