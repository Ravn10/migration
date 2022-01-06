import frappe

def pre_process(doc):
    frappe.msgprint("Hi in preprocess")
    doc['data']['Compnay']=""
    doc['data']['compnay']=""
    if doc.item_group == "WinStator-C":
        return json.loads(doc['data'])
    else:
        pass

