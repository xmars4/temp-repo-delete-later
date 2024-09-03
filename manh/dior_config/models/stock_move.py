# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_uom_qty = fields.Float(digits='Product Unit of Measure extra')
    quantity_done = fields.Float(digits='Product Unit of Measure extra')


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    product_uom_qty = fields.Float(digits='Product Unit of Measure extra')
    qty_done = fields.Float(digits='Product Unit of Measure extra')

    x_invoice_id = fields.Many2one('account.move', 'Số chứng từ', related='move_id.x_invoice_line_id.move_id')
    x_date_invoice = fields.Date('Ngày hoá đơn', related='x_invoice_id.invoice_date', store=True)
    x_type = fields.Selection([
        ('in', 'Nhập hàng'),
        ('out', 'Bán hàng'),
        ('kk', 'Kiểm kê')
    ], string='Phương thức', compute='auto_set_type')
    x_partner_id = fields.Many2one('res.partner', 'Đối tác', related='x_invoice_id.partner_id')
    x_cost = fields.Float('Giá', compute='compute_x_cost')
    x_qty = fields.Float('Số lượng', compute='auto_set_type', store=True)

    @api.depends('is_inventory', 'location_id')
    def auto_set_type(self):
        for rec in self:
            if rec.is_inventory:
                rec.x_type = 'kk'
                if rec.location_id.id == 8:
                    rec.x_qty = -rec.qty_done
                else:
                    rec.x_qty = rec.qty_done
            else:
                if rec.location_id.id == 8:
                    rec.x_type = 'out'
                    rec.x_qty = -rec.qty_done
                else:
                    rec.x_type = 'in'
                    rec.x_qty = rec.qty_done

    def compute_x_cost(self):
        for rec in self:
            query = """
                    select svl.unit_cost
                    from stock_move sm
                    left join stock_valuation_layer svl on sm.id = svl.stock_move_id
                    where sm.id = {0}
                    """.format(rec.move_id.id)
            self._cr.execute(query)
            lst = self._cr.dictfetchall()
            if lst:
                rec.x_cost = lst[0]['unit_cost']
            else:
                rec.x_cost = 0
