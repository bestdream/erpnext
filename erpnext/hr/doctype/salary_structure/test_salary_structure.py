# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
import erpnext
from frappe.utils.make_random import get_random
from frappe.utils import nowdate, add_days, add_years, getdate, add_months
from erpnext.hr.doctype.salary_structure.salary_structure import make_salary_slip
from erpnext.hr.doctype.salary_slip.test_salary_slip import get_earnings_component,\
	get_deductions_component, make_employee_salary_slip
from erpnext.hr.doctype.employee.test_employee import make_employee


test_dependencies = ["Fiscal Year"]

class TestSalaryStructure(unittest.TestCase):
	def setUp(self):
		for dt in ["Salary Slip", "Salary Structure", "Salary Structure Assignment"]:
			frappe.db.sql("delete from `tab%s`" % dt)

		self.make_holiday_list()
		frappe.db.set_value("Company", erpnext.get_default_company(), "default_holiday_list", "Salary Structure Test Holiday List")
		make_employee("test_employee@salary.com")
		make_employee("test_employee_2@salary.com")


	def make_holiday_list(self):
		if not frappe.db.get_value("Holiday List", "Salary Structure Test Holiday List"):
			holiday_list = frappe.get_doc({
				"doctype": "Holiday List",
				"holiday_list_name": "Salary Structure Test Holiday List",
				"from_date": nowdate(),
				"to_date": add_years(nowdate(), 1),
				"weekly_off": "Sunday"
			}).insert()	
			holiday_list.get_weekly_off_dates()
			holiday_list.save()

	def test_amount_totals(self):
		sal_slip = frappe.get_value("Salary Slip", {"employee_name":"test_employee_2@salary.com"})
		if not sal_slip:
			sal_slip = make_employee_salary_slip("test_employee_2@salary.com", "Monthly", "Salary Structure Sample")
			self.assertEqual(sal_slip.get("salary_structure"), 'Salary Structure Sample')
			self.assertEqual(sal_slip.get("earnings")[0].amount, 25000)
			self.assertEqual(sal_slip.get("earnings")[1].amount, 3000)
			self.assertEqual(sal_slip.get("earnings")[2].amount, 12500)
			self.assertEqual(sal_slip.get("gross_pay"), 40500)
			self.assertEqual(sal_slip.get("deductions")[0].amount, 5000)
			self.assertEqual(sal_slip.get("deductions")[1].amount, 5000)
			self.assertEqual(sal_slip.get("total_deduction"), 10000)
			self.assertEqual(sal_slip.get("net_pay"), 30500)

	def test_whitespaces_in_formula_conditions_fields(self):
		make_salary_structure("Salary Structure Sample", "Monthly")
		salary_structure = frappe.get_doc("Salary Structure", "Salary Structure Sample")

		for row in salary_structure.earnings:
			row.formula = "\n%s\n\n"%row.formula
			row.condition = "\n%s\n\n"%row.condition

		for row in salary_structure.deductions:
			row.formula = "\n%s\n\n"%row.formula
			row.condition = "\n%s\n\n"%row.condition

		salary_structure.save()

		for row in salary_structure.earnings:
			self.assertFalse("\n" in row.formula or "\n" in row.condition)

		for row in salary_structure.deductions:
			self.assertFalse(("\n" in row.formula) or ("\n" in row.condition))


def make_salary_structure(salary_structure, payroll_frequency, employee=None):
	if not frappe.db.exists('Salary Structure', salary_structure):
		salary_structure_doc = frappe.get_doc({
			"doctype": "Salary Structure",
			"name": salary_structure,
			"company": erpnext.get_default_company(),
			"earnings": get_earnings_component(),
			"deductions": get_deductions_component(),
			"payroll_frequency": payroll_frequency,
			"payment_account": get_random("Account")
		}).insert()
		if employee:
			create_salary_structure_assignment(employee, salary_structure)

	elif employee and not frappe.db.get_value("Salary Structure Assignment",{'salary_structure':salary_structure, 'employee':employee},'name'):
		create_salary_structure_assignment(employee, salary_structure)
	return salary_structure

def create_salary_structure_assignment(employee, salary_structure):
	salary_structure_assignment = frappe.new_doc("Salary Structure Assignment")
	salary_structure_assignment.employee = employee
	salary_structure_assignment.base = 50000
	salary_structure_assignment.variable = 5000
	salary_structure_assignment.from_date = add_months(nowdate(), -1)
	salary_structure_assignment.salary_structure = salary_structure
	salary_structure_assignment.company = erpnext.get_default_company()
	salary_structure_assignment.save(ignore_permissions=True)
	salary_structure_assignment.submit()
	return salary_structure_assignment