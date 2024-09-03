# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    x_rate_active = fields.Boolean(string='Payment register manual currency rate', default=False, copy=False)
    x_rate = fields.Float(string='Payment register currency rate', copy=False)
    x_compare_currency = fields.Boolean(string='Is Compare currency', compute='_compute_compare_currency')

    @api.depends('currency_id')
    def _compute_compare_currency(self):
        for record in self:
            if record.currency_id.id == record.company_currency_id.id:
                record.x_compare_currency = True
                record.x_rate_active = False
            else:
                record.x_compare_currency = False

    def _create_payment_vals_from_wizard(self):
        result = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        if self.x_rate_active and self.x_rate != 0:
            result.update({
                'x_rate_active': self.x_rate_active,
                'x_rate': self.x_rate
            })
        return result

    def _init_payments(self, to_process, edit_mode=False):
        payments = super(AccountPaymentRegister, self)._init_payments(to_process, edit_mode)
        if payments.move_id and payments.move_id.x_rate_active and payments.move_id.x_rate:
            payments.move_id.onchange_x_rate()
        return payments

