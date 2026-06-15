#!/usr/bin/env python3
"""Step 2 of the attachments rework: add an edit-mode "Previously Saved Photos"
section to scrAudit using the only context where SharePoint exposes attachments —
an outer gallery row (ThisItem.Attachments) with a nested gallery (ThisItem.Value).

Inserted as a child of MainContainer_Audit, immediately after frmAudit, so it flows
below the input cards in the same scroll region. Indentation (spaces):
  section dash 18 | keys 22 | props 24 | child dash 24 | child keys 28 | child props 30
  | template-child dash 30 | keys 34 | props 36 | img dash 36 | keys 40 | props 42
"""
import os, re

SRC = os.path.join(os.path.dirname(__file__), "..", "src", "Src", "scrAudit.pa.yaml")
LISTS = [
    ("Machine", "Audit_Machine_Failures"),
    ("Operator", "Audit_Operator_Failures"),
    ("Bag", "Audit_Bag_Failures"),
]


def outer_gallery(name, ds):
    g = f"galSaved{name}"
    lbl = f"lblSaved{name}Type"
    ng = f"galSaved{name}Photos"
    img = f"imgSaved{name}"
    flt = f"Filter({ds}, Audit_ID = varSelectedAudit.Title)"
    L = []
    a = " " * 24   # this gallery is a child of the section -> dash 24
    k = " " * 28   # keys
    p = " " * 30   # props
    td = " " * 30  # template child dash
    tk = " " * 34
    tp = " " * 36
    id_ = " " * 36 # image dash
    ik = " " * 40
    ip = " " * 42
    L.append(f"{a}- {g}:")
    L.append(f"{k}Control: Gallery@2.15.0")
    L.append(f"{k}Layout: Vertical")
    L.append(f"{k}Variant: BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0")
    L.append(f"{k}Properties:")
    L.append(f"{p}BorderColor: =RGBA(245, 245, 245, 1)")
    L.append(f"{p}Fill: =RGBA(255, 255, 255, 1)")
    L.append(f"{p}FillPortions: =0")
    L.append(f"{p}Height: =Max(CountRows({flt}), 0) * Self.TemplateSize")
    L.append(f"{p}Items: ={flt}")
    L.append(f"{p}LayoutMinHeight: =16")
    L.append(f"{p}LayoutMinWidth: =16")
    L.append(f"{p}TemplateSize: =188")
    L.append(f"{p}Visible: =varEditMode")
    L.append(f"{p}Width: =Parent.Width")
    L.append(f"{k}Children:")
    # row label
    L.append(f"{td}- {lbl}:")
    L.append(f"{tk}Control: Label@2.5.1")
    L.append(f"{tk}Properties:")
    L.append(f"{tp}Color: =cNavy")
    L.append(f"{tp}Font: =gFont")
    L.append(f"{tp}FontWeight: =FontWeight.Semibold")
    L.append(f"{tp}Height: =26")
    L.append(f"{tp}OnSelect: =Select(Parent)")
    L.append(f"{tp}PaddingLeft: =8")
    L.append(f"{tp}Size: =14")
    L.append(f"{tp}Text: =ThisItem.Failure_Label")
    L.append(f"{tp}Width: =Parent.TemplateWidth - 16")
    L.append(f"{tp}X: =8")
    L.append(f"{tp}Y: =6")
    # nested horizontal gallery over the row's attachments
    L.append(f"{td}- {ng}:")
    L.append(f"{tk}Control: Gallery@2.15.0")
    L.append(f"{tk}Layout: Horizontal")
    L.append(f"{tk}Variant: BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0")
    L.append(f"{tk}Properties:")
    L.append(f"{tp}Fill: =RGBA(255, 255, 255, 1)")
    L.append(f"{tp}Height: =150")
    L.append(f"{tp}Items: =ThisItem.Attachments")
    L.append(f"{tp}LayoutMinHeight: =16")
    L.append(f"{tp}LayoutMinWidth: =16")
    L.append(f"{tp}TemplateSize: =150")
    L.append(f"{tp}Width: =Parent.TemplateWidth - 16")
    L.append(f"{tp}X: =8")
    L.append(f"{tp}Y: ={lbl}.Y + {lbl}.Height + 4")
    L.append(f"{tk}Children:")
    L.append(f"{id_}- {img}:")
    L.append(f"{ik}Control: Image@2.2.3")
    L.append(f"{ik}Properties:")
    L.append(f"{ip}Height: =Parent.TemplateHeight - 12")
    L.append(f"{ip}Image: =ThisItem.Value")
    L.append(f"{ip}ImagePosition: =ImagePosition.Fit")
    L.append(f"{ip}OnSelect: =Select(Parent)")
    L.append(f"{ip}Width: =Parent.TemplateWidth - 12")
    L.append(f"{ip}X: =6")
    L.append(f"{ip}Y: =6")
    return L


def build_section():
    d = " " * 18   # section dash
    k = " " * 22
    p = " " * 24
    cd = " " * 24  # section children dash (galleries + header label)
    ck = " " * 28
    cp = " " * 30
    L = []
    L.append(f"{d}- SavedPhotosSection_Audit:")
    L.append(f"{k}Control: GroupContainer@1.5.0")
    L.append(f"{k}Variant: AutoLayout")
    L.append(f"{k}Properties:")
    L.append(f"{p}Fill: =RGBA(255, 255, 255, 1)")
    L.append(f"{p}FillPortions: =0")
    L.append(f"{p}LayoutAlignItems: =LayoutAlignItems.Stretch")
    L.append(f"{p}LayoutDirection: =LayoutDirection.Vertical")
    L.append(f"{p}LayoutGap: =8")
    L.append(f"{p}LayoutMinHeight: =16")
    L.append(f"{p}LayoutMinWidth: =16")
    L.append(f"{p}PaddingBottom: =8")
    L.append(f"{p}PaddingLeft: =8")
    L.append(f"{p}PaddingRight: =8")
    L.append(f"{p}PaddingTop: =8")
    L.append(f"{p}RadiusBottomLeft: =8")
    L.append(f"{p}RadiusBottomRight: =8")
    L.append(f"{p}RadiusTopLeft: =8")
    L.append(f"{p}RadiusTopRight: =8")
    L.append(f"{p}Visible: =varEditMode")
    L.append(f"{k}Children:")
    # section header label
    L.append(f"{cd}- lblSavedPhotosHeader_Audit:")
    L.append(f"{ck}Control: Text@0.0.51")
    L.append(f"{ck}Properties:")
    L.append(f"{cp}Align: =\"\"")
    L.append(f"{cp}FillPortions: =0")
    L.append(f"{cp}Font: =gFont")
    L.append(f"{cp}FontColor: =cNavy")
    L.append(f"{cp}Height: =32")
    L.append(f"{cp}Size: =16")
    L.append(f"{cp}Text: =\"Previously Saved Photos\"")
    L.append(f"{cp}VerticalAlign: =\"Middle\"")
    L.append(f"{cp}Weight: =\"Semibold\"")
    L.append(f"{cp}Width: =Parent.Width - 16")
    for name, ds in LISTS:
        L.extend(outer_gallery(name, ds))
    return [ln + "\n" for ln in L]


def main():
    with open(SRC, "r", newline="") as f:
        lines = f.readlines()
    if any("SavedPhotosSection_Audit" in ln for ln in lines):
        raise SystemExit("section already present; aborting")
    # insert before the FooterContainer (sibling of MainContainer), but at MainContainer
    # child indent (18) so it lands inside MainContainer_Audit, after frmAudit.
    foot = next(i for i, ln in enumerate(lines)
                if ln.rstrip("\n") == " " * 12 + "- FooterContainer_Audit:")
    block = build_section()
    lines[foot:foot] = block
    with open(SRC, "w", newline="") as f:
        f.writelines(lines)
    print(f"inserted SavedPhotosSection ({len(block)} lines) before FooterContainer at line {foot+1}")


if __name__ == "__main__":
    main()
