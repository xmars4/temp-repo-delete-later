# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo.tools.misc import formatLang, format_date

INV_LINES_PER_STUB = 9


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payment_vals_from_wizard(self):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        val_invoice_lines = [(0, 0, {
                'move_id': self._context.get('active_id') if self._context.get('active_id') else None,
                'amount': self.amount,
                'selected': True
            })]
        res.update({
            'x_payment_bank': True if self.journal_id.type == 'bank' else False,
            'x_payment_type': 'inv_auto',
            'x_payment_invoice_ids': val_invoice_lines
        })
        return res
