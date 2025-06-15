odoo.define('gms.DepartmentDropdown', function (require) {
    "use strict"

    const { Component, useState, onWillStart } =  owl;
    const { Dropdown } = require("@web/core/dropdown/dropdown");
    const { DropdownItem } = require("@web/core/dropdown/dropdown_item");
    const { useService } = require('@web/core/utils/hooks')
    
    class DepartmentDropdown extends Component {
        setup(){
            this.orm = useService("orm")
            this.state = useState({
                departmentList: [],
            })

            onWillStart(async () => {
                await this.getAllDepartment()
            })
        }

        changeDepartmentFilter(option) {
            let flagArr = [{
                description: `Department is contains "${option.name}"`,
                domain: ['|', ['department_id.id', '=', `${option.id}`], ['department_id.parent_id.id', '=', `${option.id}`]],
                type: 'filter',
            }]
            this.env.searchModel.createNewFilters(flagArr);
        }

        async getAllDepartment() {
            this.state.departmentList = await this.orm.searchRead('hr.department', [], ['name', 'id'])
        }

        
    }

    DepartmentDropdown.template = 'gms.DepartmentDropdown'
    DepartmentDropdown.components = { Dropdown, DropdownItem }

    return DepartmentDropdown;
})