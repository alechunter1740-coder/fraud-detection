#!/usr/bin/env python3
"""scrDetail: the read-only photo view used 23 manual cards that read SharePoint
.Attachments via LookUp on a collection - illegal outside a gallery/form row.

Replace those cards with three gallery sections (one per failure list). Outer
gallery Items = Filter(Audit_*_Failures, Audit_ID = varSelectedAudit.Title)
(delegable equality); height uses Self.AllItemsCount (no CountRows -> no
delegation warning). Nested gallery over ThisItem.Attachments renders each
ThisItem.Value; tapping a photo opens the existing lightbox overlay.

Also drops the now-unused ClearCollect(col*PhotosDetail) lines from OnVisible.
"""
import os

SRC = os.path.join(os.path.dirname(__file__), "..", "src", "Src", "scrDetail.pa.yaml")
LISTS = [
    ("Machine", "Audit_Machine_Failures"),
    ("Operator", "Audit_Operator_Failures"),
    ("Bag", "Audit_Bag_Failures"),
]


def outer_gallery(name, ds):
    g, lbl, ng, img = f"galDetail{name}", f"lblDetail{name}Type", f"galDetail{name}Photos", f"imgDetail{name}"
    flt = f"Filter({ds}, Audit_ID = varSelectedAudit.Title)"
    a, k, p = " " * 24, " " * 28, " " * 30
    td, tk, tp = " " * 30, " " * 34, " " * 36
    id_, ik, ip = " " * 36, " " * 40, " " * 42
    L = [
        f"{a}- {g}:",
        f"{k}Control: Gallery@2.15.0",
        f"{k}Variant: BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0",
        f"{k}Properties:",
        f"{p}BorderColor: =RGBA(245, 245, 245, 1)",
        f"{p}Fill: =RGBA(255, 255, 255, 1)",
        f"{p}FillPortions: =0",
        f"{p}Height: =Self.AllItemsCount * Self.TemplateSize",
        f"{p}Items: ={flt}",
        f"{p}LayoutMinHeight: =16",
        f"{p}LayoutMinWidth: =16",
        f"{p}TemplateSize: =220",
        f"{p}Width: =Parent.Width",
        f"{k}Children:",
        f"{td}- {lbl}:",
        f"{tk}Control: Label@2.5.1",
        f"{tk}Properties:",
        f"{tp}Color: =cNavy",
        f"{tp}Font: =gFont",
        f"{tp}FontWeight: =FontWeight.Semibold",
        f"{tp}Height: =26",
        f"{tp}OnSelect: =Select(Parent)",
        f"{tp}PaddingLeft: =8",
        f"{tp}Size: =14",
        f"{tp}Text: =ThisItem.Failure_Label",
        f"{tp}Width: =Parent.TemplateWidth - 16",
        f"{tp}X: =8",
        f"{tp}Y: =6",
        f"{td}- {ng}:",
        f"{tk}Control: Gallery@2.15.0",
        f"{tk}Variant: BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0",
        f"{tk}Properties:",
        f"{tp}Fill: =RGBA(255, 255, 255, 1)",
        f"{tp}Height: =184",
        f"{tp}Items: =ThisItem.Attachments",
        f"{tp}LayoutMinHeight: =16",
        f"{tp}LayoutMinWidth: =16",
        f"{tp}TemplateSize: =92",
        f"{tp}Width: =Parent.TemplateWidth - 16",
        f"{tp}WrapCount: =3",
        f"{tp}X: =8",
        f"{tp}Y: ={lbl}.Y + {lbl}.Height + 4",
        f"{tk}Children:",
        f"{id_}- {img}:",
        f"{ik}Control: Image@2.2.3",
        f"{ik}Properties:",
        f"{ip}Height: =Parent.TemplateHeight - 8",
        f"{ip}Image: =ThisItem.Value",
        f"{ip}ImagePosition: =ImagePosition.Fit",
        f"{ip}OnSelect: =Set(varLightboxImage, ThisItem.Value); Set(varShowLightbox, true)",
        f"{ip}Width: =Parent.TemplateWidth - 8",
        f"{ip}X: =4",
        f"{ip}Y: =4",
    ]
    return L


def build_section():
    d, k, p, cd, ck, cp = " " * 18, " " * 22, " " * 24, " " * 24, " " * 28, " " * 30
    L = [
        f"{d}- PhotosSection_Detail:",
        f"{k}Control: GroupContainer@1.5.0",
        f"{k}Variant: AutoLayout",
        f"{k}Properties:",
        f"{p}Fill: =RGBA(255, 255, 255, 1)",
        f"{p}FillPortions: =0",
        f"{p}LayoutAlignItems: =LayoutAlignItems.Stretch",
        f"{p}LayoutDirection: =LayoutDirection.Vertical",
        f"{p}LayoutGap: =8",
        f"{p}LayoutMinHeight: =16",
        f"{p}LayoutMinWidth: =16",
        f"{p}PaddingBottom: =8",
        f"{p}PaddingLeft: =8",
        f"{p}PaddingRight: =8",
        f"{p}PaddingTop: =8",
        f"{p}RadiusBottomLeft: =8",
        f"{p}RadiusBottomRight: =8",
        f"{p}RadiusTopLeft: =8",
        f"{p}RadiusTopRight: =8",
        f"{k}Children:",
        f"{cd}- lblPhotosHeader_Detail:",
        f"{ck}Control: Text@0.0.51",
        f"{ck}Properties:",
        f'{cp}Align: =""',
        f"{cp}FillPortions: =0",
        f"{cp}Font: =gFont",
        f"{cp}FontColor: =cNavy",
        f"{cp}Height: =32",
        f"{cp}Size: =16",
        f'{cp}Text: ="Photos"',
        f'{cp}VerticalAlign: ="Middle"',
        f'{cp}Weight: ="Semibold"',
        f"{cp}Width: =Parent.Width - 16",
    ]
    for name, ds in LISTS:
        L.extend(outer_gallery(name, ds))
    return [ln + "\n" for ln in L]


def main():
    with open(SRC, "r", newline="") as f:
        text = f.read()
    cr = text.count("\r")

    # 1) OnVisible: drop the three unused ClearCollect(col*PhotosDetail) lines
    old_ov = (
        "        =Set(varAuditTitle, varSelectedAudit.Title);\n"
        "        ClearCollect(colMachinePhotosDetail,  Filter(Audit_Machine_Failures,  Audit_ID = varSelectedAudit.Title));\n"
        "        ClearCollect(colOperatorPhotosDetail, Filter(Audit_Operator_Failures, Audit_ID = varSelectedAudit.Title));\n"
        "        ClearCollect(colBagPhotosDetail,      Filter(Audit_Bag_Failures,      Audit_ID = varSelectedAudit.Title))"
    )
    assert old_ov in text, "OnVisible block not found"
    text = text.replace(old_ov, "        =Set(varAuditTitle, varSelectedAudit.Title)")

    lines = text.splitlines(keepends=True)

    # 2) delete the 23 photo cards: from CardDetail_MFLowVac up to (not incl) CardDetail_Findings
    start = next(i for i, ln in enumerate(lines)
                 if ln.rstrip("\n") == " " * 24 + "- CardDetail_MFLowVac:")
    end = next(i for i, ln in enumerate(lines)
               if ln.rstrip("\n") == " " * 24 + "- CardDetail_Findings:")
    del lines[start:end]

    # 3) insert gallery section before FooterContainer_Detail (sibling of frmDetail, dash 18)
    foot = next(i for i, ln in enumerate(lines)
                if ln.rstrip("\n") == " " * 12 + "- FooterContainer_Detail:")
    lines[foot:foot] = build_section()

    out = "".join(lines)
    assert out.count(".Attachments") == 3, out.count(".Attachments")  # only nested gallery Items
    assert out.count("col") == out.count("col"), ""  # no-op guard
    assert "colMachinePhotosDetail" not in out and "colBagPhotosDetail" not in out
    assert out.count("\r") == cr, (out.count("\r"), cr)
    with open(SRC, "w", newline="") as f:
        f.write(out)
    print(f"scrDetail: deleted photo cards [{start+1}..{end}], inserted galleries; "
          f".Attachments now={out.count('.Attachments')} (3 nested Items), "
          f"Detail collections removed={'colMachinePhotosDetail' not in out}")


if __name__ == "__main__":
    main()
