# -*- coding: utf-8 -*-

from markupsafe import Markup
from odoo.tools.zeep.helpers import serialize_object

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_repr
from odoo.tools.safe_eval import const_eval

import requests



class ProviderCamex(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[
        ('camex', "CAMEX")
    ], ondelete={'camex': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    camex_base_url = fields.Char(string="CAMEX BaseUrl", groups="base.group_system")
    camex_provider_key = fields.Char(string="CAMEX Provider Key", groups="base.group_system")
    camex_client_key = fields.Char(string="CAMEX Client Key", groups="base.group_system")
    camex_store_id = fields.Many2one('camex.store', string="Store", groups="base.group_system")
    camex_store_name = fields.Char(string="Store Name", related='camex_store_id.name', readonly=True, store=True)

    def camex_send_shipping(self, picking):
        if picking.camex_shipment_id:
            return [{ 'exact_price': 0,
                      'tracking_number': picking.camex_shipment_id }]

        content, trace_id = self.sudo().camex_create_shipment(picking)
        picking.camex_shipment_id = content
        picking.carrier_tracking_ref = content
        picking.camex_shipment_trace_id = trace_id

        if not isinstance(content, str):
            content = str(content)
        return [{ 'exact_price': 0,
                 'tracking_number': content }]

    def camex_rate_shipment(self, order):
        self.ensure_one()
        if not order.base_area_id:
            raise UserError(_('You must select a city first.'))
        vals = {'success': True,
                'price': order.get_carrier_shipping_price('camex'),
                'error_message': False,
                'warning_message': False}

        return vals

    def get_camex_shipment_status(self, picking, status):
        # statuses: out_partially_delivered, out_delivered, out_returned
        self.ensure_one()
        # Todo: Need to understand the camex statuses meaning
        if picking.camex_shipment_sate == '6':
            status = "out_delivered"
        elif picking.camex_shipment_sate == '11':
            status = "out_returned"
        return status


    def camex_request(self, method, url, headers=None, data=None):
        url = f"{self.sudo().camex_base_url}/{url}"
        if hasattr(requests, method):
            if method == "post":
                response = requests.post(url, headers=headers, data=data)
            else:
                response = getattr(requests, method)(url, headers=headers, data=data)
            if response.status_code == 200:

                response_json = response.json()
                messages = '\n'.join(response_json.get('messages', []))
                res_type = response_json.get('type', 0)

                if res_type == 1:
                    return response_json.get('content'), response_json.get('traceId')
                elif res_type == 2:
                    raise UserError(_(f"Request failed; System Error: \n{messages}"))
                elif res_type == 3:
                    raise UserError(_(f"Request failed; Technical Issue: \n{messages}"))
                else:
                    raise UserError(_(f"Request failed; Unknown Reason: \n{response_json}"))
            else:
                raise UserError(_(f"Request failed with status code: {response.status_code}"))
        else:
            raise UserError(_(f"Request failed; Wrong Method Name: {method}"))

    def camex_login(self):
        self = self.sudo()
        url = f"ApiEndpoints/Login?providerKey={self.camex_provider_key}&clientKey={self.camex_client_key}"
        content, trace_id = self.camex_request('get', url)
        if content and content.get('value'):
            return content['value']
        else:
            raise UserError(_(f"Login failed no content.value: \n{content}"))

    def camex_get_stores(self):
        headers = {
            "Authorization": f"Bearer {self.camex_login()}"
        }
        url = f"ApiEndpoints/Stores?culture=ar-LY"
        content, trace_id = self.camex_request('get', url, headers=headers)
        for store in content:
            store_id = self.env['camex.store'].search([('name', '=', store)], limit=1)
            if store_id:
                store_id.write({"name": store})
            else:
                store_id.create({"name": store})

    def camex_get_cities(self):
        headers = {
            "Authorization": f"Bearer {self.camex_login()}"
        }
        url = f"ApiEndpoints/Cities?culture=ar-LY"
        content, trace_id = self.camex_request('get', url, headers=headers)
        for c in content:
            city_id = self.env['camex.city'].search([('camex_city_id', '=', c['cityId'])], limit=1)
            if city_id:
                city_id.write({"camex_city_id": c['cityId'],
                               "camex_city_name": c['cityName'],
                               "camex_area_name": c['areaName'],
                               "camex_total_cost": c['totalCost']})
            else:
                city_id.create({
                    "camex_city_id": c['cityId'],
                    "camex_city_name": c['cityName'],
                    "camex_area_name": c['areaName'],
                    "camex_total_cost": c['totalCost']})

    def camex_create_shipment(self, picking):

        extra_bundled_packs = self._context.get('extra_bundled_packs')
        is_refund = self._context.get('is_refund', False)

        all_pack_ids = self.env['stock.picking'].browse(extra_bundled_packs) + picking

        sale_id = picking.sale_id

        mapping_id = self.env['camex.location.mapping'].search([('base_area_id', '=', sale_id.base_area_id.id)], limit=1)
        city_id = mapping_id.camex_area_id

        quantity_mapping = 'move_ids.product_uom_qty' if is_refund else 'move_ids.quantity'

        price = 0
        all_sales = all_pack_ids.mapped('sale_id')
        for sale in all_sales:
            price += sale.get_shipment_price()

        data = {
            "cityId": int(city_id.camex_city_id),
            "noItems": int(sum(all_pack_ids.mapped(quantity_mapping))),
            "price": price,
            "DeliveryCost": 1,
            "productDescrp": ' - '.join(all_pack_ids.mapped('sale_id.name')),
            "storeName": self.camex_store_name,
            "areaName": city_id.camex_area_name,
            "receiverPhone": sale_id.get_customer_phone(),
            "address": "Test Address",
            "notes": "السماح بالاختيار" + " - " + " - ".join(all_sales.mapped('name')) + f"\n{sale_id.get_order_note()}" + "\nرقم إضافي للزبون: "+ sale_id.get_customer_phone_2()
        }

        headers = {
            "Authorization": f"Bearer {self.camex_login()}",
            "Content-Type": "application/json"
        }
        url = "ApiEndpoints/"
        # content, trace_id = self.camex_request('post', url, headers=headers, data=data)


        url = f"{self.camex_base_url}/{url}"
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            response_json = response.json()
            messages = '\n'.join(response_json.get('messages', []))
            res_type = response_json.get('type', 0)

            if res_type == 1:
                return response_json.get('content'), response_json.get('traceId')
            elif res_type == 2:
                raise UserError(_(f"Request failed; System Error: \n{messages}"))
            elif res_type == 3:
                raise UserError(_(f"Request failed; Technical Issue: \n{messages}"))
            else:
                raise UserError(_(f"Request failed; Unknown Reason: \n{response_json}"))
        else:
            raise UserError(_(f"Request failed with status code: {response.status_code}"))

    def action_get_camex_cities(self):
        try:
            self.camex_get_cities()
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except Exception as e:
            raise UserError(_("Failed to fetch cities: %s") % e)

    def action_get_camex_stores(self):
        try:
            self.camex_get_stores()
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except Exception as e:
            raise UserError(_("Failed to fetch stores: %s") % e)
