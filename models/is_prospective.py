# -*- coding: utf-8 -*-
from odoo import api, fields, models
import datetime


def _annee_creation():
    now=datetime.date.today()
    return now.strftime('%Y')


class is_prospective(models.Model):
    _name='is.prospective'
    _description='Prospective'
    _order='name desc'
    _sql_constraints = [('name_uniq','UNIQUE(name)', 'Cette année existe deja')]

    name     = fields.Integer("Année", required=True)
    state    = fields.Selection([('en_cours', 'En cours'),('termine', 'Terminé')], "État", readonly=True, index=True)
    line_ids = fields.One2many('is.prospective.line', 'prospective_id', 'Lignes')


    _defaults = {
        'name' : lambda *a: _annee_creation(),
        'state': 'en_cours',
    }


    def action_recalculer(self):
        cr      = self._cr
        for obj in self:
            sql="""
                select 
                    ia.id,
                    ia.date_creation,
                    ia.pilote_id,
                    ia.client_id,
                    ia.article_id,
                    ia.intitule,
                    ia.duree_prestation,
                    ia.budget_bas,
                    ia.budget_haut,
                    ia.budget_propose,
                    ia.budget_propose_annee,
                    ia.date_validation,
                    ia.date_solde,
                    ia.state
                from is_affaire ia
                where state<>'annule' 
            """
            line_obj = self.env['is.prospective.line']
            obj.line_ids.unlink()
            cr.execute(sql)
            for row in cr.fetchall():
                affaire_id      = str(row[0])
                date_creation   = str(row[1])
                date_solde      = str(row[12])
                if (date_solde=='None' or date_solde[:4]>=str(obj.name)) and date_creation[:4]<=str(obj.name):
                    associe01     = self.get_montant_intervenant(str(obj.name), affaire_id, 'o.laval@coheliance.com')      # Olivier
                    associe02     = self.get_montant_intervenant(str(obj.name), affaire_id, 'jp.fiasson@coheliance.com')   # JP
                    associe03     = self.get_montant_intervenant(str(obj.name), affaire_id, 'patrice@coheliance.com')      # Patrice
                    associe04     = self.get_montant_intervenant(str(obj.name), affaire_id, 'f.monjournal@coheliance.com') # Frédérique
                    associe05     = self.get_montant_intervenant(str(obj.name), affaire_id, 'i.boltz@coheliance.com')      # Isabelle
                    sous_traitant = self.get_montant_intervenant(str(obj.name), affaire_id, '')                            # Sous-traitance
                    total=associe01+associe02+associe03+associe04+associe05+sous_traitant
                    if total>0:
                        vals={
                            'prospective_id'      : obj.id,
                            'name'                : row[0],
                            'date_creation'       : row[1],
                            'pilote_id'           : row[2],
                            'client_id'           : row[3],
                            'article_id'          : row[4],
                            'intitule'            : row[5],
                            'duree_prestation'    : row[6],
                            'budget_bas'          : row[7],
                            'budget_haut'         : row[8],
                            'budget_propose'      : row[9],
                            'budget_propose_annee': row[10],
                            'date_validation'     : row[11],
                            'date_solde'          : row[12],
                            'state'               : row[13],
                            'associe01'           : associe01,
                            'associe02'           : associe02,
                            'associe03'           : associe03,
                            'associe04'           : associe04,
                            'associe05'           : associe05,
                            'sous_traitant'       : sous_traitant,
                            'total'               : total,
                        }
                        line_obj.create(vals)
            return self.action_detail_lignes()


    def action_detail_lignes(self):
        for obj in self:
            return {
                'name': "Lignes de prospective",
                'view_type': 'form',
                'view_mode': 'list,form',
                'res_model': 'is.prospective.line',
                'type': 'ir.actions.act_window',
                'limit': 200,
                'domain': [('prospective_id','=',obj.id)],
            }


    def get_montant_intervenant(self,annee, affaire_id, login):
        cr      = self._cr
        sql="""
            SELECT sum(iai.budget_prevu)
            FROM is_affaire_intervenant iai left outer join res_users ru on iai.associe_id=ru.id
            WHERE 
                iai.annee="""+annee+""" and
                iai.affaire_id="""+str(affaire_id)+""" 
        """
        if login!='':
            sql=sql+" and ru.login='"+login+"' "
        else:
            sql=sql+" and iai.sous_traitant_id is not null"
        cr.execute(sql)
        montant=0
        for row in cr.fetchall():
            montant=row[0]
        if str(montant)=='None':
            montant=0
        return montant


class is_prospective_line(models.Model):
    _name='is.prospective.line'
    _description='is.prospective.line'
    _order='name desc'

    prospective_id       = fields.Many2one('is.prospective', 'Année', required=True, ondelete='cascade')
    name                 = fields.Many2one('is.affaire', 'Affaire')
    date_creation        = fields.Date("Date de création")
    pilote_id            = fields.Many2one('res.users', 'Pilote')
    client_id            = fields.Many2one('res.partner', 'Client')
    article_id           = fields.Many2one('product.template', 'Article')
    intitule             = fields.Text("Intitulé")
    duree_prestation     = fields.Text("Durée de la prestation")
    budget_bas           = fields.Float("Budget bas")
    budget_haut          = fields.Float("Budget haut")
    budget_propose       = fields.Float("Budget proposé ")
    budget_propose_annee = fields.Float("Budget année en cours")
    date_validation      = fields.Date("Date de validation")
    date_solde           = fields.Date("Date annulé ou soldé")
    state                = fields.Selection(selection=[
                                ('en_attente', 'En attente'),
                                ('valide'    , 'Validé'),
                                ('annule'    , 'Annulé'),
                                ('solde'     , 'Soldé')], string="État", readonly=True, index=True)
    associe01            = fields.Integer("Olivier")
    associe02            = fields.Integer("JP")
    associe03            = fields.Integer("Patrice")
    associe04            = fields.Integer("Frédérique")
    associe05            = fields.Integer("Isabelle")
    sous_traitant        = fields.Integer("Sous traitance")
    total                = fields.Integer("Total")


