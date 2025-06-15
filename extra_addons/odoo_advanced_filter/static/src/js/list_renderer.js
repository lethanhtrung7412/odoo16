odoo.define('@odoo_advanced_filter/js/list_renderer', async function(require) {
    'use strict';
    let __exports = {};
    const {DatePicker} = require("@web/core/datepicker/datepicker");
    const {DatePickerAdvanced} = require("@odoo_advanced_filter/js/datepicker_advanced");
    const {ListRenderer} = require("@web/views/list/list_renderer");
    const {_lt} = require("@web/core/l10n/translation");
    const {_t} = require('web.core');
    const {getActiveHotkey} = require("@web/core/hotkeys/hotkey_service");
    const {patch} = require("@web/core/utils/patch");
    const FIELD_TYPES = {
        binary: "binary",
        boolean: "boolean",
        char: "char",
        date: "date",
        datetime: "datetime",
        float: "number",
        id: "id",
        integer: "number",
        html: "char",
        many2many: "char",
        many2one: "char",
        monetary: "number",
        one2many: "char",
        text: "char",
        selection: "selection",
    };
    const FIELD_OPERATORS = {
        binary: [{
            symbol: "!=",
            description: _lt("is set"),
            value: false
        }, {
            symbol: "=",
            description: _lt("is not set"),
            value: false
        }, ],
        boolean: [{
            symbol: "=",
            description: _lt("is"),
        }],
        char: [{
            symbol: "ilike",
            description: _lt("contains")
        }, {
            symbol: "not ilike",
            description: _lt("doesn't contain")
        }, {
            symbol: "=",
            description: _lt("is equal to")
        }, {
            symbol: "!=",
            description: _lt("is not equal to")
        }, {
            symbol: "!=",
            description: _lt("is set"),
            value: false
        }, {
            symbol: "=",
            description: _lt("is not set"),
            value: false
        }, ],
        date: [{
            symbol: "=",
            description: _lt("is equal to")
        }, {
            symbol: "!=",
            description: _lt("is not equal to")
        }, {
            symbol: ">",
            description: _lt("is after")
        }, {
            symbol: "<",
            description: _lt("is before")
        }, {
            symbol: ">=",
            description: _lt("is after or equal to")
        }, {
            symbol: "<=",
            description: _lt("is before or equal to")
        }, {
            symbol: "between",
            description: _lt("is between")
        }, {
            symbol: "!=",
            description: _lt("is set"),
            value: false
        }, {
            symbol: "=",
            description: _lt("is not set"),
            value: false
        }, ],
        datetime: [{
            symbol: "between",
            description: _lt("is between")
        }, {
            symbol: "=",
            description: _lt("is equal to")
        }, {
            symbol: "!=",
            description: _lt("is not equal to")
        }, {
            symbol: ">",
            description: _lt("is after")
        }, {
            symbol: "<",
            description: _lt("is before")
        }, {
            symbol: ">=",
            description: _lt("is after or equal to")
        }, {
            symbol: "<=",
            description: _lt("is before or equal to")
        }, {
            symbol: "!=",
            description: _lt("is set"),
            value: false
        }, {
            symbol: "=",
            description: _lt("is not set"),
            value: false
        }, ],
        id: [{
            symbol: "=",
            description: _lt("is")
        }],
        number: [{
            symbol: "<=",
            description: _lt("less than or equal to")
        }, {
            symbol: "=",
            description: _lt("is equal to")
        }, {
            symbol: "!=",
            description: _lt("is not equal to")
        }, {
            symbol: ">",
            description: _lt("greater than")
        }, {
            symbol: "<",
            description: _lt("less than")
        }, {
            symbol: ">=",
            description: _lt("greater than or equal to")
        }, {
            symbol: "!=",
            description: _lt("is set"),
            value: false
        }, {
            symbol: "=",
            description: _lt("is not set"),
            value: false
        }, ],
        selection: [{
            symbol: "=",
            description: _lt("is")
        }, {
            symbol: "!=",
            description: _lt("is not")
        }, {
            symbol: "!=",
            description: _lt("is set"),
            value: false
        }, {
            symbol: "=",
            description: _lt("is not set"),
            value: false
        }, ],
    };
    var FIELD_CLASSES = {
        char: 'o_list_char',
        float: 'o_list_number',
        integer: 'o_list_number',
        monetary: 'o_list_number',
        text: 'o_list_text',
        many2one: 'o_list_many2one',
    };
    var search_filters_registry = require('web.field_registry');
    var datepicker = require('web.datepicker');
    patch(ListRenderer.prototype, 'web_advanced_search/static/src/js/views/list_renderer.js', {
        setup() {
            this._super();
        },
        getColumnType(column) {
            const {type} = this.fields[column.name];
            return ["float", "integer", "monetary"].includes(type);
        },
        get canShowAdvanceSearch() {
            const activeElement = document.activeElement;
            return !_.has(this.props.list, '__viewType');
        },
        set canShowAdvanceSearch(value) {
            console.log(value)
        },
        getSelectOptions(column) {
            const {type} = this.fields[column.name];
            return FIELD_OPERATORS[FIELD_TYPES[type]];
        },
        isDatetimeColumn(column) {
            const {type} = this.fields[column.name];
            return ["date", "datetime"].includes(type);
        },
        isSearchable(column) {
            const {searchable} = this.fields[column.name];
            return searchable;
        },
        isBooleanColumn(column){
            const {type} = this.fields[column.name];
            return ["boolean"].includes(type);
        },
        getBooleanOptions(column) {
            let select_options = [['true', "Yes"], ['false', "No"]];
            return select_options
        },
        getSelectionOptions(column) {
            const {type} = this.fields[column.name];
            const is_selection = ["selection"].includes(type);
            let select_options = undefined;
            if (is_selection) {
                select_options = this.fields[column.name].selection
            }
            return select_options;
        },
        onchangeDatetimeFrom: function(date_value, column) {
            column.date_start = date_value;
            var domains = []
            if (!this.editable) {
                if (column.date_start) {
                    var field_name = column.name;
                    var value = date_value.toISODate('YYYY-MM-DD');
                    domains.push([field_name, '>=', value]);
                }
                if (column.date_end) {
                    var field_name = column.name;
                    var value = column.date_end.toISODate('YYYY-MM-DD');
                    domains.push([field_name, '<=', value]);
                }
                this.do_advance_search(column, domains);
            }
        },
        onchangeDatetimeTo: function(date_value, column) {
            column.date_end = date_value;
            var domains = []
            if (!this.editable) {
                if (column.date_start) {
                    var field_name = column.name;
                    var value = column.date_start.toISODate('YYYY-MM-DD');
                    domains.push([field_name, '>=', value]);
                }
                if (column.date_end) {
                    var field_name = column.name;
                    var value = date_value.toISODate('YYYY-MM-DD');
                    domains.push([field_name, '<=', value]);
                }
                this.do_advance_search(column, domains);
            }
        },
        _onKeyDownSearch: function(e) {
            const hotkey = getActiveHotkey(e);
            var self = this;
            if (!this.editable) {
                switch (hotkey) {
                case "enter":
                    var target = $(e.target);
                    this._process_filter_search(target)
                    break;
                }
            }
        },
        _process_filter_search: function(target, options) {
            const searchModel = this.env.searchModel;
            options = options || {};
            var value = target.val() || options.value;
            if (!!!value) {
                return
            }
            var field_string = target && target.attr('alt')
            var searchGroupId = target && parseInt(target.attr('searchGroupId'));
            var op_select = target.parent() && target.parent().find('select') && target.parent().find('select')[0];
            var selected_operator = op_select && op_select && op_select.options[op_select.selectedIndex];
            var operator = selected_operator && selected_operator.value || options.operator_value
            var operator_description = selected_operator && selected_operator.text || options.operator_str
            if (searchGroupId) {
                searchModel.deactivateGroup(searchGroupId);
            }
            var field_name = target.attr('data-field');
            const domainArray = []
            domainArray.push([field_name, operator, value]);
            const descriptionArray = [field_string, operator_description, value || ''];
            const preFilters = [{
                description: descriptionArray.join(" "),
                domain: domainArray,
                type: 'filter',
            }];
            target.attr('searchGroupId', searchModel.nextGroupId);
            searchModel.createNewFilters(preFilters);
        },
        do_advance_search: function(column, domains) {
            var new_domains = [];
            const searchModel = this.env.searchModel;
            let descriptionArray;
            let field_string = column.string;
            if (domains.length > 1) {
                var betweens = []
                for (let domain of domains) {
                    betweens.push(domain[2])
                }
                descriptionArray = [field_string, "is between", betweens.join(" of ") || ''];
            }
            if (domains.length == 1) {
                var domain = domains[0]
                descriptionArray = [field_string, domain[1] == "<=" ? "is before" : "is after" || '', domain[2]];
            }
            if (column.searchGroupId) {
                searchModel.deactivateGroup(column.searchGroupId);
            }
            if (descriptionArray) {
                const preFilter = [{
                    description: descriptionArray.join(" "),
                    domain: domains,
                    type: 'filter',
                }]
                column.searchGroupId = searchModel.nextGroupId;
                searchModel.createNewFilters(preFilter);
            } else {
                searchModel.search();
            }
        },
        _onChangedBooleanSearch: function(e, column) {
            if (!this.editable) {
                const searchModel = this.env.searchModel;
                var target = $(e.target);
                var searchGroupId = target && parseInt(target.attr('searchGroupId'));
                var op_select = target.parent() && target.parent().find('select') && target.parent().find('select')[0];
                var selected_operator = op_select && op_select && op_select.options[op_select.selectedIndex];
                var selectedValue = selected_operator && selected_operator.value
                var selectedStr = selected_operator && selected_operator.text
                if (searchGroupId) {
                    searchModel.deactivateGroup(searchGroupId);
                }
                if (!selectedValue) {
                    column.seleted_value = "";
                    searchModel.search();
                    return
                }
                var field_name = target.attr('data-field');
                var field_string = target && target.attr('alt') || `"${field_name}"`
                const domainArray = []
                domainArray.push([field_name, "=", eval(selectedValue)]);
                const descriptionArray = [field_string, "is", selectedStr];
                const preFilter = [{
                    description: descriptionArray.join(" "),
                    domain: domainArray,
                    type: 'filter',
                }];
                column.seleted_value = selectedValue
                target.attr('searchGroupId', searchModel.nextGroupId);
                searchModel.createNewFilters(preFilter);
            }
        },
        _onChangedSelectionSearch: function(e, column) {
            if (!this.editable) {
                const searchModel = this.env.searchModel;
                var target = $(e.target);
                var searchGroupId = target && parseInt(target.attr('searchGroupId'));
                var op_select = target.parent() && target.parent().find('select') && target.parent().find('select')[0];
                var selected_operator = op_select && op_select && op_select.options[op_select.selectedIndex];
                var selectedValue = selected_operator && selected_operator.value
                var selectedStr = selected_operator && selected_operator.text
                if (searchGroupId) {
                    searchModel.deactivateGroup(searchGroupId);
                }
                if (!selectedValue) {
                    column.seleted_value = "";
                    searchModel.search();
                    return
                }
                var field_name = target.attr('data-field');
                var field_string = target && target.attr('alt') || `"${field_name}"`
                const domainArray = []
                domainArray.push([field_name, "=", selectedValue]);
                const descriptionArray = [field_string, "is", selectedStr];
                const preFilter = [{
                    description: descriptionArray.join(" "),
                    domain: domainArray,
                    type: 'filter',
                }];
                console.log(preFilter, "preFilter")
                column.seleted_value = selectedValue
                target.attr('searchGroupId', searchModel.nextGroupId);
                searchModel.createNewFilters(preFilter);
            }
        }
    })
    ListRenderer.InputField = "odoo_advanced_filter.InputField";
    ListRenderer.DatetimeField = "odoo_advanced_filter.DatetimeField";
    ListRenderer.SelectionField = "odoo_advanced_filter.SelectionField";
    ListRenderer.BooleanField = "odoo_advanced_filter.BooleanField";
    ListRenderer.components = {
        ...ListRenderer.components,
        DatePicker: DatePicker,
        DatePickerAdvanced: DatePickerAdvanced
    }
    ListRenderer.defaultProps = {
        ...ListRenderer.defaultProps,
        canShowAdvanceSearch: false
    };
    return __exports;
});


odoo.define(`odoo_advanced_filter.ListRenderer`, async function(require) {
    return require('@odoo_advanced_filter/js/list_renderer')[Symbol.for("default")];
});