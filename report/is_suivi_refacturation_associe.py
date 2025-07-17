# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class is_suivi_refacturation_associe(models.Model):
    _name='is.suivi.refacturation.associe'
    _description='is.suivi.refacturation.associe'
    _order='date desc'
    _auto = False

    type_donnee           = fields.Char('Type de donnée')
    affaire_id            = fields.Many2one('is.affaire', u'Affaire')
    associe_id            = fields.Many2one('res.users', u'Associé')
    type_frais            = fields.Char(u'Type de frais')
    type_frais_km         = fields.Char(u'Frais Km ou autres frais')
    is_type_frais_hors_km = fields.Boolean('Type de frais hors km')
    montant               = fields.Float('Montant')
    km                    = fields.Integer('Km')
    donnee                = fields.Float('Donnée')
    date                  = fields.Date('Date')
    commentaire           = fields.Char('Commentaire')


    def init(self):
        cr=self.env.cr
        tools.drop_view_if_exists(cr, 'is_suivi_refacturation_associe')
        cr.execute("""

            CREATE OR REPLACE FUNCTION is_frais_km(frais text) RETURNS text AS $$
                    BEGIN
                        IF frais ='' THEN
                            RETURN '';
                        END IF;
                        IF frais ='FRAIS DEPLACEMENT KM' THEN
                            RETURN 'FRAIS DEPLACEMENT KM';
                        ELSE
                            IF frais ='FRAIS DEPLACEMENT KM SANS TVA' THEN
                                RETURN 'FRAIS DEPLACEMENT KM';
                            ELSE
                                RETURN 'AUTRES FRAIS';
                            END IF;
                        END IF;
                    END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE view is_suivi_refacturation_associe AS (
                select 
                    id+1000000 as id, 
                    'intervention' as type_donnee, 
                    affaire_id, 
                    associe_id, 
                    '' as type_frais, 
                    '' as type_frais_km, 
                    'f' as is_type_frais_hors_km, 
                    date, 
                    montant_facture as montant, 
                    0 as km,
                    montant_facture as donnee, 
                    commentaire as commentaire
                from is_affaire_intervention 
                where associe_id is not null and montant_facture!=0 

                Union

                select 
                    ifl.id+2000000 as id, 
                    'frais' as type_donnee, 
                    if.affaire_id, 
                    if.intervenant_id as associe_id, 
                    pt.name->>'fr_FR' as type_frais, 
                    is_frais_km(pt.name->>'fr_FR') as type_frais_km, 
                    pt.is_type_frais_hors_km as is_type_frais_hors_km, 
                    ifl.date, 
                    ifl.montant_ht  as montant, 
                    0 as km,
                    ifl.montant_ht  as donnee, 
                    '' as commentaire
                from is_frais if inner join is_frais_ligne ifl on if.id=ifl.frais_id 
                                 left outer join product_template pt on ifl.type_frais_id=pt.id


                Union

                select 
                    ifl.id+3000000       as id, 
                    'km'                 as type_donnee, 
                    if.affaire_id, 
                    if.intervenant_id    as associe_id, 
                    pt.name->>'fr_FR'              as type_frais, 
                    is_frais_km(pt.name->>'fr_FR') as type_frais_km, 
                    pt.is_type_frais_hors_km as is_type_frais_hors_km, 
                    ifl.date, 
                    0                    as montant, 
                    ifl.km               as km,
                    ifl.km               as donnee,
                    ''                   as commentaire
                from is_frais if inner join is_frais_ligne ifl on if.id=ifl.frais_id 

                                 left outer join product_template pt on ifl.type_frais_id=pt.id


            )
        """)





