# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    camex_secret_key = fields.Char(string='Camex Secret Key',
                                   config_parameter='delivery_camex.camex_secret_key',default=False)
