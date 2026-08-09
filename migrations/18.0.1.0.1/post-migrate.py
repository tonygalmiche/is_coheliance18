# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Repare le mapping ir_model_data <-> uom.uom / uom.category laisse
    incoherent par la migration Odoo 14.0 -> 18.0.

    Constat (verifie ligne a ligne par contenu : nom, facteur, categorie) :
    la table uom_uom/uom_category de cette base est celle d'Odoo 14 (22
    unites, 5 categories), alors que ir_model_data pointe deja vers le
    schema Odoo 18 (26 unites, 6 categories). Resultat : la quasi-totalite
    des xmlids standards uom.* pointent vers la mauvaise ligne (ex:
    uom.product_uom_hour pointait vers la ligne "g" (grammes) au lieu de
    "Heures"), et les xmlids des unites/categories ajoutees apres la v14
    (millimeter, uom_square_meter, product_uom_yard, uom_square_foot,
    uom_categ_surface) pointaient vers des lignes existantes usurpees ou
    vers des lignes inexistantes.

    Cela ne touche que la table ir_model_data : aucune donnee des tables
    uom_uom / uom_category n'est modifiee, et aucun enregistrement metier
    (produits, lignes de vente/achat...) n'est modifie puisque ceux-ci
    referencent une unite par son id concret, jamais par xmlid.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    imd_model = env["ir.model.data"]

    def imd_for(model, name):
        return imd_model.search(
            [("module", "=", "uom"), ("name", "=", name), ("model", "=", model)],
            limit=1,
        )

    def apply_remap(model, remap):
        target_model = env[model]
        reclaimed_ids = set(remap.values())
        for name, res_id in remap.items():
            imd = imd_for(model, name)
            if imd and imd.res_id != res_id and target_model.browse(res_id).exists():
                imd.write({"res_id": res_id})
        return reclaimed_ids

    # --- Categories -----------------------------------------------------
    categ_remap = {
        "product_uom_categ_vol": 5,
    }
    categ_reclaimed = apply_remap("uom.category", categ_remap)

    categ_surface_imd = imd_for("uom.category", "uom_categ_surface")
    if categ_surface_imd and categ_surface_imd.res_id in categ_reclaimed:
        new_categ = env["uom.category"].create({"name": "Surface"})
        categ_surface_imd.write({"res_id": new_categ.id})
        categ_surface_id = new_categ.id
    else:
        categ_surface_id = categ_surface_imd.res_id

    # --- Units of measure -------------------------------------------------
    uom_remap = {
        "product_uom_kgm": 3,
        "product_uom_gram": 4,
        "product_uom_day": 5,
        "product_uom_hour": 6,
        "product_uom_ton": 7,
        "product_uom_meter": 8,
        "product_uom_km": 9,
        "product_uom_cm": 10,
        "product_uom_litre": 11,
        "product_uom_cubic_meter": 12,
        "product_uom_lb": 13,
        "product_uom_oz": 14,
        "product_uom_inch": 15,
        "product_uom_foot": 16,
        "product_uom_mile": 17,
        "product_uom_floz": 18,
        "product_uom_qt": 19,
        "product_uom_gal": 20,
        "product_uom_cubic_inch": 21,
        "product_uom_cubic_foot": 22,
    }
    uom_reclaimed = apply_remap("uom.uom", uom_remap)

    categ_length_id = imd_for("uom.category", "uom_categ_length").res_id

    uom_to_create = [
        (
            "product_uom_millimeter",
            {"name": "mm", "category_id": categ_length_id, "factor": 1000, "uom_type": "smaller"},
        ),
        (
            "uom_square_meter",
            {"name": "m²", "category_id": categ_surface_id, "factor": 1.0, "uom_type": "reference"},
        ),
        (
            "product_uom_yard",
            {"name": "yd", "category_id": categ_length_id, "factor": 1.09361, "uom_type": "smaller"},
        ),
        (
            "uom_square_foot",
            {"name": "ft²", "category_id": categ_surface_id, "factor": 10.76391, "uom_type": "smaller"},
        ),
    ]
    for name, vals in uom_to_create:
        imd = imd_for("uom.uom", name)
        if imd and imd.res_id in uom_reclaimed:
            new_record = env["uom.uom"].create(vals)
            imd.write({"res_id": new_record.id})
