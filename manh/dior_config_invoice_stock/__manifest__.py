# -*- coding: utf-8 -*-
{
    'name': "diorConfigInvoiceStock",
    'version': '15.0.1.0.0',
    'summary': """""",
    'description': """""",
    'author': "",
    'live_test_url': '',
    'company': '',
    'website': "",
    'category': 'stock',
    'depends': ['base', 'product', 'stock', 'invoice_stock', 'dior_config'],
    'data': [
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': True,
    'application': False,
    'post_init_hook': '_edit_rounding',

}
