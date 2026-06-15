#!/usr/bin/env python3
"""scrSummary: the pre-submit preview must not read SharePoint .Attachments
(only valid inside a gallery/form row). The captured photos for this session are
already in colPhotos, so the preview uses colPhotos only and drops the broken
list-attachment fallback. The submit (Patch colPhotos -> list Attachments) is
left untouched."""
import os, re

SRC = os.path.join(os.path.dirname(__file__), "..", "src", "Src", "scrSummary.pa.yaml")

# =Coalesce(<colphoto>, Index(LookUp(<list>, Row_Key = ...).Attachments, N).Value) -> =<colphoto>
IMG = re.compile(
    r'=Coalesce\((LookUp\(colPhotos, key="[^"]+" && index=\d+\)\.photo), '
    r'Index\(LookUp\(Audit_[A-Za-z_]+, Row_Key = varAuditKey & "[^"]+"\)\.Attachments, \d+\)\.Value\)')
# (!IsBlank(<colphoto>) || (CountRows(LookUp(<list>,...).Attachments) >= N)) -> !IsBlank(<colphoto>)
COND = re.compile(
    r'\(!IsBlank\((LookUp\(colPhotos, key="[^"]+" && index=\d+\)\.photo)\) \|\| '
    r'\(CountRows\(LookUp\(Audit_[A-Za-z_]+, Row_Key = varAuditKey & "[^"]+"\)\.Attachments\) >= \d+\)\)')


def main():
    with open(SRC, "r", newline="") as f:
        t = f.read()
    cr = t.count("\r")
    t, n_img = IMG.subn(r"=\1", t)
    t, n_cond = COND.subn(r"!IsBlank(\1)", t)
    assert t.count(".Attachments") == 0, f"residual .Attachments: {t.count('.Attachments')}"
    assert t.count("\r") == cr
    with open(SRC, "w", newline="") as f:
        f.write(t)
    print(f"scrSummary: image fallbacks removed={n_img}, condition fallbacks removed={n_cond}, "
          f".Attachments now={t.count('.Attachments')}")


if __name__ == "__main__":
    main()
