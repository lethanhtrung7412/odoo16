{
    'name': 'odoo_advanced_filter',
    'application': True,
    'depends': [
        'web',
        'mail',
    ],
    'assets': {
        'web.assets_backend': [
            '/odoo_advanced_filter/static/src/js/*.js',
            '/odoo_advanced_filter/static/src/xml/*.xml',
            '/odoo_advanced_filter/static/src/css/*.scss',
        ]
    },
}
