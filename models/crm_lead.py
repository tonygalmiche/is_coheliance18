# -*- coding: utf-8 -*-
from odoo import api, fields, models

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    affaire_id          = fields.Many2one('is.affaire', 'Affaire')
    amene_par_id        = fields.Many2one('res.users', 'Nouveau client amené par')
    realisee_id         = fields.Many2one('res.users', 'Offre commerciale réalisée par')
    produit_cree_par_id = fields.Many2one('res.users', 'Réalisé grâce à 1 produit créé par')
    encadrement_par_id  = fields.Many2one('res.users', 'Encadrement du sous-traitant par')
