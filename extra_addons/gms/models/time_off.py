from datetime import timedelta, datetime, date
import urllib, webbrowser
from odoo import fields, models, api, exceptions,_

class HolidaysRequest(models.Model):
    _inherit = ["hr.leave"]

    mail_value = fields.Char(string="hello", compute='_mail_send')

    @api.model
    def create(self, vals):
        annual_leave_type_id = int(self.env['ir.config_parameter'].sudo().get_param('leave.annual_leave_id', 0))
        if not annual_leave_type_id:
            raise exceptions.ValidationError("Parameter 'leave.annual_leave_id' not exists")
        personal_leave_type_id = int(self.env['ir.config_parameter'].sudo().get_param('leave.personal_leave_id', 0))
        if not personal_leave_type_id:
            raise exceptions.ValidationError("Parameter 'leave.personal_leave_id' not exists")
        
        if vals['holiday_status_id'] == personal_leave_type_id:
            records = self.env['hr.leave.type'].browse(annual_leave_type_id)
            if records.virtual_remaining_leaves > 0:
                raise exceptions.ValidationError("Annual Leave must be used first. Please adjust your leave request.")
        # leaves_taken = allocations.holiday_status_id._get_employees_days_per_allocation(self.ids)
        return super(HolidaysRequest, self).create(vals)

    # @api.depends('employee_id', 'request_date_from', 'request_date_to')
    # def _mail_send(self):
    #     self.ensure_one()
    #     email_address = self.employee_id.work_email
    #     subject = 'Leave Approval'
    #     body = f"""
    #     Dear Everyone,

    #     Please be informed that {self.employee_id.name} has been granted a leave of absence from {self.request_date_from} to {self.request_date_to}.

    #     Leave Details:

    #     Type of Leave: {self.holiday_status_id.name}
    #     Reason for Leave: {self.name or 'None'}
    #     Please ensure that {self.employee_id.name}'s absence is taken into account for any relevant tasks, meetings, or projects.

    #     Thank you for your attention to this matter.

    #     Sincerely, 

    #     {self.env.user.employee_id.name} 

    #     {self.env.user.employee_id.job_title or 'None'}, {self.employee_id.department_id.name}
    #     """
    #     subject_encoded = urllib.parse.quote(subject)
    #     body_encoded = urllib.parse.quote(body)
    #     mailto_link = f'mailto:{email_address}?subject={subject_encoded}&body={body_encoded}'
    #     self.mail_value = mailto_link
        
    # def mail_send(self):
    #     pass
