# -*- coding: utf-8 -*-
{
    'name': "account_doc_rate",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'account', 'sale', 'payment'],

    # always loaded
    'data': [
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/sale_order_views.xml',
        'wizard/account_payment_register_views.xml',
        'views/account_payment_views.xml',
    ],
    'license': 'LGPL-3',
}
