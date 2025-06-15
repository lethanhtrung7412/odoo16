/** @odoo-module **/
import { registry } from "@web/core/registry";
import time from 'web.time';
var translation = require('web.translation');
var _t = translation._t;
const { Component,useRef, useState} = owl;

export class DomainSelectorTextField extends Component {
    static template = 'FieldDateMultipleDate'

    setup(){
        super.setup();
        this.input = useRef('inputdate')
        this.state = useState({
            date: this.props.value,
            actualDate: []
        })
    }

    _onSelectDateField(ev){
        var dateFormat = time.getLangDateFormat();
       if (dateFormat.includes('MMMM')){
          var dates = dateFormat.toLowerCase()
          var result = dates.replace(/mmmm/g, 'MM');
          dateFormat = result
      }
      else if (dateFormat.includes('MMM')) {
          var dates = dateFormat.toLowerCase()
          var result = dates.replace(/mmm/g, 'M');
          dateFormat = result
      }
      else if(dateFormat.includes('ddd')){
          var dates =new dateFormat.toLowerCase()
          var result = new dates.replace(/ddd/g, 'DD');
          dateFormat = result
      }
     else{
        dateFormat = dateFormat.toLowerCase()
     }
        if (this.input.el){
            $(this.input.el).datepicker({
                multidate: true,
                format: dateFormat,
                multidateSeparator: " - "
            }).on('changeDate',async (ev) => {
                await this.onSelectDate(ev, dateFormat)
            }).trigger('focus');
        }
    }

    async onSelectDate(ev, dateFormat) {
        var newArr = []
        for (let i = 0; i < ev.dates.length; i++) {
            const newDate = moment(ev.dates[i]).format(this.convertToMomentFormat(dateFormat));
            newArr.push(newDate)
        }
        this.state.date = newArr.join(" - ")
        await this.props.update(this.state.date)
    }

    convertToMomentFormat(format) {
        return format.replace(/d{1,2}/g, 'DD')
                 .replace(/m{1,2}/g, 'MM')
                 .replace(/y{2,4}/g, 'YYYY');
    }
}
registry.category("fields").add("multiple_datepicker", DomainSelectorTextField);
