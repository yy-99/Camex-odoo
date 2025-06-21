# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CamexStore(models.Model):
    _name = "camex.store"
    _inherit = ['mail.thread']
    _description = 'Camex Store'

    name = fields.Char(string="Store Name", tracking=True)
