"""Configurable Retail Issue Taxonomy for Voice of Store Engine.

Documented taxonomy of ~30 issue types mapped strictly across the 5 core departments:
- Store Operations
- Supply Chain
- Merchandising
- Digital
- HR

Each entry specifies department owner, default severity, actionability flag,
associated compliance/operational SOP policy, and indicator keywords.
"""
from typing import Dict, Any, List

DEPARTMENTS = {
    "Store Operations",
    "Supply Chain",
    "Merchandising",
    "Digital",
    "HR",
}

TAXONOMY: Dict[str, Dict[str, Any]] = {
    # --- Store Operations (10 categories) ---
    "allergen_label": {
        "department": "Store Operations",
        "default_severity": "Critical",
        "actionable": True,
        "is_safety": True,
        "policy": "FDA Allergen Compliance & Customer Protection SOP-201",
        "description": "Zero-tolerance undeclared food allergen protocol (§4.2). Immediate product lot quarantine and recall verification.",
        "max_response_hours": 2,
        "keywords": ["allergen", "allergy", "wrong label", "ingredient label", "peanut", "nut warning", "milk warning", "gluten free label", "undeclared allergen"],
    },
    "food_safety": {
        "department": "Store Operations",
        "default_severity": "Critical",
        "actionable": True,
        "is_safety": True,
        "policy": "HACCP Food Safety & Contamination Protocol SOP-104",
        "description": "Biological hazard prevention standard. Immediate lot audit, cold chain quarantine, and Store Operations investigation.",
        "max_response_hours": 2,
        "keywords": ["food poisoning", "contaminated", "foreign object", "unsafe food", "raw chicken", "stomach illness", "nausea", "vomiting", "food bug", "spoiled meal"],
    },
    "hygiene": {
        "department": "Store Operations",
        "default_severity": "High",
        "actionable": True,
        "is_safety": True,
        "policy": "Store Sanitation & Pest Defense Standard SOP-302",
        "description": "Critical hygiene compliance. 4-hour remediation deadline and commercial vendor dispatch if pest or sanitation breach is detected.",
        "max_response_hours": 4,
        "keywords": ["dirty", "unhygienic", "pest", "cockroach", "rat", "mice", "rodent", "mold", "mould", "infestation", "droppings"],
    },
    "freezer_failure": {
        "department": "Store Operations",
        "default_severity": "High",
        "actionable": True,
        "is_safety": False,
        "policy": "Cold-Chain Integrity & Refrigeration Equipment SOP-405",
        "description": "Temperature telemetry audit, backup refrigeration transfer, and immediate HVAC technician dispatch within 4 hours.",
        "max_response_hours": 4,
        "keywords": ["freezer", "fridge not cold", "refrigerator", "cold storage", "chiller", "thawed", "melting", "compressor", "cold cabinet", "freezer alarm"],
    },
    "spill_hazard": {
        "department": "Store Operations",
        "default_severity": "High",
        "actionable": True,
        "is_safety": True,
        "policy": "Floor Safety & Slip/Trip/Fall Prevention SOP-305",
        "description": "Immediate floor barricade and rapid spill cleanup within 15 minutes to prevent customer injuries.",
        "max_response_hours": 1,
        "keywords": ["spill", "wet floor", "slippery", "liquid on floor", "broken glass", "trip hazard", "fall risk", "oil leak"],
    },
    "store_cleanliness": {
        "department": "Store Operations",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "Retail Environment & Housekeeping Standard SOP-310",
        "description": "Aisle sweeping, trash can emptying, and general store tidiness protocol.",
        "max_response_hours": 12,
        "keywords": ["messy aisle", "trash overflowing", "dusty shelves", "dirty floor", "garbage", "cluttered aisle", "litter"],
    },
    "restroom_maintenance": {
        "department": "Store Operations",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "Customer Amenities & Restroom Hygiene SOP-315",
        "description": "Sanitary restroom checks every 2 hours, restocking paper towels, soap, and resolving plumbing issues.",
        "max_response_hours": 4,
        "keywords": ["restroom", "toilet", "washroom", "no soap", "no toilet paper", "clogged toilet", "restroom smell", "hand dryer broken"],
    },
    "queue_management": {
        "department": "Store Operations",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "Front-End Line Flow & Cashier Allocation SOP-110",
        "description": "Queue length monitoring; open additional registers when queue exceeds 4 customers.",
        "max_response_hours": 1,
        "keywords": ["long queue", "line too long", "wait time", "slow checkout", "only one register open", "cashier queue", "crowded billing"],
    },
    "ac_temperature": {
        "department": "Store Operations",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "Store Climate & HVAC Comfort Standards SOP-420",
        "description": "Indoor air conditioning monitoring to maintain ambient store temperature between 21-24°C.",
        "max_response_hours": 6,
        "keywords": ["ac not working", "too hot in store", "air conditioning broken", "suffocating", "humid store", "no cooling", "hvac"],
    },
    "cart_basket_availability": {
        "department": "Store Operations",
        "default_severity": "Low",
        "actionable": True,
        "is_safety": False,
        "policy": "Shopping Equipment & Cart Management SOP-105",
        "description": "Cart corral roundups and hand basket replenishment at entrance foyer.",
        "max_response_hours": 2,
        "keywords": ["no carts", "no baskets", "broken trolley", "cart wheel stuck", "shopping cart missing", "need basket"],
    },

    # --- Supply Chain (6 categories) ---
    "stockout": {
        "department": "Supply Chain",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "On-Shelf Availability & Replenishment SOP-701",
        "description": "Essential SKU inventory tracking. Expedited DC delivery request if high-velocity items out of stock for >12 hours.",
        "max_response_hours": 24,
        "keywords": ["out of stock", "stockout", "not available", "empty shelf", "bare shelf", "unavailable", "sold out", "item missing"],
    },
    "fresh_produce_spoilage": {
        "department": "Supply Chain",
        "default_severity": "High",
        "actionable": True,
        "is_safety": True,
        "policy": "Perishable Fresh Inbound Quality Control SOP-715",
        "description": "Daily produce culling and cold-chain transport audit for damaged or rotting fruit and vegetables.",
        "max_response_hours": 4,
        "keywords": ["rotten vegetables", "spoiled fruit", "moldy tomato", "decayed", "stale greens", "bruised fruit", "produce bad"],
    },
    "damaged_packaging": {
        "department": "Supply Chain",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "Product Packaging Integrity Standard SOP-720",
        "description": "Immediate removal of dented cans, torn bags, or punctured containers with supplier claims.",
        "max_response_hours": 12,
        "keywords": ["damaged box", "dented can", "torn package", "broken seal", "leaking bottle", "crushed box", "opened package"],
    },
    "expired_stock_on_shelf": {
        "department": "Supply Chain",
        "default_severity": "Critical",
        "actionable": True,
        "is_safety": True,
        "policy": "Zero Expired Goods & Rotation Mandate SOP-730",
        "description": "Immediate removal and destruction of past best-before or expired merchandise from sales floor.",
        "max_response_hours": 2,
        "keywords": ["expired", "past expiry", "expiry date passed", "outdated milk", "expired bread", "best before expired"],
    },
    "warehouse_delay": {
        "department": "Supply Chain",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "Distribution Logistics & Inbound Delivery SOP-740",
        "description": "DC shipment tracking and resolution of delayed cross-dock delivery trucks.",
        "max_response_hours": 24,
        "keywords": ["truck delayed", "delivery late", "shipment delayed", "dc shipment missing", "inbound delayed", "restock truck late"],
    },
    "inaccurate_inventory_count": {
        "department": "Supply Chain",
        "default_severity": "Low",
        "actionable": True,
        "is_safety": False,
        "policy": "Perpetual Inventory & Cycle Count SOP-750",
        "description": "Cycle counting reconciliation between ERP record and physical on-hand inventory.",
        "max_response_hours": 48,
        "keywords": ["system shows stock but empty", "inventory count mismatch", "stock count wrong", "system error stock", "ghost inventory"],
    },

    # --- Merchandising (5 categories) ---
    "pricing": {
        "department": "Merchandising",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "Shelf Price Accuracy Guarantee SOP-801",
        "description": "Physical price tag audit and POS price matching across registers within 24 hours.",
        "max_response_hours": 24,
        "keywords": ["wrong price", "price mismatch", "price tag", "price label", "register price", "charged more than tag", "price difference"],
    },
    "missing_price_tag": {
        "department": "Merchandising",
        "default_severity": "Low",
        "actionable": True,
        "is_safety": False,
        "policy": "Shelf Edge Labeling Compliance SOP-805",
        "description": "Print and replace missing ESL or paper barcode shelf tags within 4 hours.",
        "max_response_hours": 8,
        "keywords": ["no price tag", "missing price", "how much is this", "unlabelled price", "no barcode tag", "price not displayed"],
    },
    "promo_discount_not_applied": {
        "department": "Merchandising",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "Promotional Integrity & Campaign Governance SOP-810",
        "description": "Verification of active circular promos and coupon code integration in POS master database.",
        "max_response_hours": 8,
        "keywords": ["discount missing", "promo not applied", "buy 1 get 1 not working", "sale price not scanned", "coupon rejected", "offer not given"],
    },
    "misleading_offer": {
        "department": "Merchandising",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "Truth in Advertising & Promotional Transparency SOP-815",
        "description": "Immediate correction or removal of ambiguous promo banners or deceptive signage.",
        "max_response_hours": 12,
        "keywords": ["fake discount", "misleading offer", "false advertisement", "hidden terms", "scam discount", "misleading banner"],
    },
    "product_quality_dissatisfaction": {
        "department": "Merchandising",
        "default_severity": "Low",
        "actionable": True,
        "is_safety": False,
        "policy": "Customer Satisfaction & Merchandising Assortment SOP-830",
        "description": "Customer brand preference feedback logged for category review and assortment planning.",
        "max_response_hours": 48,
        "keywords": ["poor quality product", "brand changed taste", "inferior quality", "cheap material", "bad fabric", "disappointed in brand"],
    },

    # --- Digital (5 categories) ---
    "payment_failure": {
        "department": "Digital",
        "default_severity": "High",
        "actionable": True,
        "is_safety": False,
        "policy": "Digital Checkout Continuity Policy SOP-502",
        "description": "POS & payment gateway failover monitoring. IT engineering escalation if checkout disruption exceeds 15 minutes.",
        "max_response_hours": 2,
        "keywords": ["payment failed", "upi failed", "card declined", "payment error", "terminal timed out", "edc machine down", "pos network error", "card swipe failed"],
    },
    "billing": {
        "department": "Digital",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "Customer Billing Integrity SOP-601",
        "description": "POS ledger reconciliation and duplicate card transaction reversals within 24 hours.",
        "max_response_hours": 24,
        "keywords": ["overcharged", "wrong bill", "billing error", "charged twice", "refund", "scanned twice", "duplicate charge", "double charged"],
    },
    "self_checkout_kiosk_down": {
        "department": "Digital",
        "default_severity": "High",
        "actionable": True,
        "is_safety": False,
        "policy": "Self-Service Terminal Uptime Standard SOP-508",
        "description": "Kiosk hardware reboot, scanner diagnostic, and technician dispatch within 2 hours.",
        "max_response_hours": 2,
        "keywords": ["self-checkout", "sco machine stuck", "kiosk frozen", "barcode scanner not reading", "self checkout screen error", "kiosk broken"],
    },
    "app_ordering_bug": {
        "department": "Digital",
        "default_severity": "High",
        "actionable": True,
        "is_safety": False,
        "policy": "Omnichannel Digital App Experience Standard SOP-512",
        "description": "Mobile app click-and-collect order sync diagnostics and hotfix deployment.",
        "max_response_hours": 4,
        "keywords": ["mobile app", "app order", "order not showing", "app crashed", "cart disappeared in app", "cannot place order online", "app login error"],
    },
    "wifi_network_outage": {
        "department": "Digital",
        "default_severity": "Low",
        "actionable": True,
        "is_safety": False,
        "policy": "In-Store Guest Wi-Fi & Connectivity SOP-520",
        "description": "Retail access point telemetry check and ISP connection reset.",
        "max_response_hours": 12,
        "keywords": ["no wifi", "store wifi not working", "guest internet down", "cannot connect to wifi", "weak signal in store"],
    },

    # --- HR (4 categories) ---
    "staff_misconduct": {
        "department": "HR",
        "default_severity": "Critical",
        "actionable": True,
        "is_safety": True,
        "policy": "Workplace Ethics & Customer Respect Policy §7.1",
        "description": "Mandatory confidential investigation by People Operations / HR within 24 hours.",
        "max_response_hours": 24,
        "keywords": ["harassment", "abusive staff", "staff threatened", "discrimination", "insulting", "threatened", "rude employee", "shouted at me", "slur"],
    },
    "staff_unhelpfulness": {
        "department": "HR",
        "default_severity": "Low",
        "actionable": True,
        "is_safety": False,
        "policy": "Customer Care & Employee Service Standards SOP-915",
        "description": "Frontline coaching and store manager feedback review on customer assistance.",
        "max_response_hours": 48,
        "keywords": ["staff unhelpful", "ignored by staff", "no one helped me", "employee was lazy", "staff chatting instead of helping", "poor attitude"],
    },
    "billing_clerk_shortage": {
        "department": "HR",
        "default_severity": "Medium",
        "actionable": True,
        "is_safety": False,
        "policy": "Store Shift Scheduling & Roster Management SOP-920",
        "description": "Shift roster adjustment and on-call cashier activation during rush hours.",
        "max_response_hours": 4,
        "keywords": ["need more cashiers", "short staffed", "cashier missing", "no one at billing counter", "registers closed"],
    },
    "health_safety_violation": {
        "department": "HR",
        "default_severity": "Critical",
        "actionable": True,
        "is_safety": True,
        "policy": "Occupational Health & Safety Regulatory SOP-950",
        "description": "Mandatory incident report on unsafe employee conditions, blocked fire exits, or lack of PPE.",
        "max_response_hours": 2,
        "keywords": ["fire exit blocked", "unsafe workplace", "no safety gear", "electric wire exposed", "ladder unstable", "osha violation", "dangerous work condition"],
    },

    # --- Fallback (1 category) ---
    "other": {
        "department": "Store Operations",
        "default_severity": "Low",
        "actionable": False,
        "is_safety": False,
        "policy": "General Customer Experience Guidelines SOP-901",
        "description": "General operational observation and customer sentiment tracking.",
        "max_response_hours": 48,
        "keywords": ["good store", "nice experience", "music loud", "parking busy", "general question"],
    },
}

def validate_taxonomy():
    """Verify that every issue type maps to an allowed department and has required fields."""
    for issue_type, details in TAXONOMY.items():
        dept = details.get("department")
        if dept not in DEPARTMENTS and dept != "Store Operations":
            raise ValueError(f"Issue type '{issue_type}' has invalid department '{dept}'")
        if "default_severity" not in details:
            raise ValueError(f"Issue type '{issue_type}' missing default_severity")
        if "policy" not in details:
            raise ValueError(f"Issue type '{issue_type}' missing policy")
        if "keywords" not in details or not details["keywords"]:
            raise ValueError(f"Issue type '{issue_type}' missing keywords")
    return True

# Validate on import
validate_taxonomy()

def get_department(issue_type: str) -> str:
    """Return the owner department for an issue type."""
    return TAXONOMY.get(issue_type, TAXONOMY["other"])["department"]

def get_policy_info(issue_type: str) -> Dict[str, Any]:
    """Return policy details for an issue type."""
    return TAXONOMY.get(issue_type, TAXONOMY["other"])

def get_all_issue_types() -> List[str]:
    """Return list of all registered issue types."""
    return list(TAXONOMY.keys())

def get_all_departments() -> List[str]:
    """Return list of supported departments."""
    return sorted(list(DEPARTMENTS))
