# -*- coding: utf-8 -*-
import datetime
import pytz
from itertools import groupby
import base64
from io import BytesIO
from xlsxwriter.utility import xl_rowcol_to_cell

from odoo import models, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, config

DEFAULT_WORK_HOUR = 8

# ! Config setup legend - color for WIO / WFH / ...
# ! Should move to model config by working activity type ??
FIX_OFFICE = 'fix_office'
WOA = 'work_at_office'
M_REQUIRED = 'manager_required'
WFH = 'work_from_home'
ACTIVITY_TYPE = {
    FIX_OFFICE: {
        'color': '#5f5f9c',
        'label': 'Fixed Office day',
        'code': 'FO',
    },
    WOA: {
        'color': '#d6bf81',
        'label': 'Work At Office',
        'code': 'WAO',
    },
    M_REQUIRED: {
        'color': '#fcba03',
        'label': 'Manager Require day',
        'code': 'M-Required'
    },
    WFH: {
        'color': '#43d9bd',
        'label': 'Work from home',
        'code': 'WFH'
    },
}

class WorkLocationSummaryXlsx(models.AbstractModel):
    _name = 'report.gms.work_location_summary_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Work Location Summary'

    def _get_logo(self):
        return self.env.company.logo or self.env['res.company']._get_logo()

    def get_employees(self):
        """
        Get employee to export work location summary
        Args:
        Returns:
            hr.employee: recordset employee to export
        """
        # TODO add domain to filter which employee should be exported
        domain = [
            ('barcode', '!=', False),
        ]
        res = self.env['hr.employee'].search(
            domain,
            order='barcode ASC',
        )
        return res

    def get_data(self, employees, date_from, date_to):
        """
            Get work location data

            Args:
                employees (hr.employee): employee recordset
                date_from (datetime.date): time from
                date_to (datetime.date): time to

            Returns:
                list: list report data
            """
        if not employees:
            return []

        user_tz = self.env.user.tz and pytz.timezone(self.env.user.tz) or pytz.utc
        # convert date_from, date_to to datetime with utc timezone offset
        dt_from = user_tz.localize(fields.Datetime.to_datetime(date_from))
        dt_from = dt_from.astimezone(pytz.utc).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        dt_to = user_tz.localize(fields.Datetime.to_datetime(date_to).replace(hour=23, minute=59, second=59))
        dt_to = dt_to.astimezone(pytz.utc).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        sql = f'''
            with att as (
                select * from hr_attendance 
                where
                    (category != 'work_from_home' or (category = 'work_from_home' and approval_status != 'request_cancelled')) and 
                    check_in >= '{dt_from}' and check_out <= '{dt_to}'
            )
            select 
                emp.id, 
                emp.barcode,
                emp.name, 
                emp.department_id,
                att.check_in::TIMESTAMP at time zone 'UTC' at time zone '{user_tz}' as check_in,
                att.check_out::TIMESTAMP at time zone 'UTC' at time zone '{user_tz}' as check_out,
                (att.check_in::TIMESTAMP at time zone 'UTC' at time zone '{user_tz}')::date as att_date,
                case
                    when att.category != 'work_from_home' then att.category
                    when att.category = 'work_from_home' and att.approval_status = 'manager_required' then att.approval_status
                    else att.category
                end as category,
                att.worked_hours
                --att.approval_status
            from hr_employee emp
            left join att on (emp.id = att.employee_id)
            where
                emp.active = True and emp.id in {tuple(employees.ids + [-1])} 
                --att.check_in >= '{dt_from}' and att.check_out <= '{dt_to}'
            order by emp.barcode asc, att.check_in asc
        '''
        self._cr.execute(sql)
        res = self._cr.dictfetchall()
        for k, vals in groupby(res, key=lambda r: (r['barcode'], r['name'], r['department_id'])):
            yield k, vals

    @staticmethod
    def get_data_department_fix_office(departments, date_from, date_to):
        """
        Get department config date for fixed work in office days
        Args:
            departments (hr.department):
            date_from (datetime.date):
            date_to (datetime.date):
        Returns:
            dict[int, set]: Dict[department_id, Set(fix_work_in_office_days)]
        """
        group_dept_period = departments.get_date_range_validity(
            date_from,
            date_to,
        )
        return group_dept_period

    def write_title(self, ws, format_title):
        """
        Write worksheet title
        Args:
            ws (xlsxwriter.worksheet.Worksheet): xlsxwriter worksheet
            format_title:
        Returns
        """
        bin_logo = self._get_logo()
        if bin_logo:
            ws.insert_image(0, 0, 'company', {
                'image_data':  BytesIO(base64.b64decode(bin_logo)),
                'x_scale': 0.4,
                'y_scale': 0.3,
            })
        ws.set_row(0, 20)
        ws.set_row(1, 20)
        ws.write(0, 2, "GIGARION", format_title)
        ws.write(1, 2, "Work Location Summary", format_title)

    @staticmethod
    def write_legend(wb, ws, format_default):
        """
        Write worksheet legend
        Args:
            wb (xlsxwriter.workbook.Workbook): xlsxwriter worksheet
            ws (xlsxwriter.worksheet.Worksheet): xlsxwriter worksheet
            format_default:
        Returns:
            dict
        """
        row = 4
        col = 2

        ws.merge_range(row, col, row, col + 2, 'Legend', format_default)
        legend_format = {}
        for key, setup in ACTIVITY_TYPE.items():
            row += 1
            legend_format[key] = wb.add_format({
                'font_name': 'Times New Roman',
                'font_size': 10,
                'valign': 'vcenter',
                'border': 1,
                'bg_color': setup['color']
            })
            ws.write(row, col, setup['code'], legend_format[key])
            ws.merge_range(row, col + 1, row, col + 2, setup['label'], format_default)
        return legend_format

    @staticmethod
    def write_header(ws, row, date_range, header_style, legend_style):
        # from xlsxwriter.worksheet import Worksheet
        """
        Write worksheet reader
        Args:
            ws (xlsxwriter.worksheet.Worksheet): xlsxwriter worksheet
            row (int): row to write header
            date_range (list[datetime.date])
            header_style:
            legend_style:
        Returns:
            int
        """
        ws.write(row, 0, 'Code', header_style)
        ws.write(row, 1, 'Employee', header_style)
        col = 2
        for d in date_range:
            ws.write(row, col, d.strftime('%d-%b-%Y'), header_style)
            col += 1
        for legend in ['Fixed Day', 'M-Required', 'WFH Register', 'Actual WFH', 'Actual Day', 'Qualified Day']:
            ws.write(row, col, legend, legend_style)
            col += 1
        return row + 1

    def generate_xlsx_report(self, workbook, data, obj):
        """
        Args:
            workbook (xlsxwriter.workbook.Workbook): xlsxwriter worksheet
            data (any):
            obj (gms.work.location.report.wizard):
        """
        obj.ensure_one() # ensure report print from only one wizard
        employees = self.get_employees()
        dept_validity_periods = self.get_data_department_fix_office(
            employees.mapped('department_id'),
            obj.date_from,
            obj.date_to,
        )
        date_ranges = [(obj.date_from + datetime.timedelta(days=delta)) for delta in range((obj.date_to - obj.date_from).days + 1)]
        ws = workbook.add_worksheet("Work Location")
        ws.freeze_panes(0, 2)

        format_config = {
            'font_name': 'Times New Roman',
            'font_size': 10,
            'valign': 'vcenter',
            'border': 1
        }
        format_default = workbook.add_format({
            **format_config,
        })
        format_number = workbook.add_format({
            **format_config,
            'num_format': '#,##0.00'
        })

        header_config = {
            **format_config,
            'bold': True,
            'align': 'left',
            'text_wrap': True,
            'bg_color': '#add8e6',
            'border': 1
        }
        format_header = workbook.add_format(header_config)
        format_header_legend = workbook.add_format({
            **header_config,
            'bg_color': '#9c6f5f',
        })

        format_head = workbook.add_format({
            **format_config,
            'font_size': 18,
            'bold': True,
            'align': 'left',
        })

        # * write title
        self.write_title(ws, format_head)
        legend_format = self.write_legend(workbook, ws, format_default)

        row = 11
        # * writer header
        row = self.write_header(ws, row, date_ranges, format_header, format_header_legend)

        # * Set column width
        ws.set_column(0, 0, width=15)
        ws.set_column(1, 1, width=25)

        format_title = workbook.add_format({
            **format_config,
            'bold': True,
            'align': 'left',
            'text_wrap': True,
            'border': 1
        })
        for emp_data, att_datas in self.get_data(employees, obj.date_from, obj.date_to):
            emp_code, emp_name, emp_dept = emp_data
            ws.write(row, 0, f'{emp_code}', format_title)
            ws.write(row, 1, f'{emp_name}', format_title)
            col = 2

            att_by_date = {
                key: list(atts) for key, atts in groupby(att_datas, lambda l: l['att_date'])
            }
            total_worked_hours = 0 # * sum all hours from WOA & FO

            col_start = xl_rowcol_to_cell(row, col)
            for d in date_ranges:
                # * get location code date from by date grouped att
                # location_at_date is one of:
                # - work_from_home
                # - work_at_office
                # - manager_required
                d_atts = att_by_date.get(d, [])
                location_at_date = set()
                worked_hours_day = 0.0
                for t in d_atts: # ! we can get rid of this for because employee has only one att row one day
                    loc_temp = t['category']
                    location_at_date.add(loc_temp)
                    worked_hours_day += t['worked_hours'] if loc_temp in (FIX_OFFICE, WOA) else 0.0
                loc_type = ', '.join(location_at_date)
                total_worked_hours += worked_hours_day

                # TODO sanitize work_from_home:
                # if work_from_home with status = 'manager_required', means manager requires employee's work_from_home request to work at office
                if emp_dept and d in dept_validity_periods[emp_dept]:
                    loc_type = FIX_OFFICE

                loc_code = ACTIVITY_TYPE.get(loc_type, {'code': loc_type})['code'] # get shortcode from work location type
                cell_format = legend_format.get(loc_type, format_default)
                ws.write(
                    row,
                    col,
                    loc_code,
                    cell_format
                )
                col += 1
            col_end = xl_rowcol_to_cell(row, col - 1)

            cell_fix_office = xl_rowcol_to_cell(row, col)
            ws.write_formula(row, col,
                             f"COUNTIF(${col_start}:${col_end},\"{ACTIVITY_TYPE[FIX_OFFICE]['code']}\")",
                             format_default) # ! Fixed Day
            col += 1

            cell_m_required = xl_rowcol_to_cell(row, col)
            ws.write_formula(row, col,
                             f"COUNTIF(${col_start}:${col_end},\"{ACTIVITY_TYPE[M_REQUIRED]['code']}\")",
                             format_default) # ! M-Required
            col += 1

            ws.write_formula(row, col,
                             f"${cell_m_required} + COUNTIF(${col_start}:${col_end},\"{ACTIVITY_TYPE[WFH]['code']}\")",
                             format_default)  # ! WFH Register
            col += 1

            ws.write_formula(row, col,
                             f"COUNTIF(${col_start}:${col_end},\"{ACTIVITY_TYPE[WFH]['code']}\")",
                             format_default)  # ! Actual WFH
            col += 1

            ws.write_formula(row, col,
                             f"${cell_fix_office} + ${cell_m_required} + COUNTIF(${col_start}:${col_end},\"{ACTIVITY_TYPE[WOA]['code']}\")",
                             format_default) # ! Actual Day
            col += 1

            ws.write(row, col,
                     total_worked_hours / DEFAULT_WORK_HOUR,
                     format_number) # ! Qualified Day
            row += 1
