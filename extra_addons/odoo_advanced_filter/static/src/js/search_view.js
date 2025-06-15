odoo.define('@odoo_advanced_filter/js/search_view', async function(require) {
    'use strict';
    let __exports = {};
    const {patchClassMethods, patchInstanceMethods} = require('@mail/utils/utils');
    const ActionModel = require("@web/legacy/js/views/action_model")[Symbol.for("default")];
    const {patch} = require("@web/core/utils/patch");
    var web_client = require('web.web_client');
    patch(ActionModel.prototype, 'web/static/src/js/views/action_model.js', {
        _getQuery() {
            var res = this._super(...arguments);
            var res_domain = res.domain;
            var inline_domain = this.get_inline_search_data();
            res_domain = inline_domain.concat(res_domain);
            res.domain = res_domain;
            return res
        },
        get_inline_search_data() {
            var listRenderer = web_client.listRenderer;
            var all_domains = []
            if (listRenderer && !_.isEmpty(listRenderer.columns)) {
                listRenderer.columns.forEach(function(node) {
                    if (node.domains) {
                        all_domains = all_domains.concat(node.domains);
                    }
                });
            }
            return all_domains;
        }
    });
    return __exports;
});