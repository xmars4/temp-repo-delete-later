# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductBrand(models.Model):
    _name = 'product.brand'

    name = fields.Char('Thương hiệu', required=True)
    note = fields.Char('Ghi chú')

    _sql_constraints = [('unique_name', 'UNIQUE(name)', 'Tên thương hiệu không được trùng!')]

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        # TDE FIXME: should probably be copy_data
        self.ensure_one()
        if default is None:
            default = {}
        if 'name' not in default:
            default['name'] = _("%s (copy)", self.name)
        return super(ProductBrand, self).copy(default=default)
