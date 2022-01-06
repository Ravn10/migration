# Copyright (c) 2021, Firsterp and contributors
# For license information, please see license.txt

import frappe, json, time
from frappe.model.document import Document
from datetime import datetime
from collections import OrderedDict

company = "Latteys Industries Limited - Group"
abbr = frappe.get_value("Company",company,'abbr')

transactions = ['Sales Invoice','Sales Order']
# [
#  'Payment Entry',
#  'Stock Reconciliation',
#  'Sales Invoice',
#  'Sales Order',
#  'Payment Entry',
#  'Journal Entry',
#  'Purchase Order',
#  'Purchase Invoice',
#  'Purchase Receipt',
#  'Delivery Note',
#  'Stock Entry',
#  'Work Order',
#  'Job Card'
# ]
VOUCHER_CHUNK_SIZE = 500

class MigrationRunLog(Document):
	# def before_insert(self):
	# 	frappe.msgprint("Before Insert" )

	# def validate(self):
	# 	frappe.msgprint("Validate" + self.name)
	@frappe.whitelist()
	def after_insert(self):
		frappe.msgprint("After Insert" + self.name)
		if frappe.db.exists(self.doctype, self.name):
			pass
		data = get_all_transaction(doctype=self.doctype,name=self.name,from_date=self.from_date,to_date=self.to_date)
		if data:
			self.set_status("Getting Transaction Data")
			self.transaction_data = json.dumps(data,indent=4,default=str)
			self.save()
			frappe.db.commit()
			time.sleep(10)
		# if not self.voucher:
			# create_vouchers(self.doctype,self.name,data)
		self.set_status("Creating Voucher Data")
		frappe.enqueue('migration.migration.doctype.migration_run_log.migration_run_log.create_vouchers',doctype=self.doctype,name=self.name,td=data)
		self.set_status("Importing Vouchers")
		frappe.enqueue('migration.migration.doctype.migration_run_log.migration_run_log.import_vouchers',doctype=self.doctype,name=self.name)
		self.set_status("Import Done")

	@frappe.whitelist()
	def import_vouchers(self):
		try:
			# Not Tested
			vouchers = json.loads(self.vouchers)

			# create ordered dic based on posting dates 
			voucher_list = json.loads(self.transaction_data)
			ordered_voucher_list = OrderedDict(sorted(voucher_list.items(), key = lambda x:datetime.strptime(x[0], '%d-%m-%Y')))

			total = len(vouchers)
			is_last = False
			self.set_status("Importing Vouchers")
			for index in range(0, total, VOUCHER_CHUNK_SIZE):
				if index + VOUCHER_CHUNK_SIZE >= total:
					is_last = True
				frappe.enqueue_doc(self.doctype, self.name, "_import_vouchers", queue="long", timeout=3600, start=index+1, total=total, is_last=is_last)

		except:
			pass
			# self.log()

		finally:
			self.set_status()

	def set_status(self, status=""):
		self.status = status
		self.save()

	def _import_vouchers(self, start, total, is_last=False):
		frappe.flags.in_migrate = True
		vouchers_file = frappe.get_doc("File", {"file_url": self.vouchers})
		vouchers = json.loads(vouchers_file.get_content())
		chunk = vouchers[start: start + VOUCHER_CHUNK_SIZE]

		for index, voucher in enumerate(chunk, start=start):
			try:
				voucher_doc = frappe.get_doc(voucher)
				voucher_doc.insert()
				# voucher_doc.submit()
				self.publish("Importing Vouchers", _("{} of {}").format(index, total), index, total)
				frappe.db.commit()
				frappe.rename_doc(voucher_doc.doctype,voucher_doc.name,voucher_doc.old_id,force=1,merge=0)
			except:
				frappe.db.rollback()
				self.log(voucher_doc)

		if is_last:
			self.status = ""
			self.is_day_book_data_imported = 1
			self.save()
			# frappe.db.set_value("Price List", "Tally Price List", "enabled", 0)
		frappe.flags.in_migrate = False
		self.set_status("Done")
	
@frappe.whitelist()
def create_vouchers(doctype,name,td):
	company = frappe.db.get_single_value("Migration Setting","company")
	vouchers = []
	if td:
		if isinstance(td,str):
			transaction_data = json.loads(td)
		elif isinstance(td,dict):
			transaction_data = td
			for voucher_type in transaction_data:
				for index,row in enumerate(transaction_data[voucher_type],start=1):
					frappe.publish_realtime('update_progress', {
						'progress': index,
						'total': len(transaction_data[voucher_type]),
						'message':row['name']
					})
					voucher = frappe.get_doc(voucher_type, row['name'])
					voucher_dict = voucher.as_dict(no_nulls=True)

					# update company in voucher
					voucher_dict['company'] = company

					# copy name in old_id field
					voucher_dict['old_id'] = voucher_dict['name']

					# find keys with cost_center
					cost_center_keys = list(get_keys('cost_center',voucher_dict))
					print("Cost Center keys")
					print(cost_center_keys)
					for key in cost_center_keys:
						if isinstance(voucher_dict.get(key),str):
							voucher_dict.key = validate_cost_center(voucher_dict.get(key))

					# find keys with warehouse
					warehouse_keys = list(get_keys('warehouse',voucher_dict))
					print("Warehouse keys")
					print(warehouse_keys)
					for key in warehouse_keys:
						if isinstance(voucher_dict.get(key),str):
							voucher_dict[key] = validate_warehouse(voucher_dict.get(key))
					
					# find keys with account
					account_keys = list(get_keys('account',voucher_dict))
					print("Accounts keys")
					print(account_keys)
					for key in account_keys:
						if isinstance(voucher_dict.get(key),str):
							voucher_dict.key = validate_account(voucher_dict.get(key))
					update_old_id_in_child_dict(voucher_dict)
					vouchers.append(voucher_dict)

	frappe.db.set_value(doctype,name,'vouchers',json.dumps(vouchers,indent=4,sort_keys=True, default=str))
	frappe.db.set_value(doctype,name,'total_vouchers',len(vouchers))
	frappe.db.set_value(doctype,name,'status',"Vouchers Created")


def validate_cost_center(cost_center):
	print("Validating Cost Center")
	if cost_center.split('-')[-1] == frappe.db.get_single_value("Migration Setting","abbr"):
		return cost_center
	new_cc = cost_center + ' - '+ frappe.db.get_single_value("Migration Setting","abbr")
	if frappe.db.exists("Cost Center",new_cc):
		return new_cc
	else:
		cc = frappe.new_doc("Cost Center")
		cc.cost_center_name = cost_center
		cc.company = frappe.db.get_single_value("Migration Setting","company")
		cc.parent_cost_center = frappe.db.get_single_value("Migration Setting","parent_cost_center")
		try:
			cc.insert()
			return cc.name
		except:
			frappe.db.rollback()
			traceback = frappe.get_traceback()
			title_=cost_center + "  Cost Center Insert ERROR"
			frappe.log_error(title = title_,message=traceback)

def validate_warehouse(warehouse):
	print("Validating Warehouse")
	print(warehouse)
	new_wh = warehouse.split('-')[0].strip() + ' - '+ frappe.db.get_single_value("Migration Setting","abbr")
	if frappe.db.exists("Warehouse",new_wh):
		return new_wh
	else:
		if '-' in warehouse:
			warehouse_doc = frappe.get_doc("Warehouse",warehouse)
			wh = frappe.copy_doc(warehouse_doc)
			wh.name = warehouse.split('-')[0]
			wh.company = frappe.db.get_single_value("Migration Setting","company")
			if wh.parent_warehouse:
				wh.parent_warehouse = validate_warehouse(wh.parent_warehouse)
			try:
				wh.insert()
				return wh.name
			except:
				frappe.db.rollback()
				traceback = frappe.get_traceback()
				frappe.log_error(title="Warehouse Insert ERROR",message=traceback)
		else:
			frappe.log_error(title="Warehouse ERROR {}".format(warehouse),message=warehouse)

def validate_account(account):
	print("Validating Account")
	print(account)
	# new_ac_ = account.split('-')
	# del new_ac_[-2:]
	new_ac = account.split('-')[0].strip() + ' - '+ frappe.db.get_single_value("Migration Setting","abbr")
	if frappe.db.exists("Account",new_ac):
		return new_ac
	else:
		if '-' in account:
			account_doc = frappe.get_doc("Account",account)
			ac = frappe.copy_doc(account_doc)
			ac.name = account.split('-')[0]
			ac.company = frappe.db.get_single_value("Migration Setting","company")
			if ac.parent_account:
				ac.parent_account = validate_account(ac.parent_account)
			try:
				ac.insert()
				return ac.name
			except:
				frappe.db.rollback()
				traceback = frappe.get_traceback()
				frappe.log_error(title="Account Insert ERROR",message=traceback)
		else:
			frappe.log_error(title="Account ERROR",message=account)
		

@frappe.whitelist()
def get_all_transaction(doctype,name,from_date,to_date):
	data = {}
	if isinstance(from_date,str):
		from_date_ = from_date
	else:
		from_date_ = from_date.strftime('%Y-%m-%d')
	if isinstance(to_date, str):
		to_date_ = to_date
	else:
		to_date_ = to_date.strftime('%Y-%m-%d')
	
	# debugging
	print("from Date : - {0} to date:- {1}".format(from_date_,to_date_))
	for transaction in transactions:
		fields = ['name','company']
		if transaction in ('Sales Order','Purchase Order'):
			filters = [
				['transaction_date','between', [ from_date_, to_date_]],
				['docstatus','=',1]
				]
			fields.append('transaction_date as date')
		elif transaction == "Work Order":
			filters = [
				['planned_start_date','between', [ from_date_, to_date_]],
				['docstatus','=',1]
				]
			fields.append('planned_start_date as date')
		else:
			filters = [
				['posting_date','between',[from_date_,to_date_]],
				['docstatus','=',1]
				]
			fields.append('posting_date as date')
		print("-----------------")
		print(transaction)
		print(filters)
		print(fields)
		print("-----------------")

		data[transaction]=frappe.db.get_all(transaction,filters=filters,fields=fields)
		print(data)

	return data
	# frappe.db.set_value(doctype,name,'transaction_data',json.dumps(data,indent=4,sort_keys=True, default=str))
	# create_vouchers(doctype=doctype,name=name,td=data)
	# frappe.enqueue('migration.migration.doctype.migration_run_log.migration_run_log.create_vouchers',doctype=doctype,name=name,td=data)


def get_keys(substring, dict):
	dictionary = dict.copy()
	for key, value in dictionary.items():
		# try is for handling Booleans
		try:
			if substring in key:
				if key.endswith(substring):
					yield key
			elif isinstance(key, dict):
				for result in get_keys(substring, key):
					if result.endswith(substring):
						yield result
			elif isinstance(key, list):
				for list_item in key:
					for result in get_keys(substring, list_item):
						if result.endswith(substring):
							yield result
		except:
			pass

def update_old_id_in_child_dict(dict):
	for key in dict:
		if isinstance(dict[key],list):
			for row in dict[key]:
				row['old_id'] = row['name']
			print(dict[key])