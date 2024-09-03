# -*- coding: utf-8 -*-


{
    "name": "Pdf Print Preview",
    "summary": """""",
    "version": "15.0.1",
    "description": """
     
    """,    
    "author": "",
    "maintainer": "",
    "license" :  "",
    "website": "",
    "images": [""],
    "category": "web",
    "depends": [
        "base",
        "web",
    ],
    "data": [
        "views/res_users.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "print_report_preview/static/src/css/style.css",
            "print_report_preview/static/src/js/user_menu_items.js",
            "print_report_preview/static/src/js/print_report_preview.js",
            "print_report_preview/static/src/js/report_preview_dialog.js",            
        ],
        "web.assets_qweb": [
            "print_report_preview/static/src/xml/*.xml",
        ],
    },
    "installable": True,
    "application": True,
    "price"                :  20,
    "currency"             :  "EUR",
    "pre_init_hook"        :  "pre_init_check",
}
