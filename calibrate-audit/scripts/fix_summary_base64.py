#!/usr/bin/env python3
"""scrSummary: SharePoint Attachments columns can't be Patched from a built table
(Power Fx requires the nominal Table(Attachment) type; ForAll yields a generic
Table). Store photos as base64 data-URIs in plain text columns Photo1..Photo5 on
each failure list instead - text columns Patch cleanly and can be read anywhere.

Each Photo<N> = the data-URI for colPhotos[key,index=N], or "" when absent:
  If(IsBlank(<photo>), "", With({j: JSON(<photo>, JSONFormat.IncludeBinaryData)}, Mid(j, 2, Len(j)-2)))
(JSON wraps the data-URI in quotes; Mid strips the leading/trailing quote.)
"""
import os, re

SRC = os.path.join(os.path.dirname(__file__), "..", "src", "Src", "scrSummary.pa.yaml")

BLOCK = re.compile(
    r'^(?P<ind> +)Attachments: ForAll\(Filter\(colPhotos, key = "(?P<code>[^"]+)"\) As p,\n'
    r' +\{Name: "[^"]+" & Text\(p\.index\) & "\.jpg", Value: p\.photo\}\)$',
    re.MULTILINE)


def photo_field(ind, code, n):
    lk = f'LookUp(colPhotos, key = "{code}" && index = {n}).photo'
    return (f'{ind}Photo{n}: If(IsBlank({lk}), "", '
            f'With({{j: JSON({lk}, JSONFormat.IncludeBinaryData)}}, Mid(j, 2, Len(j) - 2)))')


def repl(m):
    ind, code = m.group("ind"), m.group("code")
    return ",\n".join(photo_field(ind, code, n) for n in range(1, 6))


def main():
    with open(SRC, "r", newline="") as f:
        t = f.read()
    cr = t.count("\r")
    t, n = BLOCK.subn(repl, t)
    assert "Attachments: ForAll" not in t, "residual Attachments ForAll"
    assert t.count("\r") == cr
    with open(SRC, "w", newline="") as f:
        f.write(t)
    print(f"scrSummary: replaced {n} Attachments blocks with Photo1..Photo5 base64 fields; "
          f"Attachments-ForAll left={t.count('Attachments: ForAll')}, Photo fields={t.count('Photo')}")


if __name__ == "__main__":
    main()
