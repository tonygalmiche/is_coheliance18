# -*- coding: utf-8 -*-
from odoo import api, fields, models
import datetime


class IsSuiviCaisse(models.Model):
    _name='is.suivi.caisse'
    _description='is.suivi.caisse'
    _order='date desc, id desc'


    def _compute_solde(self):
        cr = self._cr
        for obj in self:
            cr.execute("select sum(credit-debit) from is_suivi_caisse where date<='"+str(obj.date)+"' and id>="+str(obj.id)+" ")
            obj.solde=cr.fetchone()[0] or 0.0


    date        = fields.Date("Date"   , required=True, index=True)
    libelle     = fields.Char("Libellé", required=True)
    invoice_id  = fields.Many2one('account.move', u'Facture')
    debit       = fields.Float("Débit" , digits=(14,2))
    credit      = fields.Float("Crédit", digits=(14,2))
    solde       = fields.Float("Solde", compute=_compute_solde)
    commentaire = fields.Char("Commentaire")

