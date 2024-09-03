# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import AccessError, UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_rate_active = fields.Boolean(string='Purchase manual currency rate', default=False, copy=False)
    x_rate = fields.Float(string='Purchase currency rate', copy=False)
    x_compare_currency = fields.Boolean(string='Is Compare currency', compute='_compute_compare_currency')

    @api.depends('currency_id')
    def _compute_compare_currency(self):
        for record in self:
            if record.currency_id.id == self.env.company.currency_id.id:
                record.x_compare_currency = True
                record.x_rate = False
            else:
                record.x_compare_currency = False

    @api.onchange('x_rate_active')
    def _onchange_x_rate_active(self):
        for record in self:
            record.x_rate = 0

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        res.update({
            'x_rate_active': self.x_rate_active,
            'x_rate': self.x_rate
        })
        return res
