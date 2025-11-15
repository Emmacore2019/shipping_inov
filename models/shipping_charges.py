# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ShippingChargeItem(models.Model):
    _name = "shipping.charge.item"
    _description = "Port / Shipping tariff grid item"
    _order = "category, code"

    code = fields.Char("Code", required=True, help="e.g. 1.1, 1.2, ...")
    name = fields.Char("Description", required=True)

    category = fields.Selection([
        ("port_charges", "1/ Outlays / PORT CHARGES"),
        ("mooring", "2/ Outlays / Terminal costs / MOORING"),
        ("other_outlays", "3/ Outlays / OTHER PORT EXPENSE"),
        ("agency_fee", "Services / Agency Fees"),
    ], string="Category", required=True)

    product_id = fields.Many2one(
        "product.product",
        string="Service Product",
        required=True,
        domain=[('type', '=', 'service')],
        help="Service product used on Sale Orders"
    )

    calc_mode = fields.Selection([
        ("fixed", "Fixed (lump sum)"),
        ("per_movement", "Per movement (pilotage in/out)"),
        ("per_tonne", "Per metric ton of cargo"),
        ("per_day", "Per day"),
        ("per_hour", "Per hour"),
        ("per_trip", "Per trip"),
        ("per_call", "Per port call"),
        ("per_visit", "Per visit"),
        ("per_night", "Per night"),
        ("eur_fixed", "EUR Fixed (with exchange rate)"),
        ("eur_per_hour", "EUR Per hour (with exchange rate)"),
        ("eur_per_call", "EUR Per call (with exchange rate)"),
    ], string="Calculation Mode", required=True)

    price_unit = fields.Monetary("Unit Price", required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    tax_ids = fields.Many2many("account.tax", string="Taxes")
    active = fields.Boolean(default=True)

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result


class ShippingChargeLine(models.Model):
    _name = "shipping.charge.line"
    _description = "Calculated shipping charge line"
    _order = "category, item_id"

    folder_id = fields.Many2one(
        "folder.transit",
        string="Shipping Folder",
        required=True,
        ondelete="cascade",
    )

    item_id = fields.Many2one(
        "shipping.charge.item",
        string="Tariff Item",
        required=True,
    )

    category = fields.Selection(
        related="item_id.category",
        store=True,
    )

    code = fields.Char(related="item_id.code", string="Code", store=True)
    description = fields.Char(related="item_id.name", string="Description", store=True)
    calc_mode = fields.Selection(related="item_id.calc_mode", string="Calculation", store=True)

    qty = fields.Float("Quantity", default=1.0, digits=(16, 3))
    price_unit = fields.Monetary("Unit Price", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        related="folder_id.currency_id",
        store=True,
    )

    amount = fields.Monetary("Amount", compute="_compute_amount", store=True)

    @api.depends("qty", "price_unit")
    def _compute_amount(self):
        for line in self:
            line.amount = line.qty * line.price_unit

    @api.onchange("item_id")
    def _onchange_item_id(self):
        if self.item_id:
            self.price_unit = self.item_id.price_unit