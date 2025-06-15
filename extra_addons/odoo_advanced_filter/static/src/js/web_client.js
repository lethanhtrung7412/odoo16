odoo.define('@odoo_advanced_filter/js/web_client', async function(require) {
    'use strict';
    let __exports = {};
    const {WebClient} = require("@web/webclient/webclient");
    const {patch} = require('web.utils');
    patch(WebClient.prototype, 'web_advanced_search/static/src/js/web_client.js', {
        mounted() {
            odoo.web_client = this;
            this._super(...arguments)
        }
    });
    return __exports;
});