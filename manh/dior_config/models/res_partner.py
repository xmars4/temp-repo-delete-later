# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ref = fields.Char(string='Mã', required=True)
    x_gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ')
    ], string='Giới tính')
    x_birth_day = fields.Date('Ngày sinh')
    x_fb = fields.Char('Facebook')

    @api.depends('name', 'ref')
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.ref:
                name = '[' + record.ref + '] ' + name
            res.append((record.id, name))
        return res

    course_line_ids = fields.One2many('res.partner.course', 'partner_id', 'Liệu trình')

    def compute_partner_course(self):
        for rec in self:
            query = """
                    select partner_id, p_id as product_id,
                           sum(sl_mua) as sl_mua,
                           sum(sl_tieu) as sl_tieu,
                           sum(sl_cl) as sl_cl
                    from (
                        select am.partner_id,
                               case when pp2.id is null then aml.product_id else pp2.id end as p_id,
                               sum(case when am.move_type = 'out_invoice' and aml.x_purchase = TRUE then aml.quantity else 0 end) as sl_mua,
                               sum(case when am.move_type = 'out_invoice' and aml.x_work = TRUE then aml.quantity else 0 end) as sl_tieu,
                               sum(case when am.move_type = 'out_invoice' and aml.x_purchase = TRUE then aml.quantity else 0 end) -
                                sum(case when am.move_type = 'out_invoice' and aml.x_work = TRUE then aml.quantity else 0 end) as sl_cl
                        from account_move am
                            left join account_move_line aml on am.id = aml.move_id
                            left join product_product pp on aml.product_id = pp.id
                            left join product_template pt on pp.product_tmpl_id = pt.id
                            left join product_product pp2 on pt.x_product_id = pp2.id
                        where move_type in ('out_invoice', 'out_refund')
                          and am.state = 'posted'
                          and am.partner_id = {0}
                          and aml.product_id is not null
                        group by am.partner_id, aml.product_id, pp2.id
                    ) t0
                    where sl_mua <> 0 or sl_tieu <> 0 or sl_cl <> 0
                    group by partner_id, p_id
                    """.format(rec.id)
            self._cr.execute(query)
            lst = self._cr.dictfetchall()

            cou_obj = self.env['res.partner.course']
            old_obj = cou_obj.search([('partner_id', '=', rec.id)])
            old_obj.unlink()
            for i in lst:
                cou_obj.create({
                    'code': i['product_id'],
                    'qty_purchased': i['sl_mua'],
                    'qty_consumable': i['sl_tieu'],
                    'qty_remain': i['sl_cl'],
                    'partner_id': i['partner_id'],
                })

    def read(self, fields=None, load='_classic_read'):
        self.compute_partner_course()
        return super(ResPartner, self).read(fields=fields, load=load)


class ResPartnerCourse(models.Model):
    _name = 'res.partner.course'

    code = fields.Many2one('product.product', 'Liệu trình đã mua')
    qty_purchased = fields.Integer('Số lượng đã mua')
    qty_consumable = fields.Integer('Số lượng đã làm')
    qty_remain = fields.Integer('Số lượng còn lại')
    partner_id = fields.Many2one('res.partner', 'Khách hàng')
