# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_type_frais         = fields.Boolean('Type de frais'        , help='Cocher cette case pour afficher cet article dans les fiches de frais')
    is_type_frais_hors_km = fields.Boolean('Type de frais hors km', help='Cocher cette case pour afficher cet article dans le tableau de refacturation total des frais')

