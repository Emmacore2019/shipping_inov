# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from datetime import datetime, timedelta, date
from ast import literal_eval
from odoo.exceptions import ValidationError
import logging

# Créez un logger
_logger = logging.getLogger(__name__)
class SaleShipTemplate(models.Model):
    _inherit='sale.order.template'

    is_proforma  = fields.Boolean("Est une Proforma")

class SaleTransit(models.Model):
    _inherit='sale.order'

    folder_id = fields.Many2one(
        'folder.transit',
        string='Dossier',
        )
    ref_customer = fields.Char(string="N° référence Client", store=True)
    vessel_id = fields.Many2one("vessel.transit",related="folder_id.vessel", strong="Navire", )
    weight_grt = fields.Float(related="folder_id.weight_grt", strong="GRT", store=True)
    vessel_loa = fields.Float(related="folder_id.vessel_loa", strong="LOA" , store=True)
    vessel_beam = fields.Float(related="folder_id.vessel_beam", strong="Beam(m)", store=True)
    vessel_draft = fields.Float(related="folder_id.vessel_draft", strong="SSWD", store=True)
    volume = fields.Float(related="folder_id.volum_vessel", strong="Volume", store=True)
    days = fields.Float("Nombre de Jours",)
    vessel_qty= fields.Float(related="folder_id.total_weighty", strong="Quantity", store=True)
    shipping_use = fields.Boolean(default=False)

    def _get_default_require_signature(self):
        return False  # Remplacez par la logique appropriée

    def _get_default_require_payment(self):
        return False  # Remplacez par la logique appropriée


    def _compute_line_data_for_vessel_change(self,line):
        if line.product_id.id == self.env.ref("inov_shipping.product_product_pilotage").id:
            return self.volume
        elif line.product_id.id == self.env.ref("inov_shipping.product_product_quay").id:
            return  self.volume*self.days
        elif line.product_id.id == self.env.ref("inov_shipping.product_product_ops").id:
            return  self.vessel_qty
        elif line.product_id.id == self.env.ref("inov_shipping.product_product_bonus").id:
            return  self.weight_grt
        elif line.product_id.id == self.env.ref("inov_shipping.product_product_pilotage_royaltie").id:
            return self.weight_grt
        elif line.product_id.id == self.env.ref("inov_shipping.product_product_royal").id:
            return self.weight_grt
        elif line.product_id.id == self.env.ref("inov_shipping.product_product_vessel").id:
            return self.days
        elif line.product_id.id == self.env.ref("inov_shipping.product_product_customs_watch").id:
            return self.days
        elif line.product_id.id == self.env.ref("inov_shipping.product_product_carservices").id:
            return self.days
        elif line.product_id.id == self.env.ref("inov_shipping.product_product_vhf").id:
            return self.days
        elif line.product_id.id == self.env.ref("inov_shipping.product_product_lumpsun").id:
            return self.vessel_qty
        else:
            return 1.0

   
    def get_shipping_price(self):

        prod1=self.env.ref("inov_shipping.product_product_pilotage")
        prod2=self.env.ref("inov_shipping.product_product_quay")
        prod3=self.env.ref("inov_shipping.product_product_ops")
        prod4=self.env.ref("inov_shipping.product_product_bonus")
        prod5=self.env.ref("inov_shipping.product_product_pilotage_bonus")
        prod6=self.env.ref("inov_shipping.product_product_chanel")
        prod7=self.env.ref("inov_shipping.product_product_tug")
        prod8=self.env.ref("inov_shipping.product_product_line")
        prod9=self.env.ref("inov_shipping.product_product_overt")
        prod10=self.env.ref("inov_shipping.product_product_royal")
        prod11=self.env.ref("inov_shipping.product_product_vessel")
        prod12=self.env.ref("inov_shipping.product_product_tax")
        prod13=self.env.ref("inov_shipping.product_product_code")
        prod14 = self.env.ref("inov_shipping.product_product_customs_watch")
        prod15 = self.env.ref("inov_shipping.product_product_navy")
        prod16 = self.env.ref("inov_shipping.product_product_health")
        prod17 = self.env.ref("inov_shipping.product_product_customs")
        prod18 = self.env.ref("inov_shipping.product_product_carservices")
        prod19 = self.env.ref("inov_shipping.product_product_vhf")
        prod20 = self.env.ref("inov_shipping.product_product_sanitary")
        prod21 = self.env.ref("inov_shipping.product_product_in/out")
        prod22 = self.env.ref("inov_shipping.product_product_ucam")
        prod23 = self.env.ref("inov_shipping.product_product_pilotage_royaltie")
        prod24 = self.env.ref("inov_shipping.product_product_miscellaneous")
        prod25 = self.env.ref("inov_shipping.product_product_cholera")
        prod26 = self.env.ref("inov_shipping.product_product_lumpsun")
        prod27 = self.env.ref("inov_shipping.product_product_vat")
        prod28 = self.env.ref("inov_shipping.product_product_vat")

        line1=self.order_line.filtered(lambda line:line.product_id.id==prod1.id)
        line2=self.order_line.filtered(lambda line:line.product_id.id==prod2.id)
        line3=self.order_line.filtered(lambda line:line.product_id.id==prod3.id)
        line4=self.order_line.filtered(lambda line:line.product_id.id==prod4.id)
        line5=self.order_line.filtered(lambda line:line.product_id.id==prod5.id)
        line6=self.order_line.filtered(lambda line:line.product_id.id==prod6.id)
        line7=self.order_line.filtered(lambda line:line.product_id.id==prod7.id)
        line8=self.order_line.filtered(lambda line:line.product_id.id==prod8.id)
        line9=self.order_line.filtered(lambda line:line.product_id.id==prod9.id)
        line10=self.order_line.filtered(lambda line:line.product_id.id==prod10.id)
        line11=self.order_line.filtered(lambda line:line.product_id.id==prod11.id)
        line12=self.order_line.filtered(lambda line:line.product_id.id==prod12.id)
        line13=self.order_line.filtered(lambda line:line.product_id.id==prod13.id)
        line14=self.order_line.filtered(lambda line:line.product_id.id==prod14.id)
        line15=self.order_line.filtered(lambda line:line.product_id.id==prod15.id)
        line16=self.order_line.filtered(lambda line:line.product_id.id==prod16.id)
        line17=self.order_line.filtered(lambda line:line.product_id.id==prod17.id)
        line18=self.order_line.filtered(lambda line:line.product_id.id==prod18.id)
        line19=self.order_line.filtered(lambda line:line.product_id.id==prod19.id)
        line20=self.order_line.filtered(lambda line:line.product_id.id==prod20.id)
        line21=self.order_line.filtered(lambda line:line.product_id.id==prod21.id)
        line22=self.order_line.filtered(lambda line:line.product_id.id==prod22.id)
        line23=self.order_line.filtered(lambda line:line.product_id.id==prod23.id)
        line24=self.order_line.filtered(lambda line:line.product_id.id==prod24.id)
        line25=self.order_line.filtered(lambda line:line.product_id.id==prod25.id)
        line26=self.order_line.filtered(lambda line:line.product_id.id==prod26.id)
        line27=self.order_line.filtered(lambda line:line.product_id.id==prod27.id)
        line28=self.order_line.filtered(lambda line:line.product_id.id==prod28.id)

        volume = self.volume
        grt = self.weight_grt
        qty = self.vessel_qty
        # Récupération du taux de change du dossier transit
        exchange_rate = self.folder_id.exchange_rate_eur if self.folder_id else 655.96
        
        if prod1 :
            line1.price_unit = 0.063 * volume * exchange_rate

        if prod2 :
            line2.price_unit = 0.0047 * volume * exchange_rate

        if prod3 :
            line3.price_unit = 0.063 * volume * exchange_rate

        if prod4 :
            line4.price_unit = 0.0047 * volume * exchange_rate

        if prod5 :
            line5.price_unit = 87.6 * line5.product_uom_qty * exchange_rate

        if prod6 :
            line6.price_unit = 30 * line6.product_uom_qty  * exchange_rate

        if prod7 :
            line7.price_unit = 87.6 * line7.product_uom_qty * exchange_rate

        if prod8 :
            line8.price_unit = 30 * line8.product_uom_qty  * exchange_rate

        if prod9 :
            line9.price_unit = 51 * exchange_rate

        if prod10 :
            line10.price_unit = 0.015 * volume * exchange_rate

        if prod11 :
            line11.price_unit = 0.014 * qty * exchange_rate

        if prod12 :
            line12.price_unit = 0.079 * grt * exchange_rate

        if prod13 :
            line13.price_unit = 182.94 * exchange_rate

        if prod14 :
            line14.price_unit = 0.063 * volume * exchange_rate

        if prod15 :
            line15.price_unit = 0.063 * volume * exchange_rate

        if prod16 :
            line16.price_unit = 0.063 * volume * exchange_rate

        if prod17 :
            line17.price_unit = 0.063 * volume * exchange_rate

        if prod18 :
            line18.price_unit = 0.063 * volume * exchange_rate

        if prod19 :
            line19.price_unit = 0.063 * volume * exchange_rate

        if prod20 :
            line20.price_unit = 0.063 * volume * exchange_rate

        if prod21 :
            line21.price_unit = 0.063 * volume * exchange_rate

        if prod22 :
            line22.price_unit = 0.063 * volume * exchange_rate

        if prod23 :
            line23.price_unit = 0.063 * volume * exchange_rate

        if prod24:
            line24.price_unit = 0.063 * volume * exchange_rate

        if prod25:
            line25.price_unit = 0.063 * volume * exchange_rate

        if prod26:
            line26.price_unit = 0.063 * volume * exchange_rate

        if prod27:
            line27.price_unit = 0.063 * volume * exchange_rate

        if prod28:
            line28.price_unit = 0.063 * volume * exchange_rate

        # if line1 and line2 and line3 and line4:
        #     line4.update({
        #         'price_unit': (line1.price_subtotal + line2.price_subtotal + line3.price_subtotal),
        #     })
        # line5.update({
        #     'product_uom_qty':
        #     (line1.price_subtotal + line2.price_subtotal + line3.price_subtotal
        #      + line4.price_subtotal + line6.price_subtotal +
        #      line7.price_subtotal + line8.price_subtotal +
        #      line9.price_subtotal + line10.price_subtotal +
        #      line11.price_subtotal + line12.price_subtotal) * 0.08,
        # })
        # line13.update({
        #     'product_uom_qty': (line14.price_subtotal),
        # })
        # self.write({
        #     'shipping_use': True,
        # })


class Saleorderline(models.Model):
    _inherit = 'sale.order.line'
    
    price_usd = fields.Float(
        string="Taux (Euro)",
        digits='Product Price',
        compute='_compute_exchange_rate_from_folder',
        store=True,
        help="Taux de change EUR récupéré automatiquement du dossier transit")
    
    price_usd_subtotal = fields.Float(
        string="Montant (Euro) ",
        compute='_compute_amount_usd',
        store=True, precompute=True)

    @api.depends('price_subtotal', 'price_usd')
    def _compute_amount_usd(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            line.update({
                'price_usd_subtotal': line.price_subtotal / line.price_usd if line.price_usd > 0 else 0.0
            })
    
    @api.depends('order_id.folder_id.exchange_rate_eur')
    def _compute_exchange_rate_from_folder(self):
        """
        Récupère le taux de change EUR du dossier transit associé
        """
        for line in self:
            if line.order_id and line.order_id.folder_id and line.order_id.folder_id.exchange_rate_eur:
                line.price_usd = line.order_id.folder_id.exchange_rate_eur
            else:
                line.price_usd = 655.96  # Valeur par défaut si pas de dossier

    
    @api.constrains("price_usd")
    def _check_price_usd(self):
        for s in self:
            if s.price_usd == 0.0:
                raise ValidationError(_("Le taux de conversion doit etre superieur a 0, Veuillez ressaisir ce taux"))     
