import frappe
from frappe.utils import date_diff, add_months, today, getdate, add_days, flt, get_last_day, get_first_day, cint, get_link_to_form, rounded

company = "Latteys Industries Limited - Group"
abbr = frappe.get_value("Company",company,'abbr')

transactions = [
 'Payment Entry',
 'Stock Reconciliation',
 'Sales Invoice',
 'Sales Order',
 'Payment Entry',
 'Journal Entry',
 'Purchase Order',
 'Purchase Invoice',
 'Purchase Receipt',
 'Delivery Note',
 'Stock Entry',
 'Work Order',
 'Job Card'
]
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# 10. Create Chart of Account with all accounts in other companies
# 11. Get all transactions for month of october
@frappe.whitelist()
def get_all_transaction_for_month(month):
    m = months.index(month)+1
    first_day = frappe.utils.datetime.date(2021,m,1)
    last_day = get_last_day(first_day)
    data = {}
    for transaction in transactions:
        if transaction in ('Sales Order','Purchase Order'):
            filters= {'transaction_date':['in',first_day.strftime('%Y-%m-%d'),last_day.strftime('%Y-%m-%d')],'docstatus':1}
        else:
            filters = {'posting_date':['in',first_day.strftime('%Y-%m-%d'),last_day.strftime('%Y-%m-%d')],'docstatus':1}
        data[transaction]=frappe.db.get_all(transaction,filters=filters,fields=['name','company'])
    return data
# 12. Identify internal transactions

# 13. Add respective branch and cost center in all transactions
@frappe.whitelist()
def create_transactions():
    transaction_data = get_all_transaction_for_month('Oct')
    for data in transaction_data:
        if data in ["Sales Invoice", "Purchase Invoice"]:
            for d in transaction_data[data]:
                create_invoice(data,d)

def get_cost_center(company):
    branch = frappe.get_value("Company",company,'branch')
    if branch:
        return frappe.get_value("Branch",branch,'cost_center')
    else:
        return ''

def validate_warehouse_cost_center(doc):
    data = {'warehouse':'','cost_center':''}
    if doc.get('warehouse'):
        if not frappe.db.exists("Warehouse",doc.get('warehouse')):
            data['warehouse'] = frappe.get_doc("Warehouse",{"name":doc.get('warehouse'),"company":company}).insert()
    if doc.get('cost_center'):
        if not frappe.db.exists("Cost Center",doc.get('cost_center')):
            data['cost_center'] = frappe.get_doc("Cost Center",{"name":doc.get('cost_center'),"company":company}).insert()
    return data
        

def create_invoice(dt,d):
    for voucher in d:
        dt_doc = frappe.copy_doc(frappe.get_doc(dt,d['name']))
        if dt=="Sales Invoice":
            if not dt_doc.get('customer').find('Latteys'):
                dt_doc.company = company
                dt_doc.cost_center = get_cost_center(d['company'])
                for row in dt_doc.items:
                    data = validate_warehouse_cost_center(row)
                    row.warehouse   = data['warehouse']
                    row.cost_center = data['cost_center']
                if dt_doc.get('tax_category'):
                    dt_doc.tax_category = ''
                dt_doc.taxes = []
                dt_doc.set_missing_values()
                dt_doc.set_missing_item_details()
                try:
                    dt_doc.insert()
                    frappe.msgprint(dt_doc.name)
                except Exception as e:
                    message = e
                    title = dt+ d['name']
                    frappe.log_error(title=title,message =message)
        elif dt == "Purchase Invoice":
            if not dt_doc.get('supplier').find('Latteys'):
                dt_doc.company = company
                dt_doc.cost_center = get_cost_center(d['company'])
                for row in dt_doc.items:
                    data = validate_warehouse_cost_center(row)
                    row.warehouse   = data['warehouse']
                    row.cost_center = data['cost_center']
                if dt_doc.get('tax_category'):
                    dt_doc.tax_category = ''
                dt_doc.taxes = []
                dt_doc.set_missing_values()
                dt_doc.set_missing_item_details()
                try:
                    dt_doc.insert()
                    frappe.msgprint(dt_doc.name)
                except Exception as e:
                    message = e
                    title = dt+ d['name']
                    frappe.log_error(title=title,message =message)



            
        
# 14. Replace all occurances of Latteys..-<branch> with one Lattys..
# 15. Map respective accounts
# 16. Replace warehouses