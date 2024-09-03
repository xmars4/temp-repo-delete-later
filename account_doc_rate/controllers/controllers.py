# -*- coding: utf-8 -*-
# from odoo import http


# class AccountDocRate(http.Controller):
#     @http.route('/account_doc_rate/account_doc_rate', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_doc_rate/account_doc_rate/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_doc_rate.listing', {
#             'root': '/account_doc_rate/account_doc_rate',
#             'objects': http.request.env['account_doc_rate.account_doc_rate'].search([]),
#         })

#     @http.route('/account_doc_rate/account_doc_rate/objects/<model("account_doc_rate.account_doc_rate"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_doc_rate.object', {
#             'object': obj
#         })
