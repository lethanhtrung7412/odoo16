from odoo import fields, models, exceptions
import hashlib
from datetime import datetime,time
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class AttendanceRawData(models.Model):
    _name = "hr.attendance.raw.data"
    _description = "Raw Data Records"

    raw_data_id = fields.Char()
    username = fields.Char()
    record_type = fields.Char()
    date = fields.Datetime()
    is_transformed = fields.Boolean(default=False, string="Transformed?")
    attendance_id = fields.Many2one('hr.attendance')
    gmsId = fields.Integer()

    _sql_constraints = [
        ('raw_data_id_unique',
         'unique(raw_data_id)',
         'Choose another value - it has to be unique!')
    ]

    def bulk_create(self, vals_list):
        value = self.create(vals_list)
        return vals_list
    
    def create(self, vals_list):
        updated_val_list = []
        for val in vals_list:
            key = val.get('username', '') + val.get('record_type', '') + val.get('date', '')
            val['raw_data_id'] = hashlib.md5(key.encode()).hexdigest()
            updated_val_list.append(val)

        raw_data_ids = [val.get('raw_data_id') for val in updated_val_list]
        existing_raws = self.search([('raw_data_id', 'in', raw_data_ids)])
        existing_raw_id_set = set()
        for raw_data in existing_raws:
            existing_raw_id_set.add(raw_data['raw_data_id'])

        new_val_list = []
        for val in updated_val_list:
            is_exist = val.get('raw_data_id') in existing_raw_id_set
            if not is_exist:
                new_val_list.append(val)

        new_raws = super(AttendanceRawData, self).create(new_val_list)

        # if len(new_val_list) == 0:
        #     return self.search([('raw_data_id', '=', -1)])

        return existing_raws | new_raws

    def transform_raw_data(self):
        raw_data = self.search([('is_transformed', '=', False)])

        if len(raw_data) == 0:
            return []

        attendance_dict = {}
        employee_id_set = set()
        employee_dict = {}
        transformed_dict = {}
        raw_data_id_list = []

        for data in raw_data:
            raw_data_id_list.append(data.id)
            ttlock_username_arr = data.username.split("_")

            if len(ttlock_username_arr) == 1:
                continue

            employee_id = ttlock_username_arr[1]

            if len(ttlock_username_arr) != 3:
                employee_id = ttlock_username_arr[-1].split(" ")[0]
                ttlock_username_arr.append(" ".join(ttlock_username_arr[-1].split(" ")[1:]))
                ttlock_username_arr[1] = employee_id

            employee_id_set.add(employee_id)
            raw_data_date = data.date

            raw_data_utc_date = pytz.UTC.localize(raw_data_date)

            vn_date = raw_data_utc_date.astimezone(pytz.timezone('Asia/Ho_Chi_Minh')).date()

            # name_arr = ttlock_username_arr[2].strip().split(" ")
            # name = " ".join(name_arr)
            # if name_arr[-1].isdigit():
            #     name = " ".join(name_arr[:-1])

            key = f'{employee_id}@{vn_date}'

            if key not in attendance_dict:
                attendance_dict[key] = [data]
            else:
                attendance_dict[key].append(data)

        employee_list = self.env['hr.employee'].search([('barcode', '=', list(employee_id_set))])

        for employee in employee_list:
            employee_dict[employee.barcode] = employee

        for key, raw_data_list in attendance_dict.items():
            employee_id = key.split("@")[0].split("_")[0]
            employee = employee_dict.get(employee_id)

            if not employee:
                continue
            
            browse_record = self.env['hr.attendance'].search([('key', '=', key)], limit=1)
            urgent_record = self.env['hr.attendance'].search([('barcode', '=', employee_id), 
                                                                ('is_urgent', '=', True),
                                                                ('check_in', '>', datetime.combine(raw_data_list[0].date.date(), time.min)),
                                                                ('check_out', '<', datetime.combine(raw_data_list[-1].date.date(), time.max))], limit=1)
            if browse_record:
                new_raw_data = []
                for raw_data_id_now in browse_record.raw_data_ids:
                    new_raw_data.append((raw_data_id_now))

                for raw_data_id in raw_data_list:
                    new_raw_data.append((raw_data_id))
                
                sort_raw_data = sorted(new_raw_data, key=lambda data: data['date'])
                if browse_record.category == 'work_from_home':
                    info = {
                        'raw_data_ids': [(4, data.id) for data in sort_raw_data]
                    }
                    browse_record.write(info)
                else: 
                    info = {
                        'raw_data_ids': [(4, data.id) for data in sort_raw_data],
                        'check_in': sort_raw_data[0].date,
                        'check_out': sort_raw_data[-1].date
                    }
                    browse_record.write(info)
            elif urgent_record:
                if not urgent_record.request_unit_half:
                    new_raw_data = []
                    for raw_data_id_now in browse_record.raw_data_ids:
                        new_raw_data.append((raw_data_id_now))

                    for raw_data_id in raw_data_list:
                        new_raw_data.append((raw_data_id))
                
                    sort_raw_data = sorted(new_raw_data, key=lambda data: data['date'])
                    info = {
                        'raw_data_ids': [(4, data.id) for data in sort_raw_data],
                    }
                    urgent_record.write(info)
                else:    
                    info = {
                        "key": key,
                        "employee_id": employee.id,
                        "check_in": raw_data_list[0].date,
                        "check_out": None,
                        "time_offset": None,
                        "approval_status": "normal",
                        "missing_time_data": None,
                        "category": "work_at_office",
                        "raw_data_ids": []
                    }

                    sort_raw_data = sorted(raw_data_list, key=lambda data: data['date'])
                    for raw_data_id in sort_raw_data:
                        info['raw_data_ids'].append((4, raw_data_id.id))

                    if len(sort_raw_data) > 1:
                        info["check_out"] = sort_raw_data[-1].date
                        time_offset = sort_raw_data[0].date - sort_raw_data[-1].date
                        time_gap = float(self.env['ir.config_parameter'].sudo().get_param('raw_data.time_gap_raw_data_record', 0))
                        if not time_gap:
                            raise exceptions.ValidationError("Parameter 'raw_data.time_gap_raw_data_record' not exists")
                        if abs(time_offset.total_seconds() / 60) < time_gap:
                            info["missing_time_data"] = True
                            info['approval_status'] = 'missing_data'
                        else:
                            info["missing_time_data"] = False

                    if len(sort_raw_data) == 1:
                        info["check_out"] = info["check_in"]
                        info["missing_time_data"] = True
                        info['approval_status'] = 'missing_data'

                    transformed_dict[key] = info
            else:
                info = {
                    "key": key,
                    "employee_id": employee.id,
                    "check_in": raw_data_list[0].date,
                    "check_out": None,
                    "time_offset": None,
                    "approval_status": "normal",
                    "missing_time_data": None,
                    "category": "work_at_office",
                    "raw_data_ids": []
                }

                sort_raw_data = sorted(raw_data_list, key=lambda data: data['date'])
                for raw_data_id in sort_raw_data:
                    info['raw_data_ids'].append((4, raw_data_id.id))

                if len(sort_raw_data) > 1:
                    info["check_out"] = sort_raw_data[-1].date
                    time_offset = sort_raw_data[0].date - sort_raw_data[-1].date
                    time_gap = float(self.env['ir.config_parameter'].sudo().get_param('raw_data.time_gap_raw_data_record', 0))
                    if not time_gap:
                        raise exceptions.ValidationError("Parameter 'raw_data.time_gap_raw_data_record' not exists")
                    if abs(time_offset.total_seconds() / 60) < time_gap:
                        info["missing_time_data"] = True
                        info['approval_status'] = 'missing_data'
                    else:
                        info["missing_time_data"] = False

                if len(sort_raw_data) == 1:
                    info["check_out"] = info["check_in"]
                    info["missing_time_data"] = True
                    info['approval_status'] = 'missing_data'

                transformed_dict[key] = info

        self.env['hr.attendance'].create(list(transformed_dict.values()))
        raw_data_to_update = self.browse(raw_data_id_list).filtered(lambda record: record.is_transformed == False)
        raw_data_to_update.write({'is_transformed': True})

        return len(raw_data_to_update) | 0
