# -*- coding: utf-8 -*-
# Copyright MingNe (https://my.mingne.dev/)

import datetime, base64

from dateutil import relativedelta

from odoo import models, fields, api


class GmsWorkLocationReportWizard(models.TransientModel):
    _name = 'gms.work.location.report.wizard'
    _description = 'Wizard to generate work location report'

    date_from = fields.Date(
        string='Date From',
        required=True,
        default=fields.Date.context_today,
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
        default=fields.Date.context_today,
    )

    @api.model
    def default_get(self, fields_list):
        res = super(GmsWorkLocationReportWizard, self).default_get(fields_list)
        td = datetime.date.today()
        first_month_date = td.replace(day=1)
        last_month_date = first_month_date + relativedelta.relativedelta(months=1, days=-1)
        res.update({
            'date_from': first_month_date,
            'date_to': last_month_date,
        })
        return res


    def action_send_time_sheet_report(self):
        """Automation to send time sheet by email"""
        for record in self: # Loop in case of multiple records
            report = self.env.ref('gms.report_gms_work_location_summary_xlsx')
            
            # Get date from and date to from context
            date_from = self.env.context.get('date_from', '1/1/2001')  # Default values if not in context
            date_to = self.env.context.get('date_to', '31/12/2001')

            report_data, report_type = self.env['ir.actions.report'].sudo()._render_xlsx(report, [record.id], data=None)
            data_record = base64.b64encode(report_data)

            ir_values = {
                'name': f'Work Location Summary {date_from} to {date_to}.{report_type}', # Use dates in the name
                'type': 'binary',
                'datas': data_record,
                'store_fname': data_record,
                'mimetype': 'application/vnd.ms-excel',
                'res_model': 'gms.work.location.report.wizard',
                'res_id': record.id,
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)

            if attachment:
                email_template = self.env.ref('gms.mail_send_report')
                email_values = {
                    'email_to': 'trung.le@gigarion.com',  # You might want to make this dynamic
                    'email_cc': False,
                    'scheduled_date': False,
                    'recipient_ids': [],
                    'partner_ids': [],
                    'auto_delete': True,
                }
                email_template.attachment_ids = [(4, attachment.id)]

                # Use date_from and date_to from context
                email_template.with_context(
                    date_from=date_from,
                    date_to=date_to,
                    inv=record
                ).send_mail(record.id, email_values=email_values, force_send=True)

                email_template.attachment_ids = [(5, 0, 0)]  # Remove the attachment from template

    def print_report(self):
        report_action = self.env.ref('gms.report_gms_work_location_summary_xlsx')
        res = report_action.report_action(
            docids=self,
            data=[],
        )
        return res
