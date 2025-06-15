from odoo import models, fields


class RawDataImportInfo(models.TransientModel):
    _name = 'raw.data.import.info'
    _description = 'Raw data importing info'

    start_date = fields.Date('Start date', required=True)
    end_date = fields.Date('End date', required=True)

    def action_import_data(self):
        self.env['hr.attendance.raw.data'].import_raw_data(start_date=self.start_date, end_date=self.end_date)
