odoo.define('gms.DateRangeGM', function (require) {
    "use strict";

    const { useModel } = require('web.Model');
    const { Component } =  owl;
    const { LegacyComponent } = require("@web/legacy/legacy_component");
    const ControlPanel = require('web.ControlPanel');
    class DateRangeGM extends Component {
        setup() {
            console.log(this.env)
            this.canDisplay = this.env.searchModel && 
            (this.env.searchModel.resModel === 'hr.attendance.report' || 
             this.env.searchModel.resModel === 'hr.attendance.wfh.report' ||
             this.env.searchModel.resModel === 'hr.leave' ||
             this.env.searchModel.resModel === 'hr.leave.report');
        }

        _onClickDateRangePicker(){

            var self = this;
            $('.btn-apply-daterange').css('display', 'unset');
            let start;
            let end;

            if($('#daterange-input').data('daterangepicker') === undefined){
                start = moment();
                end = moment();
            }
            else{
                start = $('#daterange-input').data('daterangepicker').startDate;
                end = $('#daterange-input').data('daterangepicker').endDate;
            }

            function cb(start, end, label) {
//                $('.result-date-statistic').html(start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD'))
                console.log(start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD'))
            }

            $('#daterange-input').daterangepicker({
                startDate: start,
                endDate: end,
                opens: 'left',
                drops: 'down'
              }, cb);
              cb(start, end);

            $('#daterange-input').data('daterangepicker').show();
            $('#daterange-input').on('apply.daterangepicker', function(ev, picker) {
              self._onApplyData();
            });
        }
        _onApplyData(){
            const field = this.env.searchModel.resModel.includes('hr.attendance') ? 'check_in' : 'date_from';
            const name = this.env.searchModel.resModel.includes('hr.attendance') ? 'Check in' : 'Date from';
            var startDate = $('#daterange-input').data('daterangepicker').startDate;
            var endDate = $('#daterange-input').data('daterangepicker').endDate;
            let attendanceFlagArr = [{
                description: `${name} is between "${startDate.format('DD-MM-YYYY')} and ${endDate.format('DD-MM-YYYY')}"`,
                domain: `[["${field}",'>=','${startDate.format('YYYY-MM-DD')} 00:00:00'],["${field}",'<=','${endDate.format('YYYY-MM-DD')} 23:59:59']]`,
                type: 'filter',
            }]


            this.env.searchModel.createNewFilters(attendanceFlagArr);

        }
    }

    DateRangeGM.template = 'gms.DateRangeGM';

    return DateRangeGM;
});
