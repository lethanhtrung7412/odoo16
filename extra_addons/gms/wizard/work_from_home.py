import pytz
import string, random
from bs4 import BeautifulSoup
from datetime import timedelta, datetime, date, timezone, time
from dateutil.relativedelta import relativedelta
from pandas import to_datetime
from odoo import fields, models, exceptions, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

def random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def float_to_time(time_float):
    # Extract hours
    hours = int(time_float)
    # Extract minutes
    minutes = int((time_float * 60) % 60)
    # Extract seconds
    seconds = int((time_float * 3600) % 60)

    return time(hours, minutes, seconds)
    
def is_in_date_range(date_to_check, date_from, date_to=None):
    if date_to_check < date_from:
        return False
    
    if date_to and date_to_check > date_to:
        return False
    
    return True

localize = pytz.timezone('Asia/Ho_Chi_Minh')


def _convert_date_arr(date_arr_str, date_format):
    """
    Args:
        date_arr_str (list[str]): list date string
        date_format (str): format date
    Returns:
        list[date]:
    """
    return list(map(lambda d: datetime.strptime(d, date_format).date(), date_arr_str))


class WorkFromHome(models.TransientModel):
    _name = "hr.attendance.work.from.home"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Create WFH request wizard"

    def _default_employee(self):
        return self.env.user.employee_id

    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True,
                                  ondelete='cascade', index=True)
    check_in = fields.Datetime(
        default=lambda self: datetime.now().replace(hour=2, minute=0, second=0) + timedelta(days=1))
    check_out = fields.Datetime(
        default=lambda self: datetime.now().replace(hour=11, minute=0, second=0) + timedelta(days=1))
    category = fields.Selection(selection=[
        ('work_from_home', 'Work from Home'),
        ('work_at_office', 'Work at Office')
    ],
        string="Category",
        default='work_from_home',
    )
    description = fields.Html(
        string="Description",
        help="Enter details for your WFH request, including ongoing needs or one-time reasons",
    )
    list_day_wao = fields.Char(
        string="Scheduled Office Days",
        compute="_list_day",
        store=False,
    )
    record_id = fields.Integer()
    multiple_date = fields.Char()
    # balance_work_from_home = fields.Char(store=False, compute="_get_all_balance")
    request_unit_half = fields.Boolean('Shift', compute='_compute_request_unit_half', store=True, readonly=False, default=False)
    # used only when the leave is taken in half days
    request_date_from_period = fields.Selection([
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
    ],
        string="Date Period Start",
        default='morning',
        help="- Morning: 8AM to 12PM.\n"
             "- Afternoon: 1PM to 5PM",
    )
    request_date_from = fields.Date(
        'Request Start Date',
        default=lambda self: datetime.now().replace(hour=2, minute=0, second=0) + timedelta(days=1),
    )
    is_urgent = fields.Boolean(
        string='Urgent',
        default=False,
    )
    is_admin = fields.Boolean(
        compute='_is_admin',
        store=False,
    )

    def get_date_in_period(self,validity_period):
        """
        List out all the fix office day for each employee
        """
        # * get language to get user's date format
        usr_lang =  self.env['res.lang'].search([
            ('code', '=', self.env.user.lang),
        ], limit=1)
        usr_lang.ensure_one() # ensure user has language
        start = 0
        end = 30
        today = date.today()

        result = []
        for validity in validity_period:
            current_date = today
            if current_date < validity.date_from:
                current_date = validity.date_from
            end_date = validity.date_to

            if end_date:
                while current_date <= end_date and start != end:
                    if current_date.isoweekday() in validity.days_restriction.mapped('code'):
                        result.append(current_date.strftime(usr_lang.date_format))
                    current_date += timedelta(days=1)
                    start += 1
            else:
                while start != end:
                    if current_date.isoweekday() in validity.days_restriction.mapped('code'):
                        result.append(current_date.strftime(usr_lang.date_format))
                    current_date += timedelta(days=1)
                    start += 1
        return result

    @api.depends('employee_id')
    def _list_day(self):
        for record in self:
            if record.employee_id.department_id.validity_period and record.employee_id.department_id.fix_day_in_office:
                result = self.get_date_in_period(record.employee_id.department_id.validity_period)
                record.list_day_wao = " - ".join(result)
            else:
                record.list_day_wao = ""

    @api.depends('employee_id')
    def _is_admin(self):
        for attendance in self:
            if self.env.is_admin():
                attendance.is_admin = True
            else:
                attendance.is_admin = False

    @api.constrains('description', 'is_urgent')
    def _check_description_content(self):
        for request in self:
            if request.is_urgent:
                soup = BeautifulSoup(request.description, 'html.parser')
                # Check for at least one image tag
                if not soup.find('img'):
                    raise exceptions.ValidationError("At least one image is required.")
                # Check for at least one paragraph with 50 characters
                paragraphs = soup.find_all('p')
                if not any(len(p.text) >= 50 for p in paragraphs):
                    raise exceptions.ValidationError("At least one paragraph with 50 or more characters is required.")

    def validate_work_from_home(self, check_in):
        """
        Check if that day is in the fix-office day
        """
        # Extract department details for easier reference
        department = self.employee_id.department_id
        check_in_weekday = check_in.weekday()
        check_in_date = check_in.date()

        date_range = department.validity_period.filtered(lambda r: r.date_from <= check_in.date()  and (not r.date_to or check_in.date() <= r.date_to))

        # Check if department exists the validity period
        if date_range:
            # Check if the period have the ending date
            if date_range.date_to:
                # Date range with end date
                if is_in_date_range(check_in_date, date_range.date_from, date_range.date_to):
                    if check_in_weekday + 1 in date_range.days_restriction.mapped('code') and check_in_date >= date_range.date_from:
                        return {
                            'status': False, 
                            'message': "The date is in work at office day"
                        }
            else:
                # Date range without end date
                if is_in_date_range(check_in_date, date_range.date_from):
                    if check_in_weekday + 1 in date_range.days_restriction.mapped('code') and check_in_date >= date_range.date_from:
                        return {
                            'status': False,
                            'message': "The date is in work at office day"
                        }
        else:
            return {
                'status': False, 
                'message': "Not configured properly to work-from-home register. Please contact your team lead."
            }
                    
        return {
            'status': True, 
            'message': ""
        }

    def _get_office_working_period(self, wfh_date):
        """
        Args:
            wfh_date (date)
        Returns:
            (date, date):
        """
        expected_date_from = int(self.env['ir.config_parameter'].sudo().get_param(
            'company.date_from',
            0,
        ))
        expected_date_to = int(self.env['ir.config_parameter'].sudo().get_param(
            'company.date_to',
            0,
        ))
        if not expected_date_from:
            raise exceptions.ValidationError('Parameter "company.date_from" does not exists')
        elif not expected_date_to:
            raise exceptions.ValidationError('Parameter "company.date_to" does not exists')

        date_from = wfh_date + relativedelta(day=expected_date_from, months=-1)
        date_to = wfh_date + relativedelta(day=expected_date_to)
        if wfh_date.day > expected_date_to:
            date_from = wfh_date + relativedelta(day=expected_date_from)
            date_to = wfh_date + relativedelta(day=expected_date_to, months=1)
        return date_from, date_to

    def _get_expected_working_dates(self, employee, date_from, date_to):
        """
        Args:
            employee (hr.employee): employee requests WFH
            date_from (date): start date of working period
            date_to (date): end date of working period
        """
        vn = pytz.timezone('Asia/Ho_Chi_Minh')
        dt_from = vn.localize(datetime.combine(date_from, time.min)) # ? should change to user's tz
        dt_to = vn.localize(datetime.combine(date_to, time.max)) # ? should change to user's tz
        # * get total expected working date at office
        working_calendar = employee.resource_calendar_id or self.env.company.resource_calendar_id
        expected_working_days = working_calendar.get_work_duration_data(
            from_datetime=dt_from,
            to_datetime=dt_to,
        ) # ! expected total working date except time-off and public holiday
        return expected_working_days # TODO

    # Perform action when click on Submit
    def action_create_wfh(self):
        if not self.employee_id.barcode:
            raise ValidationError(_("Please setup Employee Code (Barcode) in employee information"))

        submit_wfh_limit = int(self.env['ir.config_parameter'].sudo().get_param('wfh.submit_wfh_time_limit', 0))
        if not submit_wfh_limit:
            raise exceptions.ValidationError("Parameter 'wfh.submit_wfh_time_limit' not exists")

        min_register = int(self.env['ir.config_parameter'].sudo().get_param('minmum_wao_register', 0))
        if not min_register:
            raise exceptions.ValidationError('Parameter "minmum_wao_register" does not exists')

        # * get language to get user's date format
        usr_lang =  self.env['res.lang'].search([
            ('code', '=', self.env.user.lang),
        ], limit=1)
        usr_lang.ensure_one() # ensure user has language
        date_format = usr_lang.date_format or DEFAULT_SERVER_DATE_FORMAT

        err_arr = []
        today = date.today()
        current_time = datetime.now(tz=timezone.utc)
        have_fo_day = self.employee_id.department_id.fix_day_in_office
        if self.multiple_date:
            date_register_arr = self.multiple_date.split(" - ")
            lst_wfh_date = _convert_date_arr(date_register_arr, date_format)

        if self.is_urgent:
            if self.request_date_from.weekday() > 4 and not self.env.is_admin():
                raise exceptions.ValidationError("Can't create work from home request on {date}. It's in the weekend".format(date= self.request_date_from))
                
            user_resource = self.env['resource.calendar.attendance'].search([('calendar_id', '=', self.employee_id.resource_calendar_id.id), 
                                                                    '&' ,('dayofweek', '=', self.request_date_from.weekday()), 
                                                                    ('day_period', '=', self.request_date_from_period)])
            if self.request_unit_half:
                self.check_in = datetime.combine(self.request_date_from, float_to_time(user_resource.hour_from - 7))
                self.check_out = datetime.combine(self.request_date_from, float_to_time(user_resource.hour_to - 7))
            else:
                self.check_in = datetime.combine(self.request_date_from, float_to_time(1))
                self.check_out = datetime.combine(self.request_date_from, float_to_time(10))
            key = self.employee_id.barcode + "@" + str(self.request_date_from)
            record = self.env['hr.attendance'].search([('key', '=', key)])
            if record:
                raise exceptions.ValidationError("Can't create work from home register on {date}. You have registered on that day.".format(date=self.request_date_from))
            elif self.check_in < datetime.today():
                raise exceptions.ValidationError("Work-from-home register cannot be submitted for past dates")
            # Create record into attendance model
            record = {
                "key": random_string(15),
                "employee_id": self.employee_id.id,
                "check_in": self.check_in,
                "check_out": self.check_out,
                "time_offset": None,
                "approval_status": "pending_approval",
                "missing_time_data": None,
                "category": "work_from_home",
                "description": self.description,
                "request_unit_half": self.request_unit_half,
                "raw_data_ids": [],
                "is_urgent": self.is_urgent,
            }

            new_record = self.env['hr.attendance'].create(record)
            self.record_id = new_record.id

            new_record.activity_schedule(
                'gms.mail_act_work_from_home_approval',
                note=f'New Work from home request created by {new_record.employee_id.name}',
                user_id=new_record.employee_id.leave_manager_id.id
            )
        else:    
            for wfh_date in lst_wfh_date:
                # Check if the day for work from home is in the weekend
                # date_obj = datetime.strptime(date_vals, date_format)
                check_in_time = datetime.combine(wfh_date, datetime.strptime('02:00:00', '%H:%M:%S').time())
                check_out_time = datetime.combine(wfh_date, datetime.strptime('11:00:00', '%H:%M:%S').time())
                # Check if the day is in the required to office day
                if have_fo_day:
                    is_in_fix_day = self.validate_work_from_home(check_in_time)
                key = self.employee_id.barcode + "@" + str(wfh_date)
                record = self.env['hr.attendance'].search([('key', '=', key)])
                if record:
                    err_arr.append("Can't create work from home register on {date}. You have registered on that day.".format(date=wfh_date))
                    continue
                elif wfh_date.weekday() > 4 and not self.env.is_admin():
                    err_arr.append("Can't create work from home request on {date}. It's in the weekend".format(date=wfh_date))
                    continue
                elif have_fo_day and not is_in_fix_day['status']:
                    # self.multiple_date = ''
                    err_arr.append("Can't create work from home in {date}. {message}".format(date=wfh_date, message=is_in_fix_day['message']))
                    continue
                elif check_in_time < datetime.today():
                    # Check if the day for work from home request is in the future or not
                    err_arr.append("Work-from-home register cannot be submitted for past dates")
                    continue
                # Check if the request is urgent or not
                elif not self.is_urgent:
                    if today.weekday() == 4 and (check_in_time.date() - today).days == 3 and current_time.hour > submit_wfh_limit - 7:
                        err_arr.append("Need to create a WFH request before 12:00pm")
                        continue
                    elif current_time.hour > submit_wfh_limit - 7 and (check_in_time.date() - today).days <= 1  and not self.env.is_admin():
                        err_arr.append("Need to create a WFH request before 12:00pm")
                        continue
                else:
                    if '<p><img' not in self.description:
                        err_arr.append("Urgent WFH Requests Require Proof (Screenshot)")
                        continue
                date_from, date_to = self._get_office_working_period(wfh_date)
                unusual_day_dict = self.employee_id._get_unusual_days(
                    date_from=date_from,
                    date_to=date_to,
                )
                unusual_day_list = [(datetime.strptime(key, '%Y-%m-%d')).date() for key, value in unusual_day_dict.items() if value and (datetime.strptime(key, '%Y-%m-%d').weekday() not in (5,6))]
                resource_wao = []
                for x in range((date_to - date_from).days + 1):
                    current_date = date_from + timedelta(days=x)
                    
                    is_in_work_day = self.env['resource.calendar.attendance'].search([
                        ('calendar_id', '=', self.employee_id.resource_calendar_id.id),
                        ('dayofweek', '=', current_date.weekday())
                    ])
                    if is_in_work_day:
                        resource_wao.append(current_date)
                expected_wao = set(resource_wao).symmetric_difference(set(unusual_day_list))
                domain = [
                    ('employee_id', '=', self.employee_id.id),
                    ('check_in', '>=', date_from),
                    ('check_in', '<=', date_to),
                    ('approval_status', 'in', ['pending_approval','ongoing', 'request_completed']),
                    ('category', '=', 'work_from_home'),
                    ('is_urgent', '=', False)
                ]

                # ? ! what does this condition check for?
                if self['check_in'].astimezone(localize).date() != self['check_out'].astimezone(localize).date():
                    raise exceptions.ValidationError("Please select the same date for check-in and check-out.")

                records = self.env['hr.attendance'].search(domain)
                if len(expected_wao) - len(records) <= min_register and not self.is_urgent:
                    err_arr.append("{date}: Your WFH limit for this month (27th - 26th) has been reached.".format(date=wfh_date))
            
                # Create record into attendance model
                record = {
                    "key": key,
                    "employee_id": self.employee_id.id,
                    "check_in": check_in_time,
                    "check_out": check_out_time,
                    "time_offset": None,
                    "approval_status": "ongoing" if have_fo_day else "pending_approval",
                    "missing_time_data": None,
                    "category": "work_from_home",
                    "description": self.description,
                    "raw_data_ids": [],
                    "is_urgent": self.is_urgent,
                }

                new_record = self.env['hr.attendance'].create(record)
                self.record_id = new_record.id

                new_record.activity_schedule(
                    'gms.mail_act_work_from_home_approval',
                    note=f'New Work from home request created by {new_record.employee_id.name}',
                    user_id=new_record.employee_id.leave_manager_id.id
                )

        if err_arr:
            raise exceptions.ValidationError("\n".join(err_arr))

        # Send email to manager
        if not have_fo_day:
            wfh_email_template = self.env.ref('gms.mail_template_notify_hr_attendance_email')
            wfh_email_template.send_mail(self.id, force_send=True)
# Send email to manager
        # wfh_email_template = self.env.ref('gms.mail_template_notify_hr_attendance_email')
        # wfh_email_template.send_mail(self.id, force_send=True)

        # return new_record.activity_schedule(
        #     'gms.mail_act_work_from_home_approval',
        #     note=f'New Work from home request created by {new_record.employee_id.name}',
        #     user_id=new_record.employee_id.leave_manager_id.id
        # )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': 'Success',
                'message': 'Work from home has been registered!!!',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
