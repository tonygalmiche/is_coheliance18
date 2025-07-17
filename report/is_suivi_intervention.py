# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class is_suivi_intervention(models.Model):
    _name='is.suivi.intervention'
    _description='is.suivi.intervention'
    _order='date desc, affaire_id'
    _auto = False

    affaire_id          = fields.Many2one('is.affaire', u'Affaire')
    client_id           = fields.Many2one('res.partner', u'Client')
    secteur_activite_id = fields.Many2one('is.secteur.activite', "Secteur d'activité")
    typologie_id        = fields.Many2one('is.typologie', "Typologie")
    intitule            = fields.Text(u"Intitulé")
    article_id          = fields.Many2one('product.template', u'Article')
    date                = fields.Date(u"Date", required=True)
    associe_id          = fields.Many2one('res.users', u'Associé')
    sous_traitant_id    = fields.Many2one('res.partner', u'Sous-Traitant')
    temps_passe         = fields.Float(u"Temps passé")
    unite_temps         = fields.Selection([('heure','Heure'),('demi-jour','Demi-journée'),('jour','Jour')], u"Unité de temps")
    temps_passe_heure   = fields.Float(string="Temps passé (H)")
    montant_facture     = fields.Float('Montant à facturer')
    commentaire         = fields.Text(u"Commentaire")


    def init(self):
        cr=self.env.cr
        tools.drop_view_if_exists(cr, 'is_suivi_intervention')
        cr.execute("""
            CREATE OR REPLACE view is_suivi_intervention AS (
                select 
                    iai.id,
                    ia.id affaire_id,
                    ia.client_id,
                    ia.intitule,
                    ia.article_id,
                    iai.date,
                    iai.associe_id,
                    iai.sous_traitant_id,
                    iai.temps_passe,
                    iai.unite_temps,
                    iai.temps_passe_heure,
                    iai.montant_facture,
                    iai.commentaire,
                    rp.is_secteur_activite_id secteur_activite_id ,
                    rp.is_typologie_id        typologie_id
                from is_affaire ia inner join is_affaire_intervention iai on ia.id=iai.affaire_id
                                   inner join res_partner rp on ia.client_id=rp.id
            )
        """)



