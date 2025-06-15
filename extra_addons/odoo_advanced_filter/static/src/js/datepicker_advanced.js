odoo.define('@odoo_advanced_filter/js/datepicker_advanced', async function(require) {
    'use strict';
    let __exports = {};
    function areEqual(value1, value2) {
        if (value1 && value2) {
            return Number(value1) === Number(value2);
        } else {
            return value1 === value2;
        }
    }
    const {DatePicker} = require("@web/core/datepicker/datepicker");
    const {DateTime} = luxon;
    const DatePickerAdvanced = __exports.DatePickerAdvanced = class DatePickerAdvanced extends DatePicker {
        onDateChange() {
            const [value,error] = this.isPickerChanged ? [this.pickerDate, null] : this.parseValue(this.inputRef.el.value, this.getOptions());
            this.state.warning = value && value > DateTime.local();
            if (error || areEqual(this.date, value)) {
                this.updateInput(this.date);
            } else {
                this.props.onDateTimeChanged(value, this.props.column);
            }
            if (this.pickerDate) {
                this.inputRef.el.select();
            }
        }
    }
    DatePickerAdvanced.props = {
        ...DatePicker.props,
        column: {}
    };
    return __exports;
});
