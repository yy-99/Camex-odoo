# -*- coding: utf-8 -*-

from odoo import models, fields, api
import secrets
import string

class MetaApp(models.Model):
    _name = "meta.app"
    _description = "Meta Developer App"

    name = fields.Char(string="App Name", required=True)
    app_id = fields.Char(string="App ID", required=True)
    app_secret = fields.Char(string="App Secret", required=True)

    verify_token = fields.Char(string="Verify Token", compute='_compute_verify_token', store=True, copy=False)
    webhook_url = fields.Char(string="Webhook URL", compute='_compute_webhook_url', readonly=True, copy=False)

    is_active = fields.Boolean(string="Is Active", default=True)

    social_account_ids = fields.One2many(
        "meta.social.account",
        "meta_app_id",
        string="Linked Social Accounts"
    )

    def _compute_webhook_url(self):
        for acc in self:
            acc.webhook_url = acc.get_base_url() + '/meta/webhook'

    @api.depends('app_id')
    def _compute_verify_token(self):
        """ verify_token only set when record is created. Not update after that."""
        for account in self:
            if account.id and not account.verify_token:
                account.verify_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(15))