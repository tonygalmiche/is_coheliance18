# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    affaire_id = fields.Many2one('is.affaire', 'Affaire', readonly=True)
