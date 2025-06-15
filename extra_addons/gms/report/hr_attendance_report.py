# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class HRAttendanceReport(models.Model):
    _name = 'hr.attendance.report'
    _inherit = 'hr.attendance.report'
    _description = "Attendance Statistics"

    time_offset = fields.Float("Time Offset", readonly=True,store=True)
    category = fields.Selection(selection=[
        ('work_from_home', 'Work from Home'),
        ('work_at_office', 'Work at Office')
    ], string="Category", default='work_at_office')

    @api.model
    def _select(self):
        return """
            SELECT
                hra.id,
                hr_employee.department_id,
                hra.employee_id,
                hr_employee.company_id,
                hra.check_in,
                hra.worked_hours,
                hra.category,
                coalesce(ot.duration, 0) as overtime_hours,
                hra.time_offset
        """

    @api.model
    def _from(self):
        return """
            FROM (
                SELECT
                    id,
                    row_number() over (partition by employee_id, CAST(check_in AS DATE)) as ot_check,
                    employee_id,
                    CAST(check_in
                            at time zone 'utc'
                            at time zone
                                (SELECT calendar.tz FROM resource_calendar as calendar
                                INNER JOIN hr_employee as employee ON employee.id = hr_attendance.employee_id
                                WHERE calendar.id = employee.resource_calendar_id)
                    as DATE) as check_in,
                    category,
                    worked_hours,
                    time_offset
                FROM
                    hr_attendance
                ) as hra
        """

    def _join(self):
        return """
            LEFT JOIN hr_employee ON hr_employee.id = hra.employee_id
            LEFT JOIN hr_attendance_overtime ot
                ON hra.ot_check = 1
                AND ot.employee_id = hra.employee_id
                AND ot.date = hra.check_in
                AND ot.adjustment = FALSE
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._join())
        )
