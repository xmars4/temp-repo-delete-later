# -*- coding: utf-8 -*-

from . import models
from odoo import api, SUPERUSER_ID, _, tools


def _edit_rounding(cr, registry):
    """chuyển đổi rounding từ 0.001 -> 0.00001"""

    env = api.Environment(cr, SUPERUSER_ID, {})
    uom = env['uom.uom'].search([])
    uom.write({'rounding': 0.00001})