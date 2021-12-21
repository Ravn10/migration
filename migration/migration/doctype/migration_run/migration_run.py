# Copyright (c) 2021, Firsterp and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import date_diff, add_months, today, getdate, add_days, flt, get_last_day, get_first_day, cint, get_link_to_form, rounded, add_to_date, get_first_day_of_week
from frappe import _ , scrub
from six import iteritems
from erpnext.accounts.utils import get_fiscal_year
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue

Months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


class MigrationRun(Document):
	def after_insert(self):
		if self.range and self.from_date and self.to_date and not self.is_new():
			from dateutil.relativedelta import relativedelta, MO
			from_date, to_date = getdate(self.from_date), getdate(self.to_date)

			increment = {
				'Monthly': 1,
				'Quarterly': 3,
				'Half-Yearly': 6,
				'Yearly': 12
			}.get(self.range, 1)

			if self.range in ['Monthly', 'Quarterly']:
				from_date = from_date.replace(day=1)
			elif self.range == 'Yearly':
				from_date = get_fiscal_year(from_date)[1]
			else:
				from_date = from_date + relativedelta(from_date, weekday=MO(-1))

			self.periodic_daterange = []
			for dummy in range(1, 53):
				if self.range == 'Weekly':
					period_end_date = add_days(from_date, 6)
				else:
					period_end_date = add_to_date(from_date, months=increment, days=-1)

				if period_end_date > to_date:
					period_end_date = to_date

				self.periodic_daterange.append(period_end_date)

				from_date = add_days(period_end_date, 1)
				if period_end_date == to_date:
					break
			
			self.periods = []
			for end_date in self.periodic_daterange:
				if self.range == 'Monthly':
					period_from_date = get_first_day(end_date)
				elif self.range == "Weekly":
					period_from_date = get_first_day_of_week(end_date)
				else:
					period_from_date = end_date
				self.periods.append({
					'from_date':period_from_date,
					'to_date':end_date
				})
			
			frappe.msgprint("Calling Enque..")
			self.create_migration_logs()
			# frappe.enqueue('migration.migration.doctype.migration_run.migration_run.create_migration_logs', periodic_daterange=self.periods,migration_run=self.name, queue='short')
	
	def create_migration_logs(self):
		frappe.publish_realtime('msgprint', 'Starting long job...')
		frappe.msgprint("Enqueing..")
		for count,date in enumerate(self.periods):
			frappe.publish_progress((count+1)*100/len(self.periods), title = _("Creating Migration Run Doc..."))
			migration_run_log = frappe.new_doc("Migration Run Log")
			migration_run_log.from_date = date['from_date']
			migration_run_log.to_date = date['to_date']
			# migration_run_log.migration_run = self.name
			migration_run_log.insert()
		frappe.publish_realtime('msgprint', 'Ending long job...')
		frappe.msgprint("Calling Enque..Ended")