from odoo import fields, models, api

class HrEmployee(models.Model):
    _inherit = ['hr.employee']

    barcode = fields.Char(groups='hr_attendance.group_hr_attendance')
    work_project = fields.Many2many('hr.department', string='Working Projects', store=True)
    identification = fields.Image(string='Identification',store=True,tracking=True)
    permanent_address = fields.Char(string='Permanent Address', help="Address on your identification", store=True, groups="hr.group_hr_user")
    children_ids = fields.One2many('hr.employee.children', 'employee_id', string='Children', store=True, groups="hr.group_hr_user")
    
    @api.onchange('children')
    def _onchange_nums_of_children(self):
        if self.children >= 0:
            existing_children = len(self.children_ids)
            child_lines = self.children_ids
            if self.children > existing_children:
                # Add new children lines
                for i in range(self.children - existing_children):
                    child_lines += self.children_ids.new({'name': f'Child {existing_children + i + 1}'})
            elif self.children < existing_children:
                # Remove excess children lines
                self.children_ids = child_lines[:self.children]

class HrEmployeePublic(models.Model):
    _inherit = ['hr.employee.public']

    barcode = fields.Char(readonly=True)
    permanent_address = fields.Char(string='Permanent Address', help="Address on your identification", save=True)

class Children(models.Model):
    _name = 'hr.employee.children'
    _description = 'Employee Children'

    name = fields.Char(string='Name', required=True)
    birthdate = fields.Date(string='Birthdate', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')