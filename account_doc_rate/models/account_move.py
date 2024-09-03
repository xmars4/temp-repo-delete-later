# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_rate_active = fields.Boolean(string='Manual currency rate', default=False, copy=False)
    x_rate = fields.Float(string='Currency rate', copy=False)
    x_compare_currency = fields.Boolean(string='Is Compare currency', compute='_compute_compare_currency')
    x_move_original_id = fields.Many2one('account.move', string='Account Move Original', required=False, copy=False)

    @api.depends('currency_id')
    def _compute_compare_currency(self):
        for record in self:
            if record.currency_id.id == record.company_currency_id.id:
                record.x_compare_currency = True
                record.x_rate_active = False
            else:
                record.x_compare_currency = False

    @api.onchange('x_rate_active', 'x_rate', 'currency_id')
    def onchange_x_rate(self):
        for record in self:
            if record.x_rate_active and record.x_rate != 0:
                rate = record.x_rate
                move_lines = [(1, line.id, {
                    'price_total': abs(line.amount_currency * rate),
                    'debit': abs(line.amount_currency * rate) if line.debit > 0 else 0,
                    'credit': abs(line.amount_currency * rate) if line.credit > 0 else 0
                }) for line in record.line_ids]

                if move_lines:
                    record.write({'line_ids': move_lines})

    @api.model_create_multi
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        for r in res:
            if r and r.x_rate_active and r.x_rate:
                r.onchange_x_rate()
        return res

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        # Tìm kiếm bút toán chênh lệch tỷ giá của Account.Move và Đưa về dự thảo
        domain = [('x_move_original_id', 'in', self.ids), ('state', '=', 'posted')]
        move_exchange_difference = self.env['account.move'].search(domain)
        if move_exchange_difference:
            move_exchange_difference.button_draft()
        return res

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        # Tìm kiếm bút toán chênh lệch tỷ giá của Account.Move và Đưa về hủy
        domain = [('x_move_original_id', 'in', self.ids), ('state', '=', 'posted')]
        move_exchange_difference = self.env['account.move'].search(domain)
        if move_exchange_difference:
            move_exchange_difference.button_cancel()
        return res

    # Tạo bút toán chênh lệch tỷ giá
    def _create_move_exchange_difference(self, payment_move_id, partial_reconcile_id):
        self.ensure_one()
        value = 0
        company_currency = self.company_id.currency_id
        amount_currency = abs(partial_reconcile_id.debit_amount_currency)
        rate_payment = payment_move_id.x_rate if payment_move_id.x_rate_active else round(
            abs(partial_reconcile_id.amount / amount_currency))
        # Trường hợp sử dụng tỷ giá thủ công
        if self.x_rate != rate_payment and self.x_rate_active:
            rate_move = self.x_rate
            value = abs(rate_move - rate_payment) * amount_currency
        # Trường hợp không sử dụng tỷ giá thủ công
        if company_currency.id != payment_move_id.currency_id.id and not value:
            rate_move = company_currency.round(self.amount_total_signed / self.amount_total_in_currency_signed)
            value = abs(rate_move - rate_payment) * amount_currency if rate_move != rate_payment else 0
        if value:
            move_lines = self._get_move_line_exchanges(rate_move, rate_payment, value)
            if move_lines:
                journal_id = self.env['account.journal'].search([('code', '=', 'EXCH')], limit=1)
                move_vals = {
                    'journal_id': journal_id.id,
                    'payment_id': payment_move_id.payment_id.id,
                    'company_id': self.company_id.id,
                    'ref': payment_move_id.payment_id.name,
                    'date': payment_move_id.date or fields.Date.today(),
                    'move_type': 'entry',
                    'x_move_original_id': self.id,
                    'line_ids': move_lines
                }
                account_move = self.env['account.move'].create(move_vals)
                account_move._post()
                account_partner = [self.partner_id.property_account_receivable_id.id, self.partner_id.property_account_payable_id.id]
                move_line_id = account_move.line_ids.filtered(lambda r: r.account_id.id in account_partner)
                update_reconciled = """ UPDATE account_move_line SET reconciled = True WHERE id = %s"""
                self._cr.execute(update_reconciled, (str(move_line_id.id),))

    def _get_move_line_exchanges(self, rate_move, rate_payment, value):
        """
        :param self: Hóa đơn (account.move)
        :param rate_move: Tỷ giá trên Hóa đơn
        :param rate_payment: Tỷ giá lúc thanh toán
        :param value: Giá trị chênh lệch tỷ giá
        :return: Trả về account_move_line của bút toán chênh lệch tỷ giá
        """
        expense_account_id = self.company_id.expense_currency_exchange_account_id.id  # 635
        income_account_id = self.company_id.income_currency_exchange_account_id.id  # 515
        account_receivable_id = self.partner_id.property_account_receivable_id.id  # 131
        account_payable_id = self.partner_id.property_account_payable_id.id  # 331
        partner_id = self.partner_id.id
        ref = self.name
        lines = []
        # Công nợ NCC
        if self.move_type == 'in_invoice':
            if rate_move < rate_payment:
                lines = self._prepare_move_lines(partner_id, value, expense_account_id, account_payable_id, ref)
            else:
                lines = self._prepare_move_lines(partner_id, value, account_payable_id, income_account_id, ref)
        # Trả hàng NCC
        if self.move_type == 'in_refund':
            if rate_move < rate_payment:
                lines = self._prepare_move_lines(partner_id, value, account_payable_id, income_account_id, ref)
            else:
                lines = self._prepare_move_lines(partner_id, value, expense_account_id, account_payable_id, ref)
        # Công nợ KH
        if self.move_type == 'out_invoice':
            if rate_move < rate_payment:
                lines = self._prepare_move_lines(partner_id, value, account_receivable_id, income_account_id, ref)
            else:
                lines = self._prepare_move_lines(partner_id, value, expense_account_id, account_receivable_id, ref)
        # Nhận lại hàng của KH
        if self.move_type == 'out_refund':
            if rate_move < rate_payment:
                lines = self._prepare_move_lines(partner_id, value, expense_account_id, account_receivable_id, ref)
            else:
                lines = self._prepare_move_lines(partner_id, value, account_receivable_id, income_account_id, ref)
        return lines

    # AccountMoveLine Chênh lệch tỷ giá
    def _prepare_move_lines(self, partner_id, value, debit_account_id, credit_account_id, ref):
        self.ensure_one()
        debit_value = self.env.company.currency_id.round(value)
        credit_value = debit_value
        debit_line_vals = (0, 0, {
            'name': _('Currency exchange rate difference'),
            'quantity': 0,
            'ref': ref,
            'partner_id': partner_id,
            'debit': debit_value,
            'credit': 0,
            'account_id': debit_account_id
        })
        credit_line_vals = (0, 0, {
            'name': _('Currency exchange rate difference'),
            'quantity': 0,
            'ref': ref,
            'partner_id': partner_id,
            'credit': credit_value,
            'debit': 0,
            'account_id': credit_account_id
        })
        res = [debit_line_vals, credit_line_vals]
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Bỏ phần sinh bút toán chênh lệch tỷ giá của Core
    def _create_exchange_difference_move(self):
        return None

    # OVERRIDE: ADD Create move exchange difference
    def reconcile(self):
        res = super(AccountMoveLine, self).reconcile()
        if res.get('partials', False):
            move_credit = res['partials'].credit_move_id.move_id
            debit_credit = res['partials'].debit_move_id.move_id
            move_invoice = move_credit if move_credit.move_type != 'entry' else debit_credit
            move_payment = move_credit if move_credit.move_type == 'entry' else debit_credit
            move_invoice._create_move_exchange_difference(move_payment, res['partials'])
        return res
