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
        cr=self._cr
        for obj in self:

            # C - Bilan financier par origine du financement *******************
            obj.financier_ids.unlink()
            financements=self.env['is.origine.financement'].search([])
            for financement in financements:
                sql="""
                    select sum(iai.montant_facture)
                    from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                    where iai.date>='"""+str(obj.name)+"""-01-01' and 
                          iai.date<='"""+str(obj.name)+"""-12-31' and
                          ia.origine_financement_id="""+str(financement.id)+"""
                """
                cr.execute(sql)
                bilan_financier=0
                for row in cr.fetchall():
                    if row[0]:
                        bilan_financier=row[0]
                vals={
                    'bilan_id'               : obj.id,
                    'origine_financement_id' : financement.id,
                    'bilan_financier'        : bilan_financier,
                }
                self.env['is.bilan.pedagogique.financier'].create(vals)

            # C - Produits résultant de la vente d'outils pédagogique **********
            sql="""
                select sum(iav.total_vente)
                from is_affaire_vente iav inner join is_affaire ia on iav.affaire_id=ia.id
                                          inner join product_template pt on ia.article_id=pt.id
                where iav.date>='"""+str(obj.name)+"""-01-01' and 
                      iav.date<='"""+str(obj.name)+"""-12-31' and
                      iav.product_id is not null and
                      (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
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
                where ai.invoice_date>='"""+str(obj.name)+"""-01-01' and 
                      ai.invoice_date<='"""+str(obj.name)+"""-12-31' and
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
                where iai.date>='"""+str(obj.name)+"""-01-01' and 
                      iai.date<='"""+str(obj.name)+"""-12-31' and
                      iai.associe_id is not null and
                      (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
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
                where iai.date>='"""+str(obj.name)+"""-01-01' and 
                      iai.date<='"""+str(obj.name)+"""-12-31' and
                      iai.associe_id is null and iai.sous_traitant_id is not null  and
                      (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
            """
            cr.execute(sql)
            heure_formation_st=0
            for row in cr.fetchall():
                if row[0]:
                    heure_formation_st=row[0]
            obj.heure_formation_st=heure_formation_st





            # F1 - Type de stagiaire de l'organisme ****************************
            obj.type_stagiaire_ids.unlink()
            res=self.env['is.type.stagiaire.organisme'].search([])
            type_stagiaires=[]
            type_stagiaires.append(False)
            for r in res:
                type_stagiaires.append(r.id)
            for type_stagiaire in type_stagiaires:
                # nb_stagiaire
                sql="""
                    select ia.id, max(ia.nb_stagiaire), max(ia.nb_stagiaire_visio)
                    from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                                     inner join product_template pt on ia.article_id=pt.id
                                                     left outer join is_origine_financement iof on ia.origine_financement_id=iof.id
                    where iai.date>='"""+str(obj.name)+"""-01-01' and 
                          iai.date<='"""+str(obj.name)+"""-12-31' and
                          (iof.name not like '11%' or iof.name is null) and
                          (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
                """
                if type_stagiaire:
                    sql=sql+" and ia.type_stagiaire_organisme_id="""+str(type_stagiaire)+" "
                else:
                    sql=sql+" and ia.type_stagiaire_organisme_id is null "
                sql=sql+"group by ia.id"
                cr.execute(sql)
                nb_stagiaire       = 0
                nb_stagiaire_visio = 0
                for row in cr.fetchall():
                    if row[1]:
                        nb_stagiaire       += row[1]
                        nb_stagiaire_visio += row[2]

                # nb_heure
                sql="""
                    select sum(iai.temps_formation)
                    from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                                     inner join product_template pt on ia.article_id=pt.id
                                                     left outer join is_origine_financement iof on ia.origine_financement_id=iof.id
                    where iai.date>='"""+str(obj.name)+"""-01-01' and 
                          iai.date<='"""+str(obj.name)+"""-12-31' and
                          (iof.name not like '11%' or iof.name is null) and
                          (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
                """
                if type_stagiaire:
                    sql=sql+" and ia.type_stagiaire_organisme_id="""+str(type_stagiaire)+" "
                else:
                    sql=sql+" and ia.type_stagiaire_organisme_id is null "
                cr.execute(sql)
                nb_heure=0
                for row in cr.fetchall():
                    if row[0]:
                        nb_heure     = row[0]
                vals={
                    'bilan_id'     : obj.id,
                    'type_stagiaire_organisme_id': type_stagiaire,
                    'nb_stagiaire'               : nb_stagiaire ,
                    'nb_stagiaire_visio'         : nb_stagiaire_visio ,
                    'nb_heure'                   : nb_heure,
                }
                self.env['is.bilan.pedagogique.type.stagiaire'].create(vals)


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
                    where iai.date>='"""+str(obj.name)+"""-01-01' and 
                          iai.date<='"""+str(obj.name)+"""-12-31' and
                          (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
                """
                if typologie:
                    sql=sql+" and ia.typologie_stagiaire_id="""+str(typologie)+" "
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
                    where iai.date>='"""+str(obj.name)+"""-01-01' and 
                          iai.date<='"""+str(obj.name)+"""-12-31' and
                          (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
                """
                if typologie:
                    sql=sql+" and ia.typologie_stagiaire_id="""+str(typologie)+" "
                else:
                    sql=sql+" and ia.typologie_stagiaire_id is null "
                #sql=sql+"group by ia.id"
                cr.execute(sql)
                nb_heure=0
                for row in cr.fetchall():
                    if row[0]:
                        nb_heure     = row[0]
                vals={
                    'bilan_id'     : obj.id,
                    'typologie_id' : typologie,
                    'nb_stagiaire' : nb_stagiaire ,
                    'nb_heure'     : nb_heure,
                }
                self.env['is.bilan.pedagogique.typologie'].create(vals)


            # F2a - Nombre de stagiaires
            sql="""
                select ia.id, max(ia.nb_stagiaire)
                from is_affaire_intervention iai inner join is_affaire ia on iai.affaire_id=ia.id
                                                 inner join product_template pt on ia.article_id=pt.id
                                                 left outer join is_origine_financement iof on ia.origine_financement_id=iof.id
                where iai.date>='"""+str(obj.name)+"""-01-01' and 
                      iai.date<='"""+str(obj.name)+"""-12-31' and
                      (iof.name not like '11%' or iof.name is null) and 
                      (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
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
                where iai.date>='"""+str(obj.name)+"""-01-01' and 
                      iai.date<='"""+str(obj.name)+"""-12-31' and
                      (iof.name not like '11%' or iof.name is null) and
                      (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
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
                where iai.date>='"""+str(obj.name)+"""-01-01' and 
                      iai.date<='"""+str(obj.name)+"""-12-31' and
                      iof.name like '11%' and
                      (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
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
                where iai.date>='"""+str(obj.name)+"""-01-01' and 
                      iai.date<='"""+str(obj.name)+"""-12-31' and
                      iof.name like '11%' and
                      (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
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
                where iai.date>='"""+str(obj.name)+"""-01-01' and 
                      iai.date<='"""+str(obj.name)+"""-12-31' and
                      iai.sous_traitant_id is not null and
                      (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
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
                where iai.date>='"""+str(obj.name)+"""-01-01' and 
                      iai.date<='"""+str(obj.name)+"""-12-31' and
                      iai.sous_traitant_id is not null and
                      (pt.name->>'fr_FR' ilike '%FORMATION%' or pt.name->>'fr_FR' ilike '%STAGE%')
            """
            cr.execute(sql)
            heure_formation_autre = 0
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



class is_bilan_pedagogique_type_stagiaire(models.Model):
    _name='is.bilan.pedagogique.type.stagiaire'
    _description='is.bilan.pedagogique.type.stagiaire'
    _order='type_stagiaire_organisme_id'

    bilan_id                    = fields.Many2one('is.bilan.pedagogique', string='Bilan Pédagogique')
    type_stagiaire_organisme_id = fields.Many2one('is.type.stagiaire.organisme', string="Type de stagiaire de l'organisme")
    nb_stagiaire                = fields.Float("Nombre de stagiaires")
    nb_stagiaire_visio          = fields.Float("Nombre de stagiaires en visio")
    nb_heure                    = fields.Float("Nombre total d'heures de formation suivies par l'ensemble des stagiaires")



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






