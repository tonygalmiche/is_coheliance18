# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from odoo import api, fields, models
from odoo.exceptions import ValidationError



STRUCTURE=[('campus_at', 'CAMPUS AT')]


def _get_annee():
    now  = datetime.now()
    return now.strftime('%Y')


def _date_creation():
    now  = date.today()
    return now.strftime('%Y-%m-%d')


class IsAffaire(models.Model):
    _name = 'is.affaire'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Affaire"
    _order='name desc'

    def _ecart_budget(self):
        for obj in self:
            total=0
            for intervenant in obj.intervenant_ids:
                total=total+intervenant.budget_prevu
            obj.ecart_budget = obj.budget_propose-total


    @api.depends('intervention_ids')
    def _nb_stagiaire(self):
        for obj in self:
            nb_stagiaire=0
            visio = False
            for intervention in obj.intervention_ids:
                if intervention.visio:
                    visio=True
                if intervention.nb_stagiaire>nb_stagiaire:
                    nb_stagiaire=intervention.nb_stagiaire
            obj.nb_stagiaire = nb_stagiaire
            nb_stagiaire_visio = 0
            if visio:
                nb_stagiaire_visio = nb_stagiaire
            obj.nb_stagiaire_visio = nb_stagiaire_visio


    @api.depends('intervenant_ids')
    def _compute(self):
        for obj in self:
            total_budget_prevu=0
            for row in obj.intervenant_ids:
                total_budget_prevu=total_budget_prevu+row.budget_prevu
            obj.total_budget_prevu=total_budget_prevu


    @api.depends('facture_ids')
    def _compute_total_refacturable(self):
        for obj in self:
            total_refacturable=0
            for row in obj.facture_ids:
                if row.is_refacturable=='oui':
                    total_refacturable=total_refacturable+row.amount_untaxed
            obj.total_refacturable=total_refacturable


    @api.depends('acompte_ids','intervention_ids','facture_ids')
    def _compute_analyse(self):
        for obj in self:
            total_acompte        = 0
            total_non_facturable = 0
            total_fournisseur    = 0
            for line in obj.acompte_ids:
                total_acompte += line.montant_acompte
            for line in obj.intervention_ids:
                total_non_facturable += line.montant_non_facturable
            for line in obj.facture_ids:
                total_fournisseur += line.amount_untaxed
            resultat_net = total_acompte - total_non_facturable - total_fournisseur
            obj.total_acompte        = total_acompte
            obj.total_non_facturable = total_non_facturable
            obj.total_fournisseur    = total_fournisseur
            obj.resultat_net         = resultat_net


    def get_annee(self):
        now  = date.today()
        return now.strftime('%Y')


    def voir_affaire(self):
        for obj in self:
            res= {
                'name': 'Affaire',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'is.affaire',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }
            return res


    name           = fields.Char("Code de l'affaire")
    version        = fields.Char("Version", required=True, size=4, default="1")
    date_creation  = fields.Date("Date de création", default=lambda self: fields.Datetime.now())
    date_signature = fields.Date("Date de signature")
    date_relance   = fields.Date("Date de relance", default=lambda self: fields.Datetime.now()+timedelta(30))
    createur_id    = fields.Many2one('res.users', 'Créateur', default=lambda self: self.env.user)
    interlocutrice_id = fields.Many2one('res.users', 'Interlocutrice administrative', default=lambda self: self.env.user)
    pilote_id = fields.Many2one('res.users', 'Pilote', required=True, default=lambda self: self.env.user)
    structure = fields.Selection(selection=STRUCTURE, string="Structure")
    client_id = fields.Many2one('res.partner', 'Client', required=True)
    contact_client_id = fields.Many2one('res.partner', 'Contact client', required=False)
    article_id = fields.Many2one('product.template', 'Article', required=True)
    intitule = fields.Text("Intitulé", required=True)
    objectif = fields.Text("Objectifs", required=False, help="Pour les conventions de formations")
    descriptif = fields.Text("Descriptif / Programme", required=True, default="Descriptif précis de la mission, des compétences et moyens mis en œuvre ainsi que des résultats attendus ou modalités de réalisation : voir document annexe.")
    methode_pedagogique = fields.Text("Méthodes et supports pédagogiques", required=False, help="Pour les conventions de formations")
    personnes_concernees = fields.Text("Personnes concernées", required=False)
    lieu_intervention = fields.Char("Lieu d'intervention")
    date_debut = fields.Char("Date de début")
    date_fin = fields.Char("Date de fin")
    duree_prestation = fields.Text("Durée de la prestation")
    budget_bas = fields.Float("Budget bas")
    budget_haut = fields.Float("Budget haut")
    budget_propose = fields.Float("Budget proposé ")
    budget_propose_annee = fields.Float("Budget année en cours", help="Il faudra modifier cette valeur au début de l'année si l'affaire n'est pas clôturée pour le suivi des tableaux de bords")
    ecart_budget = fields.Float(compute=_ecart_budget, string="Ecart budget", help="Ecart entre le budget prévu par intervenant et le budget proposé", store=True, )
    modalite_paiement = fields.Text("Modalités de paiement")
    frais_a_refacturer = fields.Text("Frais à refacturer")
    intervenant_ids = fields.One2many('is.affaire.intervenant', 'affaire_id', 'Intervenants')
    date_validation = fields.Date("Date de validation", copy=False)
    date_solde = fields.Date("Date annulé ou soldé", copy=False)
    order_id = fields.Many2one('sale.order', 'Commande', readonly=False, copy=False)
    origine_financement_id = fields.Many2one('is.origine.financement', 'Origine du financement')
    nb_stagiaire       = fields.Integer(compute=_nb_stagiaire, string="Nombre de stagiaires"         , store=True, )
    nb_stagiaire_visio = fields.Integer(compute=_nb_stagiaire, string="Nombre de stagiaires en visio", store=True, )
    type_stagiaire_organisme_id = fields.Many2one('is.type.stagiaire.organisme', "Type de stagiaire de l'organisme")
    typologie_stagiaire_id = fields.Many2one('is.typologie.stagiaire', 'Objectif général des prestations dispensées')
    intervention_ids = fields.One2many('is.affaire.intervention', 'affaire_id', 'Interventions')
    frais_ids = fields.One2many('is.frais', 'affaire_id', 'Frais')
    vente_ids = fields.One2many('is.affaire.vente', 'affaire_id', 'Ventes')
    acompte_ids = fields.One2many('is.acompte', 'affaire_id', 'Acomptes')

    total_budget_prevu   = fields.Float('Budget prévu', compute='_compute', readonly=True, store=True)
    affaire_parent_id    = fields.Many2one('is.affaire', u'Affaire parent')
    affaire_child_ids    = fields.One2many('is.affaire', 'affaire_parent_id', 'Affaires liées', readonly=True)
    facture_ids          = fields.One2many('account.move', 'is_affaire_id', u'Factures fournisseur', readonly=True, domain=[('move_type', 'in', ['in_invoice', 'in_refund'])])
    total_refacturable   = fields.Float(u'Total refacturable HT', compute='_compute_total_refacturable', readonly=True, store=False)
    total_acompte        = fields.Float(u'Total des accomptes' , compute='_compute_analyse', readonly=True, store=False, help=u"Total des lignes des accomptes de l'onglet 'Facturation'")
    total_non_facturable = fields.Float(u'Total non facturable', compute='_compute_analyse', readonly=True, store=False, help=u"Total non facturable de l'onglet 'Interventions'")
    total_fournisseur    = fields.Float(u'Total fournisseur'   , compute='_compute_analyse', readonly=True, store=False, help=u"Total des factures de l'onglet 'Factures Fournisseurs'")
    resultat_net         = fields.Float(u'Résultat net affaire', compute='_compute_analyse', readonly=True, store=False, help=u"Résultat net affaire = Total des accomptes - Total non facturable - Total fournisseur")

    state = fields.Selection(selection=[
        ('en_attente', 'En attente'),
        ('valide'    , 'Validé'),
        ('annule'    , 'Annulé'),
        ('solde'     , 'Soldé')], string="État", readonly=False, index=True, default="en_attente")

 

    def action_generer_commande(self):
        for obj in self:
            if obj.order_id :
                if obj.order_id.state in ('draft', 'sent', 'cancel'):
                    obj.order_id.unlink()
                else:
                    raise ValidationError('Vous ne pouvez pas créer une autre commande, car celle-ci est déjà confirmée')

            quotation_line={
                'product_id': obj.article_id.id, 
                'product_uom_qty': 1
            }
            intitule="Intitulé :\n"+obj.intitule+"\n\n"
            intitule=intitule+"Descriptif :\n"+obj.descriptif+"\n\n"
            if obj.personnes_concernees:
                intitule=intitule+"Personnes Concernées :\n"+obj.personnes_concernees+"\n\n"
            if obj.lieu_intervention:
                intitule=intitule+"Lieu d'intervention :\n"+obj.lieu_intervention+"\n\n"
            if obj.date_debut:
                intitule=intitule+"Date de début :\n"+obj.date_debut+"\n\n"
            if obj.date_fin:
                intitule=intitule+"Date de fin :\n"+obj.date_fin+"\n\n"
            if obj.duree_prestation:
                intitule=intitule+"Durée de la prestation :\n"+obj.duree_prestation+"\n\n"
            intitule=intitule+"Intervenants :"
            for intervenant in obj.intervenant_ids:
                name=""
                if intervenant.associe_id:
                    name=intervenant.associe_id.name
                if intervenant.sous_traitant_id:
                    name=intervenant.sous_traitant_id.name
                    if intervenant.sous_traitant_id.is_prenom:
                        name=intervenant.sous_traitant_id.is_prenom+' '+intervenant.sous_traitant_id.name
                intitule=intitule+"\n- "+name
            quotation_line.update({'name': intitule})
            quotation_line.update({'price_unit': obj.budget_propose})
            lines = []
            lines.append([0,False,quotation_line])
            vals = {
                'partner_id': obj.client_id.id,
                'origin': obj.name,
                'order_line': lines,
                'picking_policy': 'direct',
                'affaire_id': obj.id,
                'warehouse_id':1,
                'invoice_status': 'to invoice',
            }
            new_id = self.env['sale.order'].create(vals)
            obj.order_id=new_id.id



    def action_detail_frais(self):
        for obj in self:
            return {
                'name': "Détail des frais",
                'view_type': 'form',
                'view_mode': 'list,form',
                'res_model': 'is.frais.ligne',
                'type': 'ir.actions.act_window',
                'domain': [('affaire_id','=',obj.id)],
            }


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('is.affaire')
        return super().create(vals_list)



    def write(self, vals):
        if 'state' in vals:
            vals["date_validation"]=False
            vals["date_solde"]=False
            if vals["state"]=='valide':
                vals["date_validation"]=datetime.now().strftime('%Y-%m-%d')
            if vals["state"]=='solde' or vals["state"]=='annule':
                vals["date_solde"]=datetime.now().strftime('%Y-%m-%d')
        res=super(IsAffaire, self).write(vals)
        return res




class is_affaire_intervenant(models.Model):
    _name = 'is.affaire.intervenant'
    _description = "Intervenants"
    
    affaire_id           = fields.Many2one('is.affaire', 'Affaire', required=True)
    annee                = fields.Integer("Année", default=lambda *a: _get_annee())
    associe_id           = fields.Many2one('res.users', 'Associé')
    sous_traitant_id     = fields.Many2one('res.partner', 'Sous-Traitant')
    duree_mission        = fields.Char("Durée mission Sous-Traitant")
    condition_financiere = fields.Char("Conditions financières Sous-Traitant")
    budget_prevu         = fields.Float("Budget prévu", help="Budget prévu pour cette personne", required=True)
    taux1                = fields.Float("Taux horaire")
    taux2                = fields.Float("Taux demi-journée")
    taux3                = fields.Float("Taux journée")


    def print_convention_st(self):
        for obj in self:
            report=self.env.ref('is_coheliance18.report_conventions_st')
            return report.report_action([obj.id])


class is_affaire_intervention(models.Model):
    _name = 'is.affaire.intervention'
    _description = "Interventions"


    def get_montant_facture(self, obj):
        intervenant_ids = obj.affaire_id.intervenant_ids
        trouve=False
        for intervenant in intervenant_ids:
            if(obj.associe_id and intervenant.associe_id.id==obj.associe_id.id):
                trouve=intervenant
            if(obj.sous_traitant_id and intervenant.sous_traitant_id.id==obj.sous_traitant_id.id):
                trouve=intervenant
        taux=0
        if trouve:
            if obj.unite_temps=="heure":
                taux=trouve.taux1
            if obj.unite_temps=="demi-jour":
                taux=trouve.taux2
            if obj.unite_temps=="jour":
                taux=trouve.taux3
        montant = taux*obj.temps_passe
        return montant


    @api.depends('unite_temps','temps_passe','facturable','nb_stagiaire')
    def _montant_facture(self):
        for obj in self:
            montant = 0
            if obj.facturable:
                montant = self.get_montant_facture(obj)
            obj.montant_facture = montant


    @api.depends('unite_temps','temps_passe','facturable','nb_stagiaire')
    def _montant_non_facturable(self):
        for obj in self:
            montant = 0
            if not obj.facturable:
                montant = self.get_montant_facture(obj)
            obj.montant_non_facturable = montant


    @api.depends('unite_temps','temps_passe','facturable','nb_stagiaire')
    def _temps_formation(self):
        for obj in self:
            taux=0
            if obj.unite_temps=="heure":
                taux=1
            if obj.unite_temps=="demi-jour":
                taux=3.5
            if obj.unite_temps=="jour":
                taux=7
            obj.temps_formation = obj.temps_passe*obj.nb_stagiaire*taux



    @api.depends('temps_passe','unite_temps')
    def _compute_temps_passe_heure(self):
        for obj in self:
            tps=0
            if obj.unite_temps=="heure":
                tps = obj.temps_passe
            if obj.unite_temps=="demi-jour":
                tps = obj.temps_passe*3.5
            if obj.unite_temps=="jour":
                tps = obj.temps_passe*7
            obj.temps_passe_heure = tps


    affaire_id             = fields.Many2one('is.affaire', 'Affaire', required=True)
    date                   = fields.Date("Date", required=True, default=lambda self: fields.Datetime.now())
    associe_id             = fields.Many2one('res.users', 'Associé', default=lambda self: self.env.user)
    sous_traitant_id       = fields.Many2one('res.partner', 'Sous-Traitant')
    temps_passe            = fields.Float("Temps passé", required=True)
    unite_temps            = fields.Selection([('heure','Heure'),('demi-jour','Demi-journée'),('jour','Jour')], "Unité de temps", default="heure", required=True)
    temps_passe_heure      = fields.Float(compute=_compute_temps_passe_heure, string="Temps passé (H)", store=True )
    nb_stagiaire           = fields.Integer("Nombre de stagiaires")
    temps_formation        = fields.Float(compute=_temps_formation, string="Temps de formation", store=True, )
    visio                  = fields.Boolean("Visio", default=False)
    facturable             = fields.Boolean("Facturable", default=True)
    montant_facture        = fields.Float(compute=_montant_facture, string="Montant à facturer", store=True)
    montant_non_facturable = fields.Float(compute=_montant_non_facturable, string="Montant non facturable", store=True)
    commentaire            = fields.Text(u"Commentaire")




class is_acompte(models.Model):
    _name = 'is.acompte'
    _description = u"Gestion acomptes"
    _order='date_acompte'

    affaire_id      = fields.Many2one('is.affaire', 'Affaire', required=True)
    date_acompte    = fields.Date("Date acompte")
    montant_acompte = fields.Float("Montant acompte")
    commentaire     = fields.Text("Commentaire")
    account_id      = fields.Many2one('account.move', "Facture d'acompte")


class is_affaire_vente(models.Model):
    _name  = 'is.affaire.vente'
    _description = u"Ventes des affaires"
    _order = 'date'

    @api.depends('quantite','prix_achat','prix_vente')
    def _compute(self):
        for obj in self:
            obj.total_achat=obj.quantite*obj.prix_achat
            obj.total_vente=obj.quantite*obj.prix_vente


    affaire_id  = fields.Many2one('is.affaire', 'Affaire', required=True)
    date        = fields.Date(u"Date", required=True)
    product_id  = fields.Many2one('product.product', u'Article', required=True)
    quantite    = fields.Float(u"Quantité")
    prix_achat  = fields.Float(u"Prix d'achat")
    prix_vente  = fields.Float(u"Prix de vente")
    total_achat = fields.Float(u"Total des achats", compute='_compute', readonly=True, store=True)
    total_vente = fields.Float(u"Total des ventes", compute='_compute', readonly=True, store=True)
    commentaire = fields.Char(u"Commentaire")


class is_frais(models.Model):
    _name = 'is.frais'
    _description = u"Fiche de frais"
    _order='name desc'

    name             = fields.Char(u"Numéro")
    date_creation    = fields.Date(u"Date de création", default=lambda self: fields.Datetime.now())
    affaire_id       = fields.Many2one('is.affaire', 'Affaire', required=True)
    intervenant_id   = fields.Many2one('res.users', u'Associé',  default=lambda self: self.env.user)
    sous_traitant_id = fields.Many2one('res.partner', u'Sous-Traitant')
    taux_km          = fields.Float(u"Taux indemnité kilométrique",  default=lambda self: self._taux_km(self._cr))
    ligne_ids        = fields.One2many('is.frais.ligne', 'frais_id', u'Lignes')


    def _taux_km(self,cr):
        sql="select taux_km from res_company limit 1";
        cr.execute(sql)
        taux_km=0
        for row in cr.fetchall():
            taux_km=row[0]
        return taux_km



    # @api.model
    # def create(self, vals):
    #     data_obj = self.env['ir.model.data']
    #     sequence_ids = data_obj.search([('name','=','is_frais_seq')])
    #     if sequence_ids:
    #         sequence_id = data_obj.browse(sequence_ids[0].id).res_id
    #         vals['name'] = self.env['ir.sequence'].get_id(sequence_id, 'id')
    #     res = super(is_frais, self).create(vals)
    #     return res


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('is.frais')
        return super().create(vals_list)





    def write(self, vals):
        for obj in self:
            if 'taux_km' in vals:
                taux_km=vals['taux_km']
                for lig in obj.ligne_ids:
                    if lig.km:
                        lig.montant_ht=lig.km*taux_km
        res = super(is_frais, self).write(vals)
        return res


    def print_fiche_frais(self):
        cr, uid, context = self.env.args
        for obj in self:
            return self.pool['report'].get_action(cr, uid, obj.id, 'is_coheliance.report_frais', context=context)


class is_frais_ligne(models.Model):
    _name = 'is.frais.ligne'
    _description = u"Lignes des fiches de frais"
    _order='date desc'

    @api.depends('type_frais_id','montant_ht')
    def _montant_ttc(self):
        res={}
        for obj in self:
            tva=0
            if obj.type_frais_id:
                if obj.type_frais_id.taxes_id:
                    for taxe in obj.type_frais_id.taxes_id:
                        tva=taxe.amount/100
            obj.montant_ttc=obj.montant_ht*(1+tva)


    frais_id         = fields.Many2one('is.frais', 'Frais', required=True)
    affaire_id       = fields.Many2one('is.affaire', 'Affaire'        , related='frais_id.affaire_id'      , readonly=True)
    intervenant_id   = fields.Many2one('res.users', u'Intervenant'    , related='frais_id.intervenant_id'  , readonly=True)
    sous_traitant_id = fields.Many2one('res.partner', u'Sous-Traitant', related='frais_id.sous_traitant_id', readonly=True)
    date             = fields.Date(u"Date")
    type_frais_id    = fields.Many2one('product.template', u'Type de frais')
    refacturable     = fields.Selection([('oui','Oui'),('non','Non')], u"Refacturable")
    km               = fields.Integer(u"Km")
    montant_ht       = fields.Float(u"Montant HT", digits=(14,2))
    montant_ttc      = fields.Float('Montant TTC', digits=(14,2), compute='_montant_ttc', readonly=True, store=True)
    refacture        = fields.Boolean(u"Frais refacturé au client")
    commentaire      = fields.Char(u"Commentaire")

    _defaults = {
        'date': lambda *a: _date_creation(),
        'refacturable': 'oui',
        'refacture': False,
    }


    # @api.model
    # def create(self,vals):
    #     obj = super(is_frais_ligne, self).create(vals)
    #     if 'km' in vals:
    #         if vals['km']!=0:
    #             taux_km=obj.frais_id.taux_km
    #             obj.montant_ht=vals['km']*taux_km
    #     return obj


    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for vals in vals_list:
            if 'km' in vals:
                if vals['km']!=0:
                    taux_km=self.frais_id.taux_km
                    res.montant_ht=vals['km']*taux_km






    def write(self, vals):
        for obj in self:
            if 'km' in vals:
                taux_km=obj.frais_id.taux_km
                vals['montant_ht']=vals['km']*taux_km
        res = super(is_frais_ligne, self).write(vals)
        return res


class is_fiche_frais(models.Model):
    _name = 'is.fiche.frais'
    _description = u"Fiche de frais mensuelle"
    _order='name desc'


    def _date_debut(self):
        now  = date.today()              # Ce jour
        j    = now.day                            # Numéro du jour dans le mois
        d    = now - timedelta(days=j)   # Dernier jour du mois précédent
        j    = d.day                              # Numéro jour mois précédent
        d    = d - timedelta(days=(j-1)) # Premier jour du mois précédent
        return d.strftime('%Y-%m-%d')


    def _date_fin(self):
        now  = date.today()            # Ce jour
        j    = now.day                          # Numéro du jour dans le mois
        d    = now - timedelta(days=j) # Dernier jour du mois précédent
        return d.strftime('%Y-%m-%d')



    name       = fields.Char(u"Numéro")
    user_id    = fields.Many2one('res.users', u'Associé', required=True, default=lambda self: self.env.user)
    date_debut = fields.Date(u"Date de début"           , required=True, default=lambda self: self._date_debut())
    date_fin   = fields.Date(u"Date de fin"             , required=True, default=lambda self: self._date_fin())


    # @api.model
    # def create(self, vals):
    #     data_obj = self.env['ir.model.data']
    #     sequence_ids = data_obj.search([('name','=','is_fiche_frais_seq')])
    #     if sequence_ids:
    #         sequence_id = data_obj.browse(sequence_ids[0].id).res_id
    #         vals['name'] = self.env['ir.sequence'].get_id(sequence_id, 'id')
    #     res = super(is_fiche_frais, self).create(vals)
    #     return res



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('is.fiche.frais')
        return super().create(vals_list)







    def get_frais(self):
        for obj in self:
            filtre=[
                ('intervenant_id','=',obj.user_id.id),
                ('date','>=',obj.date_debut),
                ('date','<=',obj.date_fin),
                ('km','>',0),
            ]
            frais = self.env['is.frais.ligne'].search(filtre,order='date',limit=5000)
            return frais

