# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.widgets.reportview import get_match_cond
from frappe.utils import add_days, cint, cstr, date_diff, rounded, flt, getdate, nowdate, \
	get_first_day, get_last_day,money_in_words, now
from frappe import _
from frappe.model.db_query import DatabaseQuery

def get_style(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""select distinct style 
		from `tabStyle Item` where parent='%s'"""%(filters.get('item_code')))

def branch_validation(doc, method):
	br = frappe.db.sql("select name from `tabBranch` where warehouse='%s' or cost_center='%s'"%(doc.warehouse, doc.cost_center),as_list=1)
	if br:
		frappe.throw(_("Branch or Warehouse already assigned to Branch '{0}'").format(br[0][0]))

def generate_project_aginst_si(doc, method):
	if not frappe.db.get_value('Project', doc.name, 'name'):
		pt = frappe.new_doc('Project')
		pt.project_name = doc.name
		pt.project_start_date = now()
		pt.save(ignore_permissions=True)
		generate_task(doc, method, pt.name)		

def generate_task(doc, method, name):
	for d in doc.get('entries'):
		if d.work_order:
			process_details = frappe.db.sql("select process from `tabWO Process` where parent='%s'"%(d.work_order))
			item_code = frappe.db.get_value('Work Order', d.work_order, 'item_code')
			if process_details:
				for process in process_details:
					create_task_against_process(doc,process[0], name, item_code)

def create_task_against_process(doc,process, name, item_code):
	if not frappe.db.get_value('Task',{'name':process,'project':name},'name') and item_code:
		c = frappe.new_doc('Task')
		c.subject = process + ' For Item ' + frappe.db.get_value('Item', item_code, 'item_name')
		c.process_name = process
		c.item_name = frappe.db.get_value('Item', item_code, 'item_name')
		c.sales_order_number = doc.name
		c.save()

def delete_project_aginst_si(doc, method):
	value = frappe.db.sql("select name from `tabTask` where sales_order_number='%s'"%(doc.name))
	if value:
		for d in value:
			frappe.db.sql("delete from `tabTime Log` where task='%s'"%(d[0]))
	frappe.db.sql("delete from `tabTask` where sales_order_number='%s'"%(doc.name))
	frappe.db.sql("delete from `tabProject` where name='%s'"%(doc.name))	

@frappe.whitelist()
def get_styles_details(item, style):
	return frappe.db.sql("""select name,  image_viewer,default_value, abbreviation,
	cost_to_customer, cost_to_tailor, extra_text_field from `tabStyle Item`
		where parent='%s' and style='%s'"""%(item, style),as_list=1)