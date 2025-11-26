# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_responsable_id = fields.Many2one('res.users', 'Responsable')


class AccountMove(models.Model):
    _inherit = 'account.move'


    def _get_custom_sequence_number(self):
        """
        Génère le numéro de séquence personnalisé : AA-MM-NNNN
        où AA = année sur 2 chiffres, MM = mois sur 2 chiffres, NNNN = numéro chronologique continu
        """
        self.ensure_one()



        invoice_date = self.invoice_date or fields.Date.context_today(self)
        year = invoice_date.strftime('%y')   # Année sur 2 chiffres
        month = invoice_date.strftime('%m')  # Mois sur 2 chiffres
        
        # Pour les factures et avoirs clients, utiliser une séquence commune
        # Pour les factures et avoirs fournisseurs, utiliser une séquence commune
        if self.move_type in ('out_invoice', 'out_refund'):
            move_types = ['out_invoice', 'out_refund']
        elif self.move_type in ('in_invoice', 'in_refund'):
            move_types = ['in_invoice', 'in_refund']
        else:
            move_types = [self.move_type]
        
        domain=[
            ('move_type', 'in', move_types),
            ('id', '!=' , self.id),
            ('state', '=' , 'posted'),
        ]
        invoices = self.env['account.move'].search(domain, order="id desc", limit=1)
        next_number = 1
        for invoice in invoices:
            next_number = invoice.sequence_number + 1
        if self.move_type in ['out_invoice','out_refund']:
            custom_number = f"{year}-{month}-{str(next_number).zfill(4)}"
        else:
            custom_number = str(next_number).zfill(5)
        return custom_number


    def _set_next_sequence(self):
        """
        Surcharge de la méthode qui attribue le prochain numéro de séquence.
        Cette méthode est appelée lors de la validation de la facture (passage à l'état 'posted').
        """
        self.ensure_one()
        # Appliquer la numérotation personnalisée uniquement pour les factures et avoirs clients/fournisseurs
        if self.move_type in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund'):
            sequence = self._get_custom_sequence_number()
            self.with_context(clear_sequence_mixin_cache=False)[self._sequence_field] = sequence
            self._compute_split_sequence()
        else:
            # Pour les autres types de documents, utiliser la séquence standard
            super(AccountMove, self)._set_next_sequence()


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


    def action_voir_lignes(self):
        self.ensure_one()
        tree_view_id = self.env.ref('is_coheliance18.is_account_move_line_tree').id
        return {
            'name': 'Lignes',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'views': [(tree_view_id, 'list'), (False, 'form')],
            'domain': [('move_id', '=', self.id), ('display_type', '=', 'product')],
            'context': {'move_id': self.id},
            'limit': 1000,
        }


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    is_responsable_id          = fields.Many2one('res.users', 'Responsable', related='account_id.is_responsable_id', readonly=True)
    is_affaire_id              = fields.Many2one('is.affaire', 'Affaire')
    is_account_invoice_line_id = fields.Integer('Lien entre account_invoice_line et account_move_line pour la migration')


