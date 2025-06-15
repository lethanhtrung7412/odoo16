/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { usePopover } from "@web/core/popover/popover_hook";
import { Component } from "@odoo/owl";

export class redirectEmail extends Component {
    setup(){
        this.actionService = useService("action")
        this.orm = useService("orm");
        this.user = useService("user");
    }

    onClickRedirect() {
        const rec = this.props.record ? this.props.record.data : false;
        const [mailtoPart, params] = rec.mail_value.split('?');
        const email = mailtoPart.split(':')[1];

        // Extract subject and body
        const subject = params.split('&').find(param => param.startsWith('subject=')).split('=')[1];
        const body = params.split('&').find(param => param.startsWith('body=')).split('=')[1];

        window.open('mailto:' +
                    email +
                    '?subject=' +
                    (subject ? window.decodeURIComponent(subject) : '') +
                    '&body=' +
                    (body ? body : ''))
        // console.log(rec)
    }


}
redirectEmail.template = "gms.RedirectTemplate"

registry.category("view_widgets").add("mail_send", redirectEmail);