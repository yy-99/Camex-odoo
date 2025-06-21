# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    base_area_id = fields.Many2one('base.area', string='Area')
    base_city_id = fields.Many2one('base.city', 'Base City', related='base_area_id.city_id', store=True)

    def action_confirm(self):
        for order in self:
            if not order.base_area_id:
                raise UserError(_('You must select an area first.'))
        return super(SaleOrder, self).action_confirm()

    def get_carrier_shipping_price(self, carrier):
        self.ensure_one()

        model_name = '%s.location.mapping' % carrier
        mapping_id = self.env[model_name].search([('base_area_id', '=', self.base_area_id.id)], limit=1)

        return mapping_id.shipping_price

    def get_shipment_price(self):
        # Override this method to calculate the Cash On Delivery price
        return 0.0

    def get_order_note(self):
        # Override this method in order to reformat the note
        return self.client_order_ref or ""

    def get_customer_phone(self):
        self.ensure_one()
        # Override this method to in carrier modules in order to reformat the phone number
        return self.partner_id.phone or ""

    def get_customer_phone_2(self):
        self.ensure_one()
        # Override this method to in carrier modules in order to reformat the phone number
        return self.partner_id.phone or ""

    def close_websers_order(self, shipment_status):
        # shipment_status: 'fully_delivered', 'partially_delivered', 'fully_returned'
        self.ensure_one()
        if shipment_status == 'fully_delivered':
            self.close_fully_delivered_order()
        elif shipment_status == 'partially_delivered':
            self.close_partially_delivered_order()
        elif shipment_status == 'fully_returned':
            self.close_fully_returned_order()
        else:
            raise UserError(_('You must select a valid final shipment status.'))

    def close_fully_delivered_order(self):
        # Override this method to close a fully delivered order
        return

    def close_partially_delivered_order(self):
        # Override this method to close a partially delivered order
        return

    def close_fully_returned_order(self):
        # Override this method to close a fully returned order
        return