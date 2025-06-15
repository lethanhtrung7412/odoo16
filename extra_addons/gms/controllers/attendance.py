import json
from odoo import http
from odoo.http import request, Response

class HrAttendance(http.Controller):

    @http.route('/api/attendance', website=True, auth='public', type="http", method=['GET'])
    def all_attendance(self, **kw):
        headers = {'Content-Type': 'application/json'}
        attendance_model = request.env['hr.attendance']
        attendances = attendance_model.search([])
        data = []
        for attendance in attendances:
            # Accessing relevant fields from attendance record
            data.append({
                'id': attendance.id,
                'employee_id': attendance.employee_id.name,
                'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_in else None,
                'check_out': attendance.check_out.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_out else None,
                # Add other relevant fields as needed
            })
        result = {
            "message": "Success",
            "data": data
        }
        return Response(json.dumps(result), headers=headers)
    
    @http.route('/api/time_off', website=True, auth='public', type="http", method=['GET'])
    def all_time_off(self, *kw):
        headers = {'Content-Type': 'application/json'}
        time_off_model = request.env['hr.leave']
        time_offs = time_off_model.search([])
        data = []
        for time_off in time_offs:
            data.append({
                'id': time_off.id,
                'employee_id': time_off.employee_id.name,
                'holiday_type': time_off.holiday_status_id.name,
                'request_date_from': time_off.request_date_from.strftime('%Y-%m-%d %H:%M:%S') if time_off.request_date_from else None,
                'request_date_to': time_off.request_date_to.strftime('%Y-%m-%d %H:%M:%S') if time_off.request_date_to else None
            })

        result = {
            "message": "Success",
            "data": data
        }
        return Response(json.dumps(result), headers=headers)