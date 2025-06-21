# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import json
import logging

import hashlib
import hmac
from markupsafe import Markup
from werkzeug.exceptions import Forbidden

from http import HTTPStatus
from odoo.tools import consteq

_logger = logging.getLogger(__name__)

class MetaWebhookController(http.Controller):

    @http.route('/meta/webhook', type='http', auth='public', methods=['GET'], csrf=False)
    def verify_webhook(self, **kwargs):
        print(999999999999999999999)
        mode = kwargs.get('hub.mode')
        token = kwargs.get('hub.verify_token')
        challenge = kwargs.get('hub.challenge')

        # Find matching verify token in DB
        meta_app = request.env['meta.app'].sudo().search([('verify_token', '=', token)], limit=1)
        print(111111111111, meta_app)

        if mode == 'subscribe' and token and meta_app:
            _logger.info("Webhook verified for app: %s", meta_app.name)
            return challenge
        else:
            return "Verification failed", 403

    @http.route('/meta/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_event(self, **kwargs):
        print(5555555555555555)
        print(5511, request.httprequest.headers)
        print(5522, request.httprequest.data)
        payload = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info("Received webhook payload: %s", json.dumps(payload, indent=2))

        # Process each entry
        for entry in payload.get("entry", []):
            page_id = entry.get("id")
            time_of_event = entry.get("time")
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                recipient_id = messaging_event.get("recipient", {}).get("id")
                message_text = messaging_event.get("message", {}).get("text")

                # Log the basic message
                _logger.info("Message from %s to %s: %s", sender_id, recipient_id, message_text)

                # Optionally, store it in a custom model or trigger logic in Odoo

        return "EVENT_RECEIVED"

