# -*- coding: utf-8 -*-
{
    'name': "INOV SHIPPING",

    'summary': "Gestion des dossiers du Shipping",

    'description': """
        ce module permet de suivre le processus de traitement d'un dossier de shipping,
        avant l'arrivee du navire, le sejour du navire et le depart du navire
    """,

    'author': "INOV CAMEROON",
    'website': "https://www.inov.cm",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'transit ',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['inov_transit','sale_management','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/stage_data.xml',
        'data/shipping_activity_type_view.xml',
        'data/product_data.xml',
        'data/devis_template.xml',
        'data/shipping_charges_data.xml',
        'data/analytic_plan_data.xml',
        'views/shipping_menu_views.xml',
        'data/template_douala.xml',
        'views/views.xml',
        'views/navire_views.xml',
        'views/bl_order_views.xml',
        'views/shipping_charges_views.xml',
        'views/payment_advance_views.xml',
        'views/templates.xml',
        'views/order_line.xml',
        'views/folder_financial_views.xml',
        'report/ir_report_account_invoice.xml',
        'report/ir_report_account_invoice_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
        'demo/port_charges_demo.xml',
        'demo/advance_payments_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

