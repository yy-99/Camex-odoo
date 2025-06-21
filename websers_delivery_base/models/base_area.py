# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BaseArea(models.Model):
    _name = "base.area"
    _inherit = ['mail.thread']
    _description = 'Base Area'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string="Area", required=True)
    code = fields.Char(string="Code", required=True)

    city_id = fields.Many2one('base.city', string="City", required=True)
    
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name', recursive=True,
        store=True)
    parent_id = fields.Many2one('base.area', 'Parent Area', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many('base.area', 'parent_id', 'Sub Areas')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for area in self:
            if area.parent_id:
                area.complete_name = '%s / %s' % (area.parent_id.complete_name, area.name)
            else:
                area.complete_name = area.name


    @api.constrains('parent_id')
    def _check_area_recursion(self):
        if self._has_cycle():
            raise ValidationError(_('You cannot create recursive areas.'))

    @api.constrains('parent_id', 'city_id')
    def _check_city_consistency(self):
        for area in self:
            # 1. Subarea must have the same city as its parent
            if area.parent_id and area.city_id != area.parent_id.city_id:
                raise ValidationError(_('The city of a sub-area must match the city of its parent area.'))

            # 2. Parent area must have the same city as all its children
            for child in area.child_id:
                if child.city_id != area.city_id:
                    raise ValidationError(
                        _('Cannot change the city of an area when one or more of its sub-areas belong to a different city.\n\n'
                          f'Area: {area.name}, Sub-Area: {child.name}'))

    @api.onchange('parent_id')
    def _onchange_parent_id_fill_city(self):
        for area in self:
            if area.parent_id:
                area.city_id = area.parent_id.city_id

    @api.model
    def name_create(self, name):
        area = self.create({'name': name})
        return area.id, area.display_name

    @api.depends_context('hierarchical_naming')
    def _compute_display_name(self):
        if self.env.context.get('hierarchical_naming', True):
            super()._compute_display_name()
        for area in self:
            area.display_name = area.name
