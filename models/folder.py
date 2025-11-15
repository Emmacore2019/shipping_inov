# -*- coding: utf-8 -*-
from ast import literal_eval
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FretTransit(models.Model):
    _name = "fret.transit"

    name = fields.Char("Name")

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    folder_id = fields.Many2one('folder.transit', string='Dossier Shipping')


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
    
    # ===========================================================================
    # CHAMPS POUR CALCULS DE CHARGES PORTUAIRES 
    # ===========================================================================
    
    # Variables pour pilotage et mouvements
    nb_pilotage_entry = fields.Integer("Nombre d'entrées", default=1, help="Nombre de mouvements d'entrée pour le pilotage IN offshore (code 1.1)")
    nb_pilotage_out = fields.Integer("Nombre de sorties", default=1, help="Nombre de mouvements de sortie pour le pilotage OUT")
    nb_pilotage_entry_offshore = fields.Integer("Entrées offshore", default=1, help="Nombre d'entrées offshore avec bonus pilote (code 1.2)")
    nb_pilotage_out_night_offshore = fields.Integer("Sorties nuit offshore", default=0, help="Nombre de sorties de nuit offshore (codes 1.3 et 1.4)")
    
    # Variables pour immobilisation pilote (en heures)
    immobilisation_in_night_hours = fields.Float("Immobilisation IN/NIGHT (h)", default=0.0, help="Heures d'immobilisation pilote IN/NIGHT avec bonus (codes 1.5 et 1.6)")
    immobilisation_special_hours = fields.Float("Immobilisation spéciale (h)", default=0.0, help="Heures d'immobilisation spéciale : nuit, week-end, férié (codes 1.7 et 1.8)")
    
    # Variables de surveillance et séjour
    security_night_hours = fields.Float("Surveillance nuit (h)", default=0.0, help="Heures de surveillance bonus de nuit (code 1.9)")
    ship_stay_days = fields.Float("Séjour rade (jours)", default=1.0, help="Nombre de jours de séjour sur rade/eaux portuaires (code 1.10)")
    
    # Variables pour tonnage et cargaison  
    cargo_weight_mt = fields.Float("Poids cargaison (MT)", default=0.0, help="Poids de cargaison en tonnes métriques pour redevance par tonne (code 1.11)")
    vessel_tonnage = fields.Float("Tonnage navire (GRT)", related="weight_grt", store=True, help="Tonnage brut du navire (Gross Register Tonnage) utilisé pour les calculs tarifaires")
    
    # Variables pour amarrage et séjour à quai
    mooring_total_hours = fields.Float("Durée amarrage (h)", default=36.0, help="Durée totale d'amarrage - forfait 36h inclus (code 1.14)")
    extra_hours_over_36 = fields.Float("Heures sup. 36h", compute="_compute_extra_hours", store=True, help="Heures supplémentaires au-delà de 36h d'amarrage (code 1.15)")
    
    # Variables pour services tiers et visites
    nb_calls = fields.Integer("Nombre d'escales", default=1, help="Nombre total d'escales portuaires (codes 1.12, 1.13, 1.16, 1.17, 1.24)")
    nb_customs_supervision_days = fields.Float("Supervision douane (j)", default=0.0, help="Nombre de jours de supervision douanière offshore (code 1.22)")
    nb_sanitation_visits = fields.Integer("Visites sanitaires", default=1, help="Nombre de visites d'officier sanitaire avec transport (code 1.19)") 
    nb_port_health_visits = fields.Integer("Visites santé port", default=1, help="Nombre d'inspections de santé portuaire (code 1.24)")
    nb_pilot_boat_trips = fields.Integer("Trajets bateau pilote", default=1, help="Nombre de trajets aller-retour du bateau pilote (codes 1.18, 1.20)")
    
    # Variables d'hébergement et transport
    nb_nuits_pilot = fields.Float("Nuits pilote", default=0.0, help="Nombre de nuits d'hébergement pour le pilote avec transport (code 1.23)")
    nb_nuits_port_health = fields.Float("Nuits agent santé", default=0.0, help="Nombre de nuits d'hébergement pour l'agent de santé portuaire avec transport (code 1.25)")
    
    # Taux de change pour conversions EUR
    exchange_rate_eur = fields.Float("Taux change EUR", default=655.96, help="Taux de change EUR vers XAF pour conversion automatique des tarifs EUR (655.96 XAF = 1 EUR)")
    
    # Relation avec les lignes de charges calculées
    shipping_charge_line_ids = fields.One2many(
        'shipping.charge.line',
        'folder_id', 
        string='Grille de Tarification',
        help="Grille complète des 26 lignes de charges portuaires calculées automatiquement selon les variables du navire (codes 1.1 à 1.26)"
    )
    
    @api.depends('mooring_total_hours')
    def _compute_extra_hours(self):
        """Calcule les heures supplémentaires au-delà de 36h"""
        for record in self:
            record.extra_hours_over_36 = max(record.mooring_total_hours - 36.0, 0.0)
    
    def _get_qty_for_item(self, item_code):
        """
        Retourne la quantité pour un item donné selon sa logique de calcul
        Basé sur l'analyse des codes 1.1 à 1.26
        """
        self.ensure_one()
        
        qty_mapping = {
            # 1/ Outlays / PORT CHARGES (1.1 → 1.13)
            "1.1": self.nb_pilotage_entry,  # PILOTAGE Entry, IN Offshore
            "1.2": self.nb_pilotage_entry_offshore,  # PILOT Bonus In Offshore  
            "1.3": self.nb_pilotage_out_night_offshore,  # PILOTAGE Out Night Offshore
            "1.4": self.nb_pilotage_out_night_offshore,  # PILOT Bonus Out Night offshore
            "1.5": self.immobilisation_in_night_hours,  # PILOT Immobilization IN/NIGHT (heures)
            "1.6": self.immobilisation_in_night_hours,  # Bonus PILOT Immobilization IN/NIGHT
            "1.7": self.immobilisation_special_hours,  # PILOT Immobilization spéciale (nuit/WE/férié)
            "1.8": self.immobilisation_special_hours,  # Bonus PILOT Immobilization spéciale
            "1.9": self.security_night_hours,  # Security Watch Bonus Night time (heures)
            "1.10": self.ship_stay_days,  # Ship stay on waters (jours)
            "1.11": self.cargo_weight_mt,  # Royalty per tonne of cargo loaded
            "1.12": self.nb_calls,  # Port Royalty / Redevance consignation classe 1
            "1.13": self.nb_calls,  # Environmental Royalties Petrolier
            
            # 2/ Outlays / Terminal costs / MOORING (1.14 → 1.16)  
            "1.14": 1,  # Mooring 36 Hrs Stay (forfait)
            "1.15": self.extra_hours_over_36,  # Each additional hour over 36 Hrs
            "1.16": self.nb_calls,  # Traffic Dues
            
            # 3/ Outlays / OTHER PORT EXPENSE (1.17 → 1.25)
            "1.17": self.nb_calls,  # Customs boarding in & out
            "1.18": 2,  # Piloting thro & fro (TWO TRIPS) - toujours 2
            "1.19": self.nb_sanitation_visits,  # Transportation Ship Sanitation Officer
            "1.20": 2,  # Piloting thro & fro (TWO TRIPS) - toujours 2  
            "1.21": 2,  # Transport Port Health officer (TWO TRIPS) - toujours 2
            "1.22": self.nb_customs_supervision_days,  # Customs supervision per day
            "1.23": max(self.nb_nuits_pilot, 1),  # Accommodation Pilot
            "1.24": self.nb_calls,  # Port health Inspection
            "1.25": max(self.nb_nuits_port_health, 1),  # Accommodation Port Health officer
            
            # Services (1.26)
            "1.26": 1,  # Agency Fees (ALL IN) - forfait
        }
        
        return qty_mapping.get(item_code, 1.0)
    
    def action_compute_shipping_grid(self):
        """
        Calcule automatiquement la grille de tarification shipping
        en créant les lignes shipping.charge.line avec les bonnes quantités
        """
        self.ensure_one()
        
        # Supprimer les anciennes lignes
        self.shipping_charge_line_ids.unlink()
        
        # Récupérer tous les items de tarification actifs
        charge_items = self.env['shipping.charge.item'].search([('active', '=', True)])
        
        lines_to_create = []
        for item in charge_items:
            qty = self._get_qty_for_item(item.code)
            
            # Ne créer que les lignes avec quantité > 0
            if qty > 0:
                price_unit = item.price_unit
                
                # Conversion EUR si nécessaire
                if item.calc_mode in ['eur_fixed', 'eur_per_hour', 'eur_per_call']:
                    price_unit = item.price_unit * self.exchange_rate_eur
                
                lines_to_create.append({
                    'folder_id': self.id,
                    'item_id': item.id,
                    'qty': qty,
                    'price_unit': price_unit,
                })
        
        # Créer toutes les lignes d'un coup
        if lines_to_create:
            self.env['shipping.charge.line'].create(lines_to_create)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f"Grille de tarification calculée : {len(lines_to_create)} lignes créées",
                'type': 'success',
                'sticky': False,
            }
        }
    sale_ids = fields.One2many(string='Proformas', comodel_name='sale.order', inverse_name='folder_id')
    sales_count = fields.Integer('Proformas', compute='compute_sales_ids', store=True)
    cargo_weight = fields.Float(string='Poids de la cargaison du navire', compute='sum_bl_qty', store=True,readonly=False)
    
    # Champs financiers pour le suivi des proformas et avances
    proforma_total_amount = fields.Monetary(
        string='Montant Total Proforma',
        currency_field='currency_id',
        compute='_compute_financial_amounts',
        store=True,
        groups='account.group_account_user',
        help="Montant total de toutes les proformas du dossier"
    )
    advance_total_received = fields.Monetary(
        string='Total Avances Reçues',
        currency_field='currency_id',
        compute='_compute_financial_amounts',
        store=True,
        groups='account.group_account_user',
        help="Total des avances reçues du client"
    )
    expenses_total_amount = fields.Monetary(
        string='Total Dépenses',
        currency_field='currency_id',
        compute='_compute_financial_amounts',
        store=True,
        groups='account.group_account_user',
        help="Total des dépenses engagées sur le dossier"
    )
    advance_remaining = fields.Monetary(
        string='Solde Avance Disponible',
        currency_field='currency_id',
        compute='_compute_financial_amounts',
        store=True,
        groups='account.group_account_user',
        help="Avance reçue - Dépenses engagées"
    )
    final_balance = fields.Monetary(
        string='Solde Final',
        currency_field='currency_id',
        compute='_compute_financial_amounts',
        store=True,
        groups='account.group_account_user',
        help="Montant final à facturer (peut être négatif si remboursement)"
    )
    advance_consumption_status = fields.Selection([
        ('available', 'Disponible'),
        ('warning', 'Attention (80%)'),
        ('critical', 'Critique (100%)'),
        ('exhausted', 'Épuisée')
    ], string='Statut Consommation Avance', compute='_compute_financial_amounts', store=True)
    
    shipping_financial_status = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_progress', 'En Cours'),
        ('ready_final', 'Prêt Facturation'),
        ('completed', 'Terminé')
    ], string='Statut Financier', compute='_compute_financial_amounts', store=True)
    
    advance_consumption_progress = fields.Float(
        string='Progression Consommation',
        compute='_compute_financial_amounts',
        store=True,
        help="Pourcentage de consommation de l'avance"
    )
    
    # Champ devise par défaut (monnaie de la société)
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # Grille tarifaire portuaire
    shipping_charge_ids = fields.One2many(
        "shipping.charge.line",
        "folder_id",
        string="Port Charges Grid",
    )

    shipping_outlays_total = fields.Monetary(
        string="Total Outlays",
        currency_field="currency_id",
        compute="_compute_shipping_totals",
        store=True,
    )

    shipping_services_total = fields.Monetary(
        string="Total Services",
        currency_field="currency_id",
        compute="_compute_shipping_totals",
        store=True,
    )
    
    # Champs pour les calculs de quantités (conservés pour compatibilité)
    mooring_hours = fields.Float("Mooring Duration (hours)", default=36.0, help="Durée d'amarrage en heures - utilisé pour calculer les heures supplémentaires au-delà du forfait de 36h")
    nb_pilot_entry = fields.Integer("Pilot Entry (Offshore)", default=0, help="Nombre d'entrées de pilotage offshore pour navires > 70.001 TJB (code 1.1)")
    nb_pilot_bonus_in = fields.Integer("Pilot Bonus In", default=0, help="Bonus pilote pour entrée offshore - tarif supplémentaire appliqué (code 1.2)")
    nb_pilot_out_night = fields.Integer("Pilot Out Night", default=0, help="Nombre de sorties de pilotage de nuit offshore pour navires > 70.001 TJB (code 1.3)")
    nb_pilot_bonus_out = fields.Integer("Pilot Bonus Out Night", default=0, help="Bonus pilote pour sortie de nuit offshore - tarif supplémentaire (code 1.4)")
    nb_pilot_immobilization_in = fields.Integer("Pilot Immobilization IN", default=0, help="Nombre d'heures d'immobilisation pilote IN/NIGHT (code 1.5)")
    nb_pilot_immobilization_bonus = fields.Integer("Pilot Immobilization Bonus", default=0, help="Bonus pour immobilisation pilote IN/NIGHT - tarif supplémentaire (code 1.6)")
    nb_pilot_immobilization_night = fields.Integer("Pilot Immobilization Night", default=0, help="Heures d'immobilisation pilote en période spéciale : nuit, week-end, jours fériés (code 1.7)")
    nb_pilot_immobilization_night_bonus = fields.Integer("Pilot Immobilization Night Bonus", default=0, help="Bonus pour immobilisation pilote en période spéciale - tarif majoré (code 1.8)")
    nb_security_watch_bonus = fields.Integer("Security Watch Bonus", default=0, help="Bonus de surveillance de sécurité pendant les heures de nuit (code 1.9)")
    nb_customs_supervision_days = fields.Integer("Customs Supervision Days", default=1, help="Nombre de jours de supervision douanière offshore (code 1.22) - version entière de nb_customs_supervision_days")
    nb_customs_boarding = fields.Integer("Customs Boarding In/Out", default=2, help="Nombre de montées/descentes douanières à bord du navire - généralement 2 (entrée/sortie) - (code 1.17)")
    nb_trips_piloting = fields.Integer("Piloting Trips (Two trips)", default=2, help="Nombre de trajets aller-retour pour pilotage - standard 2 voyages (codes 1.18, 1.20)")
    nb_trips_sanitation = fields.Integer("Sanitation Officer Trips", default=2, help="Nombre de trajets aller-retour pour transport de l'officier sanitaire (code 1.19)")
    nb_trips_health = fields.Integer("Health Officer Trips", default=2, help="Nombre de trajets aller-retour pour transport de l'officier de santé portuaire (code 1.21)")
    nb_port_health_inspection = fields.Integer("Port Health Inspections", default=1, help="Nombre d'inspections de santé portuaire pour obtenir la libre pratique (code 1.24)")
    nb_accommodation_pilot = fields.Integer("Accommodation Pilot", default=1, help="Nombre de nuits d'hébergement et transport aller-retour pour le pilote (code 1.23)")
    nb_accommodation_health = fields.Integer("Accommodation Health Officer", default=1, help="Nombre de nuits d'hébergement et transport aller-retour pour l'officier de santé (code 1.25)")
    

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


            # Assigner la somme au champ cargo_weight
            record.cargo_weight = total_qty

    @api.depends('sale_ids')
    def compute_sales_ids(self):
        for record in self:
            record.sales_count = len(record.sale_ids)

    def act_folder_transit_2_sale_order(self):
        """Action pour afficher les proformas de ce dossier shipping"""
        self.ensure_one()
        return {
            'name': f'Proformas - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('folder_id', '=', self.id)],
            'context': {
                'default_folder_id': self.id,
                'default_partner_id': self.customer_id.id,
                'search_default_folder_id': self.id,
            },
            'target': 'current',
        }
    
    @api.depends('sale_ids', 'sale_ids.amount_total', 'line_ids', 'line_ids.amount')
    def _compute_financial_amounts(self):
        """Calcule tous les montants financiers du dossier shipping"""
        for record in self:
            # Calcul du montant total des proformas
            proforma_total = sum(record.sale_ids.mapped('amount_total'))
            record.proforma_total_amount = proforma_total
            
            # Calcul des avances reçues (si le module inov_account est installé)
            advance_total = 0.0
            if hasattr(record, 'advance_payment_ids'):
                advance_total = sum(record.advance_payment_ids.mapped('amount_total'))
            record.advance_total_received = advance_total
            
            # Calcul des dépenses (lignes analytiques négatives)
            expenses_total = 0.0
            if hasattr(record, 'line_ids'):
                expenses_total = sum(
                    abs(line.amount) for line in record.line_ids 
                    if line.amount < 0
                )
            record.expenses_total_amount = expenses_total
            
            # Calcul du solde avance disponible
            advance_remaining = advance_total - expenses_total
            record.advance_remaining = advance_remaining
            
            # Calcul du solde final (proforma - avances - dépenses supplémentaires)
            final_balance = proforma_total - advance_total
            record.final_balance = final_balance
            
            # Calcul du statut de consommation de l'avance
            if advance_total > 0:
                consumption_rate = (expenses_total / advance_total) * 100
                record.advance_consumption_progress = min(consumption_rate, 100)
                
                if consumption_rate < 80:
                    status = 'available'
                elif consumption_rate < 100:
                    status = 'warning'
                elif consumption_rate >= 100 and advance_remaining >= 0:
                    status = 'critical'
                else:
                    status = 'exhausted'
            else:
                record.advance_consumption_progress = 0
                status = 'available' if expenses_total == 0 else 'exhausted'
            
            record.advance_consumption_status = status
            
            # Calcul du statut financier global
            if not record.sale_ids:
                financial_status = 'draft'
            elif expenses_total == 0:
                financial_status = 'in_progress'
            elif expenses_total > 0 and advance_total > 0:
                financial_status = 'ready_final'
            else:
                financial_status = 'completed'
            
            record.shipping_financial_status = financial_status
    
    @api.depends("shipping_charge_ids.amount", "shipping_charge_ids.category")
    def _compute_shipping_totals(self):
        """Calcule les totaux par catégorie de la grille tarifaire"""
        for rec in self:
            outlays = 0.0
            services = 0.0
            for line in rec.shipping_charge_ids:
                if line.category in ("port_charges", "mooring", "other_outlays"):
                    outlays += line.amount
                elif line.category == "agency_fee":
                    services += line.amount
            rec.shipping_outlays_total = outlays
            rec.shipping_services_total = services
    
    def _get_category_label(self, category):
        """Retourne le libellé d'affichage pour une catégorie"""
        return {
            "port_charges": "1/ Outlays / PORT CHARGES",
            "mooring": "2/ Outlays / Terminal costs / MOORING",
            "other_outlays": "3/ Outlays / OTHER PORT EXPENSE",
            "agency_fee": "Services – Agency Fees",
        }.get(category, "Other Charges")
    
    def _get_qty_for_item(self, item):
        """Calcule la quantité à appliquer pour un élément tarifaire donné"""
        self.ensure_one()
        
        # PORT CHARGES
        if item.code == "1.1":  # PILOTAGE Entry, IN Offshore > 70.001 TJB
            return float(self.nb_pilot_entry or 0)
        elif item.code == "1.2":  # PILOT Bonus In Offshore
            return float(self.nb_pilot_bonus_in or 0)
        elif item.code == "1.3":  # PILOTAGE Out Night Offshore > 70.001 TJB
            return float(self.nb_pilot_out_night or 0)
        elif item.code == "1.4":  # PILOT Bonus Out Night offshore
            return float(self.nb_pilot_bonus_out or 0)
        elif item.code == "1.5":  # PILOT Immobilization --- IN/NIGHT
            return float(self.nb_pilot_immobilization_in or 0)
        elif item.code == "1.6":  # Bonus PILOT Immobilization --- IN/NIGHT
            return float(self.nb_pilot_immobilization_bonus or 0)
        elif item.code == "1.7":  # PILOT Immobilization --- Night, Weekend & holidays (IN)
            return float(self.nb_pilot_immobilization_night or 0)
        elif item.code == "1.8":  # Bonus PILOT Immobilization --- Night, Weekend & holidays (IN)
            return float(self.nb_pilot_immobilization_night_bonus or 0)
        elif item.code == "1.9":  # Security Watch Bonus --- Night time
            return float(self.nb_security_watch_bonus or 0)
        elif item.code == "1.10":  # Ship stay on waters
            return float(self.nbr_escale or 0)
        elif item.code == "1.11":  # Royalty stay on operation per tonne of cargo loaded
            return self.cargo_weight or 0.0
        elif item.code == "1.12":  # Port Royalty / Redevance consignation classe 1 KK1
            return 1.0  # Lump sum
        elif item.code == "1.13":  # Environmental Royalties / REDEVANCE ENVIR Petrolier
            return 1.0  # Lump sum
            
        # MOORING
        elif item.code == "1.14":  # Mooring / per 36 Hrs Stay (lumpsum)
            return 1.0
        elif item.code == "1.15":  # Per each additional hour over 36 Hrs
            return max(self.mooring_hours - 36.0, 0.0)
        elif item.code == "1.16":  # Traffic Dues
            return 1.0  # Lump sum
            
        # OTHER PORT EXPENSE
        elif item.code == "1.17":  # Customs boarding in & out
            return float(self.nb_customs_boarding or 0)
        elif item.code == "1.18":  # Piloting thro & fro (TWO TRIPS)
            return float(self.nb_trips_piloting or 0)
        elif item.code == "1.19":  # Transportation of Ship Sanitation Control Officer (thro & fro)
            return float(self.nb_trips_sanitation or 0)
        elif item.code == "1.20":  # Piloting thro & fro (TWO TRIPS) - duplicate of 1.18
            return float(self.nb_trips_piloting or 0)
        elif item.code == "1.21":  # Transport of Port Health officer thro & fro (TWO TRIPS)
            return float(self.nb_trips_health or 0)
        elif item.code == "1.22":  # Customs supervision per day (Offshore)
            return float(self.nb_customs_supervision_days or 0)
        elif item.code == "1.23":  # Accommodation and Transportation to the Port - Pilot (Thro & fro)
            return float(self.nb_accommodation_pilot or 0)
        elif item.code == "1.24":  # Port health Inspection (Free Pratique granted)
            return float(self.nb_port_health_inspection or 0)
        elif item.code == "1.25":  # Accommodation and Transportation to the Port - Port health officer (Thro & fro)
            return float(self.nb_accommodation_health or 0)
            
        # SERVICES
        elif item.code == "1.26":  # Agency Fees (ALL IN)
            return 1.0  # Lump sum
            
        return 0.0
    
    def action_compute_shipping_grid(self):
        """Calcule la grille tarifaire portuaire"""
        for rec in self:
            items = rec.env["shipping.charge.item"].search([("active", "=", True)])

            # Supprimer les calculs précédents
            rec.shipping_charge_ids.unlink()

            lines_vals = []
            for item in items:
                qty = rec._get_qty_for_item(item)
                if not qty:
                    continue
                lines_vals.append((0, 0, {
                    "item_id": item.id,
                    "qty": qty,
                    "price_unit": item.price_unit,
                }))

            rec.shipping_charge_ids = lines_vals
        
        return True
    
    def action_create_grid_proforma(self):
        """Crée ou met à jour une proforma basée sur la grille tarifaire"""
        self.ensure_one()

        if not self.customer_id:
            raise UserError(_("Please set a customer on the shipping folder."))

        # S'assurer que la grille est à jour
        self.action_compute_shipping_grid()

        SaleOrder = self.env["sale.order"]

        # Réutiliser une proforma existante ou en créer une nouvelle
        if self.sale_ids:
            order = self.sale_ids[0]
            order.order_line.unlink()
        else:
            order_vals = {
                "partner_id": self.customer_id.id,
                "folder_id": self.id,
                "currency_id": self.currency_id.id,
                "origin": self.name,
            }
            if self.order_template_id:
                order_vals["sale_order_template_id"] = self.order_template_id.id
            order = SaleOrder.create(order_vals)

        line_vals = []
        current_category = None

        # Trier les lignes par catégorie puis par code
        for line in self.shipping_charge_ids.sorted(key=lambda l: (l.category, l.item_id.code)):
            # Ajouter une section pour chaque nouvelle catégorie
            if line.category != current_category:
                line_vals.append((0, 0, {
                    "display_type": "line_section",
                    "name": self._get_category_label(line.category),
                }))
                current_category = line.category

            product = line.item_id.product_id
            if not product:
                continue

            # Ajouter la ligne de service
            line_vals.append((0, 0, {
                "product_id": product.id,
                "name": f"{line.item_id.code} - {line.item_id.name}",
                "product_uom_qty": line.qty,
                "price_unit": line.price_unit,
                "tax_id": [(6, 0, line.item_id.tax_ids.ids)],
                "folder_transit_id": self.id,
            }))

        order.order_line = line_vals

        # Mise à jour automatique de la distribution analytique si le module inov_account est installé
        if  self.analytic_id  and self.analytic_distribution and self.sale_ids:
            # Récupérer la proforma créée/mise à jour (la première ou celle qui vient d'être modifiée)
            order = self.sale_ids[0] if self.sale_ids else None
            
            if order and order.order_line:
                # Mettre à jour la distribution analytique sur toutes les lignes de la proforma
                for line in order.order_line.filtered(lambda l: not l.display_type):
                    line.write({
                        'analytic_distribution': self.analytic_distribution
                    })

        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": order.id,
            "target": "current",
            "context": {"create": False},
        }
    
    def action_create_final_invoice(self):
        """Créer une proforma définitive basée sur les dépenses réelles du dossier shipping"""
        self.ensure_one()
        
        if not self.customer_id:
            raise UserError(_("Aucun client défini pour ce dossier"))
        
        if self.stages != 'ship':
            raise UserError(_("Cette action n'est disponible que pour les dossiers shipping"))
        
        # Créer la proforma définitive
        proforma_vals = {
            'partner_id': self.customer_id.id,
            'folder_id': self.id,
            'order_template_id': self.order_template_id.id if self.order_template_id else False,
            'note': f"""
PROFORMA DÉFINITIVE - DOSSIER {self.name}

Résumé financier:
• Montant proformas initiales: {self.proforma_total_amount:,.2f}
• Avances reçues: {self.advance_total_received:,.2f}
• Dépenses réelles engagées: {self.expenses_total_amount:,.2f}
• Solde final: {self.final_balance:,.2f}

Cette proforma définitive reflète les coûts réels du shipping.
            """,
        }
        
        # Ajouter les lignes basées sur les dépenses réelles
        order_lines = []
        
        # Section des services réels
        if hasattr(self, 'line_ids') and self.line_ids:
            # Regrouper les lignes par type
            expense_lines = self.line_ids.filtered(lambda l: l.amount < 0)
            
            if expense_lines:
                # Ligne de section pour les services
                order_lines.append((0, 0, {
                    'display_type': 'line_section',
                    'name': f'=== SERVICES RÉELS - {self.name} ===',
                }))
                
                # Ajouter chaque dépense comme ligne
                for line in expense_lines:
                    order_lines.append((0, 0, {
                        'name': line.name or f'Service shipping - {line.ref or "N/A"}',
                        'price_unit': abs(line.amount),
                        'product_uom_qty': 1,
                        'folder_transit_id': self.id,
                    }))
        
        # Si pas de lignes analytiques, utiliser un service standard
        if not order_lines:
            order_lines.append((0, 0, {
                'name': f'Services Shipping - {self.name}',
                'price_unit': self.expenses_total_amount or self.proforma_total_amount,
                'product_uom_qty': 1,
                'folder_transit_id': self.id,
            }))
        
        # Ajouter section d'ajustement si nécessaire
        if abs(self.final_balance) > 0.01:  # Éviter les erreurs d'arrondi
            order_lines.append((0, 0, {
                'display_type': 'line_section',
                'name': '=== AJUSTEMENT FINAL ===',
            }))
            
            if self.final_balance > 0:
                order_lines.append((0, 0, {
                    'name': 'Complément à facturer',
                    'price_unit': self.final_balance,
                    'product_uom_qty': 1,
                    'folder_transit_id': self.id,
                }))
            else:
                order_lines.append((0, 0, {
                    'name': 'Avoir client (remboursement)',
                    'price_unit': self.final_balance,  # Déjà négatif
                    'product_uom_qty': 1,
                    'folder_transit_id': self.id,
                }))
        
        proforma_vals['order_line'] = order_lines
        
        # Créer la proforma
        final_proforma = self.env['sale.order'].create(proforma_vals)
        
        return {
            'name': 'Proforma Définitive Créée',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': final_proforma.id,
            'view_mode': 'form',
            'target': 'current',
        }


class FolderTransitBL(models.Model):
    _name = 'folder.transit.bl'
    _description = 'BL'

    name = fields.Char(string='Numero de BL')
    customer_id = fields.Many2one(
        'res.partner',
        string='Client',
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