# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'template_anhdior',
    'category': 'Hidden',
    'version': '1.0',
    'description': """

""",
    'depends': ['base', 'account', 'dior_config', 'account_payment_up'],
    'auto_install': True,
    'data': [
        'data/report_layout.xml',
        'views/report_templates.xml',
        'views/report_invoice.xml',
        'views/report_invoice_sale.xml',
        'views/acccount_invoice.xml',
    ],
    'bootstrap': True,  # load translations for login screen,
    'license': 'LGPL-3',
}
