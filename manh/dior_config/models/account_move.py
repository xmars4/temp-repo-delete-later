# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree
import json
from datetime import datetime, timedelta


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_purchase = fields.Boolean('Mua LT')
    x_work = fields.Boolean('Làm LT')
    x_bom = fields.Boolean('Có định mức', compute='get_bom_from_product_id')
    x_user_id = fields.Many2one('res.users', 'NVKD', default=lambda self: self.env.user)
    x_count = fields.Char('Đã làm')
    x_count_current = fields.Char('Lần hiện tại')

    @api.depends('product_id')
    def get_bom_from_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.x_bom = True if rec.product_id.bom_count > 0 else False
            else:
                rec.x_bom = False

    @api.onchange('product_id', 'partner_id', 'quantity')
    def get_number_of_service(self):
        course_obj = self.env['res.partner.course']
        for rec in self:
            if rec.partner_id and rec.product_id.detailed_type in ('consu', 'service'):
                c = course_obj.search([('partner_id', '=', rec.partner_id.id), ('code', '=', rec.product_id.id)])
                if c:
                    rec.x_count = str(c.qty_consumable) + '/' + str(c.qty_purchased)
                    if rec.quantity == 1:
                        rec.x_count_current = 'lần ' + str(c.qty_consumable + 1) + '/' + str(c.qty_purchased)
                    elif rec.quantity > 1:
                        rec.x_count_current = 'lần ' + str(c.qty_consumable + 1) + '/' + str(
                            c.qty_purchased) + ' --> ' + \
                                              'lần ' + str(round(c.qty_consumable + rec.quantity)) + '/' + str(
                            c.qty_purchased)
                    else:
                        rec.x_count_current = ''
                else:
                    rec.x_count = ''
                    rec.x_count_current = ''
            else:
                rec.x_count = ''
                rec.x_count_current = ''

    @api.onchange('x_work')
    def onchange_x_work_to_price(self):
        if self.x_work:
            self.price_unit = 0


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_phone = fields.Char('Số điện thoại', related='partner_id.phone')

    x_discount_total = fields.Monetary(string='C/k Tổng', currency_field='currency_id')
    x_discount_move_id = fields.Many2one('account.move', string='Bút toán chiết khấu')
    x_photo_giveaway = fields.Boolean(string='Công ty tặng ảnh sau 3 tháng.')

    def action_post(self):
        res = super(AccountMove, self).action_post()
        acc_discount_id = self.env["ir.config_parameter"].sudo().get_param("dior_config.discout_account_id")
        for rec in self:
            rec.partner_id.compute_partner_course()
            if rec.move_type in ('out_invoice') and rec.x_discount_total:
                account_move = self.env['account.move']
                vals = {'move_type': 'entry',
                        'journal_id': account_move._get_default_journal().id,
                        'currency_id': account_move._get_default_currency().id,
                        'ref': rec.name,
                        'line_ids': [(0, 0, {'account_id': int(acc_discount_id),
                                             'partner_id': rec.partner_id.id,
                                             'debit': rec.x_discount_total,
                                             }),
                                     (0, 0, {'account_id': rec.partner_id.property_account_receivable_id.id,
                                             'partner_id': rec.partner_id.id,
                                             'credit': rec.x_discount_total,
                                             })
                                     ]
                        }
                am = account_move.create(vals)
                rec.x_discount_move_id = am
                am.post()
        return res

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        for rec in self:
            rec.partner_id.compute_partner_course()
            if rec.x_discount_move_id:
                rec.x_discount_move_id.button_draft()
                # rec.unlink()
        return res

    @api.onchange('line_ids.product_id', 'partner_id', 'line_ids.quantity')
    def get_number_of_service(self):
        course_obj = self.env['res.partner.course']
        for r in self:
            for rec in r.line_ids:
                if r.partner_id and rec.product_id.detailed_type in ('consu', 'service'):
                    c = course_obj.search([('partner_id', '=', r.partner_id.id), ('code', '=', rec.product_id.id)])
                    if c:
                        rec.x_count = str(c.qty_consumable) + '/' + str(c.qty_purchased)
                        if rec.quantity == 1:
                            rec.x_count_current = 'lần ' + str(c.qty_consumable + 1) + '/' + str(c.qty_purchased)
                        elif rec.quantity > 1:
                            rec.x_count_current = 'lần ' + str(c.qty_consumable + 1) + '/' + str(
                                c.qty_purchased) + ' --> ' + \
                                                  'lần ' + str(round(c.qty_consumable + rec.quantity)) + '/' + str(
                                c.qty_purchased)
                        else:
                            rec.x_count_current = ''
                    else:
                        rec.x_count = ''
                        rec.x_count_current = ''
                else:
                    rec.x_count = ''
                    rec.x_count_current = ''

    def _unlink_forbid_parts_of_chain(self):
        pass

    x_check_lock = fields.Boolean(compute='get_field_lock')

    @api.depends('create_date')
    def get_field_lock(self):
        try:
            h = int(self.env["ir.config_parameter"].sudo().get_param("dior.house_lock_invoice"))
        except:
            h = 24
        for r in self:
            time_lock = r.create_date + timedelta(hours=h)
            if fields.Datetime.now() >= time_lock:
                r.x_check_lock = True
            else:
                r.x_check_lock = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMove, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                       submenu=submenu)
        doc = etree.XML(res['arch'])
        if self.env.context.get('multiple_approve', False):
            if view_type == 'form':
                node = doc.xpath("//form")[0]
                node.set("create", 'false')
                node.set("edit", 'false')
                node.set("delete", 'false')
            res['arch'] = etree.tostring(doc, encoding='unicode')
        if not self.user_has_groups('dior_config.group_edit_invoice') and view_type == 'form':
            for field in res['fields']:
                for node in doc.xpath("//field[@name='%s']" % field):
                    node.set("readonly", "1")
                    modifiers = json.loads(node.get("modifiers"))
                    readonly = json.loads(node.get("modifiers")).get('readonly', False)
                    type_readonly = type(json.loads(node.get("modifiers")).get('readonly', False))
                    if readonly:
                        if not type_readonly is bool:
                            modifiers.update({'readonly': f"['|',['x_check_lock', '!=', False], {str(readonly[0])}]"})
                    else:
                        modifiers.update({'readonly': "[['x_check_lock', '!=', False]]"})
                    node.set("modifiers", json.dumps(modifiers))
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def unlink(self):
        """Overridden method to add validation before delete the history."""
        for r in self:
            if r.x_check_lock and not self.user_has_groups('dior_config.group_edit_invoice'):
                raise UserError(_("Bạn không có quyền xoá tài liệu quá thời gian quy định"))
        return super(AccountMove, self).unlink()

    def button_cancel(self):
        for r in self:
            if r.x_check_lock and not self.user_has_groups('dior_config.group_edit_invoice'):
                raise UserError(_("Bạn không có quyền huỷ tài liệu quá thời gian quy định"))
        return super(AccountMove, self).button_cancel()

    def button_draft(self):
        for r in self:
            if r.x_check_lock and not self.user_has_groups('dior_config.group_edit_invoice'):
                raise UserError(_("Bạn không có quyền đưa tài liệu về dự thảo khi quá thời gian quy định"))
        return super(AccountMove, self).button_draft()
