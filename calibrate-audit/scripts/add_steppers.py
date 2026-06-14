#!/usr/bin/env python3
"""Add - / + steppers to every numeric count input on scrAudit while keeping the
typed entry, the live % label, and responsive (Parent.Width-relative) sizing.

Layout per count row:  [ - ][  text input  ][ + ][  % label  ]
Total Packages row:    [ - ][  text input  ][ + ]   (no % label)

The 23 failure inputs all anchor their X/Width to txtMFLowVac, so geometry is set
once on that anchor; every row gets its own buttons wired to its own var, and the
input Default is made var-driven (OnVisible already seeds the vars from the record
in edit mode, so dropping the Parent.Default branch is safe and lets Reset() reflect
stepper changes)."""
import os, re, sys

SRC = os.path.join(os.path.dirname(__file__), "..", "src", "Src", "scrAudit.pa.yaml")

# (control, var, is_total) ; suffix is control[3:], pct label is lblPct_<suffix>
TOTAL = ("txtTotalPackages", "varTotalPackages")
COUNTS = [
    ("txtMFLowVac", "varMF_LowVac"),
    ("txtMFColdSeal", "varMF_ColdSeal"),
    ("txtMFEdgeTear", "varMF_EdgeTear"),
    ("txtMFPullBack", "varMF_PullBack"),
    ("txtMFBurntSeals", "varMF_BurntSeals"),
    ("txtMFOther", "varMF_Other"),
    ("txtOFMeatInSeals", "varOF_MeatInSeals"),
    ("txtOFProdReject", "varOF_ProdReject"),
    ("txtOFMultiplePleat", "varOF_MultiplePleat"),
    ("txtOFBagTear", "varOF_BagTear"),
    ("txtOFIncompleteSeal", "varOF_IncompleteSeal"),
    ("txtOFUncoveredBone", "varOF_UncoveredBone"),
    ("txtOFPullBack", "varOF_PullBack"),
    ("txtOFTwoPerPlaten", "varOF_TwoPerPlaten"),
    ("txtOFOther", "varOF_Other"),
    ("txtBRFHoleBeforeShrink", "varBRF_HoleBeforeShrink"),
    ("txtBRFHoleAfterShrink", "varBRF_HoleAfterShrink"),
    ("txtBRFCoveredBone", "varBRF_CoveredBone"),
    ("txtBRFSinglePleat", "varBRF_SinglePleat"),
    ("txtBRFEdgeTear", "varBRF_EdgeTear"),
    ("txtBRFFactorySeal", "varBRF_FactorySeal"),
    ("txtBRFHealBreak", "varBRF_HealBreak"),
    ("txtBRFOther", "varBRF_Other"),
]
ANCHOR = "txtMFLowVac"


def find_block(lines, name):
    """Return (start, end, dash_indent) for the control entry named `name`.
    Block runs from the '- name:' line up to (not including) the next line whose
    indent <= dash_indent."""
    pat = re.compile(r"^(\s*)- " + re.escape(name) + r":\s*$")
    start = dash = None
    for i, ln in enumerate(lines):
        m = pat.match(ln)
        if m:
            start, dash = i, len(m.group(1))
            break
    if start is None:
        raise SystemExit(f"control not found: {name}")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        s = lines[j]
        if s.strip() == "":
            continue
        if len(s) - len(s.lstrip(" ")) <= dash:
            end = j
            break
    return start, end, dash


def set_prop(lines, start, end, prop, value):
    """Replace the first `<indent>prop: =...` line within [start,end). `value`
    includes its leading '='. Preserves the trailing newline."""
    pr = re.compile(r"^(\s*)" + re.escape(prop) + r": =.*?(\r?\n)$")
    for i in range(start, end):
        m = pr.match(lines[i])
        if m:
            lines[i] = f"{m.group(1)}{prop}: {value}{m.group(2)}"
            return
    raise SystemExit(f"prop {prop} not found in block at line {start+1}")


def button(dash, name, var, txt, kind, minus_x):
    p = " " * (dash + 4)      # Control:/Properties:
    q = " " * (dash + 6)      # property lines
    d = " " * dash
    if kind == "minus":
        disp = f"=If({var} <= 0, DisplayMode.Disabled, Parent.DisplayMode)"
        onsel = f"=Set({var}, Max({var} - 1, 0)); Reset({txt})"
        text = '="-"'
        x = f"={minus_x}"
    else:
        disp = "=Parent.DisplayMode"
        onsel = f"=Set({var}, {var} + 1); Reset({txt})"
        text = '="+"'
        x = f"={txt}.X + {txt}.Width + 6"
    return "\n".join([
        f"{d}- {name}:",
        f"{p}Control: Classic/Button@2.2.0",
        f"{p}Properties:",
        f"{q}BorderColor: =cBlue",
        f"{q}BorderThickness: =1",
        f"{q}Color: =cBlue",
        f"{q}DisabledBorderColor: =RGBA(214, 214, 214, 1)",
        f"{q}DisabledColor: =RGBA(190, 190, 190, 1)",
        f"{q}DisabledFill: =RGBA(248, 248, 248, 1)",
        f"{q}DisplayMode: {disp}",
        f"{q}Fill: =RGBA(255, 255, 255, 1)",
        f"{q}Font: =gFont",
        f"{q}Height: ={txt}.Height",
        f"{q}HoverBorderColor: =cBlue",
        f"{q}HoverColor: =cWhite",
        f"{q}HoverFill: =cBlue",
        f"{q}OnSelect: {onsel}",
        f"{q}PressedBorderColor: =cBlue",
        f"{q}PressedColor: =cWhite",
        f"{q}PressedFill: =RGBA(0, 130, 180, 1)",
        f"{q}RadiusBottomLeft: =4",
        f"{q}RadiusBottomRight: =4",
        f"{q}RadiusTopLeft: =4",
        f"{q}RadiusTopRight: =4",
        f"{q}Size: =20",
        f"{q}Text: {text}",
        f"{q}Width: =40",
        f"{q}X: {x}",
        f"{q}Y: ={txt}.Y",
    ]) + "\n"


def process(txtname, var, is_total, lines):
    suffix = txtname[3:]
    minus_name = f"btnMinus_{suffix}"
    plus_name = f"btnPlus_{suffix}"
    minus_x = 24 if is_total else 36

    start, end, dash = find_block(lines, txtname)
    # var-driven Default so steppers (via Reset) and typing share one source of truth
    set_prop(lines, start, end, "Default", f'=If({var} = 0, "", Text({var}))')
    # geometry: total row + the anchor row carry literal X/Width; other count rows
    # inherit from the anchor, so leave them untouched.
    if is_total:
        set_prop(lines, start, end, "X", "=70")
        set_prop(lines, start, end, "Width", "=Parent.Width - 140")
    elif txtname == ANCHOR:
        set_prop(lines, start, end, "X", "=82")
        set_prop(lines, start, end, "Width", "=Parent.Width - 245")

    # recompute block end (Default replacement keeps line count, safe) and insert buttons
    start, end, dash = find_block(lines, txtname)
    blocks = button(dash, minus_name, var, txtname, "minus", minus_x) + \
             button(dash, plus_name, var, txtname, "plus", minus_x)
    lines[end:end] = blocks.splitlines(keepends=True)

    # repoint the % label to sit after the plus button (count rows only)
    if not is_total:
        ls, le, _ = find_block(lines, f"lblPct_{suffix}")
        set_prop(lines, ls, le, "X", f"={plus_name}.X + {plus_name}.Width + 6")


def main():
    with open(SRC, "r", newline="") as f:
        text = f.read()
    if "btnMinus_" in text:
        raise SystemExit("steppers already present; aborting to avoid double-insert")
    cr = text.count("\r")
    lines = text.splitlines(keepends=True)

    process(TOTAL[0], TOTAL[1], True, lines)
    for txtname, var in COUNTS:
        process(txtname, var, False, lines)

    out = "".join(lines)
    # sanity: 24 minus + 24 plus buttons, CR count unchanged
    assert out.count("- btnMinus_") == 24, out.count("- btnMinus_")
    assert out.count("- btnPlus_") == 24, out.count("- btnPlus_")
    assert out.count("\r") == cr, (out.count("\r"), cr)
    with open(SRC, "w", newline="") as f:
        f.write(out)
    print(f"steppers added: minus={out.count('- btnMinus_')} plus={out.count('- btnPlus_')} CR={out.count(chr(13))}")


if __name__ == "__main__":
    main()
