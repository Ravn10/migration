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
					freeze: true
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
