from odoo import http
from odoo.http import request

class CustomEmailController(http.Controller):

    @http.route('/api/custom_send_email',website=False, type='json', auth='none', methods=['POST'])
    def send_email(self, **post):
        value = request.get_json_data()
        subject = value.get('subject')
        body = value.get('body')
        email_to = value.get('email_to')
        email_from = value.get('email_from')
        
        if not (subject and body and email_to and email_from):
            return {'status': 'error', 'message': 'Missing parameters'}
        
        # Create and send email
        mail = request.env['mail.mail'].sudo().create({
            'subject': subject,
            'body_html': body,
            'email_from': email_from,
            'email_to': email_to,
        })
        mail.send()
        
        return {'status': 'success', 'message': 'Email sent'}
