# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ReportStockValue(models.TransientModel):
    _name = 'report.stock.value'


    product = fields.Char('Sản phẩm')
    product_code = fields.Char('Mã sản phẩm')
    uom = fields.Char('ĐVT')
    qty_dk = fields.Float('SL Đầu kỳ')
    value_dk = fields.Float('Giá trị Đk')
    qty_in = fields.Float('SL nhập')
    value_in = fields.Float('Giá Trị Nhập')
    qty_out = fields.Float('SL xuất')
    value_out = fields.Float('Giá trị xuất')
    qty_ck = fields.Float('SL cuối kỳ')
    value_ck = fields.Float('Giá trị cuối kỳ')
    check_origin = fields.Boolean('UOM Gốc')

    def init(self):
        self.env.cr.execute(f"""DROP FUNCTION IF EXISTS fnc_stock_value_report(from_date date, to_date date, tz character varying)""")
        self.env.cr.execute("""CREATE OR REPLACE FUNCTION fnc_stock_value_report(from_date date, to_date date, tz character varying)
                 RETURNS VOID
                 LANGUAGE plpgsql
                    AS $function$
                    BEGIN
                        insert into report_stock_value (product_code, product, uom, qty_dk, value_dk, qty_in, value_in, qty_out, value_out, qty_ck, value_ck, check_origin)
                        with giatri as ( select svl.product_id,
                                        sum(case when (sm.date at time zone 'utc' at time zone tz)::date < from_date then svl.value else 0 end) gt_dk,
                                        sum(case when svl.value > 0  and (sm.date at time zone 'utc' at time zone tz)::date between from_date and to_date  then svl.value else 0 end) gt_nhap,
                                        abs(sum(case when svl.value < 0  and (sm.date at time zone 'utc' at time zone tz)::date between from_date and to_date  then svl.value else 0 end)) gt_xuat,
                                        sum(case when (sm.date at time zone 'utc' at time zone tz)::date < to_date then svl.value else 0 end) gt_ck
                                        from stock_valuation_layer svl
                                        left join stock_move sm on sm.id = svl.stock_move_id 
                                        where sm.state = 'done'
                                        group by svl.product_id ),
                         product_uom_origin as (    select pp.id pp_id, pt.id pt_id, pp.default_code code, pt.name product, uu.name uom,
                                   t.dk qty_dk, 
                                   gt.gt_dk as value_dk,
                                   t.nhap qty_in, 
                                   gt.gt_nhap as value_in,
                                   t.xuat qty_out, 
                                   gt.gt_xuat as value_out,
                                   t.ck qty_ck, 
                                   gt_ck as value_ck,
                                   True as check_origin
                            from (
                                select sm.product_id, sm.product_uom,
                                       sum(case when (sm.date at time zone 'utc' at time zone tz)::date < from_date and sm.location_dest_id = 8 
                                       then sm.product_uom_qty
                                           when (sm.date at time zone 'utc' at time zone tz)::date < from_date and location_id = 8 
                                           then -sm.product_uom_qty
                                           else 0 end) as dk,
                                       sum(case when (sm.date at time zone 'utc' at time zone tz)::date between from_date and to_date and sm.location_dest_id = 8 
                                       then sm.product_uom_qty else 0 end) as nhap,
                                       sum(case when (sm.date at time zone 'utc' at time zone tz)::date between from_date and to_date and sm.location_id = 8 
                                       then sm.product_uom_qty else 0 end) as xuat,
                                       sum(case when (sm.date at time zone 'utc' at time zone tz)::date <= to_date and location_dest_id = 8
                                        then sm.product_uom_qty
                                           when (sm.date at time zone 'utc' at time zone tz)::date <= to_date and sm.location_id = 8
                                            then -sm.product_uom_qty
                                           else 0 end) as ck
                                from stock_move sm
                                where sm.state = 'done' and sm.company_id = 1
                                group by sm.product_id, sm.product_uom
                                ) t
                                left join product_product pp on t.product_id = pp.id
                                left join product_template pt on pp.product_tmpl_id = pt.id
                                left join uom_uom uu on t.product_uom = uu.id
                                left join giatri gt on gt.product_id = pp.id
                            where pt.x_product_id is null
                              and pt.detailed_type = 'product'
                            order by code ),

                        product_uom_fake as (
                                        select puo.pp_id, puo.pt_id,puo.code, pt.name product, uu.name uom,
                                                                       puo.qty_dk * pt.x_rate_conver qty_dk, 
                                                                       puo.value_dk/pt.x_rate_conver as value_dk,
                                                                       puo.qty_in * pt.x_rate_conver as qty_in, 
                                                                       puo.value_in / pt.x_rate_conver as value_in,
                                                                       puo.qty_out * pt.x_rate_conver as qty_out, 
                                                                       puo.value_out / pt.x_rate_conver as value_out,
                                                                       puo.qty_ck * pt.x_rate_conver as qty_ck, 
                                                                       puo.value_ck / pt.x_rate_conver as value_ck,
                                                                       False as check_origin
                                                                       from product_uom_origin puo
                                        inner join product_template pt on pt.id = puo.pt_id and pt.x_uom_id is not null
                                        left join uom_uom uu on uu.id = pt.x_uom_id
                                     )
                        select main.code , main.product, main.uom, main.qty_dk, main.value_dk, main.qty_in, main.value_in, main.qty_out, main.value_out, main.qty_ck, main.value_ck, main.check_origin from (
                                 select * from product_uom_fake
                                 union all
                                 select * from product_uom_origin
                                 ) main 
                                 order by main.code, main.uom
                            ;
                    END;
                    $function$;""")


class WzStockValue(models.TransientModel):
    _name = 'wz.stock.value'

    from_date = fields.Date('Từ ngày')
    to_date = fields.Date('Đến ngày', required=True, default=fields.Date.today())

    def action_print(self):
        self.ensure_one()
        tz = self.env.user.tz if self.env.user.tz else 'Asia/Ho_Chi_Minh'
        from_date = self.from_date if self.from_date else '1900-01-01'
        self.env.cr.execute(
            f"""delete from report_stock_value where id is not null""")
        self.env.cr.execute(
            f"""SELECT fnc_stock_value_report('{from_date}'::date, '{self.to_date}'::date, '{tz}')""")
        return {
            'name': _('Báo cáo Xuất nhập tồn'),
            'res_model': 'report.stock.value',
            'view_mode': 'tree',
            'view_ids': [(4, self.env.ref('dior_config.report_stock_value_view_tree').id)],
            'type': 'ir.actions.act_window',
            'target': 'main'
        }
