#!/usr/bin/env python3
"""Task 1 save fix + Task 4 Audit Desc.
- scrCustomer & scrMachine: resolve the audit row by varAuditSPID, else by Title, create only if
  neither exists, always write Title, capture the id back into varAuditSPID. Save order no longer
  matters and always hits exactly one row.
- scrCustomer: set varSavedCustomer / varSavedDate (used by scrSummary failure-row upserts) and
  add a labelled multi-line txtAuditDesc, writing 'Audit Desc' to varCustomerRecord."""
import re, os

SRC = os.path.join(os.path.dirname(__file__), "..", "src", "Src")


def read(n):
    with open(os.path.join(SRC, n), "r", newline="") as f:
        return f.read()


def write(n, t):
    assert t.count("\r") == 8, f"unexpected CR count {t.count(chr(13))}"
    with open(os.path.join(SRC, n), "w", newline="") as f:
        f.write(t)


def subn_assert(pat, repl, text, n, flags=0):
    # Only the first (live) save block is real; the second is commented-out dead code.
    out, c = re.subn(pat, repl, text, count=1, flags=flags)
    assert c == n, f"expected {n} replacements, got {c} for /{pat[:60]}.../"
    return out


# ---------------- scrCustomer ----------------
def do_customer():
    t = read("scrCustomer.pa.yaml")

    # 1) add 'Audit Desc' to varCustomerRecord (both save blocks)
    t = subn_assert(
        r"(Audit_Type_Detail:(\s+)txtAuditTypeDetail\.Text,\n)(\s*)",
        r"\1\3'Audit Desc':            txtAuditDesc.Text,\n\3",
        t, 1)

    # 2) replace the connected-branch resolution with id-or-title resolver
    resolver_old = re.compile(
        r"If\(\s*IsBlank\(varAuditSPID\) && !varEditMode,\s*"
        r"Set\(varAuditSPID,\s*"
        r"Patch\(Calibrate_Audit_Data, Defaults\(Calibrate_Audit_Data\), varCustomerRecord\)\.ID\s*"
        r"\),\s*"
        r"Patch\(Calibrate_Audit_Data,\s*"
        r"LookUp\(Calibrate_Audit_Data, ID = If\(varEditMode, varSelectedAudit\.ID, varAuditSPID\)\),\s*"
        r"varCustomerRecord\s*\)\s*\);")
    resolver_new = (
        "With({_byId: LookUp(Calibrate_Audit_Data, ID = varAuditSPID)},\n"
        "                                  With({_row: If(!IsBlank(_byId), _byId, LookUp(Calibrate_Audit_Data, Title = varAuditKey))},\n"
        "                                      Set(varAuditSPID,\n"
        "                                          Patch(Calibrate_Audit_Data, If(IsBlank(_row), Defaults(Calibrate_Audit_Data), _row), varCustomerRecord).ID\n"
        "                                      )\n"
        "                                  )\n"
        "                              );\n"
        "                              Set(varSavedCustomer, varCustomerRecord.Customer);\n"
        "                              Set(varSavedDate, varCustomerRecord.Audit_Date);")
    t = subn_assert(resolver_old, resolver_new, t, 1)

    # 3) offline branch: also stamp the saved customer/date
    t = subn_assert(
        r'(SaveData\(colCustomerRecordCache, "CustomerRecordCache"\);\n)(\s*)(Notify\("No connection)',
        r'\1\2Set(varSavedCustomer, varCustomerRecord.Customer);\n\2Set(varSavedDate, varCustomerRecord.Audit_Date);\n\2\3',
        t, 1)

    # 4) add the Audit Desc data card just before crdProtein
    card = (
        "                        - crdAuditDesc:\n"
        "                            Control: TypedDataCard@1.0.7\n"
        "                            Variant: TextualEdit\n"
        "                            Properties:\n"
        "                              BorderColor: =RGBA(245, 245, 245, 1)\n"
        '                              DataField: ="Audit Desc"\n'
        '                              Default: =""\n'
        '                              DisplayName: ="Audit Description"\n'
        "                              MaxLength: =4000\n"
        "                              Required: =false\n"
        "                              Update: =txtAuditDesc.Text\n"
        "                              Visible: =true\n"
        "                              Width: =Parent.Width\n"
        "                              X: =0\n"
        "                              Y: =3\n"
        "                            Children:\n"
        "                              - lblAuditDesc:\n"
        "                                  Control: Text@0.0.51\n"
        "                                  Properties:\n"
        "                                    Height: =22\n"
        '                                    Text: ="Audit Description"\n'
        "                                    Weight: ='TextCanvas.Weight'.Semibold\n"
        "                                    Width: =Parent.Width - 48\n"
        "                                    Wrap: =false\n"
        "                                    X: =24\n"
        "                                    Y: =10\n"
        "                              - txtAuditDesc:\n"
        "                                  Control: ModernTextInput@1.0.0\n"
        "                                  Properties:\n"
        '                                    AccessibleLabel: ="Audit Description"\n'
        "                                    Default: =If(varEditMode, varSelectedAudit.'Audit Desc', \"\")\n"
        "                                    DisplayMode: =Parent.DisplayMode\n"
        '                                    FontWeight: =""\n'
        "                                    Height: =96\n"
        "                                    MaxLength: =-1\n"
        '                                    Placeholder: ="Describe the audit..."\n'
        "                                    Required: =false\n"
        "                                    Size: =0\n"
        "                                    TriggerOutput: =TriggerOutput.FocusOut\n"
        "                                    Type: =TextInputType.Multiline\n"
        "                                    Width: =Parent.Width - 48\n"
        "                                    X: =24\n"
        "                                    Y: =lblAuditDesc.Y + lblAuditDesc.Height + 4\n")
    t = subn_assert(r"(                        - crdProtein:\n)", card + r"\1", t, 1)

    write("scrCustomer.pa.yaml", t)
    print("scrCustomer: save fix + Audit Desc applied")


# ---------------- scrMachine ----------------
def do_machine():
    t = read("scrMachine.pa.yaml")

    # opener: wrap Patch with id-or-title resolver and always write Title
    opener_old = re.compile(
        r"Patch\(Calibrate_Audit_Data,\s*"
        r"LookUp\(Calibrate_Audit_Data, ID = If\(varEditMode, varSelectedAudit\.ID, varAuditSPID\)\),\s*\{")
    opener_new = (
        "Set(varAuditSPID,\n"
        "                                  With({_byId: LookUp(Calibrate_Audit_Data, ID = varAuditSPID)},\n"
        "                                  With({_row: If(!IsBlank(_byId), _byId, LookUp(Calibrate_Audit_Data, Title = varAuditKey))},\n"
        "                                  Patch(Calibrate_Audit_Data,\n"
        "                                      If(IsBlank(_row), Defaults(Calibrate_Audit_Data), _row),\n"
        "                                  {\n"
        "                                      Title: varAuditKey,")
    t = subn_assert(opener_old, opener_new, t, 1)

    # closer: close record, Patch, two With, Set, then capture .ID
    closer_old = re.compile(
        r"MS_General_Comments:(\s+)txtGeneralComments\.Text\n(\s*)\}\n(\s*)\);")
    closer_new = (
        r"MS_General_Comments:\1txtGeneralComments.Text\n\2}\n"
        "                                  )\n"
        "                                  )\n"
        "                                  ).ID\n"
        "                                  );")
    t = subn_assert(closer_old, closer_new, t, 1)

    write("scrMachine.pa.yaml", t)
    print("scrMachine: save fix applied")


if __name__ == "__main__":
    do_customer()
    do_machine()
    print("save fix done")
