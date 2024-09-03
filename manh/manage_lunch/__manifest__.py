# -*- coding: utf-8 -*-

{
    'name': "Lunch Management Additional",

    'summary': """
        This module will help you manage lunch of company""",

    'description': """
        
    """,

    'author': "CTWW",
    'category': 'Stock',
    'version': '15.0.1.0.1',
    'depends': ['stock', 'mrp', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_lunch.xml',
    ],
    'demo': [
    ],
    'post_init_hook': None,
    'installable': True,
}
