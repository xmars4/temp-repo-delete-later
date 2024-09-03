# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_invoice_line_id = fields.Many2one('account.move.line', string='Line invoice')

    @api.constrains('product_uom')
    def _check_uom(self):
        pass

    def action_confirm(self):
        return super(StockMove, self).action_confirm()

    def _action_confirm(self, merge=True, merge_into=False):
        res = super(StockMove, self)._action_confirm(merge,merge_into)
        for r in res.search([('id', 'in', res.ids),
                             ('x_invoice_line_id', '!=', False),
                             ('x_invoice_line_id.move_id.move_type', '=', 'out_refund')]):
            ivl = r.x_invoice_line_id
            if ivl.id != ivl.x_inv_line_origin_id.id:
                sm_id = self.env['stock.move'].search([('product_id', '=', r.product_id.id),
                                                       ('x_invoice_line_id', '=', ivl.x_inv_line_origin_id.id)])
                if sm_id:
                    stock_value_layer = self.env['stock.valuation.layer'].search([('stock_move_id', '=', sm_id[0].id)])
                    r.price_unit = stock_value_layer.unit_cost
            else:
                r.price_unit = r.product_id.standard_price
        return res

    def _action_done(self, cancel_backorder=False):

        for m in self:
            if m.x_invoice_line_id:
                force_period_date = m.x_invoice_line_id.move_id.invoice_date
                self = self.with_context(
                    force_period_date=force_period_date
                )
                self.write({'date': force_period_date})
        res = super(StockMove, self)._action_done(cancel_backorder)
        for i in self:
            if i.x_invoice_line_id:
                force_period_date = i.x_invoice_line_id.move_id.invoice_date
                self.write({'date': force_period_date})
        return res
        

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        return super(StockMoveLine, self).create(vals_list)