# -*- coding: utf-8 -*-

{
    'name': "Dior Config",

    'summary': """
        This module will help you manage Dior Config of company""",

    'description': """
        
    """,

    'author': "ManhNT",
    'category': 'Uncategorized',
    'version': '15.0.1.0.1',
    'depends': ['base', 'stock', 'account', 'mrp', 'stock_account', 'sale', 'purchase',
                'account_followup', 'account_auto_transfer', 'account_asset', 'account_accountant', 'account_reports'],
    'data': [
        'data/data.xml',
        'data/data2.xml',
        'security/sercurity.xml',
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/product_brand.xml',
        'views/product_template.xml',
        'views/account_move.xml',
        'views/edit_menu.xml',
        'views/res_config.xml',
        'views/report_stock_value.xml',
        'views/stock_move.xml',
    ],
    'demo': [
    ],
    'post_init_hook': None,
    'installable': True,
}
