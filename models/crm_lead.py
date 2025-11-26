# -*- coding: utf-8 -*-
from odoo import api, fields, models

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    affaire_id          = fields.Many2one('is.affaire', 'Affaire')
    amene_par_id        = fields.Many2one('res.users', 'Nouveau client amené par')
    realisee_id         = fields.Many2one('res.users', 'Offre commerciale réalisée par')
    produit_cree_par_id = fields.Many2one('res.users', 'Réalisé grâce à 1 produit créé par')
    encadrement_par_id  = fields.Many2one('res.users', 'Encadrement du sous-traitant par')



class mail_activity(models.Model):
    _inherit = 'mail.activity'

    is_partner_id = fields.Many2one('res.partner', 'Partenaire', compute='_compute_is_partner_id', readonly=True, store=True)

    @api.depends('res_model','res_id')
    def _compute_is_partner_id(self):
        for obj in self:
            partner_id = False
            if obj.res_model=='res.partner':
                partner_id= obj.res_id
            obj.is_partner_id = partner_id






