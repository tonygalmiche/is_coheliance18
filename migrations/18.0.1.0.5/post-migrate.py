# -*- coding: utf-8 -*-
import logging

from lxml import etree

from odoo import api, Command, SUPERUSER_ID
from odoo.tools import file_open

_logger = logging.getLogger(__name__)


# xmlid -> (id, modele, libelle fr_FR) du sous-type correspondant, verifie
# ligne par ligne (modele, libelle, parent) sur odoo18 et odoo18-formation
# le 2026-11-07 (memes ids sur les deux bases)
SUBTYPES = {
    "account.mt_invoice_validated": (4, "account.move", "Validé"),
    "account.mt_invoice_paid": (5, "account.move", "Payé"),
    "account.mt_invoice_created": (6, "account.move", "Facture créée"),
    "calendar.subtype_invitation": (7, "calendar.event", "Invitation"),
    "purchase.mt_rfq_confirmed": (28, "purchase.order", "Demande de prix confirmée"),
    "purchase.mt_rfq_approved": (29, "purchase.order", "Demande de prix approuvée"),
    "purchase.mt_rfq_done": (30, "purchase.order", "Demande de prix terminée"),
    "sale.mt_order_sent": (31, "sale.order", "Devis envoyé"),
    "sale.mt_order_confirmed": (32, "sale.order", "Commande de vente confirmée"),
    "sale.mt_salesteam_order_sent": (33, "crm.team", "Devis envoyé"),
    "sale.mt_salesteam_order_confirmed": (34, "crm.team", "Commande de vente confirmée"),
    "sale.mt_salesteam_invoice_created": (35, "crm.team", "Facture créée"),
    "sale.mt_salesteam_invoice_confirmed": (36, "crm.team", "Facture confirmée"),
}

# Sous-types standard absents de la base (valeurs de
# sale/data/mail_message_subtype_data.xml et purchase/data/purchase_data.xml).
# Crees ici : utilises par env.ref() (portail des devis, purchase_order.py).
# Ordre important : mt_order_viewed est le parent de mt_salesteam_order_viewed.
SUBTYPES_TO_CREATE = [
    ("sale.mt_order_viewed", {
        "name": "Devis consulté", "res_model": "sale.order",
        "internal": True, "default": True,
    }),
    ("sale.mt_salesteam_order_viewed", {
        "name": "Devis consulté", "sequence": 25, "res_model": "crm.team",
        "default": True, "parent_xmlid": "sale.mt_order_viewed", "relation_field": "team_id",
    }),
    ("purchase.mt_rfq_sent", {
        "name": "Demande de prix envoyée", "res_model": "purchase.order", "default": False,
    }),
]


def migrate(cr, version):
    """Repare les xmlids standards laisses incoherents par la migration de
    cette base vers Odoo 18.0 (17/07/2025), meme defaut que sur
    is_clair_sarl18 (migrations 18.0.0.2 et 18.0.0.4) et que pour les unites
    de mesure (migration 18.0.1.0.1 de ce module).

    Constat (odoo18 et odoo18-formation, 2026-11-07) : ir_model_data a ete
    rempli avec les ids d'une base 18 neuve, sans regarder le contenu des
    tables :
    - utilisateurs : base.public_user vers "portaltemplate",
      base.template_portal_user_id vers Florence ROY, base.default_user vers
      "public" (pas d'utilisateur "default"). Le -u base echoue
      (res_users_login_key) en voulant renommer Florence ROY en
      "portaltemplate" ;
    - l'utilisateur "public" a recu les groupes du modele des nouveaux
      utilisateurs (interne, administrateur ventes, achats, comptabilite) :
      une fois base.public_user corrige, les visiteurs non connectes
      auraient ces droits ;
    - devises : xmlids base.<CODE> decales (base.EUR vers KPW, base.USD vers
      EUR) ; res_country.currency_id enregistre avec ces mauvais ids
      (France vers KPW) ;
    - sous-types de messages account.*, calendar.*, sale.*, purchase.*
      decales, 3 sous-types standard absents.

    Seuls ir_model_data, les groupes de l'utilisateur "public",
    res_country.currency_id et la creation de 3 sous-types sont touches :
    aucune donnee metier (pieces, partenaires, messages) n'est modifiee.

    A lancer par un -u is_coheliance18 SEUL, AVANT tout -u base / -u all,
    qui echoue sinon sur les utilisateurs avant d'arriver a ce module.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    imd_model = env["ir.model.data"]

    def imd_for(xmlid, model):
        module, name = xmlid.split(".")
        return imd_model.search(
            [("module", "=", module), ("name", "=", name), ("model", "=", model)], limit=1
        )

    def realign(xmlid, model, res_id):
        """Pointe l'xmlid vers res_id, ou le supprime si res_id est vide."""
        imd = imd_for(xmlid, model)
        if not imd:
            return
        if not res_id:
            _logger.info("is_coheliance18 : suppression de %s (res_id %s)", xmlid, imd.res_id)
            imd.unlink()
        elif imd.res_id != res_id:
            _logger.info("is_coheliance18 : %s %s -> %s", xmlid, imd.res_id, res_id)
            imd.write({"res_id": res_id})

    # --- Utilisateurs et partenaires systeme ------------------------------
    # Meme logique que dev_odoo/migration-odoo/correctif-utilisateurs-techniques-coheliance18.py
    # (essaye sur bookworm le 26/09/2026, cf. Documentation/migration-odoo/
    # correctif-utilisateurs-techniques-coheliance18.md)
    users = env["res.users"].with_context(active_test=False, no_reset_password=True)
    public = users.search([("login", "=", "public")], limit=1)
    portal_template = users.search([("login", "=", "portaltemplate")], limit=1)
    if not public or not portal_template:
        raise Exception("is_coheliance18 1.0.5 : utilisateur 'public' ou 'portaltemplate' introuvable")
    group_public = env["res.groups"].browse(imd_for("base.group_public", "res.groups").res_id)
    group_portal = env["res.groups"].browse(imd_for("base.group_portal", "res.groups").res_id)
    members_model = env["discuss.channel.member"].sudo()
    members_before = members_model.search([]).ids

    # Modele des nouveaux utilisateurs internes, avec les groupes par defaut
    # actuels (ceux de l'utilisateur "public", qui jouait ce role). Sans
    # active_test=False : Odoo refuse sinon d'archiver le partenaire.
    default = users.search([("login", "=", "default")], limit=1)
    if not default:
        default = env["res.users"].with_context(no_reset_password=True).create({
            "name": "Default User Template",
            "login": "default",
            "active": False,
            "groups_id": [Command.set(public.groups_id.ids)],
        })
        _logger.info("is_coheliance18 : creation de l'utilisateur 'default' (id %s)", default.id)

    realign("base.default_user", "res.users", default.id)
    realign("base.default_user_res_partner", "res.partner", default.partner_id.id)
    realign("base.public_user", "res.users", public.id)
    realign("base.public_partner", "res.partner", public.partner_id.id)
    realign("base.template_portal_user_id", "res.users", portal_template.id)
    realign("base.template_portal_user_id_res_partner", "res.partner", portal_template.partner_id.id)
    env["ir.config_parameter"].set_param("base.template_portal_user_id", str(portal_template.id))
    # Ecrire les nouveaux res_id puis vider le cache : sinon base.default_user
    # resterait sur "public" et changer ses groupes les propagerait a tous les
    # utilisateurs internes
    env.flush_all()
    env.registry.clear_cache()
    if (env.ref("base.default_user") != default or env.ref("base.public_user") != public
            or env.ref("base.template_portal_user_id") != portal_template):
        raise Exception("is_coheliance18 1.0.5 : xmlids des utilisateurs non realignes")

    # Visiteurs non connectes : groupe Public seul ; modele portail : groupe
    # Portail seul (le -u base ajoute des groupes sans jamais en retirer)
    public.write({"groups_id": [Command.set([group_public.id])]})
    portal_template.write({"groups_id": [Command.set([group_portal.id])]})

    # Creer un utilisateur interne abonne les utilisateurs internes au canal
    # Discuss "general" (inutilise ici) : abonnements retires, sinon le -u base
    # plante (discuss_channel_member_partner_unique)
    new_members = members_model.search([("id", "not in", members_before)])
    if new_members:
        _logger.info("is_coheliance18 : %s abonnement(s) Discuss retire(s)", len(new_members))
        new_members.unlink()
    env.flush_all()

    if not users.browse(5).active:
        raise Exception("is_coheliance18 1.0.5 : l'utilisateur 5 (Florence ROY) doit rester actif")

    # --- Devises : xmlids base.<CODE> -------------------------------------
    # active_test=False : presque toutes les devises sont inactives
    currency_model = env["res.currency"].with_context(active_test=False)
    for imd in imd_model.search([("module", "=", "base"), ("model", "=", "res.currency")]):
        currency = currency_model.search([("name", "=", imd.name)], limit=1)
        if not currency:
            # Devise absente de la base : le -u base la creera une fois
            # l'xmlid supprime
            imd.unlink()
        elif imd.res_id != currency.id:
            imd.write({"res_id": currency.id})

    # --- Pays : res_country.currency_id -----------------------------------
    # Devise de chaque pays d'apres la donnee standard (noupdate : pas
    # corrigee par le -u base)
    with file_open("base/data/res_country_data.xml", "rb") as f:
        doc = etree.parse(f)
    country_model = env["res.country"].with_context(active_test=False)
    for record in doc.iterfind(".//record[@model='res.country']"):
        code = record.findtext("field[@name='code']")
        currency_field = record.find("field[@name='currency_id']")
        if not code or currency_field is None:
            continue
        country = country_model.search([("code", "=", code.upper())], limit=1)
        currency = currency_model.search([("name", "=", currency_field.get("ref"))], limit=1)
        if country and currency and country.currency_id != currency:
            country.currency_id = currency.id

    # --- Sous-types de messages -------------------------------------------
    subtype_model = env["mail.message.subtype"].with_context(lang="fr_FR")
    for xmlid, (res_id, res_model, label) in SUBTYPES.items():
        subtype = subtype_model.browse(res_id).exists()
        if subtype and subtype.res_model == res_model and subtype.name == label:
            realign(xmlid, "mail.message.subtype", res_id)
        else:
            _logger.warning("is_coheliance18 : sous-type %s non trouve (id %s %r)", xmlid, res_id, label)

    # Id du sous-type par xmlid lu dans ir_model_data, pas par env.ref() :
    # son cache garde l'ancien res_id d'un xmlid modifie plus haut
    mapped_ids = [res_id for res_id, _, _ in SUBTYPES.values()]
    subtype_ids = {}
    for xmlid, vals in SUBTYPES_TO_CREATE:
        vals = dict(vals)
        imd = imd_for(xmlid, "mail.message.subtype")
        current = imd and subtype_model.browse(imd.res_id).exists()
        if current and current.id not in mapped_ids and current.res_model == vals["res_model"]:
            subtype_ids[xmlid] = current.id  # deja correct
            continue
        parent_xmlid = vals.pop("parent_xmlid", False)
        if parent_xmlid:
            vals["parent_id"] = subtype_ids[parent_xmlid]
        subtype = subtype_model.create(vals)
        subtype_ids[xmlid] = subtype.id
        _logger.info("is_coheliance18 : creation du sous-type %s (id %s)", xmlid, subtype.id)
        if imd:
            imd.write({"res_id": subtype.id})
        else:
            module, name = xmlid.split(".")
            imd_model.create({
                "module": module, "name": name, "model": "mail.message.subtype",
                "res_id": subtype.id, "noupdate": True,
            })
