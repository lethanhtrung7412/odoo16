from odoo import models, fields, api

GMS_USER_FIELDS = ['identification', 'permanent_address', 'children_ids']

class ResUsers(models.Model):
    _inherit = 'res.users'

    identification = fields.Image(string="Identification",related="employee_id.identification", readonly=False, related_sudo=False)
    permanent_address = fields.Char(string='Permanent Address', help="Address on your identification", related="employee_id.permanent_address", readonly=False, related_sudo=False)
    children_ids = fields.One2many(string='Children', related="employee_id.children_ids", readonly=False, related_sudo=False)
    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + GMS_USER_FIELDS

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + GMS_USER_FIELDS

    def _all_owned_dept(self):
        self.ensure_one()
        department_obj = self.env['hr.department']
        own_dept = department_obj.search([
            ('manager_id', '=', self.env.user.employee_id.id),
        ])
        if own_dept:
            return department_obj.search([('child_ids', 'child_of', own_dept.ids)])
        return department_obj
