# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.picking"

    camex_shipment_id = fields.Char(string="Camex Shipment ID", readonly=True, tracking=True)
    camex_shipment_trace_id = fields.Char(string="Camex Shipment traceId", readonly=True, tracking=True)
    camex_shipment_sate = fields.Selection(
        [('-2', 'Unaccepted from stock management yet'),
         ('0', 'Data Entry done but not accepted in store yet'),
         ('1', 'Prepare shipment started'),
         ('2', 'Ready from stock management'),
         ('3', 'Enter store'),
         ('4', 'In convert to another branch'),
         ('5', 'In delivery with delegate'),
         ('6', 'Delivered'),
         ('8', 'In return to main branch'),
         ('9', 'In return with delegate'),
         ('11', 'Returned to client'),
         ('12', 'Money was collected by client'),
         ('19', 'Returned to stock management')],
        string="Camex Shipment Status", readonly=True, default="-2", tracking=True)
    
    def write(self,vals):
        res = super(Picking, self).write(vals)
        if 'camex_shipment_sate' in vals.keys():
            for pick in self:
                if pick.camex_shipment_sate == '6':
                    pick.group_id.sale_id.close_websers_order('fully_delivered')
                elif pick.camex_shipment_sate == '11':
                    pick.group_id.sale_id.close_websers_order('fully_returned')

        return res