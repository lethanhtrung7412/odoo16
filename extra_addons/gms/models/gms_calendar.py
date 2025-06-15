from odoo import models, fields, api
from pytz import UTC
from datetime import datetime, time

class GmsCalendar(models.TransientModel):
    _name = 'gms.calendar'
    _description = 'Combined Model for Attendance and Time Off'

    name = fields.Char(string='Employee')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    reason = fields.Char(string='Reason')
    record_type = fields.Selection([('work_from_home', 'Work from Home'), ('time_off', 'Time Off')], string='Record Type')
    department_id = fields.Many2one('hr.department', string="Department",
        readonly=True, store=True)
    holiday_type = fields.Char(string='Time off types', default="None")
    link_id = fields.Char()
    record_form_url = fields.Char(string='Record Form URL')
    
    @api.model
    def fetch_combined_data(self):
        # Fetch attendance data
        attendance_records = self.env['hr.attendance'].search([('category', '=', 'work_from_home'), ('approval_status', 'not in', ['request_cancelled', 'manager_required'])])

        # Fetch time off data
        time_off_records = self.env['hr.leave'].search([('state', '=', 'validate')])

        # Combine data logic
        combined_data = []
        for record in attendance_records:
            combined_data.append({
                'name': record.employee_id.name,
                'start_date': record.check_in,
                'end_date': record.check_out,
                'reason': record.reason,
                'record_type': 'work_from_home',
                'link_id': str(record.id) + ' ' + str('hr.attendance'),
                'department_id': record.department_id.id,
                'record_form_url': f"/web?#model=hr.attendance&id={record.id}&view_type=form"   
            })

        for record in time_off_records:
            combined_data.append({
                'name': record.employee_id.name,
                'start_date': record.date_from,
                'end_date': record.date_to,
                'reason': None,
                'record_type': 'time_off',
                'holiday_type': record.holiday_status_id.name,
                'link_id': str(record.id) + ' ' + str('hr.leave'),
                'department_id': record.department_id.id,
                'record_form_url': f"/web?#model=hr.leave&id={record.id}&view_type=form"   
            })            

        records_to_delete = self.env['gms.calendar'].search([('link_id', 'not in', [data['link_id'] for data in combined_data])])
        records_to_delete.unlink()

        # Create combined records
        for data in combined_data:
            existing_record = self.env['gms.calendar'].search([('link_id', '=', data['link_id'])])
            if existing_record:
                existing_record.write(data)  # Update existing record
            else:
                self.create(data)

    @api.model
    def get_unusual_days(self, date_from, date_to=None):
        return self.env.user.employee_id._get_unusual_days(date_from, date_to)
    
    @api.model
    def _get_view(self, view_id=None, view_type='calendar', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        self.fetch_combined_data()
        
        return arch, view
