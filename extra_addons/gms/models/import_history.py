from odoo import fields, models
from odoo.addons.base_import.models import base_import
import datetime


class ImportFile(base_import.Import):
    _inherit = "base_import.import"

    def execute_import(self, fields, columns, options, dryrun=False):
        import_history = self.env['hr.attendance.import.history']
        # file_data = self.file.decode('utf-8')
        try:
            input_file_data, import_fields = self._convert_import_data(fields, options)
            # Parse date and float field
            input_file_data = self._parse_import_data(input_file_data, import_fields, options)
        except base_import.ImportValidationError as error:
            return {'messages': [error.__dict__]}
        # Count the number of rows in the CSV file
        # total_records = len(list(file_data))
        import_history.create({
            "date_import": datetime.datetime.now(),
            "file_name": self.file_name,
            "total_record": len(input_file_data)
        })
        return super(ImportFile, self).execute_import(fields, columns, options, dryrun)


class ImportHistory(models.Model):
    _name = "hr.attendance.import.history"
    _description = "Import History"

    date_import = fields.Datetime()
    file_name = fields.Char()
    total_record = fields.Integer()
