from odoo import fields, models, api, _

class DayOfWeek(models.Model):
    _name = 'day.of.week'
    _description = 'Day of the Week'

    code = fields.Integer(string="Code")
    name = fields.Char(string='Day Name')


class HrDepartment(models.Model):
    _name = 'hr.department'
    _inherit = 'hr.department'

    fix_day_in_office = fields.Boolean(
        default=False,
        string="Fixed In-office day",
    )
    validity_period = fields.One2many(
        'validity.period',
        'department_id',
        tracking=True,
        cascade=True,
    )
    wfh_day = fields.Integer("Work From Home Day")
    is_manager = fields.Boolean(
        default=True,
        compute='_check_is_editable',
        store=False,
    )
    allow_leader_edit = fields.Boolean(
        default=True,
        compute='_check_is_editable',
        store=False,
    )

    @api.depends('manager_id')
    def _check_is_editable(self):
        child_depts = self.env.user._all_owned_dept()
        is_hr_officer = self.env.user.has_group('hr.group_hr_user')
        is_leader = self.env.user.has_group('gms.group_hr_leader')
        for record in self:
            record.is_manager = True
            record.allow_leader_edit = True
            if is_hr_officer or self.env.is_admin():
                continue

            if is_leader:
                record.allow_leader_edit = False

            if record not in child_depts:
                record.is_manager = False

    def get_date_range_validity(self, date_from, date_to):
        """
        Args:
            date_from (datetime.date): start date
            date_to (datetime.date): end date

        Returns:
            dict[int, set[datetime.date]]: dict of [department_id, set(fix_office_day)]
        """
        # date_to >= a and date_from <= b
        domain = [
            ('department_id', 'in', self.filtered('fix_day_in_office').ids),
            '&',
            ('date_from', '<=', date_to),
            '|',
            ('date_to', '>=', date_from),
            ('date_to', '=', False),
        ]
        valid_periods = self.validity_period.search(
            domain,
            order='date_from asc',
        )

        dept_fix_days = {dep_id: set() for dep_id in self.ids} # do not use method dict.fromkey because it's ref
        for validity in valid_periods:
            dept_fix_days[validity.department_id.id].update(
                validity.get_dates_in_period(date_from, date_to)
            )
            # result.update(validity.get_dates_in_period(date_from, date_to))
        return dept_fix_days
