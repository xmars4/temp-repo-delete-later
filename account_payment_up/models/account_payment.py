# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from copy import deepcopy

PAYMENT_TYPES = [
    ('nor', 'Normal payment'),
    ('inv_auto', 'Auto pay for specific invoices'),
    ('inv_manual', 'Manual pay for specific invoices')
]

OPERATION_TYPES = [
    ('production', 'HĐ SXKD'),
    ('invest', 'HĐ Đầu tư'),
    ('finance', 'HĐ Tài chính')
]


class AccountPayment(models.Model):
    _inherit = "account.payment"

    currency_id = fields.Many2one('res.currency', default=23)
    x_payment_bank = fields.Boolean(string='Is payment bank', default=False)
    x_payment_type = fields.Selection(
        selection=PAYMENT_TYPES,
        default='nor',
        string='Payment Type'
    )
    x_payment_line_ids = fields.One2many(
        comodel_name='account.payment.line',
        inverse_name='payment_id',
        string='Payment Lines'
    )
    x_payment_invoice_ids = fields.One2many(
        comodel_name='account.payment.invoice',
        inverse_name='payment_id',
        string='Payment Invoices'
    )
    x_tax_type = fields.Selection([
        ('purchase', 'Purchases'),
        ('sale', 'Sales'),
    ], 'Tax type', store=False, compute='compute_x_tax_type')
    create_uid = fields.Many2one('res.users', string='Creator', default=lambda s: s._uid)
    x_director = fields.Many2one('res.users', string='Director')
    x_cashier = fields.Many2one('res.users', string='Cashier')
    x_receiver = fields.Char(string='Receiver')
    x_liquid = fields.Boolean(string='Is liquidation of assets', default=False)
    x_operation_type = fields.Selection(selection=OPERATION_TYPES, string='Operation type')
    x_note = fields.Text(string='Notes')
    x_warning_message = fields.Char(string='Warning message', compute='_compute_warning_message')
    x_payment_remain_id = fields.Many2one('account.payment', string='Account payment amount remain')


    def get_header_name(self):
        name = None
        list_111 = self.env['account.account'].sudo().search([('code', 'ilike', '111%')])
        list_112 = self.env['account.account'].sudo().search([('code', 'ilike', '112%')])
        if self.payment_type == 'inbound':
            name = "PHIẾU THU"
        # elif self.payment_type == 'inbound' and self.journal_id.default_debit_account_id.id in list_112.ids:
        #     name = "BÁO CÓ"
        elif self.payment_type == 'outbound':
            name = "PHIẾU CHI"
        # elif self.payment_type == 'outbound' and self.journal_id.default_debit_account_id.id in list_112.ids:
        #     name = "ỦY NHIỆM CHI"
        elif self.is_internal_transfer and self.journal_id.type == 'bank':
            name = "ỦY NHIỆM CHI"
        elif self.is_internal_transfer and self.journal_id.type == 'cash':
            name = "PHIẾU CHI"
        else:
            name = ""
        # if self.journal_des_id.default_debit_account_id.id in list_112.ids and self.journal_id.default_debit_account_id.id in list_111.ids:
        #     name = "PHIẾU CHI"
        # if self.journal_des_id.default_debit_account_id.id in list_111.ids and self.journal_id.default_debit_account_id.id in list_112.ids:
        #     name = "PHIẾU THU"
        return name

    @api.model
    def get_amount_word(self):
        utility_obj = self.env['hcsv.utility']
        # res = num2word(int(self.amount_total))
        res = self.amount_total
        res = utility_obj.convert_amount_to_words(amount=res, currency=self.currency_id).capitalize() or ''
        # if self.currency_id.currency_unit_label:
        # res += ' ' + self.currency_id.currency_unit_label.lower()
        return res

    @api.onchange('payment_type')
    def compute_x_tax_type(self):
        if self.payment_type:
            self.x_tax_type = 'sale' if self.payment_type == 'inbound' else 'purchase'

    @api.onchange('journal_id')
    def _check_change_journal_id(self):
        if not self.is_internal_transfer:
            if not self.x_payment_bank and self.journal_id.type != 'cash':
                raise ValidationError(_('You must to choose a cash journal'))
            if self.x_payment_bank and self.journal_id.type != 'bank':
                raise ValidationError(_('You must to choose a bank journal'))

    @api.depends('partner_id', 'journal_id', 'destination_journal_id')
    def _compute_is_internal_transfer(self):
        pass

    @api.depends('journal_id')
    def _compute_currency_id(self):
        pass

    @api.depends('x_payment_invoice_ids.amount', 'x_payment_type', 'amount')
    def _compute_warning_message(self):
        for record in self:
            invoice_lines = self.x_payment_invoice_ids.filtered(lambda r: r.selected)
            if record.x_payment_type == 'inv_auto' and not record.is_internal_transfer and invoice_lines and record.state == 'draft':
                amount_remain = self.amount - sum(invoice_lines.mapped('amount'))
                if amount_remain > 0:
                    record.x_warning_message = 'Tổng tiền đang dư %s so với chi tiết thanh toán. Hệ thống sẽ tự động hạch toán số dư vào tài khoản công nợ' % str(
                        amount_remain)
                else:
                    record.x_warning_message = ''
            else:
                record.x_warning_message = ''

    @api.onchange('amount')
    def onchange_payment_amount(self):
        if self.x_payment_type == 'inv_auto' and self.x_payment_invoice_ids:
            payment_amount = self.amount
            for line in self.x_payment_invoice_ids.sorted(lambda r: (r.move_date)):
                if payment_amount > 0:
                    if payment_amount >= line.amount_residual:
                        line.update({'selected': True, 'amount': line.amount_residual})
                        payment_amount = payment_amount - line.amount
                    elif payment_amount < line.amount_residual:
                        line.update({'selected': True, 'amount': payment_amount})
                        payment_amount = 0
                else:
                    line.update({'selected': False, 'amount': line.amount_residual})

    @api.onchange('x_payment_type')
    def onchange_x_payment_type(self):
        for record in self:
            record.x_payment_line_ids = False
            record.amount = 0

    @api.onchange('partner_id', 'x_payment_type', 'journal_id', 'currency_id')
    def onchange_partner_id(self):
        self.ensure_one()
        # self.amount = 0
        if not self.is_internal_transfer:
            self.x_payment_invoice_ids = False
            if self.x_payment_type != 'nor' and self.partner_id and self.journal_id:
                type = ['in_invoice', 'out_refund'] if self.payment_type == 'outbound' else ['out_invoice', 'in_refund']
                domain = [
                    ('partner_id', '=', self.partner_id.id), ('state', '=', 'posted'),
                    ('move_type', 'in', type), ('payment_state', 'in', ['not_paid', 'partial']),
                ]
                if self.currency_id:
                    domain += [('currency_id', '=', self.currency_id.id), ]
                else:
                    domain += ['|', ('currency_id', '=', False),
                               ('currency_id', '=', self.env.company.currency_id.id), ]
                invoices = self.env['account.move'].search(domain, order='date')
                invoice_lines = [(0, 0, {'move_id': inv.id, 'amount': inv.amount_residual}) for inv in invoices]
                self.x_payment_invoice_ids = invoice_lines
        if self.x_payment_invoice_ids or self.x_payment_line_ids:
            self.onchange_compute_amount()

    @api.onchange('x_payment_invoice_ids', 'x_payment_line_ids')
    def onchange_compute_amount(self):
        amount = 0
        for record in self:
            if record.x_payment_invoice_ids and record.x_payment_type == 'inv_manual':
                if record.x_payment_invoice_ids.filtered(lambda r: r.selected and r.amount_residual < r.amount):
                    raise ValidationError(_("Payment amount cannot be greater than current residual!"))
                amount_line = sum(record.x_payment_invoice_ids.filtered(lambda r: r.selected).mapped('amount'))
                record.amount = amount_line if amount_line else amount
            if record.x_payment_line_ids:
                if record.x_payment_line_ids.filtered(lambda r: r.value < 0):
                    raise ValidationError(_("Payment amount cannot be negative!"))
                amount_line = sum(record.x_payment_line_ids.filtered(lambda r: r.value).mapped('value'))
                record.amount = amount_line if amount_line else amount

    # OVERRIDE
    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        if self.x_payment_invoice_ids.filtered(lambda r: r.selected and r.amount > 0):
            for line in self.x_payment_invoice_ids.filtered(lambda r: r.selected):
                line.selected = False
        if self.x_payment_remain_id:
            self.x_payment_remain_id.action_draft()
            self.x_payment_remain_id.unlink()
        return res

    # OVERRIDE
    def _synchronize_to_moves(self, changed_fields):
        """Hàm này update lại giá trị bên bút toán,
        Nhưng trường hợp thanh toán cho nhiều Hóa đơn sẽ có nhiều account.move.line nên bị lỗi Singleton"""

        if (not self.x_payment_invoice_ids and not self.x_payment_line_ids):
            return super(AccountPayment, self)._synchronize_to_moves(changed_fields)
        else:
            pass

    # OVERRIDE
    def _synchronize_from_moves(self, changed_fields):
        """Hàm này update lại giá trị bên bút toán,
        Nhưng trường hợp thanh toán cho nhiều Hóa đơn sẽ có nhiều account.move.line nên bị lỗi Singleton"""

        if (not self.x_payment_invoice_ids and not self.x_payment_line_ids):
            return super(AccountPayment, self)._synchronize_from_moves(changed_fields)
        else:
            pass

    def button_compute_taxes(self):
        lines = []
        if len(self.x_payment_line_ids):
            # remove auto-generated tax lines
            lines = [(2, line.id, False) for line in self.x_payment_line_ids.filtered(lambda i: i.is_auto_gen)]
            # append tax lines
            for line in self.x_payment_line_ids.filtered(lambda i: not i.is_auto_gen):
                lines.append((0, 0, {
                    'account_id': line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'value': line.value,
                    'name': line.name,
                    'tax_ids': [(6, 0, line.tax_ids.ids)],
                }))
                for tax_id in line.tax_ids:
                    tax = tax_id.invoice_repartition_line_ids._origin.filtered(lambda x: x.repartition_type == "tax")
                    lines.append((0, 0, {
                        'is_auto_gen': True,
                        'account_id': tax.account_id.id,
                        'currency_id': line.currency_id.id,
                        'value': round(tax_id._compute_amount(line.value, None), 0),
                        'name': line.name
                    }))
        self.x_payment_line_ids = False
        self.x_payment_line_ids = lines
        amount_line = sum(self.x_payment_line_ids.filtered(lambda r: r.value).mapped('value'))
        self.amount = amount_line if amount_line else 0

    def action_post(self):
        number = self.env['ir.sequence'].next_by_code('seq_%s_%s' % (self.journal_id.type, self.partner_type))
        self.move_id.write({'name': number})
        if self._context.get('active_id') or self.is_internal_transfer:
            res = super(AccountPayment, self).action_post()
            if self.is_internal_transfer:
                self.move_id.onchange_x_rate()
            return res
        company_currency_id = self.env.company.currency_id
        # Thanh toán cho các hóa đơn cụ thể
        if self.x_payment_type != 'nor':
            payment_invoices = self.x_payment_invoice_ids.filtered(lambda r: r.selected and r.amount > 0)
            if not payment_invoices:
                raise ValidationError(_("Hiện tại đang không có hóa đơn nào được thanh toán. Vui lòng kiểm tra lại!"))
            else:
                move_lines = [(0, 0, line._prepare_move_line_vals()) for line in payment_invoices]
                amount_remain = 0
                if self.x_payment_type == 'inv_auto':
                    amount_total_invoices = sum(payment_invoices.filtered(lambda r: r.selected).mapped('amount'))
                    amount_remain = self.amount - amount_total_invoices
                    if amount_remain > 0:
                        payment_remain_id = self._create_account_payment_amount_remain(amount_remain)
                        self.x_payment_remain_id = payment_remain_id.id
                move_lines.append((0, 0, self.move_liquidity_line(amount_remain)))
                self.move_id.line_ids = False
                self.move_id.write({'line_ids': move_lines,
                                    'x_rate_active': self.x_rate_active if self.x_rate_active else False,
                                    'x_rate': self.x_rate if self.x_rate_active else 0,
                                    })

        # Thanh toán thường
        if self.x_payment_type == 'nor':
            if self.amount <= 0:
                raise ValidationError(_("Giá trị của tổng tiền phải lớn hơn 0!"))
            if not self.x_payment_line_ids:
                raise ValidationError(_("Vui lòng nhập ít nhất 1 dòng Chi tiết thanh toán!"))
            # Theo dõi các lines thuế được tạo ra từ mục thanh toán nào
            parent_line_id = self.env['account.payment.line'].browse()
            for line in self.x_payment_line_ids:
                if not line.is_auto_gen:
                    parent_line_id = line
                else:
                    if not parent_line_id:
                        raise ValidationError(_("Dữ liệu không hợp lệ, vui lòng kiểm tra lại!"))
                    line.parent_line_id = parent_line_id.id

            # Tạo bút toán
            _in = (self.payment_type == 'inbound')
            payment_lines = self.x_payment_line_ids.filtered(lambda r: r.value > 0)
            move_lines = [(0, 0, self._normal_move_lines(line, company_currency_id, _in)) for line in payment_lines]
            amount_currency = sum(payment_lines.mapped('value'))
            amount = 0
            if self.currency_id and self.currency_id != company_currency_id:
                if self.x_rate_active:
                    amount = company_currency_id.round(amount_currency * self.x_rate)
                else:
                    date = self.date or fields.Date.today()
                    amount = self.currency_id._convert(amount_currency, company_currency_id, self.env.company, date)
            amount = amount if amount else amount_currency
            line_vals = {
                'ref': self.ref,
                'name': self.name,
                'date': self.date,
                'account_id': self.journal_id.default_account_id.id,
                'debit': amount if _in else 0.0,
                'credit': 0 if _in else amount,
                'company_id': self.env.company.id,
                'currency_id': self.currency_id.id if self.currency_id != company_currency_id else False,
                'payment_id': self.id
            }
            if self.currency_id != company_currency_id:
                line_vals['amount_currency'] = amount_currency if _in else -amount_currency
            move_lines.append((0, 0, line_vals))
            self.move_id.line_ids = False
            self.move_id.write({'line_ids': move_lines,
                                'x_rate_active': self.x_rate_active if self.x_rate_active else False,
                                'x_rate': self.x_rate if self.x_rate_active else 0,
                                })
        res = super(AccountPayment, self).action_post()
        if self.x_payment_type != 'nor':
            self.reconcile_invoice(self.move_id)
        return res

    def move_liquidity_line(self, amount_remain):
        # Liquidity line.
        amount = self.amount if amount_remain == 0 else self.amount - amount_remain
        liquidity_amount_currency = amount if self.payment_type == 'inbound' else -amount
        if self.x_rate and self.x_rate_active:
            liquidity_balance = liquidity_amount_currency * self.x_rate
        else:
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
        liquidity_line_name = self.payment_reference
        payment_display_name = self._prepare_payment_display_name()
        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name[
                '%s-%s' % (self.payment_type, self.partner_type)], amount, self.currency_id, self.date,
            partner=self.partner_id,
        )
        liquidity_line = {
            'name': liquidity_line_name or default_line_name,
            'date_maturity': self.date,
            'amount_currency': liquidity_amount_currency,
            'currency_id': self.currency_id.id,
            'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
            'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
            'partner_id': self.partner_id.id,
            'account_id': self.journal_id.default_account_id.id,
        }
        return liquidity_line

    # Thanh toán hóa đơn cụ thể
    def _prepare_move_line_remain_vals(self, amount_remain):
        self.ensure_one()
        liquidity_amount_currency = amount_remain if self.payment_type == 'inbound' else -amount_remain
        write_off_amount_currency = 0.0 if self.payment_type == 'inbound' else -0.0
        write_off_balance = self.currency_id._convert(
            write_off_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        if self.x_rate and self.x_rate_active:
            liquidity_balance = liquidity_amount_currency * self.x_rate
        else:
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id
        payment_display_name = self._prepare_payment_display_name()
        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name[
                '%s-%s' % (self.payment_type, self.partner_type)],
            amount_remain,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )
        if self.partner_type == 'inbound':
            account_id = self.partner_id.property_account_receivable_id.id
        elif self.partner_type == 'outbound':
            account_id = self.partner_id.property_account_payable_id.id
        else:
            account_id = self.destination_account_id.id
        vals_list = {
            'name': self.payment_reference or default_line_name,
            'date_maturity': self.date,
            'amount_currency': counterpart_amount_currency,
            'currency_id': currency_id,
            'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
            'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
            'partner_id': self.partner_id.id,
            'account_id': account_id
        }
        return vals_list

    def _create_account_payment_amount_remain(self, amount_remain):
        self.ensure_one()
        if self.partner_type == 'inbound':
            account_id = self.partner_id.property_account_receivable_id.id
        elif self.partner_type == 'outbound':
            account_id = self.partner_id.property_account_payable_id.id
        else:
            account_id = self.destination_account_id.id
        vals_payment_line = {
            'name': self.name,
            'currency_id': self.currency_id.id,
            'value': amount_remain,
            'partner_id': self.partner_id.id,
            'account_id': account_id
        }
        payment_id = self.env['account.payment'].create({
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'amount': amount_remain,
            'date': self.date,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'x_payment_type': 'nor',
            'x_rate_active': self.x_rate_active,
            'x_rate': self.x_rate,
            'x_payment_line_ids': [(0, 0, vals_payment_line)]
        })
        payment_id.action_post()
        return payment_id

    def reconcile_invoice(self, move):
        domain = [
            ('parent_state', '=', 'posted'),
            ('account_internal_type', 'in', ('receivable', 'payable')),
            ('reconciled', '=', False),
        ]
        for line in move.line_ids.filtered_domain(domain):
            if line.x_payment_invoice_id:
                line.x_payment_invoice_id.move_id.js_assign_outstanding_line(line.id)

    # AccountMoveLine thanh toán thường
    def _normal_move_lines(self, line, company_currency_id, _in):
        value = line.value
        if self.currency_id and self.currency_id != company_currency_id:
            if self.x_rate_active:
                value = company_currency_id.round(value * self.x_rate)
            else:
                date = self.date or fields.Date.today()
                value = self.currency_id._convert(value, company_currency_id, self.env.company, date)
        vals = {
            'name': line.name,
            'ref': self.ref,
            'date': self.date,
            'account_id': line.account_id.id,
            'debit': 0.0 if _in else value,
            'credit': value if _in else 0.0,
            'partner_id': self.partner_id.id if self.partner_id else None,
            'product_id': line.product_id.id,
            'company_id': self.env.company.id,
            'currency_id': self.currency_id.id if self.currency_id != company_currency_id else False,
            'x_payment_line_id': line.id,
            'tax_ids': [(6, 0, line.tax_ids.ids)],
        }
        if self.currency_id and self.currency_id != company_currency_id:
            vals['amount_currency'] = -line.value if _in else line.value
        return vals

    def action_post(self):
        return super(AccountPayment, self).action_post()

class AccountPaymentLine(models.Model):
    _name = 'account.payment.line'

    payment_id = fields.Many2one('account.payment', string='Payment')
    parent_line_id = fields.Many2one('account.payment.line', string='Payment Line')
    product_id = fields.Many2one('product.product', string='Category')
    account_id = fields.Many2one('account.account', string='Account')
    partner_id = fields.Many2one('res.partner', string='Partner')
    currency_id = fields.Many2one('res.currency', string='Currency', default=23)
    tax_ids = fields.Many2many('account.tax', 'payment_line_tax_rel', 'payment_line_id', 'tax_id', string='Taxs')
    name = fields.Char(string='Description')
    value = fields.Monetary(string='Value', required=True, currency_field='currency_id')
    is_auto_gen = fields.Boolean(string='Is record created auto', default=False)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            if self.payment_id.payment_type == 'inbound':
                self.account_id = self.partner_id.property_account_receivable_id.id
            elif self.payment_id.payment_type == 'outbound':
                self.account_id = self.partner_id.property_account_payable_id.id

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.payment_id.payment_type and self.product_id and not self.account_id:
            if self.payment_id.payment_type == 'inbound':
                self.account_id = self.product_id.property_account_income_id
            else:
                self.account_id = self.product_id.property_account_expense_id


class AccountPaymentInvoice(models.Model):
    _name = 'account.payment.invoice'
    _description = 'Account Payment Invoice'

    payment_id = fields.Many2one('account.payment', string="Payment")
    selected = fields.Boolean('Selected', default=False)
    move_id = fields.Many2one('account.move', 'Invoice ID')
    move_currency_id = fields.Many2one(related='move_id.currency_id', string='Currency')
    move_date = fields.Date(related='move_id.date', string='Invoice date')
    move_ref = fields.Char(related='move_id.ref', string='Invoice description')
    move_total = fields.Monetary(related='move_id.amount_total', string='Total', currency_field='move_currency_id')
    amount_residual = fields.Monetary(related='move_id.amount_residual', string='Due',
                                      currency_field='move_currency_id')
    amount = fields.Monetary(string='Payment amount', currency_field='move_currency_id')
    note = fields.Char('Remark')

    @api.onchange('amount')
    def onchange_amount(self):
        if self.amount < 0:
            raise ValidationError('The payment amount cannot be negative.')

    @api.onchange('selected')
    def onchange_selected_field(self):
        if self.selected and self.payment_id.x_payment_type == 'inv_auto':
            amount = self.payment_id.amount
            if amount <= 0:
                self.selected = False
                raise ValidationError('The payment must be greater than 0.')
            else:
                move_id = self.move_id.id
                amount_total = sum(self.payment_id.x_payment_invoice_ids.filtered(
                    lambda r: r.selected and r != self and r.move_id.id != move_id).mapped('amount'))
                amount_remain = amount - amount_total
                if amount_remain - self.amount >= 0:
                    return
                elif amount_remain - self.amount < 0 and amount_remain > 0:
                    self.amount = amount_remain
                else:
                    self.selected = False
        else:
            self.amount = self.amount_residual

    # Thanh toán hóa đơn cụ thể
    def _prepare_move_line_vals(self):
        self.ensure_one()
        liquidity_amount_currency = self.amount if self.payment_id.payment_type == 'inbound' else -self.amount
        write_off_amount_currency = 0.0 if self.payment_id.payment_type == 'inbound' else -0.0
        write_off_balance = self.payment_id.currency_id._convert(
            write_off_amount_currency,
            self.payment_id.company_id.currency_id,
            self.payment_id.company_id,
            self.payment_id.date,
        )
        if self.payment_id.x_rate and self.payment_id.x_rate_active:
            liquidity_balance = liquidity_amount_currency * self.payment_id.x_rate
        else:
            liquidity_balance = self.payment_id.currency_id._convert(
                liquidity_amount_currency,
                self.payment_id.company_id.currency_id,
                self.payment_id.company_id,
                self.payment_id.date,
            )
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.payment_id.currency_id.id
        payment_display_name = self.payment_id._prepare_payment_display_name()
        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.payment_id.is_internal_transfer else payment_display_name[
                '%s-%s' % (self.payment_id.payment_type, self.payment_id.partner_type)],
            self.amount,
            self.payment_id.currency_id,
            self.payment_id.date,
            partner=self.payment_id.partner_id,
        )
        if self.move_id.move_type == 'out_refund':
            account_id = self.payment_id.partner_id.property_account_receivable_id.id
        elif self.move_id.move_type == 'in_refund':
            account_id = self.payment_id.partner_id.property_account_payable_id.id
        else:
            account_id = self.payment_id.destination_account_id.id
        vals_list = {
            'name': self.payment_id.payment_reference or default_line_name,
            'date_maturity': self.payment_id.date,
            'amount_currency': counterpart_amount_currency,
            'currency_id': currency_id,
            'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
            'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
            'partner_id': self.payment_id.partner_id.id,
            'account_id': account_id,
            'x_payment_invoice_id': self.id,
        }
        return vals_list
