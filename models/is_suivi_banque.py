# -*- coding: utf-8 -*-
from odoo import api, fields, models
import datetime


def _date_creation():
    now  = datetime.date.today()
    return now.strftime('%Y-%m-%d')


class IsSuiviBanque(models.Model):
    _name='is.suivi.banque'
    _description='is.suivi.banque'
    _order='import_banque_id desc,ligne, id'


    def _compute_solde(self):
        cr = self._cr
        for obj in self:
            cr.execute("select sum(credit-debit) from is_suivi_banque where date<='"+str(obj.date)+"' and ligne>="+str(obj.ligne)+" ")
            obj.solde=cr.fetchone()[0] or 0.0


    import_banque_id = fields.Many2one('is.import.banque', 'Import Banque', required=True, ondelete='cascade')
    ligne            = fields.Integer("Ligne", index=True)
    date             = fields.Date("Date"   , required=True, index=True)
    libelle          = fields.Char("Libellé", required=True)
    ref_cb           = fields.Char("Réf CB")
    invoice_id       = fields.Many2one('account.move', u'Facture')
    debit            = fields.Float("Débit" , digits=(14,2))
    credit           = fields.Float("Crédit", digits=(14,2))
    solde            = fields.Float("Solde", compute=_compute_solde)
    commentaire      = fields.Char("Commentaire")


class IsImportBanque(models.Model):
    _name='is.import.banque'
    _description='is.import.banque'
    _order='name desc'

    name               = fields.Date(u"Date de création", default=lambda *a: _date_creation())
    banque = fields.Selection([
        ('BP', 'Banque Populaire'),
        ('SG', 'Société Générale'),
    ], 'Banque')
    file_operation_ids = fields.Many2many('ir.attachment', 'is_import_banque_operation_attachment_rel', 'doc_id', 'file_id', 'Opérations à importer')
    file_cb_ids        = fields.Many2many('ir.attachment', 'is_import_banque_cb_attachment_rel'       , 'doc_id', 'file_id', 'Détail CB à importer')
    ligne_ids          = fields.One2many('is.suivi.banque', 'import_banque_id', u'Lignes')


    def _ecrire_ligne(self,ligne,date,libelle,debit,credit):
        for obj in self:
            vals={
                'import_banque_id'  : obj.id,
                'ligne'             : (1000-ligne+1),
                'date'              : date,
                'libelle'           : libelle,
                'debit'             : debit,
                'credit'            : credit,
            }
            self.env['is.suivi.banque'].create(vals)


    def action_importer_fichier(self):
        for obj in self:
            if obj.banque=='BP':
                ct=0
                obj.ligne_ids.unlink()
                for attachment in obj.file_operation_ids:
                    attachment=base64.decodestring(attachment.datas)
                    attachment=attachment.decode('iso-8859-1').encode('utf8')
                    csvfile=attachment.split("\n")
                    tab=[]
                    for row in csvfile:
                        ct=ct+1
                        if ct>1:
                            lig=row.split(";")
                            if len(lig)>5:
                                date    = lig[1]
                                libelle = lig[3]
                                montant = lig[6].replace(',', '.')
                                try:
                                    montant = float(montant)
                                except ValueError:
                                    montant=0
                                debit=0
                                credit=0
                                if montant<0:
                                    debit=-montant
                                else:
                                    credit=montant
                                vals={
                                    'import_banque_id'  : obj.id,
                                    'ligne'             : (ct-1),
                                    'date'              : date,
                                    'libelle'           : libelle,
                                    'debit'             : debit,
                                    'credit'            : credit,
                                }
                                self.env['is.suivi.banque'].create(vals)
                for attachment in obj.file_cb_ids:
                    attachment=base64.decodestring(attachment.datas)
                    attachment=attachment.decode('iso-8859-1').encode('utf8')
                    csvfile=attachment.split("\n")
                    tab=[]
                    for row in csvfile:
                        ct=ct+1
                        if ct>1:
                            lig=row.split(";")
                            if len(lig)>5:
                                date    = lig[1]
                                libelle = lig[2]
                                ref_cb  = lig[3]
                                montant = lig[4].replace(',', '.')
                                try:
                                    montant = float(montant)
                                except ValueError:
                                    montant=0
                                debit=0
                                credit=0
                                if montant<0:
                                    debit=-montant
                                else:
                                    credit=montant
                                vals={
                                    'import_banque_id'  : obj.id,
                                    'ligne'             : (ct-1),
                                    'date'              : date,
                                    'libelle'           : libelle,
                                    'ref_cb'            : ref_cb,
                                    'debit'             : debit,
                                    'credit'            : credit,
                                }
                                self.env['is.suivi.banque'].create(vals)

            if obj.banque=='SG':
                ct=0
                obj.ligne_ids.unlink()
                for attachment in obj.file_operation_ids:
                    attachment=base64.decodestring(attachment.datas)
                    attachment=attachment.decode('iso-8859-1').encode('utf8')
                    csvfile=attachment.split("\n")
                    csvfile = csv.reader(csvfile, delimiter=';')
                    date=''
                    libelle=''
                    debit=0
                    credit=0
                    ligne=0
                    for ct, lig in enumerate(csvfile):
                        if len(lig)>=7:
                            ct=ct+1
                            if ct>1:
                                if lig[0]:
                                    if date:
                                        self._ecrire_ligne(ligne,date,libelle,debit,credit)
                                    ligne=ligne+1
                                    date    = lig[0]
                                    try:
                                        d = datetime.datetime.strptime(date, '%d/%m/%Y')
                                        date = d.strftime('%Y-%m-%d')
                                    except ValueError:
                                        date=False
                                    libelle = lig[1]
                                    debit   = lig[2].replace(',', '.').replace(' ', '')
                                    try:
                                        debit = -float(debit)
                                    except ValueError:
                                        debit=0
                                    credit  = lig[3].replace(',', '.').replace(' ', '')
                                    try:
                                        credit = float(credit)
                                    except ValueError:
                                        credit=0
                                else:
                                    libelle=libelle+' '+lig[1]
                    self._ecrire_ligne(ligne,date,libelle,debit,credit)
            return {
                'name': u'Suivi banque '+obj.name,
                'view_mode': 'list,form',
                'view_type': 'form',
                'res_model': 'is.suivi.banque',
                'domain': [
                    ('import_banque_id','=',obj.id),
                ],
                'context':{
                    'default_import_banque_id': obj.id,
                },
                'type': 'ir.actions.act_window',
                'limit': 500,
            }



