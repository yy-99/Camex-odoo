# -*- coding: utf-8 -*-
{
    'name': "Websers Delivery Base",
    'summary': "Websers delivery base",
    'description': "Websers Delivery Base",

    'author': "Websers",
    'website': "https://websers.odoo.com",
    'license': 'OPL-1',

    'category': 'Websers/Delivery',
    'version': '18.0.1.0.0',

    'depends': ['base', 'contacts', 'sale', 'stock', 'delivery'],

    'data': [
        'security/ir.model.access.csv',
        'views/base_city_view.xml',
        'views/base_area_view.xml',
        'views/sale_view.xml',
    ],

    'installable': True,
    'application': True,
}

