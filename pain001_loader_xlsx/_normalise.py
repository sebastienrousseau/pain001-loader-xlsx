# SPDX-License-Identifier: Apache-2.0 OR MIT
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Turn Excel cell values into the strings a CSV would have carried.

pain001's CSV loader is :class:`csv.DictReader`, so every value it
produces is a ``str``. The generated XML is rendered from those
strings. For an ``.xlsx`` file to produce *byte-identical* XML to the
equivalent CSV — the acceptance criterion for this package — the values
this loader emits have to be the same strings.

That is harder than it sounds, because Excel does not store what it
displays. A cell showing ``100.00`` is the float ``100.0``; a cell
showing ``0023456`` may be the int ``23456`` with the leading zeros
gone for good. Recovering the displayed text needs the cell's
``number_format``, and where the information is genuinely destroyed
this module's job is to say so rather than guess.

The rules, in order:

* ``str`` — used as Excel displays it: OOXML's ``_xHHHH_`` escapes
  (ECMA-376 Part 1, ST_Xstring) are decoded, so a cell holding a
  carriage return yields one rather than the six characters
  ``_x000D_``. This is the good case, and the reason the documentation
  tells users to format columns as Text.
* ``None`` — the empty string, matching how ``DictReader`` reports an
  empty field.
* ``bool`` — ``"TRUE"`` / ``"FALSE"``, which is what Excel shows.
* ``int`` / ``float`` — rendered through the cell's ``number_format``
  when that format pins the number of decimals (``0.00`` -> two), and
  otherwise with the shortest representation that round-trips.
* ``datetime`` / ``date`` / ``time`` — rejected. See
  :mod:`pain001_loader_xlsx.errors`.

No quote is added in front of a value starting with ``=``, ``+``,
``-`` or ``@``. pain001 writes ISO 20022 XML, which nothing evaluates,
and since 0.0.74 its CSV loader keeps such values raw too (pain001
ADR-0008), so the same sheet renders the same XML either way.
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

#: Matches the decimal places a numeric ``number_format`` pins, e.g.
#: ``0.00``, ``#,##0.000``, ``0.00;[Red]-0.00``. Only the first section
#: matters: Excel's positive-form section governs an ordinary value.
_DECIMALS = re.compile(r"[0#]\.([0#]+)")

#: Formats that carry no decimal information worth honouring.
_UNFORMATTED = frozenset({"General", "@", ""})

#: ECMA-376 Part 1, ST_Xstring: ``_xHHHH_`` stands for the UTF-16 code
#: unit ``HHHH``. A literal ``_xHHHH_`` is stored with its underscore
#: escaped (``_x005F_xHHHH_``), which a single left-to-right pass decodes.
_ESCAPE = re.compile(r"_x([0-9A-Fa-f]{4})_")

#: What XML 1.0's ``Char`` production excludes: no payment message can
#: carry these, so a cell holding one is refused rather than passed on.
_NOT_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")


def decimals_in(number_format: str | None) -> int | None:
    """Return the decimal places pinned by ``number_format``, if any.

    Args:
        number_format: The cell's Excel number format, as openpyxl
            reports it. ``None`` for cells that carry none.

    Returns:
        The count of digits after the decimal point that the format
        pins, or ``None`` when the format leaves it open (``General``,
        text, or a format with no decimal section).

    Example:
        >>> decimals_in("0.00")
        2
        >>> decimals_in("#,##0.000")
        3
        >>> decimals_in("General") is None
        True
    """
    if not number_format or number_format in _UNFORMATTED:
        return None
    first_section = number_format.split(";", 1)[0]
    match = _DECIMALS.search(first_section)
    if match is None:
        return None
    return len(match.group(1))


def decode_escapes(text: str) -> str:
    """Decode OOXML ``_xHHHH_`` escapes into the characters Excel shows.

    openpyxl returns shared and inline strings with the escapes intact.
    An escaped surrogate pair decodes to the one character it encodes;
    a lone surrogate stays, for :func:`not_xml` to report.

    Args:
        text: A string cell's value as openpyxl read it.

    Returns:
        The text with every escape decoded.

    Example:
        >>> decode_escapes("Line1_x000D_\\nLine2")
        'Line1\\r\\nLine2'
        >>> decode_escapes("_x005F_x0041_")
        '_x0041_'
    """
    if "_x" not in text:
        return text
    decoded = _ESCAPE.sub(lambda match: chr(int(match[1], 16)), text)
    return decoded.encode("utf-16-le", "surrogatepass").decode(
        "utf-16-le", "surrogatepass"
    )


def not_xml(text: str) -> str | None:
    """Return the first character in ``text`` that XML 1.0 cannot carry.

    Args:
        text: Decoded cell text.

    Returns:
        The offending character, or ``None`` when every character is
        allowed.

    Example:
        >>> not_xml("ACME\\x07Ltd")
        '\\x07'
        >>> not_xml("Line1\\r\\nLine2") is None
        True
    """
    match = _NOT_XML.search(text)
    return None if match is None else match[0]


def _number_to_text(value: int | float, number_format: str | None) -> str:
    """Render a numeric cell the way Excel displays it.

    Args:
        value: The numeric cell value openpyxl produced.
        number_format: The cell's Excel number format.

    Returns:
        The number as text.
    """
    places = decimals_in(number_format)
    if places is not None:
        try:
            quantum = Decimal(1).scaleb(-places)
            return str(
                Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
            )
        except (InvalidOperation, ValueError):  # pragma: no cover - guard
            return str(value)

    if isinstance(value, int):
        return str(value)

    # An unformatted float. `100.0` came from a cell showing `100`, so
    # drop the artefact zero; anything else keeps its shortest
    # round-tripping form, which is what `str` already gives.
    if value.is_integer():
        return str(int(value))
    return str(value)


def to_text(value: Any, number_format: str | None) -> str:
    """Convert one cell value to the string a CSV would have held.

    Args:
        value: The cell value openpyxl produced.
        number_format: The cell's Excel number format, used to recover
            the displayed precision of numeric cells.

    Returns:
        The cell as text.

    Example:
        >>> to_text("DE89370400440532013000", "@")
        'DE89370400440532013000'
        >>> to_text(100.0, "0.00")
        '100.00'
        >>> to_text(None, None)
        ''
        >>> to_text("+44 20 7946 0000", None)
        '+44 20 7946 0000'
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return decode_escapes(value)
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return _number_to_text(value, number_format)
    return str(value)
