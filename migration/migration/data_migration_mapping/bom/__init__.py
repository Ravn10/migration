import frappe, json

def pre_process(doc):
    # frappe.msgprint("Hi in preprocess")
    # doc.company = ""
    print("\n\n\n\n\n\n\n\n\n\n")
    print("Preprocess")
    # print(doc.as_dict())
    print("\n")
    print(doc.item_group)
    print(type(doc))
    print("\n\n\n\n\n\n\n\n\n\n")
    return doc.as_dict()

def post_process(doc):
    print("\n\n\n\n\n\n\n\n\n\n")
    print("Post process")
    print(doc.as_dict())
    print("\n\n\n\n\n")
    print(doc.item_group)
    print(type(doc))
    print("\n\n\n\n\n\n\n\n\n\n")
