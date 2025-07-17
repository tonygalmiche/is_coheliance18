# -*- coding: utf-8 -*-
from odoo import api, fields, models
import datetime


def _date_creation():
    now  = datetime.date.today()
    return now.strftime('%Y-%m-%d')


class is_suivi_tresorerie(models.Model):
    _name='is.suivi.tresorerie'
    _description = "Suivi Trésorerie"
    _order='name desc'

    name               = fields.Date("Date"               , required=True)
    montant_tresorerie = fields.Float("Montant banque"    , required=True)
    reste_a_payer      = fields.Float("Reste à payer")
    tresorerie         = fields.Float("Trésorerie"        , readonly=True)

    _defaults = {
        'name'       : lambda *a: _date_creation(),
        'tresorerie' : 0,
    }


    def _tresorerie(self, vals, obj):
        if 'reste_a_payer' in vals:
            reste_a_payer = vals['reste_a_payer']
        else:
            reste_a_payer = obj.reste_a_payer
        if 'montant_tresorerie' in vals:
            montant_tresorerie = vals['montant_tresorerie']
        else:
            montant_tresorerie = obj.montant_tresorerie
        return montant_tresorerie+reste_a_payer


    # @api.model
    # def create(self, vals):
    #     cr=self._cr
    #     cr.execute("""
    #         SELECT sum(amount_residual_signed)
    #         FROM account_move
    #         WHERE state in ('posted') and move_type in ('out_invoice', 'out_refund')
    #               and invoice_date>='2016-06-01' 
    #     """)
    #     reste_a_payer=0
    #     for row in cr.fetchall():
    #         reste_a_payer=row[0]
    #     vals['reste_a_payer']=reste_a_payer
    #     vals['tresorerie']=vals['montant_tresorerie']+reste_a_payer
    #     res = super(is_suivi_tresorerie, self).create(vals)
    #     return res


    def write(self, vals):
        for obj in self:
            if 'reste_a_payer' in vals:
                reste_a_payer = vals['reste_a_payer']
            else:
                reste_a_payer = obj.reste_a_payer
            if 'montant_tresorerie' in vals:
                montant_tresorerie = vals['montant_tresorerie']
            else:
                montant_tresorerie = obj.montant_tresorerie
            vals['tresorerie']=self._tresorerie(vals, obj)
        res = super(is_suivi_tresorerie, self).write(vals)
        return res

