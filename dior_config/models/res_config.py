# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_discout_account_id = fields.Many2one('account.account', string="Tài toản chiết khấu tổng invoice", config_parameter='dior_config.discout_account_id')