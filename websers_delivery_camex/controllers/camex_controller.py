# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
from odoo.addons.websers_delivery_base.controllers.common.BaseApiResponse import BaseApiResponse


class VendorController(http.Controller):

    @http.route('/api/camex_shipment_state', type='http', auth='public', methods=['POST'], csrf=False)
    def update_camex_shipment_state(self):
        data = json.loads(request.httprequest.data)
        secret_key = data['secretKey']
        state = data['state']
        shipment_id = data['id']
        if secret_key == request.env['ir.config_parameter'].sudo().get_param('delivery_camex.camex_secret_key'):
            out_picking_id = request.env['stock.picking'].sudo().search([
                ('camex_shipment_id', '=', shipment_id),
                ('picking_type_code', '=', 'outgoing')], limit=1)
            if out_picking_id.state != 'done':
                return BaseApiResponse.error(message=f"This picking {out_picking_id.name} is not validated yet")
            if out_picking_id.camex_shipment_sate in ["6", "11"]:
                statuses = {"6": "Delivered", "11": "Returned"}
                return BaseApiResponse.error(message=f"This picking {out_picking_id.name} is already marked as {statuses[out_picking_id.camex_shipment_sate]}")
            out_picking_id.sudo().camex_shipment_sate = state

