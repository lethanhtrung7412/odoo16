# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools

class HRWorkFromHomeReport(models.Model):
    _name = 'hr.attendance.wfh.report'
    _description = "Work from Home Statistics"
    _auto = False
    _order = "check_in desc"

    department_id = fields.Many2one('hr.department', string="Department", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    company_id = fields.Many2one('res.company', string="Company", readonly=True)
    check_in = fields.Date(string='Date', readonly=True) # Changed to Date field
    wfh_count = fields.Integer(string='WFH Count', readonly=True, group_operator='sum')

    @api.model
    def _select(self):
        return """
            SELECT
                min(hra.id) as id,
                hr_employee.department_id,
                hra.employee_id,
                hr_employee.company_id,
                CAST(hra.check_in 
                    at time zone 'utc'
                    at time zone
                        (SELECT calendar.tz FROM resource_calendar as calendar
                        INNER JOIN hr_employee as employee ON employee.id = hra.employee_id
                        WHERE calendar.id = employee.resource_calendar_id)
                as DATE) as check_in,
                COUNT(*) as wfh_count
        """

    @api.model
    def _from(self):
        return """
            FROM hr_attendance as hra
        """

    def _where(self):
        return """
            WHERE hra.category = 'work_from_home'    
        """

    def _group_by(self):
        return """
            GROUP BY
                hr_employee.department_id,
                hra.employee_id,
                hr_employee.company_id,
                CAST(hra.check_in 
                    at time zone 'utc'
                    at time zone
                        (SELECT calendar.tz FROM resource_calendar as calendar
                        INNER JOIN hr_employee as employee ON employee.id = hra.employee_id
                        WHERE calendar.id = employee.resource_calendar_id)
                as DATE)
        """
    
    def _join(self):
        return """
            LEFT JOIN hr_employee ON hr_employee.id = hra.employee_id
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._join(), self._where(), self._group_by())
        )