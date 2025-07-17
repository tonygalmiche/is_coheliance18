# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_responsable_id = fields.Many2one('res.users', 'Responsable')


class AccountMove(models.Model):
    _inherit = 'account.move'


    @api.depends('invoice_date','amount_total','partner_id')
    def _compute_is_msg_err(self):
        for obj in self:
            filter=[
                ('invoice_date', '=' , obj.invoice_date),
                ('amount_total', '=' , obj.amount_total),
                ('partner_id'  , '=' , obj.partner_id.id),
            ]
            invoices = self.env['account.move'].search(filter)
            msg=False
            if len(invoices)>1:
                msg='Attention : Il existe une autre facture du même montant à cette même date et pour ce même fournisseur'
            obj.is_msg_err=msg


    @api.depends('invoice_line_ids','state')
    def _compute_order_id(self):
        for obj in self:
            for line in obj.invoice_line_ids:
                for order in line.sale_line_ids:
                    obj.order_id=order.order_id.id
                    affaire_id = order.order_id.affaire_id.id
                    if affaire_id:
                        obj.is_affaire_id=affaire_id
            if obj.is_affaire_id:
                for line in obj.invoice_line_ids:
                    if not line.is_affaire_id:
                        line.is_affaire_id=obj.is_affaire_id.id


    order_id                 = fields.Many2one('sale.order', 'Commande', compute=_compute_order_id,store=True)
    is_affaire_id            = fields.Many2one('is.affaire', 'Affaire')
    is_refacturable          = fields.Selection([('oui','Oui'),('non','Non')], u"Refacturable")
    is_nom_fournisseur       = fields.Char('Nom du fournisseur')
    is_personne_concernee_id = fields.Many2one('res.users', u'Personne concernée')
    is_msg_err               = fields.Char('Message', compute='_compute_is_msg_err', readonly=True)
    supplier_invoice_number  = fields.Char('Numéro de facture fournisseur')


    def voir_facture_fournisseur(self):
        for obj in self:
            res= {
                'name': 'Facture',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'account.move',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    is_responsable_id          = fields.Many2one('res.users', 'Responsable', related='account_id.is_responsable_id', readonly=True)
    is_affaire_id              = fields.Many2one('is.affaire', 'Affaire')
    is_account_invoice_line_id = fields.Integer('Lien entre account_invoice_line et account_move_line pour la migration')


