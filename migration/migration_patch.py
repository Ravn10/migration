import pandas as pd
from collections import OrderedDict
import frappe
# TODO
# 1. create a transaction doctype list
# 2. Get all transactions
# 3. Sort all transactios by their posting dates
# 4.  
Transaction_Type_List = [
    'Purchase Invoice',
    'Sales Invoice',
    'Stock Entry',
    'Delivery Note',
    'Purchase Receipt',
    'Sales Order',
    'Purchase Order',
    'Production Plan',
    'Material Request',
    'Work Order',
    'Job Card'
]

Months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def get_all_transactions(month):
    all_transactions = {}
    all_transactions_df_dict = {}
    all_transactions_clubbed_df = pd.DataFrame()

    # loop through list of doctypes to get docnames and posting dates
    for Transaction_Type in Transaction_Type_List:
        if Transaction_Type in ['Purchase Invoice','Sales Invoice','Stock Entry','Delivery Note','Purchase Receipt','Production Plan']:
            date_field = 'posting_date'
            filters=[['docstatus', 'between', '0 and 1'],['posting_date','between',(from_date, to_date)]]
        elif Transaction_Type in ['Sales Order','Purchase Order','Material Request']:
            date_field = 'transaction_date'
        transaction_list_ = frappe.get_all(Transaction_Type,filters=filters,fields=['name',date_field])
        transaction_list = [dict(x) for x in transaction_list_]
        all_transactions.setdefault(Transaction_Type, transaction_list)

    # create dataframes of list of doctypes to get docnames and posting dates
    for tx in all_transactions:
        all_transactions_df_dict[tx] = pd.DataFrame(all_transactions[tx])
        # update doctype column in dataframe
        all_transactions_df_dict[tx]['doctype'] = tx

    # club all dataframes into one
    all_transactions_clubbed_df = pd.concat(all_transactions_df_dict.values(), ignore_index=True)
    # merge dates in single column
    all_transactions_clubbed_df['dates'] = all_transactions_clubbed_df['posting_date']
    all_transactions_clubbed_df['dates'] = all_transactions_clubbed_df.dates.fillna(all_transactions_clubbed_df['transaction_date'])
    # sort by dates in ascending order
    all_transactions_clubbed_df.sort_values(by='dates',ascending=True)
    all_transactions_clubbed = all_transactions_clubbed_df.to_dict('records')
    all_transactions_clubbed_sorted = sorted(all_transactions_clubbed, key=lambda d: d['dates'],reverse=True)
    return all_transactions_clubbed_sorted

def create_voucher_data_frame():
    all_transactions_clubbed = get_all_transactions()
    all_transactions_data = []
    # create monthly chunks
    # create multiple documents for migration
    # create chunks in migration run doc
    # enque each chunk for submittion
    # create voucher
    # insert vouchers
    # rename 
    # submit
    for transaction in all_transactions_clubbed:
        all_transactions_data.append(dict(frappe.get_doc(transaction['doctype'],transaction['name']).as_dict))
