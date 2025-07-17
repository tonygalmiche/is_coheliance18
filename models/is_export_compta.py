# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError  
from odoo.addons.is_coheliance18.models.is_coheliance import STRUCTURE
import datetime


class is_export_compta(models.Model):
    _name='is.export.compta'
    _description = u"Export en compta"
    _order='name desc'

    name               = fields.Char("N°Folio"      , readonly=True)
    type_interface     = fields.Selection([('ventes', u'Ventes'),('achats', u'Achats'),('banque', u'Banque')], "Interface", required=True)
    date_debut         = fields.Date("Date de début")
    date_fin           = fields.Date("Date de fin")
    num_debut          = fields.Char("N° facture début")
    num_fin            = fields.Char("N° facture fin")

    ligne_ids          = fields.One2many('is.export.compta.ligne', 'export_compta_id', u'Lignes')


    _defaults = {
        'type_interface':  'ventes',
    }


    # @api.model
    # def create(self, vals):
    #     data_obj = self.env['ir.model.data']
    #     sequence_ids = data_obj.search([('name','=','is_export_compta_seq')])
    #     if sequence_ids:
    #         sequence_id = data_obj.browse(sequence_ids[0].id).res_id
    #         vals['name'] = self.env['ir.sequence'].get_id(sequence_id, 'id')
    #     res = super(is_export_compta, self).create(vals)
    #     return res


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('is.export.compta')
        return super().create(vals_list)






    def action_export_compta(self):
        cr=self._cr
        for obj in self:
            obj.ligne_ids.unlink()

            if obj.type_interface=='ventes' or obj.type_interface=='achats':

                if obj.type_interface=='ventes':
                    type_facture=['out_invoice', 'out_refund']
                    journal='VTE'
                else:
                    type_facture=['in_invoice', 'in_refund']
                    journal='AC'
                filter=[
                    ('state'    , 'in' , ['posted']),
                    ('move_type', 'in' , type_facture)
                ]
                if obj.date_debut:
                    filter.append(('invoice_date', '>=', obj.date_debut))
                if obj.date_fin:
                    filter.append(('invoice_date', '<=', obj.date_fin))
                if obj.num_debut:
                    filter.append(('name', '>=', obj.num_debut))
                if obj.num_fin:
                    filter.append(('name', '<=', obj.num_fin))
                invoices = self.env['account.move'].search(filter, order="invoice_date,id")
                if len(invoices)==0:
                    raise ValidationError('Aucune facture à traiter')
                for invoice in invoices:
                    sql="""
                        SELECT  
                            am.invoice_date,
                            aa.code, 
                            am.name, 
                            rp.name, 
                            aml.name,
                            am.move_type, 
                            rp.is_code_fournisseur,
                            am.is_nom_fournisseur,
                            aml.account_id,
                            am.is_affaire_id,
                            am.id,
                            sum(aml.debit), 
                            sum(aml.credit)

                        FROM account_move_line aml inner join account_move am                on aml.move_id=am.id
                                                   inner join account_account aa             on aml.account_id=aa.id
                                                   inner join res_partner rp                 on am.partner_id=rp.id
                        WHERE am.id="""+str(invoice.id)+"""
                        GROUP BY am.invoice_date, am.name, rp.name, aml.name, aa.code, am.move_type, am.invoice_date_due, rp.is_code_fournisseur,am.is_nom_fournisseur,aml.account_id,am.is_affaire_id,am.id
                        ORDER BY am.invoice_date, am.name, rp.name, aml.name, aa.code, am.move_type, am.invoice_date_due, rp.is_code_fournisseur,am.is_nom_fournisseur,aml.account_id,am.is_affaire_id,am.id
                    """
                    cr.execute(sql)
                    for row in cr.fetchall():

                        #** Recherche de l'affaire *********************************
                        affaire = structure = ''
                        affaire_id = row[9] or False
                        filter=[
                            ('move_id', '=', row[10]),
                            ('account_id', '=', row[8]),
                            ('name'      , '=', row[4]),
                        ]
                        lines = self.env['account.move.line'].search(filter)
                        for line in lines:
                            if line.is_affaire_id.id:
                                affaire_id = line.is_affaire_id.id
                        if affaire_id : 
                            affaire_obj = self.env['is.affaire'].browse(affaire_id)
                            affaire   = affaire_obj.name
                            structure = affaire_obj.structure
                        #***********************************************************

                        nom_fournisseur=row[7]
                        if nom_fournisseur==None:
                            nom_fournisseur=row[3]
                        libelle=nom_fournisseur+' - '+(row[4] or '')
                        libelle=libelle.replace("\n"," ")[:200]
                        compte=str(row[1])
                        if obj.type_interface=='achats' and compte=='401100':
                            compte=str(row[6])
                        vals={
                            'export_compta_id'  : obj.id,
                            'date_facture'      : row[0],
                            'journal'           : journal,
                            'compte'            : compte,
                            'libelle'           : libelle,
                            'affaire'           : affaire,
                            'debit'             : row[11],
                            'credit'            : row[12],
                            'devise'            : 'E',
                            'piece'             : row[2],
                            'structure'         : structure,
                            'commentaire'       : False,
                        }
                        self.env['is.export.compta.ligne'].create(vals)


class is_export_compta_ligne(models.Model):
    _name = 'is.export.compta.ligne'
    _description = u"Lignes d'export en compta"
    _order='date_facture'

    export_compta_id = fields.Many2one('is.export.compta', 'Export Compta', required=True)
    date_facture     = fields.Date("Date")
    journal          = fields.Char("Journal")
    compte           = fields.Char("N°Compte")
    piece            = fields.Char("Pièce")
    libelle          = fields.Char("Libellé")
    affaire          = fields.Char('Affaire')
    debit            = fields.Float("Débit")
    credit           = fields.Float("Crédit")
    devise           = fields.Char("Devise")
    structure        = fields.Selection(selection=STRUCTURE, string="Structure")
    commentaire      = fields.Char("Commentaire")


    _defaults = {
        'journal': 'VTE',
        'devise' : 'E',
    }

