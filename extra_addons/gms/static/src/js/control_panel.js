

/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { device } from "web.config";


const DateRangeGM = require('gms.DateRangeGM');
const DepartmentDropdown = require('gms.DepartmentDropdown');

if (!device.isMobile) {
    patch(ControlPanel.prototype, "gms", {
        get SearchMenuCustom(){
            return { Component: DateRangeGM, key: 'daterange' }
        },
        get DropdownMenuCustom() {
            return { Component: DepartmentDropdown, key: 'dropdown' }
        }
    });
}

