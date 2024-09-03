# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    x_rate_active = fields.Boolean(string='Payment manual currency rate', default=False, copy=False)
    x_rate = fields.Float(string='Payment currency rate', copy=False)
    x_move_rate_count = fields.Integer(string="# Reconciled Exchange Difference",
        compute="_compute_x_move_rate_count")
    x_compare_currency = fields.Boolean(string='Is Compare currency', compute='_compute_compare_currency')

    @api.onchange('x_rate_active')
    def _onchange_x_rate_active(self):
        for record in self:
            record.x_rate = 0

    @api.depends('currency_id')
    def _compute_compare_currency(self):
        for record in self:
            if record.currency_id.id == self.env.company.currency_id.id or not record.currency_id.id:
                record.x_compare_currency = True
                record.x_rate_active = False
            else:
                record.x_compare_currency = False
                if not record.x_rate_active:
                    record.x_rate = 0

    def _compute_x_move_rate_count(self):
        """
        Func count Account Move ExChange Difference Rate
        :return: Number of Account Move
        """
        for record in self:
            # journal_id = self.env['account.journal'].search([('code', '=', 'EXCH')], limit=1)
            # sql_count_move = """
            #     SELECT count(am.id)
            #     FROM account_move am
            #     JOIN account_payment ap on am.payment_id = ap.id
            #     WHERE am.state = 'posted'
            #     AND am.journal_id = %s
            #     AND ap.id = %s
            # """
            # self._cr.execute(sql_count_move, [journal_id.id, record.id])
            # record.x_move_rate_count = self._cr.fetchone()[0]
            record.x_move_rate_count = 0

    def button_open_move_exchange_difference(self):
        """
        Function Open Account Move Exchange Difference Rate of Account Payment
        :return: View Account Move
        """
        self.ensure_one()
        action = {
            'name': _("Move Exchange Difference"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
        }
        journal_id = self.env['account.journal'].search([('code', '=', 'EXCH')], limit=1)
        sql_count_move = """
            SELECT distinct am.id move_id
            FROM account_move am
            JOIN account_payment ap on am.payment_id = ap.id
            WHERE am.state = 'posted'
            AND am.journal_id = %s
            AND ap.id = %s
        """
        self._cr.execute(sql_count_move, [journal_id.id, self.id])
        move_ids = [x['move_id'] for x in self._cr.dictfetchall()]

        if len(move_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': move_ids[0],
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', move_ids)],
            })
        return action

    def action_cancel(self):
        """
        Override Func action_cancel, add cancel account.move exchange rate in Account Payment
        :return:
        """
        res = super(AccountPayment, self).action_cancel()
        domain = [('payment_id', '=', self.id), ('state', '=', 'posted'), ('journal_id.code', '=', 'EXCH')]
        account_move_ids = self.env['account.move'].search(domain)
        account_move_ids.button_cancel()
        return res

    def action_draft(self):
        """
        Override Func action_draft, add set to draft account.move exchange rate in Account Payment
        :return:
        """
        res = super(AccountPayment, self).action_draft()
        domain = [('payment_id', '=', self.id), ('state', '=', 'posted'), ('journal_id.code', '=', 'EXCH')]
        account_move_ids = self.env['account.move'].search(domain)
        account_move_ids.button_draft()
        return res