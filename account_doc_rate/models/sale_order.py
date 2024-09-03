# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_rate_active = fields.Boolean(string='Sale manual currency rate', default=False, copy=False)
    x_rate = fields.Float(string='Sale currency rate', copy=False)

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'x_rate_active': self.x_rate_active,
            'x_rate': self.x_rate
        })
        return res

