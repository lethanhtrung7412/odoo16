# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': 'Multiple DatePicker Widget',
    'version': '16.0.1.0.2',
    'summary': 'Widget for picking multiple dates',
    'description': 'Widget for picking multiple dates',
    'category': 'Tools',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'web'],
    'assets': {
        'web.assets_backend': {
            'https://cdn.jsdelivr.net/npm/moment@2.29.4/min/moment.min.js',
            '/multiple_datepicker_widget/static/src/css/datepicker_widget.css',
            '/multiple_datepicker_widget/static/src/js/lib/bootstrap-datepicker.min.js',
            '/multiple_datepicker_widget/static/src/js/multiple_date_picker_widget.js',
            '/multiple_datepicker_widget/static/src/xml/datepicker_widget.xml',
        },
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
