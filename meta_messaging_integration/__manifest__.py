# -*- coding: utf-8 -*-
{
    "name": "Meta Messaging Integration",
    "version": "1.0",
    "category": "Social",
    "summary": "Integrate Meta (Facebook & Instagram) messaging into Odoo",
    "description": """
        This module allows you to integrate your Facebook Business Pages and Instagram Professional Accounts
        with Odoo to send and receive messages using Meta's Graph API.
        It provides models to manage app credentials and connected social accounts.
    """,
    "author": "ORO",
    'company': 'ORO',
    'website': "https://www.oro.com",
    "depends": ["base", "mail", "sales_team"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",

        "views/meta_app_views.xml",
        "views/meta_social_account_views.xml",
    ],
}
