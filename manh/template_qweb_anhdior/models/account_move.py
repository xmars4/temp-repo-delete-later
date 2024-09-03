# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    amount_pay_cash = fields.Monetary('Tiền đã trả tiền mặt', compute='get_amount_payment_cash', store=True)
    amount_pay_bank = fields.Monetary('Tiền đã trả tiền ngân hàng', compute='get_amount_payment_bank', store=True)
    x_payment_invoice_ids = fields.One2many('account.payment.invoice', 'move_id', 'Thanh toán',
                                            domain="[('state', '=', 'post')]")
    x_date = fields.Datetime(string='Ngày lên phiếu', default=fields.Datetime.now, required=True, readonly=True,
                             states={'draft': [('readonly', False)]})

    @api.onchange('x_date')
    def onc_date(self):
        self.invoice_date = self.x_date
        self.date = self.x_date

    def get_phone_partner(self):
        return self.partner_id.phone or self.partner_id.mobile or ''

    @api.depends('invoice_payments_widget')
    def get_amount_payment_cash(self):
        for rec in self:
            payment = self.env['account.payment.invoice'].search(
                [('move_id', '=', rec.id), ('payment_id.journal_id.type', '=', 'cash')])
            amount = sum(p.amount for p in payment) or 0
            rec.amount_pay_cash = amount

    @api.depends('invoice_payments_widget')
    def get_amount_payment_bank(self):
        for rec in self:
            payment = self.env['account.payment.invoice'].search(
                [('move_id', '=', rec.id), ('payment_id.journal_id.type', '=', 'bank')])
            amount = sum(p.amount for p in payment) or 0
            rec.amount_pay_bank = amount


    def get_amount_word(self):
        payment = self.x_payment_invoice_ids.filtered(lambda r: r.payment_id.state == 'posted')
        amount = sum(p.amount for p in payment) or 0
        if amount == 0:
            return '---'
        utility_obj = self.env['hcsv.utility']
        amount_word = utility_obj.convert_amount_to_words(amount=amount,
                                                          currency=self.currency_id).capitalize() or '---'
        return amount_word


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def get_price_discount(self):
        a = self.price_unit - (self.price_unit * self.discount / 100)
        return a
