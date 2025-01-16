# -*- coding: utf-8 -*-
from ast import literal_eval
from odoo import models, fields, api, _


class FretTransit(models.Model):
    _name = "fret.transit"

    name = fields.Char("Name")

class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'
    transit_id = fields.Many2one('folder.transit', string='Dossier')
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    folder_transit_id = fields.Many2one('folder.transit', string='Expédition')
class FolderTransit(models.Model):
    _inherit = 'folder.transit'
    # Exemple de fichier de configuration
    {
        "inov_shipping": {
            "report_folder_transit": "inov_shipping.report_folder_transit"
        }
    }

    number_of_hold = fields.Integer(related="vessel.number_of_hold", string='Nombre de Compartiment', store=True, )
    nce = fields.Char("C/E N")
    sign = fields.Char("CALL SIGN")
    type_carry = fields.Selection(related="vessel.type_carry", string="Type of Carrier")
    flag_id = fields.Many2one(
        related="vessel.flag_id",
        string='PAVILLON (FLAG)',
        store=True
    )
    weight_grt = fields.Float(related="vessel.weight_grt", strong="GRT", store=True)
    weight_drt = fields.Float(related="vessel.weight_drt", strong="NRT(mt)", store=True)
    vessel_loa = fields.Float(related="vessel.vessel_loa", strong="LOA", store=True)
    vessel_beam = fields.Float(related="vessel.vessel_beam", strong="Beam(m)", store=True)
    vessel_draft = fields.Float(related="vessel.vessel_draft", strong="Vessel Summer Draft", store=True)
    total_crew = fields.Integer(string="Equipage Vessel")
    captain_name = fields.Char(string="Nom du Capitaine")
    nbr_escale = fields.Integer(
        string="Nombre de Jour d'escale",
    )
    volum_vessel = fields.Float("Volume:cbm", compute='_get_data_vessel', store=True)

    # Ajout du champ Many2One pour le modèle de devis
    order_template_id = fields.Many2one(
    comodel_name = 'sale.order.template',
    string = "Modèle de Devis")

    # order_line_ids = fields.One2many('sale.order.line',pping 'folder_transit_id')

    # fret_id = fields.Many2one(string='Affreteur', comodel_name='res.partner', ondelete='restrict')
    bl_many_ids = fields.Many2many('folder.transit.bl', 'rel_transit_bl_order', string="BLs")
    sale_ids = fields.One2many(string='Proformas', comodel_name='sale.order', inverse_name='folder_id')
    sales_count = fields.Integer('Proformas', compute='compute_sales_ids', store=True)
    cargo_weight = fields.Float(string='Poids de la cargaison du navire', compute='sum_bl_qty', store=True)
    

    @api.depends('vessel_draft','vessel_loa','vessel_beam')
    def _get_data_vessel(self):
        for record in self:
            record.volum_vessel = record.vessel_draft * record.vessel_loa * record.vessel_beam

    @api.depends('bl_many_ids.qty')
    def sum_bl_qty(self):
        for record in self:
            # Initialiser une variable pour la somme
            total_qty = 0.0

            # Itérer sur chaque enregistrement de bl_many_ids pour additionner les quantités
            for bl in record.bl_many_ids:
                total_qty += bl.qty  # Ajouter la quantité à la somme

            # Afficher le tableau des quantités dans la console
            print("Quantités des enregistrements BL :", [bl.qty for bl in record.bl_many_ids])

            # Assigner la somme au champ cargo_weight
            record.cargo_weight = total_qty

    @api.depends('sale_ids')
    def compute_sales_ids(self):
        for record in self:
            record.sales_count = len(record.sale_ids)

    def act_folder_transit_2_sale_order(self):
        action = self.env.ref('inov_shipping.act_folder_transit_2_sale_order').read()[0]
        saleids = self.mapped('sale_ids')
        data = {
            'search_default_folder_id': self.id,
            'search_default_partner_id': self.customer_id.id,
        }

        action['context'] = data
        if len(saleids) > 1:
            action['domain'] = [('id', 'in', saleids.ids)]
        # else:
        #     action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        #     action['res_id'] = saleids.id
        return action


class FolderTransitBL(models.Model):
    _name = 'folder.transit.bl'
    _description = 'BL'

    name = fields.Char(string='Numero de BL')
    customer_id = fields.Many2one(
        'res.partner',
        string='Client',
        domain=[('customer_rank', '=', True)],
        tracking=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Produit',
        domain=[('type', '=', 'product')],
    )
    package = fields.Selection([('manos', 'T20'), ('plus', 'T40'), ('other', 'Colis')], string="Colisage")
    qty = fields.Float(string='Quantite')
    package_uom_id = fields.Many2one(
        'uom.uom',
        string='Unite de Mesure',
    )

    state_related = fields.Selection([('transit', 'Dedouanement'), ('accone', 'Acconage'), ('ship', 'Shipping')],
                                     string="Processus")
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoye'),
    ], string='Etat', default='draft')