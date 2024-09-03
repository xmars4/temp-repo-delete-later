# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MrpLunch(models.Model):
    _name = 'mrp.lunch'
    _description = 'Mrp Lunch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    name = fields.Char('Số phiếu', default='/', readonly=True, copy=False)
    from_date = fields.Date('Từ ngày', default=fields.Date.today())
    to_date = fields.Date('Đến ngày', default=fields.Date.today())
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirm', 'Đã tổng hợp'),
        ('calculator', 'Đã tính toán'),
        ('done', 'Đã lên lệnh'),
        ('cancel', 'Hủy')
    ], 'Trạng thái', default='draft', track_visibility='onchange')
    desc = fields.Char('Diễn giải')

    def button_sum(self):
        self.state = 'confirm'

    def button_mat(self):
        self.state = 'calculator'

    def button_push(self):
        self.state = 'done'

    out_line_ids = fields.One2many('mrp.lunch.goods', 'header_id', 'Goods')
    in_line_ids = fields.One2many('mrp.lunch.material', 'header_id', 'Goods')

    @api.model
    def create(self, vals):
        rec = super(MrpLunch, self).create(vals)
        number = self.env['ir.sequence'].next_by_code('con_pro_seq')
        rec.name = number
        return rec


class MrpLunchGoods(models.Model):
    _name = 'mrp.lunch.goods'
    _description = 'Mrp Lunch Goods'

    product_id = fields.Many2one('product.product', 'Món ăn')
    qty = fields.Integer('Tổng số lượng đặt')
    note = fields.Char('Ghi chú')
    header_id = fields.Many2one('mrp.lunch', 'header')


class MrpLunchMaterial(models.Model):
    _name = 'mrp.lunch.material'
    _description = 'Mrp Lunch Material'

    product_id = fields.Many2one('product.product', 'Nguyên liệu')
    uom_id = fields.Many2one('uom.uom', 'Đơn vị tính')
    qty = fields.Float('Tổng số lượng cần')
    onhand = fields.Float('Tồn kho hiện có')
    qty1 = fields.Float('Số lượng khuyến nghị')
    note = fields.Char('Ghi chú')
    header_id = fields.Many2one('mrp.lunch', 'header')
