# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_payment_invoice_id = fields.Many2one('account.payment.invoice', string="Account Payment Invoice")
    x_payment_line_id = fields.Many2one('account.payment.line', string="Account Payment Line")
