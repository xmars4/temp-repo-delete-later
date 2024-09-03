# -*- coding: utf-8 -*-
{
    'name': "Account Payment",
    'summary': """
    """,
    'author': 'THGDX',
    'website': 'http://thgdx.vn',
    'category': 'Account Payment',
    'version': '0.1',
    'depends': ['base', 'account', 'account_payment', 'account_accountant', 'account_doc_rate'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/account_payment_views.xml',
        'views/account_payment_cash_out_views.xml',
        'views/account_payment_cash_in_views.xml',
        'views/account_payment_bank_in_views.xml',
        'views/account_payment_bank_out_views.xml',
        'views/account_payment_internal_views.xml',
        'views/account_payment_menuitem.xml',
        'views/report_payment_bills.xml',
    ],
    'license': 'LGPL-3',
}
