# -*- coding: utf-8 -*-


from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError
from copy import deepcopy


class UomUom(models.Model):
    _inherit = 'uom.uom'


    def get_domain_filter(self, domain):
        add_domain = []
        if self._context.get('uom_product', False):
            product_id = self.env['product.product'].browse(self._context.get('uom_product'))
            uom_id = [product_id.uom_id.id, product_id.x_uom_id.id if product_id.x_uom_id else 0]
            if uom_id:
                add_domain += [
                    ['id', 'in', uom_id]
                ]
        if not domain and add_domain:
            domain = deepcopy(add_domain)
        elif add_domain:
            domain.insert(0, '&')
            domain.extend(deepcopy(add_domain))
        return domain


    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        domain = self.get_domain_filter(domain)
        res = super(UomUom, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                      order=order)
        return res


    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = self.get_domain_filter(args)
        res = super(UomUom, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return res