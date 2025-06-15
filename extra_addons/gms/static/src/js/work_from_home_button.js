/** @odoo-module */
import {ListController} from "@web/views/list/list_controller";
import {registry} from '@web/core/registry';
import {listView} from '@web/views/list/list_view';
import {useService} from "@web/core/utils/hooks";

const { onWillStart } = owl;

export class AttendanceListController extends ListController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.user = useService("user");
        // session.user_has_group
        this.showExport = true;
        onWillStart(async () => {
          var res = await this.user.hasGroup('hr_attendance.group_hr_attendance_user')
          this.showExport = res;
          // return res
      })
    }

    // async isShown() {
    //   var res = await this.user.hasGroup('hr_attendance.group_hr_attendance_user')
    //   console.log("come here", res)
    //   return res;
    // }

    OnTestClick() {
        this.actionService.doAction({
          type: 'ir.actions.act_window',
          res_model: 'hr.attendance.work.from.home',
          name:'New WFH register',
          view_mode: 'form',
          view_type: 'form',
            views: [[false, 'form']],
          target: 'new',
          res_id: false,
            context: {'approval_status': 'normal','raw_data_ids':[]}
      });
    }

    OnCreateNewAttendance() {
        this.actionService.doAction({
          type: 'ir.actions.act_window',
          res_model: 'hr.attendance',
          name:'New Attendance',
          view_mode: 'form',
          view_type: 'form',
            views: [[false, 'form']],
          target: 'new',
          res_id: false,
      });
    }

    OnUrgentClick() {
      this.actionService.doAction({
        type: 'ir.actions.act_window',
        res_model: 'hr.attendance.work.from.home',
        name:'Urgent WFH request',
        view_mode: 'form',
        view_type: 'form',
        views: [[false, 'form']],
        target: 'new',
        res_id: false,
          context: {'default_is_urgent': true,'raw_data_ids':[]}
      });
    }

    OnExportTimeSheet() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'gms.work.location.report.wizard',
            name: 'Work Location Summary',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: false,
        })
    }
}

registry.category("views").add("button_wfh", {
    ...listView,
    Controller: AttendanceListController,
    buttonTemplate: "button_wfh_create.ListView.Buttons",
});