# -*- coding: utf-8 -*-
# from odoo import http


# class AccountPaymentUp(http.Controller):
#     @http.route('/account_payment_up/account_payment_up', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_payment_up/account_payment_up/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_payment_up.listing', {
#             'root': '/account_payment_up/account_payment_up',
#             'objects': http.request.env['account_payment_up.account_payment_up'].search([]),
#         })

#     @http.route('/account_payment_up/account_payment_up/objects/<model("account_payment_up.account_payment_up"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_payment_up.object', {
#             'object': obj
#         })
