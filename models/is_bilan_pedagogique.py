# -*- coding: utf-8 -*-
from odoo import api, fields, models
import datetime


class is_bilan_pedagogique(models.Model):
    _name='is.bilan.pedagogique'
    _description='is.bilan.pedagogique'
    _order='name desc'
    _sql_constraints = [('name_uniq','UNIQUE(name)', u'Cette année existe déjà')]

    name                  = fields.Integer("Année", required=True, index=True)
    financier_ids         = fields.One2many('is.bilan.pedagogique.financier', 'bilan_id', string='C - Bilan financier par origine du financement')
    vente_outil           = fields.Integer("C - Produits résultant de la vente d'outils pédagogique")
    sous_traitance        = fields.Integer("D - Honoraires de sous-traitance")
    heure_formation       = fields.Integer("E - Nombre d'heures de formation associés")
    heure_formation_st    = fields.Integer("E - Nombre d'heures de formation des sous-traitant")

    type_stagiaire_ids    = fields.One2many('is.bilan.pedagogique.type.stagiaire', 'bilan_id', string="F1a - Type de stagiaires de l'organisme")

    f2a_nb_stagiaire    = fields.Integer("F2a - Formés par votre organisme pour son propre compte - Nombre de stagiaires")
    f2a_heure_formation = fields.Integer("F2a - Formés par votre organisme pour son propre compte - Nombre total d'heures")

    f2b_nb_stagiaire    = fields.Integer("F2b - Formés par votre organisme pour le compte d'un autre organisme - Nombre de stagiaires")
    f2b_heure_formation = fields.Integer("F2b - Formés par votre organisme pour le compte d'un autre organisme - Nombre total d'heures")

    typologie_ids         = fields.One2many('is.bilan.pedagogique.typologie', 'bilan_id', string="F3 - Objectif général des formations dispensées")

    nb_stagiaire_autre    = fields.Integer("G - Nombre de stagiaires confiés à un autre organisme de formation")
    heure_formation_autre = fields.Integer("G - Total heures formation stagiaires confiés à un autre organisme de formation")


    def action_calculer(self):
        for obj in self:
            self._calculer_bilan(obj)


    def _calculer_bilan(self, obj):
        date_from = f"{obj.name}-01-01"
        date_to   = f"{obj.name}-12-31"

        # C - Bilan financier par origine du financement *******************
        obj.financier_ids.unlink()
        financements = self.env['is.origine.financement'].search([])
        for financement in financements:
            financier_rec = self.env['is.bilan.pedagogique.financier'].create({
                'bilan_id'               : obj.id,
                'origine_financement_id' : financement.id,
                'bilan_financier'        : 0,
            })
            interventions = financier_rec._get_interventions()
            financier_rec.bilan_financier = sum(i.montant_facture for i in interventions)

        cr=self._cr

        # C - Produits résultant de la vente d'outils pédagogique **********
        sql="""
            select sum(iav.total_vente)
            from is_affaire_vente iav inner join is_affaire ia on iav.affaire_id=ia.id
                                      inner join product_template pt on ia.article_id=pt.id
            where iav.date>='"""+date_from+"""' and 
                  iav.date<='"""+date_to+"""' and
                  iav.product_id is not null and
                  (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%' or pt.name->>'fr_FR' ilike '%CAMPUS%')
        """
        cr.execute(sql)
        vente_outil=0
        for row in cr.fetchall():
            if row[0]:
                vente_outil=row[0]
        obj.vente_outil=vente_outil

        sql="""
            select sum(ail.quantity*price_unit)
            from account_move_line ail inner join account_move ai on ail.move_id=ai.id
                                          inner join product_product pp on ail.product_id=pp.id
                                          inner join res_partner     rp on ai.partner_id=rp.id 
            where ai.invoice_date>='"""+date_from+"""' and 
                  ai.invoice_date<='"""+date_to+"""' and
                  ai.move_type='in_invoice' and
                  rp.name='SOUS-TRAITANTS' 
        """
        cr.execute(sql)
        sous_traitance=0
        for row in cr.fetchall():
            if row[0]:
                sous_traitance=row[0]
        obj.sous_traitance=sous_traitance


        # E - Nombre d'heure de formation associés *************************
        sql="""
            select sum(iai.temps_formation/coalesce(NULLIF(iai.nb_stagiaire,0),1))
            from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                             inner join product_template pt on ia.article_id=pt.id
            where iai.date>='"""+date_from+"""' and 
                  iai.date<='"""+date_to+"""' and
                  iai.associe_id is not null and
                  (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%' or pt.name->>'fr_FR' ilike '%CAMPUS%')
        """
        cr.execute(sql)
        heure_formation=0
        for row in cr.fetchall():
            if row[0]:
                heure_formation=row[0]
        obj.heure_formation=heure_formation


        # E - Nombre d'heures de formation des sous-traitant ***************
        sql="""
            select sum(iai.temps_formation/coalesce(NULLIF(iai.nb_stagiaire,0),1))
            from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                             inner join product_template pt on ia.article_id=pt.id
            where iai.date>='"""+date_from+"""' and 
                  iai.date<='"""+date_to+"""' and
                  iai.associe_id is null and iai.sous_traitant_id is not null  and
                  (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%' or pt.name->>'fr_FR' ilike '%CAMPUS%')
        """
        cr.execute(sql)
        heure_formation_st=0
        for row in cr.fetchall():
            if row[0]:
                heure_formation_st=row[0]
        obj.heure_formation_st=heure_formation_st


        # F1 - Type de stagiaire de l'organisme ****************************
        obj.type_stagiaire_ids.unlink()
        type_stagiaires = [False] + self.env['is.type.stagiaire.organisme'].search([]).ids
        for type_stagiaire_id in type_stagiaires:
            ts_rec = self.env['is.bilan.pedagogique.type.stagiaire'].create({
                'bilan_id'                   : obj.id,
                'type_stagiaire_organisme_id': type_stagiaire_id,
                'nb_stagiaire'               : 0,
                'nb_stagiaire_visio'         : 0,
                'nb_heure'                   : 0,
            })
            interventions             = ts_rec._get_interventions()
            affaires                  = interventions.mapped('affaire_id')
            ts_rec.nb_stagiaire       = sum(a.nb_stagiaire for a in affaires)
            ts_rec.nb_stagiaire_visio = sum(a.nb_stagiaire_visio for a in affaires)
            ts_rec.nb_heure           = sum(i.temps_formation for i in interventions)


        # F3 - Objectif général des formations dispensées ***************
        obj.typologie_ids.unlink()
        res=self.env['is.typologie.stagiaire'].search([])
        typologies=[]
        typologies.append(False)
        for r in res:
            typologies.append(r.id)
        for typologie in typologies:
            # nb_stagiaire
            sql="""
                select ia.id, max(ia.nb_stagiaire)
                from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                                 inner join product_template pt on ia.article_id=pt.id
                where iai.date>='"""+date_from+"""' and 
                      iai.date<='"""+date_to+"""' and
                      (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%' or pt.name->>'fr_FR' ilike '%CAMPUS%')
            """
            if typologie:
                sql=sql+" and ia.typologie_stagiaire_id="+str(typologie)+" "
            else:
                sql=sql+" and ia.typologie_stagiaire_id is null "
            sql=sql+"group by ia.id"
            cr.execute(sql)
            nb_stagiaire=0
            for row in cr.fetchall():
                if row[1]:
                    nb_stagiaire=nb_stagiaire+row[1]

            # nb_heure
            sql="""
                select sum(iai.temps_formation)
                from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                                 inner join product_template pt on ia.article_id=pt.id
                where iai.date>='"""+date_from+"""' and 
                      iai.date<='"""+date_to+"""' and
                      (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%' or pt.name->>'fr_FR' ilike '%CAMPUS%')
            """
            if typologie:
                sql=sql+" and ia.typologie_stagiaire_id="+str(typologie)+" "
            else:
                sql=sql+" and ia.typologie_stagiaire_id is null "
            cr.execute(sql)
            nb_heure=0
            for row in cr.fetchall():
                if row[0]:
                    nb_heure=row[0]
            vals={
                'bilan_id'     : obj.id,
                'typologie_id' : typologie,
                'nb_stagiaire' : nb_stagiaire,
                'nb_heure'     : nb_heure,
            }
            self.env['is.bilan.pedagogique.typologie'].create(vals)


        # F2a - Nombre de stagiaires
        sql="""
            select ia.id, max(ia.nb_stagiaire)
            from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                             inner join product_template pt on ia.article_id=pt.id
                                             left outer join is_origine_financement iof on ia.origine_financement_id=iof.id
            where iai.date>='"""+date_from+"""' and 
                  iai.date<='"""+date_to+"""' and
                  (iof.name not like '11%' or iof.name is null) and 
                  (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%' or pt.name->>'fr_FR' ilike '%CAMPUS%')
            group by ia.id
        """
        cr.execute(sql)
        f2a_nb_stagiaire=0
        for row in cr.fetchall():
            if row[1]:
                f2a_nb_stagiaire=f2a_nb_stagiaire+row[1]
        obj.f2a_nb_stagiaire=f2a_nb_stagiaire


        # F2a - Nombre total d'heures
        sql="""
            select sum(iai.temps_formation)
            from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                             inner join product_template pt on ia.article_id=pt.id
                                             left outer join is_origine_financement iof on ia.origine_financement_id=iof.id
            where iai.date>='"""+date_from+"""' and 
                  iai.date<='"""+date_to+"""' and
                  (iof.name not like '11%' or iof.name is null) and
                  (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%' or pt.name->>'fr_FR' ilike '%CAMPUS%')
        """
        cr.execute(sql)
        f2a_heure_formation=0
        for row in cr.fetchall():
            if row[0]:
                f2a_heure_formation=f2a_heure_formation+row[0]
        obj.f2a_heure_formation=f2a_heure_formation


        # F2b - Nombre de stagiaires
        sql="""
            select ia.id, max(ia.nb_stagiaire)
            from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                             inner join product_template pt on ia.article_id=pt.id
                                             left outer join is_origine_financement iof on ia.origine_financement_id=iof.id
            where iai.date>='"""+date_from+"""' and 
                  iai.date<='"""+date_to+"""' and
                  iof.name like '11%' and
                  (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%' or pt.name->>'fr_FR' ilike '%CAMPUS%')
            group by ia.id
        """
        cr.execute(sql)
        f2b_nb_stagiaire=0
        for row in cr.fetchall():
            if row[1]:
                f2b_nb_stagiaire=f2b_nb_stagiaire+row[1]
        obj.f2b_nb_stagiaire=f2b_nb_stagiaire


        # F2b - Nombre total d'heures
        sql="""
            select sum(iai.temps_formation)
            from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                             inner join product_template pt on ia.article_id=pt.id
                                             left outer join is_origine_financement iof on ia.origine_financement_id=iof.id
            where iai.date>='"""+date_from+"""' and 
                  iai.date<='"""+date_to+"""' and
                  iof.name like '11%' and
                  (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%' or pt.name->>'fr_FR' ilike '%CAMPUS%')
        """
        cr.execute(sql)
        f2b_heure_formation=0
        for row in cr.fetchall():
            if row[0]:
                f2b_heure_formation=f2b_heure_formation+row[0]
        obj.f2b_heure_formation=f2b_heure_formation


        # G - Nombre de stagiaires confiés à un autre organisme de formation
        sql="""
            select ia.id, max(ia.nb_stagiaire)
            from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                             inner join product_template pt on ia.article_id=pt.id
            where iai.date>='"""+date_from+"""' and 
                  iai.date<='"""+date_to+"""' and
                  iai.sous_traitant_id is not null and
                  (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%' or pt.name->>'fr_FR' ilike '%CAMPUS%')
            group by ia.id
        """
        cr.execute(sql)
        nb_stagiaire_autre=0
        for row in cr.fetchall():
            if row[1]:
                nb_stagiaire_autre=nb_stagiaire_autre+row[1]
        obj.nb_stagiaire_autre=nb_stagiaire_autre


        # G - Total heures formation stagiaires confiés à un autre organisme de formation
        sql="""
            select sum(iai.temps_formation)
            from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                             inner join product_template pt on ia.article_id=pt.id
            where iai.date>='"""+date_from+"""' and 
                  iai.date<='"""+date_to+"""' and
                  iai.sous_traitant_id is not null and
                  (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%' or pt.name->>'fr_FR' ilike '%CAMPUS%')
        """
        cr.execute(sql)
        heure_formation_autre=0
        for row in cr.fetchall():
            heure_formation_autre=row[0]
        obj.heure_formation_autre=heure_formation_autre


class is_bilan_pedagogique_financier(models.Model):
    _name='is.bilan.pedagogique.financier'
    _description='is.bilan.pedagogique.financier'
    _order='origine_financement_id'

    bilan_id               = fields.Many2one('is.bilan.pedagogique', string='Bilan Pédagogique')
    origine_financement_id = fields.Many2one('is.origine.financement', string='Origine du financement')
    bilan_financier        = fields.Float("Bilan Financier")

    def _get_interventions(self):
        self.ensure_one()
        date_from = f"{self.bilan_id.name}-01-01"
        date_to   = f"{self.bilan_id.name}-12-31"
        return self.env['is.affaire.intervention'].search([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('affaire_id.origine_financement_id', '=', self.origine_financement_id.id),
        ])

    def action_voir_interventions(self):
        self.ensure_one()
        interventions = self._get_interventions()
        return {
            'type'      : 'ir.actions.act_window',
            'name'      : f"Interventions - {self.origine_financement_id.name}",
            'res_model' : 'is.affaire.intervention',
            'view_mode' : 'list,form',
            'views'     : [
                (self.env.ref('is_coheliance18.is_affaire_intervention_bilan_list').id, 'list'),
                (False, 'form'),
            ],
            'domain'    : [('id', 'in', interventions.ids)],
            'limit'     : 500,
        }



class is_bilan_pedagogique_type_stagiaire(models.Model):
    _name='is.bilan.pedagogique.type.stagiaire'
    _description='is.bilan.pedagogique.type.stagiaire'
    _order='type_stagiaire_organisme_id'

    bilan_id                    = fields.Many2one('is.bilan.pedagogique', string='Bilan Pédagogique')
    type_stagiaire_organisme_id = fields.Many2one('is.type.stagiaire.organisme', string="Type de stagiaire de l'organisme")
    nb_stagiaire                = fields.Float("Nombre de stagiaires")
    nb_stagiaire_visio          = fields.Float("Nombre de stagiaires en visio")
    nb_heure                    = fields.Float("Nombre total d'heures de formation suivies par l'ensemble des stagiaires")

    def _get_interventions(self):
        self.ensure_one()
        date_from = f"{self.bilan_id.name}-01-01"
        date_to   = f"{self.bilan_id.name}-12-31"
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            '|', ('affaire_id.origine_financement_id.name', 'not like', '11%'),
                 ('affaire_id.origine_financement_id', '=', False),
            '|', '|',
            ('affaire_id.article_id.name', 'ilike', 'FORMATION'),
            ('affaire_id.article_id.name', 'ilike', 'STAGE'),
            ('affaire_id.article_id.name', 'ilike', 'CAMPUS'),
        ]
        if self.type_stagiaire_organisme_id:
            domain.append(('affaire_id.type_stagiaire_organisme_id', '=', self.type_stagiaire_organisme_id.id))
        else:
            domain.append(('affaire_id.type_stagiaire_organisme_id', '=', False))
        return self.env['is.affaire.intervention'].search(domain)

    def action_voir_interventions(self):
        self.ensure_one()
        interventions = self._get_interventions()
        label = self.type_stagiaire_organisme_id.name if self.type_stagiaire_organisme_id else "Non défini"
        return {
            'type'      : 'ir.actions.act_window',
            'name'      : f"Interventions - {label}",
            'res_model' : 'is.affaire.intervention',
            'view_mode' : 'list,form',
            'views'     : [
                (self.env.ref('is_coheliance18.is_affaire_intervention_bilan_list').id, 'list'),
                (False, 'form'),
            ],
            'domain'    : [('id', 'in', interventions.ids)],
            'limit'     : 500,
        }



class is_bilan_pedagogique_typologie(models.Model):
    _name='is.bilan.pedagogique.typologie'
    _description='is.bilan.pedagogique.typologie'
    _order='typologie_id'

    bilan_id     = fields.Many2one('is.bilan.pedagogique', string='Bilan Pédagogique')
    typologie_id = fields.Many2one('is.typologie.stagiaire', string='Objectif général des prestations dispensées')
    nb_stagiaire = fields.Float("Nombre de stagiaires")
    nb_heure     = fields.Float("Nombre total d'heures de formation suivies par l'ensemble des stagiaires")


class is_origine_financement(models.Model):
    _name = 'is.origine.financement'
    _description = 'is.origine.financement'
    _order='name'

    name = fields.Char('Origine financement', required=True)


class is_type_stagiaire_organisme(models.Model):
    _name = 'is.type.stagiaire.organisme'
    _description = 'is.type.stagiaire.organisme'
    _order='name'

    name = fields.Char("Type de stagiaire de l'organisme", required=True)


class is_typologie_stagiaire(models.Model):
    _name = 'is.typologie.stagiaire'
    _description = 'is.typologie.stagiaire'
    _order='name'

    name = fields.Char('Objectif général des prestations dispensées', required=True)






