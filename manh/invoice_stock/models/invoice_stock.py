# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, fields, api, _


class InvoiceStockMove(models.Model):
    _inherit = 'account.move'

    def _get_stock_warehouse_id(self):
        company_id = self.env.context.get('default_company_id', self.env.company.id)
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', company_id)], limit=1
        )
        return warehouse
    def _get_stock_type_ids(self):
        if not self.warehouse_id:
            wh = self._get_stock_warehouse_id()
        else:
            wh = self.warehouse_id
        data = self.env['stock.picking.type'].search([('warehouse_id', '=', wh.id)])
        if self._context.get('default_move_type') in ('out_invoice', 'in_refund'):
            for line in data:
                if line.code == 'outgoing':
                    return line
        if self._context.get('default_move_type') in ('in_invoice', 'out_refund'):
            for line in data:
                if line.code == 'incoming':
                    return line

    picking_count = fields.Integer(string="Count", copy=False)
    invoice_picking_id = fields.Many2one('stock.picking', string="Picking Id", copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', string="Kho",default=_get_stock_warehouse_id, required=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type',
                                      default=_get_stock_type_ids,
                                      help="This will determine picking type of incoming shipment")


    @api.onchange('warehouse_id')
    def onc_warehouse_id(self):
        pk_type = self._get_stock_type_ids()
        self.picking_type_id = pk_type

    def action_stock_move(self):
        # pk_type = self.get_stock_picking_type()
        # self.picking_type_id = pk_type
        if not self.picking_type_id:
            raise UserError(_(
                " Please select a picking type"))
        for order in self:
            if not self.invoice_picking_id or self.invoice_picking_id.state not in ('draft', 'done', ''):
                pick = {}
                if self.picking_type_id.code == 'outgoing':
                    pick = {
                        'picking_type_id': self.picking_type_id.id,
                        'partner_id': self.partner_id.id,
                        'origin': self.name,
                        'location_dest_id': self.partner_id.property_stock_customer.id,
                        'location_id': self.picking_type_id.default_location_src_id.id,
                        'move_type': 'direct'
                    }
                if self.picking_type_id.code == 'incoming':
                    pick = {
                        'picking_type_id': self.picking_type_id.id,
                        'partner_id': self.partner_id.id,
                        'origin': self.name,
                        'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                        'location_id': self.partner_id.property_stock_supplier.id,
                        'move_type': 'direct'
                    }

                picking = self.env['stock.picking'].create(pick)
                self.invoice_picking_id = picking.id
                self.picking_count = len(picking)
                moves = order.invoice_line_ids.filtered(
                    lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)
                move_ids = moves._action_confirm()
                move_ids._action_assign()

    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_ready')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        result['domain'] = [('id', '=', self.invoice_picking_id.id)]
        pick_ids = sum([self.invoice_picking_id.id])
        if pick_ids:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids or False
        return result

    def _reverse_moves(self, default_values_list=None, cancel=False):
        if self.picking_type_id.code == 'outgoing':
            data = self.env['stock.picking.type'].search(
                [('company_id', '=', self.company_id.id), ('code', '=', 'incoming')], limit=1)
            self.picking_type_id = data.id
        elif self.picking_type_id.code == 'incoming':
            data = self.env['stock.picking.type'].search(
                [('company_id', '=', self.company_id.id), ('code', '=', 'outgoing')], limit=1)
            self.picking_type_id = data.id
        reverse_moves = super(InvoiceStockMove, self)._reverse_moves()
        return reverse_moves

    def action_post(self):
        res = super(InvoiceStockMove, self).action_post()
        if self.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
            create_move = self.invoice_line_ids.filtered(
                lambda r: r.product_id.type in ['product', 'consu'])
            if create_move:
                self.action_stock_move()
            if self.invoice_picking_id:
                self.invoice_picking_id.button_validate()
        return res

    def button_draft(self):
        res = super(InvoiceStockMove, self).button_draft()
        for rec in self:
            if rec.invoice_picking_id:
                rec.invoice_picking_id.action_cancel()
                rec.invoice_picking_id = False
        return res


class SupplierInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    x_inv_line_origin_id = fields.Many2one('account.move.line', string='invoice line origin')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', domain="", ondelete="restrict")

    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            price_unit = line.price_unit
            if picking.picking_type_id.code == 'outgoing':
                template = {
                    'name': line.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': picking.picking_type_id.default_location_src_id.id,
                    'location_dest_id': line.move_id.partner_id.property_stock_customer.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'company_id': line.move_id.company_id.id,
                    'picking_type_id': picking.picking_type_id.id,
                    'x_invoice_line_id': line.id,
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                }
            if picking.picking_type_id.code == 'incoming':
                template = {
                    'name': line.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': line.move_id.partner_id.property_stock_supplier.id,
                    'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'company_id': line.move_id.company_id.id,
                    'price_unit': price_unit,
                    'x_invoice_line_id': line.id,
                    'picking_type_id': picking.picking_type_id.id,
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                }
            diff_quantity = line.quantity
            tmp = template.copy()
            tmp.update({
                'product_uom_qty': diff_quantity,
            })
            template['product_uom_qty'] = diff_quantity
            done += moves.create(template)
        return done

    @api.model_create_multi
    def create(self, vals):
        res = super(SupplierInvoiceLine, self).create(vals)
        for r in res:
            if not r.x_inv_line_origin_id:
                r.x_inv_line_origin_id = r.id
        return res

    def copy(self, default=None):
        self.ensure_one()
        default = default or {}
        return super(SupplierInvoiceLine, self).copy(default=default)

    def copy_data(self, default=None):
        res = super(SupplierInvoiceLine, self).copy_data(default=default)
        for r in res:
            if r['x_inv_line_origin_id'] != self.id:
                r['x_inv_line_origin_id'] = self.id
        return res
