/** @odoo-module */
import {ListController} from "@web/views/list/list_controller";
import {registry} from '@web/core/registry';
import {listView} from '@web/views/list/list_view';
import {useService} from "@web/core/utils/hooks";

export class RawDataListController extends ListController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notificationService = useService("notification");
    }

    OnTransformClick() {
        this.orm.call("hr.attendance.raw.data", "transform_raw_data", [[]])
            .then(result => {
                if (result > 0) {
                    return this.notificationService.add(`${result} record have been transformed`, {
                        "type": "success",
                        "title": "Success"
                    })
                } else {
                    return this.notificationService.add(`There is no valid record to transform`, {
                        "type": "warning",
                        "title": "Warning"
                    })
                }
            });

    }
}

registry.category("views").add("button_in_tree", {
    ...listView,
    Controller: RawDataListController,
    buttonTemplate: "button_transform.ListView.Buttons",
});