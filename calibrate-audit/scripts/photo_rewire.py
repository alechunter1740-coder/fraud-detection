#!/usr/bin/env python3
"""Retire Calibrate_Audit_Photos (doc library) and Calibrate_Audit_App_Photos (flow).
Rewire photo capture/read/write/display to the three failure lists' native Attachments.
Operates on ./src/Src/*.pa.yaml (SourceCode layout, LF endings)."""
import re, sys, os

SRC = os.path.join(os.path.dirname(__file__), "..", "src", "Src")

# code (as used in colPhotos keys / filenames) -> (group, label)
CODES = [
    ("MF_Low_Vacuum", "MF", "Low Vacuum"),
    ("MF_Cold_Seal", "MF", "Cold Seal"),
    ("MF_Edge_Tear", "MF", "Edge Tear"),
    ("MF_Pull_Back", "MF", "Pull Back"),
    ("MF_Burnt_Seals", "MF", "Burnt Seals"),
    ("MF_Other", "MF", "Other"),
    ("OF_Meat_In_Seals", "OF", "Meat In Seals"),
    ("OF_Prod_Reject", "OF", "Product Related Reject"),
    ("OF_Multiple_Pleat", "OF", "Multiple Pleat"),
    ("OF_Bag_Tear", "OF", "Bag Tear"),
    ("OF_Incomplete_Seal", "OF", "Incomplete Seal"),
    ("OF_Uncovered_Bone", "OF", "Uncovered Bone Puncture"),
    ("OF_Pull_Back", "OF", "Pull Back Meat DTS"),
    ("OF_Two_Per_Platen", "OF", "Two Per Platen"),
    ("OF_Other", "OF", "Other"),
    ("BRF_Hole_Before_Shrink", "BRF", "Hole Before Shrink"),
    ("BRF_Hole_After_Shrink", "BRF", "Hole After Shrink"),
    ("BRF_Covered_Bone", "BRF", "Covered Bone Puncture"),
    ("BRF_Single_Pleat", "BRF", "Single Pleat"),
    ("BRF_Edge_Tear", "BRF", "Edge Tear"),
    ("BRF_Factory_Seal", "BRF", "Factory Seal"),
    ("BRF_Heal_Break", "BRF", "Heel Break"),
    ("BRF_Other", "BRF", "Other"),
]
LIST = {"MF": "Audit_Machine_Failures", "OF": "Audit_Operator_Failures", "BRF": "Audit_Bag_Failures"}
DCOL = {"MF": "colMachinePhotosDetail", "OF": "colOperatorPhotosDetail", "BRF": "colBagPhotosDetail"}
GRP = {c: g for c, g, l in CODES}
LABEL = {c: l for c, g, l in CODES}
CODE_ALT = "|".join(sorted([c for c, _, _ in CODES], key=len, reverse=True))


def read(name):
    with open(os.path.join(SRC, name), "r", newline="\n") as f:
        return f.read()


def write(name, text):
    # Preserve the 8 CRs in the generated header; just ensure we did not add more.
    assert text.count("\r") == 8, f"unexpected CR count {text.count(chr(13))}"
    with open(os.path.join(SRC, name), "w", newline="") as f:
        f.write(text)


def count(text):
    return text.count("Calibrate_Audit_Photos"), text.count("Calibrate_Audit_App_Photos")


# ---------------- scrDetail ----------------
def do_detail():
    t = read("scrDetail.pa.yaml")
    before = count(t)
    # OnVisible: replace single doc-library collect with three indexed list collects
    old = ('ClearCollect(colAuditPhotosDetail, Filter(Calibrate_Audit_Photos, '
           'StartsWith(\'File name with extension\', varSelectedAudit.Title & "_")))')
    new = ('ClearCollect(colMachinePhotosDetail,  Filter(Audit_Machine_Failures,  Audit_ID = varSelectedAudit.Title));\n'
           '        ClearCollect(colOperatorPhotosDetail, Filter(Audit_Operator_Failures, Audit_ID = varSelectedAudit.Title));\n'
           '        ClearCollect(colBagPhotosDetail,      Filter(Audit_Bag_Failures,      Audit_ID = varSelectedAudit.Title))')
    assert t.count(old) == 1, "scrDetail OnVisible collect not found uniquely"
    t = t.replace(old, new)

    # Image source: LookUp(...).Thumbnail.Large|Full -> Index(LookUp(detailcol, Failure_Code=..).Attachments, N).Value
    def img_repl(m):
        code, n = m.group("code"), m.group("n")
        return (f'Index(LookUp({DCOL[GRP[code]]}, Failure_Code = "{code}").Attachments, {n}).Value')
    img_pat = re.compile(
        r'LookUp\(Calibrate_Audit_Photos, \'File name with extension\' = varSelectedAudit\.Title & "_'
        r'(?P<code>' + CODE_ALT + r')_(?P<n>\d+)\.png"\)\.Thumbnail\.(?:Large|Full)')
    t, ni = img_pat.subn(img_repl, t)

    # Visibility/height: !IsBlank(LookUp(...)) -> (CountRows(LookUp(detailcol,...).Attachments) >= N)
    def cond_repl(m):
        code, n = m.group("code"), m.group("n")
        return (f'(CountRows(LookUp({DCOL[GRP[code]]}, Failure_Code = "{code}").Attachments) >= {n})')
    cond_pat = re.compile(
        r'!IsBlank\(LookUp\(Calibrate_Audit_Photos, \'File name with extension\' = varSelectedAudit\.Title & "_'
        r'(?P<code>' + CODE_ALT + r')_(?P<n>\d+)\.png"\)\)')
    t, nc = cond_pat.subn(cond_repl, t)

    # Lightbox: thumbnail OnSelect stored a "CODE_N" string key; instead store the resolved image,
    # and have the lightbox render that variable directly.
    def lb_repl(m):
        code, n = m.group("code"), m.group("n")
        return (f'OnSelect: =Set(varLightboxImage, Index(LookUp({DCOL[GRP[code]]}, '
                f'Failure_Code = "{code}").Attachments, {n}).Value); Set(varShowLightbox, true)')
    lb_pat = re.compile(
        r'OnSelect: =Set\(varLightboxPhotoKey, "(?P<code>' + CODE_ALT + r')_(?P<n>\d+)"\); '
        r'Set\(varShowLightbox, true\)')
    t, nlb = lb_pat.subn(lb_repl, t)
    t = t.replace(
        'Image: =LookUp(Calibrate_Audit_Photos, \'File name with extension\' = '
        'varSelectedAudit.Title & "_" & varLightboxPhotoKey & ".png").Thumbnail.Full',
        'Image: =varLightboxImage')

    write("scrDetail.pa.yaml", t)
    after = count(t)
    print(f"scrDetail: images={ni} conds={nc} lightbox={nlb} refs {before} -> {after}")


# ---------------- scrAudit ----------------
def do_audit():
    t = read("scrAudit.pa.yaml")
    before = count(t)
    # OnVisible read: replace doc-library collect with three list collects + edit-mode colPhotos load
    old = ('=ClearCollect(colAuditPhotos, Filter(Calibrate_Audit_Photos, StartsWith('
           '\'File name with extension\', If(varEditMode, varSelectedAudit.Title, varAuditKey) & "_")));')
    assert t.count(old) == 1, "scrAudit OnVisible collect not found uniquely"
    new = (
        '=ClearCollect(colBagPhotos,      Filter(Audit_Bag_Failures,      Audit_ID = If(varEditMode, varSelectedAudit.Title, varAuditKey)));\n'
        '        ClearCollect(colMachinePhotos,  Filter(Audit_Machine_Failures,  Audit_ID = If(varEditMode, varSelectedAudit.Title, varAuditKey)));\n'
        '        ClearCollect(colOperatorPhotos, Filter(Audit_Operator_Failures, Audit_ID = If(varEditMode, varSelectedAudit.Title, varAuditKey)));\n'
        '        If(varEditMode && !varComingFromSummary,\n'
        '            Clear(colPhotos);\n'
        '            ForAll(colMachinePhotos As r, ForAll(Sequence(CountRows(r.Attachments)) As i,\n'
        '                Collect(colPhotos, {key: r.Failure_Code, index: i.Value, photo: Index(r.Attachments, i.Value).Value})));\n'
        '            ForAll(colOperatorPhotos As r, ForAll(Sequence(CountRows(r.Attachments)) As i,\n'
        '                Collect(colPhotos, {key: r.Failure_Code, index: i.Value, photo: Index(r.Attachments, i.Value).Value})));\n'
        '            ForAll(colBagPhotos As r, ForAll(Sequence(CountRows(r.Attachments)) As i,\n'
        '                Collect(colPhotos, {key: r.Failure_Code, index: i.Value, photo: Index(r.Attachments, i.Value).Value})))\n'
        '        );'
    )
    t = t.replace(old, new)

    # Count vars: colAuditPhotos StartsWith(...) -> colPhotos key = "CODE"
    def cnt_repl(m):
        code = m.group("code")
        return f'CountRows(Filter(colPhotos, key = "{code}"))'
    cnt_pat = re.compile(
        r'CountRows\(Filter\(colAuditPhotos, StartsWith\(\'File name with extension\', '
        r'varSelectedAudit\.Title & "_(?P<code>' + CODE_ALT + r')"\)\)\)')
    t, ncnt = cnt_pat.subn(cnt_repl, t)

    # Delete buttons: drop the doc-library RemoveIf line; keep colPhotos remove as first formula line
    del_pat = re.compile(
        r'=RemoveIf\(Calibrate_Audit_Photos, [^\n]*?\.png"\);\n\s*RemoveIf\(colPhotos,')
    t, ndel = del_pat.subn('=RemoveIf(colPhotos,', t)

    write("scrAudit.pa.yaml", t)
    after = count(t)
    print(f"scrAudit: counts={ncnt} deletes={ndel} refs {before} -> {after}; colAuditPhotos left={t.count('colAuditPhotos')}")


# ---------------- scrSummary ----------------
def upsert_block(code):
    g = GRP[code]
    lst, label = LIST[g], LABEL[code]
    ind = " " * 30
    b = []
    b.append(f'{ind}With({{ex: LookUp({lst}, Row_Key = varAuditKey & "|{code}")}},')
    b.append(f'{ind}    If(CountRows(Filter(colPhotos, key = "{code}")) > 0,')
    b.append(f'{ind}        Patch({lst}, If(IsBlank(ex), Defaults({lst}), ex),')
    b.append(f'{ind}            {{')
    b.append(f'{ind}                Title: varAuditKey & " | {label}",')
    b.append(f'{ind}                Audit_ID: varAuditKey,')
    b.append(f'{ind}                Failure_Code: "{code}",')
    b.append(f'{ind}                Failure_Label: "{label}",')
    b.append(f'{ind}                Row_Key: varAuditKey & "|{code}",')
    b.append(f'{ind}                Customer: varSavedCustomer,')
    b.append(f'{ind}                Audit_Date: varSavedDate,')
    b.append(f'{ind}                Attachments: ForAll(Filter(colPhotos, key = "{code}") As p,')
    b.append(f'{ind}                    {{Name: "{code}_" & Text(p.index) & ".jpg", Value: p.photo}})')
    b.append(f'{ind}            }}')
    b.append(f'{ind}        ),')
    b.append(f'{ind}        If(!IsBlank(ex), Remove({lst}, ex))')
    b.append(f'{ind}    )')
    b.append(f'{ind});')
    return "\n".join(b)


def do_summary():
    t = read("scrSummary.pa.yaml")
    before = count(t)
    # Replace the entire flow-upload region between "IsEmpty(Errors..)," and "Clear(localAuditQueue);"
    region = re.compile(
        r'(IsEmpty\(Errors\(Calibrate_Audit_Data\)\),\n)(.*?)(\n {30}Clear\(localAuditQueue\);)',
        re.DOTALL)
    blocks = "\n".join(upsert_block(c) for c, _, _ in CODES)
    m = region.search(t)
    assert m, "scrSummary submit region not found"
    assert "Calibrate_Audit_App_Photos.Run" in m.group(2), "region missing flow blocks"
    t = t[:m.start(2)] + blocks + t[m.end(2):]

    # Remaining display conditions: !IsBlank(LookUp(doclib, ... varAuditKey & "_CODE_N.png"))
    def cond_repl(m):
        code, n = m.group("code"), m.group("n")
        return (f'(CountRows(LookUp({LIST[GRP[code]]}, Row_Key = varAuditKey & "|{code}").Attachments) >= {n})')
    cond_pat = re.compile(
        r'!IsBlank\(LookUp\(Calibrate_Audit_Photos, \'File name with extension\' = varAuditKey & "_'
        r'(?P<code>' + CODE_ALT + r')_(?P<n>\d+)\.png"\)\)')
    t, nc = cond_pat.subn(cond_repl, t)

    # Preview image fallback: Coalesce(colPhotos.photo, doclib.Thumbnail.Large) -> list attachment
    def img_repl(m):
        code, n = m.group("code"), m.group("n")
        return (f'Index(LookUp({LIST[GRP[code]]}, Row_Key = varAuditKey & "|{code}").Attachments, {n}).Value')
    img_pat = re.compile(
        r'LookUp\(Calibrate_Audit_Photos, \'File name with extension\' = varAuditKey & "_'
        r'(?P<code>' + CODE_ALT + r')_(?P<n>\d+)\.png"\)\.Thumbnail\.Large')
    t, ni = img_pat.subn(img_repl, t)

    write("scrSummary.pa.yaml", t)
    after = count(t)
    print(f"scrSummary: conds={nc} images={ni} refs {before} -> {after}")


if __name__ == "__main__":
    do_detail()
    do_audit()
    do_summary()
    print("photo rewire done")
