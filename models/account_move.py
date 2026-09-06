# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_responsable_id = fields.Many2one('res.users', 'Responsable')


class AccountMove(models.Model):
    _inherit = 'account.move'


    def _get_custom_sequence_number(self):
        """
        Génère le numéro de séquence personnalisé : AA-MM-NNNN
        où AA = année sur 2 chiffres, MM = mois sur 2 chiffres, NNNN = numéro chronologique continu

        Le compteur NNNN est attribué par une ir.sequence en mode "no_gap" (is.account.move.client /
        is.account.move.supplier) : l'incrémentation est atomique (verrou de ligne dans la transaction
        en cours), ce qui évite les doublons obtenus précédemment avec une recherche "dernière facture
        postée, order by id desc" (l'id ne reflète pas l'ordre de validation, cf brouillons validés
        dans le désordre). Le numéro n'étant consommé qu'à la validation (jamais à la création du
        brouillon), la suppression d'un brouillon ne crée pas de trou ; un rollback (échec de
        validation) n'en crée pas non plus car le mode "no_gap" est transactionnel.
        """
        self.ensure_one()

        invoice_date = self.invoice_date or fields.Date.context_today(self)
        year = invoice_date.strftime('%y')   # Année sur 2 chiffres
        month = invoice_date.strftime('%m')  # Mois sur 2 chiffres

        if self.move_type in ('out_invoice', 'out_refund'):
            # Séquence commune factures + avoirs clients
            return f"{year}-{month}-{self.env['ir.sequence'].next_by_code('is.account.move.client')}"
        elif self.move_type in ('in_invoice', 'in_refund'):
            # Séquence commune factures + avoirs fournisseurs
            return self.env['ir.sequence'].next_by_code('is.account.move.supplier')
        return False


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


    def _post(self, soft=True):
        """
        Le numéro (name) d'une facture/avoir en brouillon reste modifiable manuellement
        (utile pour corriger une anomalie de numérotation). On bloque en contrepartie la
        validation si le numéro saisi entre en conflit avec une facture déjà comptabilisée :
        - le numéro complet existe déjà (tous types confondus) ;
        - pour les factures/avoirs clients, la partie "-NNNN" en fin de numéro (le compteur
          continu is.account.move.client) est déjà utilisée par une autre facture/avoir client,
          même sous un préfixe AA-MM différent (la numérotation est continue, indépendante du
          mois : deux factures ne doivent jamais partager le même compteur).
        Un numéro auto-généré par _get_custom_sequence_number est toujours garanti unique et
        ne déclenche donc jamais ce blocage.
        """
        self._check_custom_sequence_number_conflicts()
        return super(AccountMove, self)._post(soft=soft)


    def _check_custom_sequence_number_conflicts(self):
        for move in self:
            if move.move_type not in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund'):
                continue
            if not move.name or move.name == '/':
                continue

            move_types = ('out_invoice', 'out_refund') if move.move_type in ('out_invoice', 'out_refund') \
                else ('in_invoice', 'in_refund')

            duplicate = self.env['account.move'].search([
                ('id', '!=', move.id),
                ('move_type', 'in', move_types),
                ('state', '=', 'posted'),
                ('name', '=', move.name),
            ], limit=1)
            if duplicate:
                raise UserError(_(
                    "Impossible de valider %(name)s : ce numéro est déjà utilisé par %(other)s.",
                    name=move.name, other=duplicate.display_name,
                ))

            if move.move_type in ('out_invoice', 'out_refund') and '-' in move.name:
                suffix = move.name.rsplit('-', 1)[-1]
                conflict = self.env['account.move'].search([
                    ('id', '!=', move.id),
                    ('move_type', 'in', move_types),
                    ('state', '=', 'posted'),
                    ('name', '=like', '%-' + suffix),
                ], limit=1)
                if conflict:
                    raise UserError(_(
                        "Impossible de valider %(name)s : le numéro de séquence %(suffix)s est "
                        "déjà utilisé par %(other)s (la numérotation est continue et indépendante "
                        "du mois, deux factures ne peuvent pas partager le même numéro final).",
                        name=move.name, suffix=suffix, other=conflict.display_name,
                    ))


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


