# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CamexLocationMapping(models.Model):
    _name = "camex.location.mapping"
    _inherit = "base.location.mapping"
    _description = 'CAMEX Location Mapping'

    camex_area_id = fields.Many2one('camex.city', 'CAMEX Area')

    shipping_price = fields.Float(string="Shipping Price", related='camex_area_id.camex_total_cost', store=True)
