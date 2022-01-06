// Copyright (c) 2021, Firsterp and contributors
// For license information, please see license.txt

frappe.ui.form.on('Migration Run Log', {
	refresh: function(frm) {
		frappe.realtime.on('update_progress', (data) => {
			console.log(data)
			frm.dashboard.show_progress("Progress", (data.progress / data.total) * 100, data.message);
		});
	},
	refresh:function (frm, label, method){
		frm.add_custom_button(
			"After Insert",
			() => {
				frm.call({
					doc:cur_frm.doc,
					method: 'after_insert',
					freeze: true,
					freeze_message:"Getting Transactions"
				});
				frm.reload_doc();
			}
		);

		frm.add_custom_button(
			label,
			() => {
				frm.call({
					method: 'migration.migration.doctype.migration_run_log.migration_run_log.get_all_transaction',
					args:{
						'doctype':cur_frm.doc.doctype,
						'name':cur_frm.doc.name,
						'from_date':cur_frm.doc.from_date,
						'to_date':cur_frm.doc.to_date
					},
					freeze: true,
					freeze_message:"Getting Transactions"
				});
				frm.reload_doc();
			}
		);
		frm.add_custom_button(
			"Create Vouchers",
			() => {
				frm.call({
					method: 'migration.migration.doctype.migration_run_log.migration_run_log.create_vouchers',
					args:{
						'doctype':cur_frm.doc.doctype,
						'name':cur_frm.doc.name,
						'td':cur_frm.doc.transaction_data
					},
					freeze: true,
					
				});
				frm.reload_doc();
			}
		);
		frm.add_custom_button(
			"Import Vouchers",
			() => {
				frm.call({
					doc:cur_frm.doc,
					method: 'import_vouchers',
					// args:{
					// 	'doctype':cur_frm.doc.doctype,
					// 	'name':cur_frm.doc.name,
					// 	'td':cur_frm.doc.transaction_data
					// },
					freeze: true,

				});
				frm.reload_doc();
			}
		);
	},
	onload: function(frm) {
		frappe.realtime.on('update_progress', (data) => {
			console.log(data)
			frm.dashboard.show_progress("Progress", (data.progress / data.total) * 100, data.message);
		});
	}
});
