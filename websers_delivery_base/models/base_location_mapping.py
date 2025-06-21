# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BaseLocationMapping(models.AbstractModel):
    _name = "base.location.mapping"
    _description = 'Base Location Mapping'

    base_area_id = fields.Many2one('base.area', 'Base Area')
    base_city_id = fields.Many2one('base.city', 'Base City', related='base_area_id.city_id')

    shipping_price = fields.Float(string="Shipping Price")
