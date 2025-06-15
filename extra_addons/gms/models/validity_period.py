from pandas import date_range
from datetime import datetime

from odoo import models, fields, api
from odoo import exceptions
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class DepartmentValidityPeriod(models.Model):
    _name = 'validity.period'

    def _default_department(self):
        return self.env.user.employee_id.department_id.id

    department_id = fields.Many2one(
        'hr.department',
        default=_default_department,
    )
    days_restriction = fields.Many2many(
        'day.of.week',
        required=True,
        string='Days Selection',
        tracking=True,
    )
    date_from = fields.Date(
        string='From',
        default=fields.Date.context_today,
    )
    date_to = fields.Date(
        string='To',
    )
    days_per_week = fields.Float(
        'Count',
        compute="_count_days",
        store=True,
        help="Measure: Days/Week",
    )

    @api.constrains('date_from', 'date_to')
    def _check_overlap_time(self):
        for record in self:
            if record.date_to and record.date_from > record.date_to:
                raise exceptions.ValidationError('The end date must be after the start date.')

            overlapping_records = self.search([
                ('id', '!=', record.id),
                ('department_id', '=', record.department_id.id),
                ('date_from', '<=', record.date_from),
                ('date_to', '>=', record.date_from)
            ])

            if overlapping_records:
                raise exceptions.ValidationError('This record overlap with existing record.')

            ongoing_records = self.search([
                ('department_id', '=', record.department_id.id),
                ('date_to', '=', False),
            ])

            if len(ongoing_records) > 1:
                raise exceptions.ValidationError("Cannot create a new record while there are ongoing records.")


    @api.depends('days_restriction')
    def _count_days(self):
        for record in self:
            record.days_per_week = len(record.days_restriction)

    def unlink(self):
        usr_lang =  self.env['res.lang'].search([
            ('code', '=', self.env.user.lang),
        ], limit=1)
        usr_lang.ensure_one() # ensure user has language
        date_format = usr_lang.date_format or DEFAULT_SERVER_DATE_FORMAT
        notifi_template = self.env.ref('gms.mail_template_change_period')
        for period in self:
            search_old_record_domain = [('category', '=', 'work_from_home'),
                                    ('check_in', '>=', period.date_from),
                                    ('department_id', 'in', period.mapped('department_id.id')),
                                    ('approval_status', '=', 'ongoing')]
            if period.date_to:
                search_old_record_domain.append(('check_in', '<=', period.date_to))
            records = self.env['hr.attendance'].search(search_old_record_domain)
            records.cancel_wfh()
            for emp in records.mapped('employee_id'):
                wfhs = records.filtered(lambda r: r.employee_id.id == emp.id)
                dates = []
                date_format = usr_lang.date_format or DEFAULT_SERVER_DATE_FORMAT
                for record in wfhs:
                    dates.append(datetime.strftime(record.check_in.date(), date_format))
                notifi_template.with_context({
                    'wfh_date': ", ".join(dates),
                    'email_to': emp.work_email,
                    'name': emp.name,
                }).send_mail(self.id)


        return super().unlink()

    def write(self, vals):
        usr_lang =  self.env['res.lang'].search([
            ('code', '=', self.env.user.lang),
        ], limit=1)
        usr_lang.ensure_one() # ensure user has language
        date_format = usr_lang.date_format or DEFAULT_SERVER_DATE_FORMAT
        notifi_template = self.env.ref('gms.mail_template_change_period')
        is_edit = False
        if 'date_from' in vals or 'date_to' in vals:
            is_edit = True
        search_old_record_domain = [('category', '=', 'work_from_home'),
                                    ('check_in', '>=', self.date_from),
                                    ('department_id', 'in', self.mapped('department_id.id')),
                                    ('approval_status', '=', 'ongoing')]
        if self.date_to:
            search_old_record_domain.append(('check_in', '<=', self.date_to))
        old_records = self.env['hr.attendance'].search(search_old_record_domain)
        res = super().write(vals)
        new_records = self.env['hr.attendance']
        if is_edit:
            for record in self:
                
                if not record.date_to:
                    continue
                else:
                    new_records |= self.env['hr.attendance'].search([('category', '=', 'work_from_home'),
                                    ('check_in', '>=', record.date_from),
                                    ('check_in', '<=', record.date_to),
                                    ('department_id', '=', record.department_id.id),
                                    ('approval_status', '=', 'ongoing')])
            
            # new_record = new_record_temp
        distinc_record = old_records - new_records
        if distinc_record != old_records:
            distinc_record.cancel_wfh()
            for emp in distinc_record.mapped('employee_id'):
                wfhs = distinc_record.filtered(lambda r: r.employee_id.id == emp.id)
                dates = []
                for record in wfhs:
                    dates.append(datetime.strftime(record.check_in.date(), date_format))
                notifi_template.with_context({
                    'wfh_date': ", ".join(dates),
                    'email_to': emp.work_email,
                    'name': emp.name,
                }).send_mail(self.id)
        return res

    def get_dates_in_period(self, date_from, date_to):
        """
        Args:
            date_from (datetime.date):
            date_to (datetime.date):
        Returns:
            list
        """
        self.ensure_one()
        d_from = max(self.date_from, date_from)
        d_to = min(self.date_to or date_to, date_to) # * in case validity does not have date_to
        res = []
        d_restricts = set(self.days_restriction.mapped('code'))
        for d in date_range(d_from, d_to):
            if d.isoweekday() in d_restricts:
                res.append(d.date())
        return res