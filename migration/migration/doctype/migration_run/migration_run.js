// Copyright (c) 2021, Firsterp and contributors
// For license information, please see license.txt

frappe.ui.form.on('Migration Run', {
	onload: function(frm) {
		frappe.realtime.on('msgprint', (data) => {
			console.log(data)
		});
	}
});
