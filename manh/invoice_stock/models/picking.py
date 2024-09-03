# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        self = self.with_context(
            skip_immediate=True,
            skip_sms=True,
        )

        for picking in self:
            for move in picking.move_lines.filtered(lambda x: not x.move_line_ids):
                self.env['stock.move.line'].create(
                    {'company_id': move.company_id.id,
                     'picking_id': move.picking_id.id,
                     'move_id': move.id,
                     'product_id': move.product_id.id,
                     'location_id': move.location_id.id,
                     'location_dest_id': move.location_dest_id.id,
                     'product_uom_id': move.product_uom.id,
                     'qty_done': move.product_uom_qty})
            # picking.move_lines._set_quantities_to_reservation()
            for move in picking.move_lines:
                for move_line in move.move_line_ids:
                    move_line.qty_done = move.product_uom_qty
                    # move_line.product_uom_qty = move.product_uom_qty

        res = super(StockPicking, self).button_validate()
        for p in self:
            date_done = None
            if p.move_lines:
                date_done = p.move_lines[0].date
            p.write({'date_done': date_done or fields.Datetime.now(), 'priority': '0'})
        return res

    def action_cancel(self):
        quant_obj = self.env['stock.quant']
        account_move_obj = self.env['account.move']
        for picking in self:
            if picking.state == 'done':
                account_moves = picking.move_lines
                for move in account_moves:
                    if move.state == 'cancel':
                        continue
                    landed_cost_rec = []
                    try:
                        landed_cost_rec = self.env['stock.landed.cost'].search(
                            [('picking_ids', '=', picking.id), ('state', '=', 'done')])
                    except:
                        pass

                    if landed_cost_rec:
                        raise ValidationError(
                            'This Delivery is set in landed cost record %s you need to delete it fisrt then you can cancel this Delivery' % ','.join(
                                landed_cost_rec.mapped('name')))

                    if move.state == "done" and move.product_id.type == "product":
                        for move_line in move.move_line_ids:
                            quantity = move_line.product_uom_id._compute_quantity(move_line.qty_done,
                                                                                  move_line.product_id.uom_id)
                            quant_obj._update_available_quantity(move_line.product_id, move_line.location_id, quantity,
                                                                 move_line.lot_id)
                            quant_obj._update_available_quantity(move_line.product_id, move_line.location_dest_id,
                                                                 quantity * -1, move_line.lot_id)
                    if move.procure_method == 'make_to_order' and not move.move_orig_ids:
                        move.state = 'waiting'
                    elif move.move_orig_ids and not all(
                            orig.state in ('done', 'cancel') for orig in move.move_orig_ids):
                        move.state = 'waiting'
                    else:
                        move.state = 'confirmed'
                    siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
                    if move.propagate_cancel:
                        # only cancel the next move if all my siblings are also cancelled
                        if all(state == 'cancel' for state in siblings_states):
                            move.move_dest_ids._action_cancel()
                    else:
                        if all(state in ('done', 'cancel') for state in siblings_states):
                            move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                        move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
                    move.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
                    account_moves = account_move_obj.search([('stock_move_id', '=', move.id)])
                    valuation = move.stock_valuation_layer_ids
                    valuation and valuation.sudo().unlink()
                    if account_moves:
                        for account_move in account_moves:
                            account_move.button_cancel()
                            account_move.mapped('line_ids').remove_move_reconcile()
                        account_moves.with_context(force_delete=True).unlink()
        res = super(StockPicking, self).action_cancel()
        return res
