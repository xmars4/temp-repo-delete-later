# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Stockquant(models.Model):
    _inherit = 'stock.quant'

    quantity = fields.Float(digits='Product Unit of Measure extra')