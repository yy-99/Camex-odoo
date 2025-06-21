# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BaseCity(models.Model):
    _name = "base.city"
    _inherit = ['mail.thread']
    _description = 'Base City'

    name = fields.Char(string="City", required=True)
    code = fields.Char(string="Code", required=True)

    area_ids = fields.One2many('base.area', 'city_id', string="Areas")

    @api.model_create_multi
    def create(self, vals_list):
        city_ids = super(BaseCity, self).create(vals_list)

        # If no areas linked, create one with the same name and code
        for city in city_ids:
            if not city.area_ids:
                self.env['base.area'].create({
                    'name': city.name,
                    'code': city.code,
                    'city_id': city.id,
                })

        return city_ids