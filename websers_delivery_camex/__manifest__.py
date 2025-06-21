# -*- coding: utf-8 -*-
{
    'name': "CAMEX Shipping",
    'summary': "CAMEX Shipping",
    'description': "CAMEX Shipping",

    'author': "Websers",
    'website': "https://websers.odoo.com",
    'license': 'OPL-1',

    'category': 'Websers/Delivery',
    'version': '18.0.1.0.0',

    'depends': ['base', 'websers_delivery_base'],

    'data': [
        'security/ir.model.access.csv',
        'views/delivery_camex_view.xml',
        'views/camex_city_view.xml',
        'views/res_config_settings_view.xml',
    ],


    'images': ["static/description/image.png"],

    'installable': True,
    'application': False,

    'controllers': [
        # 'controllers/example_controller.py'
    ],

    'maintainer': 'Websers Technology',
    'currency': 'USD',
    'price': '60.00'

}
