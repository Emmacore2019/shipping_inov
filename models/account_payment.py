# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ShippingAccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        """Surcharge pour créer des lignes analytiques lors de paiements sur proformas shipping"""
        res = super(ShippingAccountPayment, self).action_post()
        
        # Traiter chaque paiement
        for payment in self:
            # Vérifier si le paiement concerne des factures de vente (proformas)
            sale_invoices = payment.reconciled_invoice_ids.filtered(
                lambda inv: inv.move_type == 'out_invoice'
            )
            
            for invoice in sale_invoices:
                # Chercher les commandes de vente (proformas) liées à cette facture
                sale_orders = self.env['sale.order'].search([
                    ('invoice_ids', 'in', invoice.ids),
                    ('folder_id', '!=', False)
                ])
                
                for order in sale_orders:
                    if order.folder_id and order.folder_id.stages == 'ship':
                        # Calculer le montant du paiement alloué à cette commande
                        payment_amount = self._calculate_payment_amount_for_order(payment, order, invoice)
                        
                        if payment_amount > 0:
                            # Créer une ligne analytique pour l'avance de paiement
                            self._create_advance_payment_analytic_line(payment, order, payment_amount)
        
        return res

    def _calculate_payment_amount_for_order(self, payment, sale_order, invoice):
        """
        Calcule le montant du paiement alloué à une commande de vente spécifique
        """
        # Si la facture ne concerne qu'une commande, tout le paiement lui est alloué
        related_orders = self.env['sale.order'].search([('invoice_ids', 'in', invoice.ids)])
        
        if len(related_orders) == 1:
            # Proportion du paiement pour cette facture
            if payment.currency_id == invoice.currency_id:
                invoice_payment_amount = min(abs(payment.amount), invoice.amount_residual_signed)
            else:
                # Conversion de devise si nécessaire
                invoice_payment_amount = payment.currency_id._convert(
                    abs(payment.amount),
                    invoice.currency_id,
                    payment.company_id,
                    payment.date
                )
                invoice_payment_amount = min(invoice_payment_amount, invoice.amount_residual_signed)
            
            return invoice_payment_amount
        else:
            # Si plusieurs commandes, répartir proportionnellement
            total_order_amount = sum(related_orders.mapped('amount_total'))
            if total_order_amount > 0:
                proportion = sale_order.amount_total / total_order_amount
                if payment.currency_id == invoice.currency_id:
                    return abs(payment.amount) * proportion
                else:
                    converted_amount = payment.currency_id._convert(
                        abs(payment.amount),
                        invoice.currency_id,
                        payment.company_id,
                        payment.date
                    )
                    return converted_amount * proportion
        
        return 0.0

    def _create_advance_payment_analytic_line(self, payment, sale_order, amount):
        """
        Crée une ligne analytique pour enregistrer l'avance de paiement dans le dossier
        """
        folder = sale_order.folder_id
        
        # Vérifier que le dossier a une distribution analytique
        if not folder.analytic_distribution:
            raise UserError(_(
                "Le dossier %s n'a pas de distribution analytique configurée. "
                "Impossible d'enregistrer l'avance de paiement."
            ) % folder.name)
        
        # Récupérer le premier compte analytique de la distribution
        account_ids = []
        for account_ids_str in folder.analytic_distribution.keys():
            account_ids.extend([int(id_) for id_ in account_ids_str.split(',')])
        
        if not account_ids:
            raise UserError(_(
                "Aucun compte analytique trouvé dans la distribution du dossier %s."
            ) % folder.name)
        
        main_analytic_account = self.env['account.analytic.account'].browse(account_ids[0])
        
        # Créer la ligne analytique pour l'avance de paiement
        analytic_line_vals = {
            'name': _('Avance de paiement - Proforma %s') % sale_order.name,
            'account_id': main_analytic_account.id,
            'partner_id': sale_order.partner_id.id,
            'amount': amount,  # Montant positif pour les revenus
            'currency_id': sale_order.currency_id.id,
            'date': payment.date,
            'ref': payment.name,
            'move_id': payment.move_id.id if payment.move_id else False,
            'general_account_id': payment.destination_account_id.id,
            'company_id': folder.company_id.id,
        }
        
        analytic_line = self.env['account.analytic.line'].create(analytic_line_vals)
        
        # Log pour traçabilité
        folder.message_post(
            body=_(
                "Avance de paiement enregistrée: %s %s pour la proforma %s (Paiement: %s)"
            ) % (
                amount,
                sale_order.currency_id.symbol,
                sale_order.name,
                payment.name
            ),
            message_type='notification'
        )
        
        return analytic_line

    @api.model
    def _get_or_create_advance_payment_product(self):
        """
        Récupère ou crée le produit pour les avances de paiement
        """
        advance_product = self.env.ref('inov_shipping.product_advance_payment', raise_if_not_found=False)
        
        if not advance_product:
            # Créer le produit s'il n'existe pas
            advance_product = self.env['product.product'].create({
                'name': 'Avance de paiement',
                'type': 'service',
                'invoice_policy': 'order',
                'default_code': 'ADV_PAY',
                'categ_id': self.env.ref('product.product_category_all').id,
                'list_price': 0.0,
                'purchase_ok': False,
                'sale_ok': True,
            })
            
            # Créer une référence externe pour le retrouver facilement
            self.env['ir.model.data'].create({
                'name': 'product_advance_payment',
                'module': 'inov_shipping',
                'model': 'product.product',
                'res_id': advance_product.id,
            })
        
        return advance_product
