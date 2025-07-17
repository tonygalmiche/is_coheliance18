# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class is_account_invoice_line(models.Model):
    _name='is.account.invoice.line'
    _description='is.account.invoice.line'
    _order='date_invoice desc'
    _auto = False


    invoice_id    = fields.Many2one('account.move', u'Facture')
    number        = fields.Char('N°facture')
    date_invoice  = fields.Date('Date facture')
    partner_id    = fields.Many2one('res.partner', u'Client / Fournisseur')
    journal_id    = fields.Many2one('account.journal', u'Journal')
    move_type     = fields.Selection(selection=[
            ('in_invoice' , u'Facture fournisseur'),
            ('in_refund'  , u'Avoir fournisseur'),
            ('out_invoice', u'Facture client'),
            ('out_refund' , u'Avoir client'),
        ], string="Type")
    state = fields.Selection(selection=[
            ('draft' , u'Brouillon'),
            ('open'  , u'Ouverte'),
            ('paid'  , u'Payée'),
            ('cancel', u'Annulée'),
        ], string="État")
    product_id      = fields.Many2one('product.product', u'Article')
    description     = fields.Char(u'Description')
    affaire_id      = fields.Many2one('is.affaire', u'Affaire')
    account_line_id = fields.Many2one('account.account', u'Compte Ligne')
    quantity        = fields.Float(u'Quantité', digits=(14,2))
    price_unit      = fields.Float(u'Prix unitaire', digits=(14,2))
    price_subtotal  = fields.Float(u'Montant', digits=(14,2))

    def init(self):
        cr=self.env.cr
        tools.drop_view_if_exists(cr, 'is_account_invoice_line')
        cr.execute("""
            CREATE OR REPLACE view is_account_invoice_line AS (
                SELECT 
                    ai.id              as id,
                    ai.id              as invoice_id,
                    ai.invoice_date    as date_invoice,
                    ai.name            as number,
                    ai.partner_id      as partner_id,
                    ai.journal_id      as journal_id,
                    -- ai.account_id      as account_id,
                    ai.move_type       as move_type,
                    ai.state           as state,
                    ail.product_id     as product_id,
                    ail.name           as description,
                    COALESCE (ail.is_affaire_id, ai.is_affaire_id) as affaire_id,
                    ail.account_id     as account_line_id,
                    ail.quantity       as quantity,
                    ail.price_unit     as price_unit,
                    ail.price_subtotal as price_subtotal
                FROM account_move ai inner join account_move_line ail on ai.id=ail.move_id
                WHERE ai.invoice_date>='2016-06-01' 
            )
        """)

