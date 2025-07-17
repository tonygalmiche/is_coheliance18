# -*- coding: utf-8 -*-
{
    "name" : "InfoSaône - Module Odoo 18 pour Coheliance",
    "version" : "0.1",
    "author" : "InfoSaône / Tony Galmiche",
    "category" : "InfoSaône",
    "description": """
InfoSaône - Module Odoo 18 pour Coheliance
===================================================

InfoSaône - Module Odoo 18 pour Coheliance
""",
    "maintainer": "InfoSaône",
    "website": "http://www.infosaone.com",
    "depends" : [
        "base",
        "account",
        "mail",
        "calendar",
        "crm",
        "sale",
        "sale_management",
        "purchase",
        #"project",        #TODO : N'est pas utilisé
        #"hr",             #TODO : N'est pas utilisé
        #"board",          #TODO : N'est pas utilisé
        #"hr_attendance",  #TODO : N'est pas utilisé
        #"hr_timesheet",   #TODO : N'est pas utilisé
        #"sale_stock",     #TODO : N'est pas utilisé
        #"stock",          #TODO : N'est pas utilisé
        #"stock_account",  #TODO : N'est pas utilisé
        #"account_menu",
        #"web_sheet_full_width",
        #"journal_sequence",
        #"crm_phonecall",
        "web_chatter_position",
    ],
    "init_xml" : [],
    "demo_xml" : [],
    "data" : [
        "security/ir.model.access.csv",
        # "views/assets.xml",
        "views/crm_lead_views.xml", 
        "views/product_view.xml", 
        "views/res_partner_view.xml", 
        "views/sale_view.xml",
        "views/account_move_view.xml",
        "views/account_bank_statement_view.xml",
        "views/is_coheliance_view.xml",
        "views/is_coheliance_sequence.xml",
        "views/is_suivi_tresorerie_view.xml",
        "views/is_export_compta.xml",
        # "views/is_coheliance_report.xml",
        "views/is_prospective_view.xml",
        "views/is_compte_resultat_view.xml",
         "views/is_bilan_pedagogique_view.xml",
        "views/is_suivi_banque_view.xml",
        "views/is_suivi_caisse_view.xml",
        # "views/layouts.xml",
        # "views/sale_report_templates.xml",
        # "views/report_affaire.xml",
        # "views/report_convention.xml",
        # "views/report_convention_st.xml",
        # "views/report_contrat_formation.xml",
        # "views/report_invoice.xml",
        "views/report_frais.xml",
        "views/report_fiche_frais.xml",
        "views/report_compte_resultat.xml",
        "report/is_suivi_facture.xml",
        "report/is_suivi_refacturation_associe.xml",
        "report/is_suivi_intervention.xml",
        "report/is_account_invoice_line.xml",
        "views/menu.xml",
    ],
   'assets': {
        'web.assets_backend': [
            'is_coheliance18/static/src/scss/styles.scss',
        ],
    },
    "installable": True,
    "active": False,
    "application": True,
    "license": "AGPL-3",
}

