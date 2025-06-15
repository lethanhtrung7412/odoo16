from datetime import date, timedelta, datetime
import random, string
from odoo import fields, models, api, _
from odoo import exceptions
from odoo.tools import format_datetime

def random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


class HrAttendances(models.Model):
    _name = 'hr.attendance'

    _inherit = ['hr.attendance', 'mail.thread', 'mail.activity.mixin']

    STATUS = [
        ('missing_data', 'Missing Data'),
        ('pending_approval', 'Pending Approval'),
        ('ongoing', 'Ongoing'),
        ('manager_required', 'Manager Required'),
        ('request_cancelled', 'WFH Cancelled'),
        ('request_completed', 'WFH Completed'),
        ('normal', 'Normal'),
        ('under_review', 'Under Review'),
        ('approved', 'Verified'),
    ]

    employee_id = fields.Many2one(tracking=True)
    check_in = fields.Datetime(tracking=True)
    check_out = fields.Datetime(tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id",
        readonly=True, store=True)
    key = fields.Char()
    time_offset = fields.Float(string='Time Offset', compute='_compute_time_offset', store=True, readonly=True)
    approval_status = fields.Selection(selection=STATUS, string="Record Status", tracking=True, default='normal')
    missing_time_data = fields.Boolean(string="Missing Time Data")
    # other_check_in = fields.Datetime(string="Others Check In", tracking=True)
    # other_check_out = fields.Datetime(string="Others Check Out", tracking=True)
    request_unit_half = fields.Boolean(default=False)
    barcode = fields.Char(related='employee_id.barcode', string="Employee ID")
    approved_by = fields.Many2one('res.users', string="Last Updated By", ondelete='cascade', index=True, readonly=True)
    category = fields.Selection(selection=[
        ('work_from_home', 'Work from Home'),
        ('work_at_office', 'Work at Office')
    ], string="Category", default='work_at_office')
    reason = fields.Char(string='Reason', tracking=True)
    is_urgent = fields.Boolean(string='Is Urgent?', default=False)
    raw_data_ids = fields.One2many('hr.attendance.raw.data', 'attendance_id', string="Raw Data")
    can_use_button = fields.Boolean(compute='_check_button_available', store=False)
    description = fields.Html(string='WFH Description', default=None)
    is_belong = fields.Boolean(compute='_is_belong', store=False)
    employee_btn_available = fields.Boolean(compute='_employee_btn', store=False)
    _sql_constraints = [
        ('key_unique',
         'unique(key)',
         'Choose another value - it has to be unique!')
    ]

    # @api.model
    # def create(self, vals):

    #     return super(HrAttendances, self).create(vals)

    @api.model
    def write_success(self, values):      
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Success'),
                'message': 'Records have been updated!!!',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

        return notification

    def write(self, values):
        if self.approval_status == 'missing_data':
            values['missing_time_data'] = False

        if ("check_in" in values and type(values['check_in']) == str) or ("check_out" in values and type(values['check_out']) == str):
            if ("check_in" in values and datetime.strptime(values['check_in'], '%Y-%m-%d %H:%M:%S').date() != self.check_in.date()) or \
                 ("check_out" in values and datetime.strptime(values['check_out'], '%Y-%m-%d %H:%M:%S').date() != self.check_out.date()):
                raise exceptions.ValidationError("Can't update check_in, check_out date, can update hour only")
            if self.approval_status == 'request_completed' or self.approval_status == 'normal':
                values['approval_status'] = 'under_review'

        return super(HrAttendances, self).write(values)

    @api.depends('employee_id')
    def _employee_btn(self):
        for attendance in self:
            if attendance.employee_id == self.env.user.employee_id:
                attendance.employee_btn_available = True
            else:
                attendance.employee_btn_available = False


    @api.depends('employee_id', 'approval_status')
    def _is_belong(self):
        for attendance in self:
            if attendance.employee_id == self.env.user.employee_id \
            or self.env.is_admin() \
            or (attendance.employee_id.leave_manager_id and attendance.employee_id.leave_manager_id.id == self.env.user.id):
                attendance.is_belong = True
            else:
                attendance.is_belong = False

    @api.depends('employee_id')
    def _check_button_available(self):
        for attendance in self:
            if self.env.user.employee_id == attendance.employee_id.leave_manager_id.employee_id or self.env.is_admin():
                attendance.can_use_button = True
            else:
                attendance.can_use_button = False

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                delta = attendance.check_out - attendance.check_in
                worked_hours = delta.total_seconds()
                if attendance.check_out.hour >= 6 and attendance.check_in.hour <= 5:
                    worked_hours -= 3600.0
                attendance.worked_hours = worked_hours / 3600.0
            else:
                attendance.worked_hours = False

    # @api.depends('other_check_in', 'other_check_out')
    # def _compute_worked_hours(self):
    #     for attendance in self:
    #         if attendance.other_check_in and attendance.other_check_out:
    #             delta = attendance.check_out - attendance.check_in
    #             delta_other = attendance.other_check_out - attendance.other_check_in
    #             total_work_hours = delta.total_seconds() + delta_other.total_seconds()
    #             if attendance.check_out.hour >= 6 and attendance.check_in.hour <= 5:
    #                 total_work_hours -= 3600.0
    #             attendance.worked_hours = total_work_hours / 3600

    @api.onchange('worked_hours')
    def _compute_time_offset(self):
        get_limit_upper = float(self.env['ir.config_parameter'].sudo().get_param('set_time_offset_limit_upper', 0.5))
        get_limit_under = float(self.env['ir.config_parameter'].sudo().get_param('set_time_offset_limit_under', -0.5))
        for attendance in self:
            time_offset = attendance.worked_hours - 8
            if time_offset > get_limit_upper or time_offset < get_limit_under:
                if attendance.approval_status == 'normal':
                    attendance.approval_status = 'under_review'
            attendance.time_offset = time_offset

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
                * has 1 record for each type in a same day
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
                ('approval_status', 'not in', ['request_cancelled', 'manager_required']),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                raise exceptions.ValidationError(
                    _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                        'empl_name': attendance.employee_id.name,
                        'datetime': format_datetime(self.env, attendance.check_in, dt_format=False),
                    })

            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if no_check_out_attendances:
                    raise exceptions.ValidationError(
                        _("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                            'empl_name': attendance.employee_id.name,
                            'datetime': format_datetime(self.env, no_check_out_attendances.check_in, dt_format=False),
                        })
            else:
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
                last_attendance_before_check_out = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '<', attendance.check_out),
                    ('id', '!=', attendance.id),
                    ('approval_status', 'not in', ['request_cancelled', 'manager_required']),
                ], order='check_in desc', limit=1)
                if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    raise exceptions.ValidationError(
                        _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                            'empl_name': attendance.employee_id.name,
                            'datetime': format_datetime(self.env, last_attendance_before_check_out.check_in,
                                                        dt_format=False),
                        })

    @api.model
    def _cron_complete_wfh(self):
        self.complete_wfh_request()

    def complete_wfh_request(self):
        attendance_record = self.search([('approval_status', '=', 'ongoing'),
                                         ('check_out', '<', fields.Datetime.now())])
        for attendance in attendance_record:
            attendance.approval_status = 'request_completed'
            attendance.approved_by = self.env.ref('base.user_root')


    @api.model
    def _cron_change_wfh_to_att(self):
        get_time_change_wfh_to_att = int(self.env['ir.config_parameter'].sudo().get_param('leave.time_change_wfh_to_att', 1))
        attendance_record = self.search([('approval_status', '=', 'request_completed'),
                                         ('check_out', '<=', datetime.now().replace(hour=11, minute=0, second=0)
                                          + timedelta(days=-get_time_change_wfh_to_att))])
        get_limit_upper = float(self.env['ir.config_parameter'].get_param('set_time_offset_limit_upper', 0.5))
        get_limit_under = float(self.env['ir.config_parameter'].get_param('set_time_offset_limit_under', -0.5))
        for attendance in attendance_record:
            if attendance.time_offset > get_limit_upper or attendance.time_offset < get_limit_under:
                attendance.approval_status = 'under_review'
                attendance.approved_by = self.env.ref('base.user_root')
            else:
                attendance.approval_status = 'normal'
                attendance.approved_by = self.env.ref('base.user_root')

    @api.model
    def _cron_approve_attendance(self):
        attendance_record = self.search([('approval_status', '=', 'normal')])
        for attendance in attendance_record:
            attendance.approval_status = 'approved'
            attendance.approved_by = self.env.ref('base.user_root')

    @api.model
    def _cron_approve_wfh(self):
        checkin = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
        checkout = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d 23:59:00')
        attendance_record = self.search([('approval_status', '=', 'submitted'), ('check_in', '>', checkin), ('check_out', '<', checkout)])
        for attendance in attendance_record:
            attendance.approval_status = 'request_accept'
            attendance.approved_by = self.env.ref('base.user_root')
            attendance.activity_unlink(['gms.mail_act_work_from_home_approval'])
            
    @api.model
    def _cron_send_time_sheet_report(self):
        today = date.today()
        first_day_current_month = today.replace(day=1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        first_day_previous_month = last_day_previous_month.replace(day=1)

        date_from = first_day_previous_month.strftime('%Y-%m-%d')
        date_to = last_day_previous_month.strftime('%Y-%m-%d')
        report_wizard = self.env['gms.work.location.report.wizard'].create({
            'date_from': date_from,
            'date_to': date_to
        })

        context = dict(self.env.context, date_from=date_from, date_to=date_to)
        report_wizard.with_context(context).action_send_time_sheet_report()

    def approve_attendance(self):
        count = 0
        for attendance in self:
            if attendance.employee_id == self.env.user.employee_id and self.env.is_admin() is False:
                continue
            elif attendance.approval_status != 'approved' and attendance.approval_status == 'under_review':
                attendance.approval_status = 'approved'
                attendance.approved_by = attendance.write_uid
                count += 1

        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success' if count >= 1 else 'warning',
                'title': _('Success') if count >= 1 else _('Warning'),
                'message': 'All {} records have been verified!!!'.format(count)
                if count >= 2
                else ('{} record has been verified!!!'.format(count)
                      if count > 0 else 'Please select valid records to verify'),
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

        return notification

    def unlink(self):
        for attendance in self:
            if attendance.approval_status == 'approved' and self.env.is_admin() is False:
                raise exceptions.UserError(_('You cannot delete approved attendance.'))
        return super(HrAttendances, self).unlink()

    def manager_required(self):
        if self.approval_status == 'ongoing':
            self.approval_status = 'manager_required'
            self.approved_by = self.write_uid
            self.key = random_string(15)
            wfh_email_template = self.env.ref('gms.mail_template_required_to_office')
            wfh_email_template.send_mail(self.id, force_send=True)

        self.activity_unlink(['gms.mail_act_work_from_home_approval'])
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Success'),
                'message': 'Required to office for {user} on {date} successfully'.format(user=self.employee_id.name, date=self.check_in.date()),
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

        return notification

    def approve_wfh(self):
        if self.approval_status == "pending_approval":
            self.approval_status = "ongoing"
            self.approved_by = self.write_uid
            wfh_email_template = self.env.ref('gms.mail_template_approved_hr_attendance_email')
            wfh_email_template.send_mail(self.id, force_send=True)

        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Success'),
                'message': 'Approve successfully',
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

        return notification

    def reject_wfh(self):
        new_record = None
        if self.reason is False:
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'title': _('Error'),
                    'message': 'Missing reason field',
                    'sticky': False,
                }
            }

            return notification

        if self.approval_status == 'pending_approval' and self.raw_data_ids:
            self.approval_status = "request_cancelled"
            self.approved_by = self.write_uid
            self.key = random_string(10)
            self.category = "work_from_home"
            new_record = {
                "key": self.employee_id.barcode + "@" + str(self.raw_data_ids[0].date.date()),
                "employee_id": self.employee_id.id,
                "check_in": self.raw_data_ids[0].date,
                "check_out": self.raw_data_ids[-1].date,
                "time_offset": None,
                "approval_status": "normal",
                "missing_time_data": None,
                "category": 'work_at_office',
                "raw_data_ids": self.raw_data_ids
            }
        elif self.approval_status == 'pending_approval':
            self.approval_status = 'request_cancelled'
            self.approved_by = self.write_uid
            self.key = random_string(15)
            wfh_email_template = self.env.ref('gms.mail_template_reject_hr_attendance_email')
            wfh_email_template.send_mail(self.id, force_send=True)

        self.activity_unlink(['gms.mail_act_work_from_home_approval'])
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Success'),
                'message': 'Reject successfully',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

        if new_record:
            self.sudo().create(new_record)
        return notification

    def cancel_wfh(self):
        new_record = None
        for attendance in self:
            if attendance.approval_status == 'ongoing' and attendance.raw_data_ids:
                attendance.approval_status = "request_cancelled"
                attendance.approved_by = attendance.write_uid
                attendance.key=random_string(15)
                new_record = {
                    "key": self.employee_id.barcode + "@" + str(self.check_in.date()),
                    "employee_id": attendance.employee_id.id,
                    "check_in": attendance.raw_data_ids[0].date,
                    "check_out": attendance.raw_data_ids[-1].date,
                    "time_offset": None,
                    "approval_status": "normal",
                    "missing_time_data": None,
                    "category": "work_at_office",
                    "raw_data_ids": attendance.raw_data_ids
                }
            elif attendance.approval_status == 'ongoing':
                attendance.approval_status = 'request_cancelled'
                attendance.key=random_string(15)
                attendance.approved_by = attendance.write_uid
            elif attendance.approval_status == 'request_completed' and attendance.raw_data_ids:
                attendance.approval_status = "request_cancelled"
                attendance.approved_by = attendance.write_uid
                attendance.key=random_string(15)
                new_record = {
                    "key": self.employee_id.barcode + "@" + str(self.check_in.date()),
                    "employee_id": attendance.employee_id.id,
                    "check_in": attendance.raw_data_ids[0].date,
                    "check_out": attendance.raw_data_ids[-1].date,
                    "time_offset": None,
                    "approval_status": "normal",
                    "missing_time_data": None,
                    "category": "work_at_office",
                    "raw_data_ids": attendance.raw_data_ids
                }
            elif attendance.approval_status == 'request_completed':
                attendance.approval_status = 'request_cancelled'
                attendance.key=random_string(15)
                attendance.approved_by = attendance.write_uid
        self.activity_unlink(['gms.mail_act_work_from_home_approval'])
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Success'),
                'message': 'WFH request has been cancelled successfully',
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
        if new_record:
            self.sudo().create(new_record)
        return notification

    def action_open_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.attendance',
            'name': _(self.employee_id.name + ', '
                      + self.check_in.date().strftime("%A") + ' '
                      + self.check_in.date().strftime("%m/%d/%Y")),
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'flags': {'action_buttons': True}
        }
