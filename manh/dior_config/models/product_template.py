# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_available = fields.Float(digits='Product Unit of Measure extra')
    virtual_available = fields.Float(digits='Product Unit of Measure extra')
    x_qty_available_2 = fields.Float(
        'Số tồn đơn vị 2', compute='_compute_quantities_2',
        digits='Product Unit of Measure', compute_sudo=False,
    )
    brand_id = fields.Many2one('product.brand', string='Thương hiệu')
    x_product_id = fields.Many2one('product.product', 'SP/DV liên kết')
    x_product_cv_id = fields.Many2one('product.product', 'SP/DV Chuyển đổi')
    x_qty_conver = fields.Float('Số lương chuyển đổi')
    x_rate_conver = fields.Float('Tỷ lệ quy đổi', help='1 đơn vị của sản phẩn gốc quy đổi ra bao nhiêu số lượng của sản phẩm chuyển đổi')
    x_uom_product_cv = fields.Many2one(related='x_product_cv_id.uom_id')
    x_uom_id = fields.Many2one('uom.uom', string='Đơn vị thứ 2')
    x_rate_conver = fields.Float('Tỷ lệ quy đổi',
                                 help='1 đơn vị của sản phẩn gốc quy đổi ra bao nhiêu số lượng của sản phẩm chuyển đổi')
    _sql_constraints = [('uniq_code', 'UNIQUE(default_code)', 'Mã hàng đã tồn tại!')]



    def get_vals_stock_quant(self, product_id, qty):
        qty_available = self.product_variant_ids[0].qty_available
        vals =  {
            'product_id': product_id.id,
            'product_uom_id': product_id.uom_id.id,
            'inventory_quantity': -qty_available if qty < 0 else qty_available * self.x_rate_conver,
            'location_id': self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1).in_type_id.default_location_dest_id.id,
        }
        if qty<0:
            vals['is_outdated']=True
            vals['inventory_quantity_set']=True
        return vals

    def button_convert(self):
        # Tăng
        quant_u = self.env['stock.quant'].create(self.get_vals_stock_quant(self.x_product_cv_id, 1))
        quant_u.action_apply_inventory()
        # giảm
        product_down = self.product_variant_ids[0]
        quant_d = self.env['stock.quant'].create(self.get_vals_stock_quant(product_down,-1))
        quant_d.action_apply_inventory()


    @api.depends('qty_available')
    def _compute_quantities_2(self):
        for rec in self:
            rec.x_qty_available_2 = rec.qty_available * rec.x_rate_conver


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, values):
        for rec in self:
            if 'x_uom_id' in values:
                invoices = self.env['account.move.line'].search([('product_id', '=', rec.id), ('product_uom_id', '=', rec.x_uom_id.id)], limit=1)
                if invoices:
                    raise ValidationError('Sản phẩm %s không thể thay đổi đơn vị tính thứ 2. đã tồn tại đvt  %s' %(rec.name, rec.x_uom_id.name))
        return super(ProductProduct, self).write(values)