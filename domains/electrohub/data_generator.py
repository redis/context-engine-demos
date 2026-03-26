"""Generate sample data for the ElectroHub electronics retail demo."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

import openai
from dotenv import load_dotenv

from backend.app.core.domain_contract import GeneratedDataset

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "output" / "electrohub"


def ts(dt: datetime) -> str:
    return dt.isoformat()


now = datetime.now(timezone.utc)


def fake_embedding(text: str) -> list[float]:
    digest = sha256(text.encode("utf-8")).digest()
    return [digest[i % len(digest)] / 255.0 for i in range(1536)]


def embed(texts: list[str]) -> list[list[float]]:
    if not os.getenv("OPENAI_API_KEY"):
        return [fake_embedding(text) for text in texts]
    client = openai.OpenAI()
    response = client.embeddings.create(
        input=texts,
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    )
    return [item.embedding for item in response.data]


def product(
    product_id: str,
    sku: str,
    name: str,
    brand: str,
    category: str,
    subcategory: str,
    form_factor: str,
    price: float,
    sale_price: float,
    rating: float,
    availability_status: str,
    pickup_eligible: bool,
    shipping_eligible: bool,
    specs_summary: str,
    use_cases: str,
    ai_fit_summary: str,
    search_text: str,
) -> dict[str, object]:
    return {
        "product_id": product_id,
        "sku": sku,
        "name": name,
        "brand": brand,
        "category": category,
        "subcategory": subcategory,
        "form_factor": form_factor,
        "price": price,
        "sale_price": sale_price,
        "rating": rating,
        "availability_status": availability_status,
        "pickup_eligible": pickup_eligible,
        "shipping_eligible": shipping_eligible,
        "specs_summary": specs_summary,
        "use_cases": use_cases,
        "ai_fit_summary": ai_fit_summary,
        "search_text": search_text,
    }


def inventory(
    inventory_id: str,
    store_id: str,
    product_id: str,
    store_name: str,
    product_name: str,
    quantity_available: int,
    pickup_status: str,
    pickup_eta_hours: int,
    aisle_location: str | None,
) -> dict[str, object]:
    return {
        "inventory_id": inventory_id,
        "store_id": store_id,
        "product_id": product_id,
        "store_name": store_name,
        "product_name": product_name,
        "quantity_available": quantity_available,
        "pickup_status": pickup_status,
        "pickup_eta_hours": pickup_eta_hours,
        "aisle_location": aisle_location,
    }


DEMO_CUSTOMER = {
    "customer_id": "CUST_EH_001",
    "name": "Maya Chen",
    "email": "maya.chen@example.com",
    "city": "Denver",
    "state": "CO",
    "member_tier": "plus",
    "home_store_id": "STORE_001",
    "home_store_name": "ElectroHub Cherry Creek",
    "account_created_at": ts(now - timedelta(days=510)),
}

CUSTOMERS = [
    DEMO_CUSTOMER,
    {
        "customer_id": "CUST_EH_002",
        "name": "Ethan Brooks",
        "email": "ethan.brooks@example.com",
        "city": "Boulder",
        "state": "CO",
        "member_tier": "none",
        "home_store_id": "STORE_002",
        "home_store_name": "ElectroHub Flatiron",
        "account_created_at": ts(now - timedelta(days=210)),
    },
    {
        "customer_id": "CUST_EH_003",
        "name": "Sofia Patel",
        "email": "sofia.patel@example.com",
        "city": "Austin",
        "state": "TX",
        "member_tier": "plus",
        "home_store_id": "STORE_003",
        "home_store_name": "ElectroHub Domain Northside",
        "account_created_at": ts(now - timedelta(days=780)),
    },
    {
        "customer_id": "CUST_EH_004",
        "name": "Noah Evans",
        "email": "noah.evans@example.com",
        "city": "Seattle",
        "state": "WA",
        "member_tier": "business",
        "home_store_id": "STORE_004",
        "home_store_name": "ElectroHub Bellevue",
        "account_created_at": ts(now - timedelta(days=1200)),
    },
]

STORES = [
    {
        "store_id": "STORE_001",
        "name": "ElectroHub Cherry Creek",
        "city": "Denver",
        "state": "CO",
        "zip_code": "80206",
        "address": "3000 E 1st Ave, Denver, CO 80206",
        "phone": "+1-303-555-0101",
        "pickup_supported": True,
        "curbside_supported": True,
        "services": "Laptop demo bar, curbside pickup, small-form-factor showroom, trade-in counter",
        "hours_summary": "Mon-Sat 10am-9pm, Sun 11am-7pm",
    },
    {
        "store_id": "STORE_002",
        "name": "ElectroHub Flatiron",
        "city": "Broomfield",
        "state": "CO",
        "zip_code": "80021",
        "address": "1 W Flatiron Crossing Dr, Broomfield, CO 80021",
        "phone": "+1-303-555-0102",
        "pickup_supported": True,
        "curbside_supported": True,
        "services": "Gaming PC room, TV wall, curbside pickup",
        "hours_summary": "Mon-Sat 10am-9pm, Sun 11am-7pm",
    },
    {
        "store_id": "STORE_003",
        "name": "ElectroHub Domain Northside",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78758",
        "address": "11410 Century Oaks Ter, Austin, TX 78758",
        "phone": "+1-512-555-0103",
        "pickup_supported": True,
        "curbside_supported": False,
        "services": "Apple shop, gaming notebooks, smart home install desk",
        "hours_summary": "Mon-Sat 10am-9pm, Sun 11am-7pm",
    },
    {
        "store_id": "STORE_004",
        "name": "ElectroHub Bellevue",
        "city": "Bellevue",
        "state": "WA",
        "zip_code": "98004",
        "address": "600 Bellevue Way NE, Bellevue, WA 98004",
        "phone": "+1-425-555-0104",
        "pickup_supported": True,
        "curbside_supported": True,
        "services": "Creator studio, appliance desk, premium pickup lockers",
        "hours_summary": "Mon-Sat 10am-8pm, Sun 11am-6pm",
    },
]

PRODUCTS = [
    product(
        "PRD_001", "NB14-7840-16-512", "NovaBook 14 Creator", "Asteron", "Computers", "Laptops", "laptop",
        1099.99, 999.99, 4.6, "in_stock", True, True,
        "14-inch Windows laptop, Ryzen 7 7840HS, Radeon 780M graphics, 16GB RAM, 512GB SSD.",
        "Portable work machine, coding, photo edits, older PC games, light creative work.",
        "Balanced portable option with enough memory and integrated graphics for lighter game compatibility questions.",
        "Windows 11 creator laptop with Ryzen 7, 16GB memory, 512GB SSD, integrated Radeon graphics, portable productivity, coding, light gaming, legacy desktop apps.",
    ),
    product(
        "PRD_002", "PTM-14600-4060", "PulseTower Mini RTX 4060", "Forgebox", "Computers", "Desktops", "desktop",
        1299.99, 1199.99, 4.8, "in_stock", True, True,
        "Compact Windows desktop, Intel Core i5-14600F, RTX 4060, 16GB RAM, 1TB SSD.",
        "PC gaming, streaming, desktop productivity, creator work, software compatibility.",
        "Strong all-around desktop when the user needs broad Windows app coverage and more graphics headroom.",
        "Compact Windows gaming desktop with RTX 4060, 16GB RAM, 1TB SSD, strong compatibility for PC software, creators, 1080p and 1440p gaming, game launchers.",
    ),
    product(
        "PRD_003", "BFM-8845-32-1T", "ByteForge Micro Pro", "ByteForge", "Computers", "Mini PCs", "mini_pc",
        849.99, 799.99, 4.5, "in_stock", True, True,
        "Mini Windows desktop, Ryzen 7 8845HS, Radeon 780M graphics, 32GB RAM, 1TB SSD.",
        "Small desk setup, home office, software development, emulation, older PC titles.",
        "Best compact-value machine for buyers who want a small desktop with strong memory and flexible compatibility.",
        "Windows mini desktop with Ryzen 7, 32GB RAM, 1TB SSD, small form factor, software development, light gaming, older PC software, home office, compact battlestation.",
    ),
    product(
        "PRD_004", "VE16-14900-4070", "VoltEdge 16 Gaming Notebook", "VoltEdge", "Computers", "Laptops", "laptop",
        1799.99, 1599.99, 4.7, "in_stock", True, True,
        "16-inch Windows gaming laptop, Intel Core i9, RTX 4070, 32GB RAM, 1TB SSD.",
        "AAA gaming, creator work, streaming, portable workstation, virtual machines.",
        "Premium option for buyers who want a laptop with very broad performance headroom.",
        "High-end Windows gaming notebook with RTX 4070, 32GB RAM, 1TB SSD, advanced gaming, content creation, heavy desktop applications, portability.",
    ),
    product(
        "PRD_005", "AIR15-I5-8-256", "AeroLite 15 Everyday Laptop", "Nimbus", "Computers", "Laptops", "laptop",
        649.99, 649.99, 4.1, "limited_stock", True, True,
        "15-inch Windows laptop, Intel Core i5, Iris Xe graphics, 8GB RAM, 256GB SSD.",
        "School, browsing, office work, light desktop apps, basic media.",
        "Budget-friendly but limited for users who may need more memory or storage.",
        "Budget Windows laptop for web, school, office, everyday tasks, light desktop software, 8GB RAM, 256GB SSD, portable.",
    ),
    product(
        "PRD_006", "QV55-MLED-120", "QuantumView 55 Mini LED TV", "QuantumView", "TV & Home Theater", "TVs", "tv",
        899.99, 799.99, 4.4, "in_stock", True, True,
        "55-inch 4K Mini LED TV, 120Hz panel, Dolby Vision, HDMI 2.1.",
        "Living room gaming, movies, sports, console setup.",
        "Good display product, but not a computer for software-compatibility questions.",
        "55 inch 4K mini LED TV for movies, console gaming, streaming, living room entertainment, HDMI 2.1, 120Hz.",
    ),
    product(
        "PRD_007", "SK100-ANC-BLK", "SoundKey 100 ANC Headphones", "SoundKey", "Audio", "Headphones", "headphones",
        249.99, 199.99, 4.3, "in_stock", True, True,
        "Wireless ANC headphones, 40-hour battery, multipoint Bluetooth.",
        "Travel, flights, office focus, calls.",
        "Useful accessory, but not a machine by itself.",
        "Wireless active noise cancelling headphones with long battery life, travel use, calls, office focus, Bluetooth multipoint.",
    ),
    product(
        "PRD_008", "QD13-TB4-8P", "QuantumDock 13-in-1 Thunderbolt Hub", "Docksmith", "Accessories", "Docks & Hubs", "dock",
        229.99, 199.99, 4.2, "in_stock", True, True,
        "Thunderbolt 4 dock with dual display output, ethernet, card reader, and 100W charging.",
        "Desk setup, laptop docking, monitors, accessories.",
        "Useful companion product after a laptop recommendation.",
        "Thunderbolt 4 dock for laptop desk setups, dual monitors, ethernet, charging, creators, office accessories.",
    ),
    product(
        "PRD_009", "MACMINI-M4-16-512", "Mac mini M4", "Apple", "Computers", "Mini PCs", "mini_pc",
        799.99, 799.99, 4.9, "in_stock", True, True,
        "Compact macOS desktop, Apple M4 chip, 16GB unified memory, 512GB SSD.",
        "macOS apps, coding, quiet desk setup, light creator work, general productivity.",
        "Excellent compact pick when the user's workflow leans toward macOS and a small desktop.",
        "Apple Mac mini desktop with M4 chip, macOS, 16GB unified memory, 512GB SSD, compact desktop, coding, office, creator, small desk setup.",
    ),
    product(
        "PRD_010", "MBA13-M3-16-512", "MacBook Air 13-inch M3", "Apple", "Computers", "Laptops", "laptop",
        1299.99, 1199.99, 4.8, "in_stock", True, True,
        "13-inch macOS laptop, Apple M3 chip, 16GB unified memory, 512GB SSD.",
        "Portable macOS work, travel, school, coding, office tasks.",
        "Best thin-and-light macOS option for mainstream productivity.",
        "Apple MacBook Air with M3 chip, macOS laptop, 16GB memory, 512GB SSD, portable coding, school, travel, office, creator basics.",
    ),
    product(
        "PRD_011", "MBP14-M4P-24-1T", "MacBook Pro 14-inch M4 Pro", "Apple", "Computers", "Laptops", "laptop",
        2199.99, 2099.99, 4.9, "in_stock", True, True,
        "14-inch macOS laptop, M4 Pro chip, 24GB unified memory, 1TB SSD.",
        "Pro apps, compiling, media production, travel workstation, heavier development.",
        "Premium macOS workstation for demanding laptop buyers.",
        "Apple MacBook Pro 14 with M4 Pro, 24GB memory, 1TB SSD, macOS workstation, software development, video, design, portable pro machine.",
    ),
    product(
        "PRD_012", "SL13-XE-16-512", "Surface Laptop 13 Copilot+", "Microsoft", "Computers", "Laptops", "laptop",
        1099.99, 1049.99, 4.4, "in_stock", True, True,
        "13-inch Windows laptop, Snapdragon X Elite, 16GB RAM, 512GB SSD.",
        "Battery life, office work, travel, web apps, light local AI features.",
        "Portable Windows option when battery life matters more than gaming.",
        "Copilot Plus Windows laptop with Snapdragon X Elite, 16GB RAM, 512GB SSD, portable office, productivity, travel, battery life.",
    ),
    product(
        "PRD_013", "LT5-14700-4070S", "Legion Tower 5 RTX 4070 Super", "Lenovo", "Computers", "Desktops", "desktop",
        1799.99, 1699.99, 4.7, "in_stock", True, True,
        "Windows gaming tower, Intel Core i7-14700F, RTX 4070 Super, 32GB RAM, 1TB SSD.",
        "High-end PC gaming, streaming, heavy Windows software, creator work.",
        "Best tower recommendation when the user wants maximum Windows performance.",
        "Windows gaming tower with RTX 4070 Super, 32GB RAM, 1TB SSD, high performance PC, streaming, creator apps, game libraries.",
    ),
    product(
        "PRD_014", "STUDIO-14700-4060TI", "StudioBox Creator Desktop", "StudioBox", "Computers", "Desktops", "desktop",
        1599.99, 1499.99, 4.5, "in_stock", True, True,
        "Windows creator desktop, Intel Core i7-14700, RTX 4060 Ti, 32GB RAM, 2TB SSD.",
        "Photo editing, video editing, 3D previews, software development, desktop multitasking.",
        "Strong creator desktop when the user values memory and storage more than a gaming-first build.",
        "Creator desktop with Intel i7, RTX 4060 Ti, 32GB RAM, 2TB SSD, design tools, editing, coding, workstation, desktop productivity.",
    ),
    product(
        "PRD_015", "CB14-I3-8-128", "ChromeLite 14 Chromebook Plus", "Acera", "Computers", "Chromebooks", "laptop",
        429.99, 379.99, 4.0, "in_stock", True, True,
        "14-inch Chromebook, Intel Core i3, 8GB RAM, 128GB storage.",
        "School, browsing, Google Workspace, lightweight tasks.",
        "Useful only when the workload is browser-first.",
        "Chromebook Plus laptop for browser tasks, school, Google apps, streaming, lightweight productivity, 8GB RAM, portable.",
    ),
    product(
        "PRD_016", "FLEX14-U7-16-512", "FlexBook 14 2-in-1", "HP", "Computers", "2-in-1 Laptops", "laptop",
        999.99, 899.99, 4.2, "in_stock", True, True,
        "14-inch Windows 2-in-1, Core Ultra 7, 16GB RAM, 512GB SSD, pen support.",
        "Hybrid work, note taking, office, light creative apps.",
        "Good convertible option when form factor matters more than gaming power.",
        "Windows 2 in 1 laptop with pen support, Core Ultra 7, 16GB RAM, 512GB SSD, hybrid work, notes, office, touch.",
    ),
    product(
        "PRD_017", "UV27-4K-USB-C", "UltraView 27 4K Monitor", "ViewPoint", "Computers", "Monitors", "monitor",
        399.99, 349.99, 4.6, "in_stock", True, True,
        "27-inch 4K monitor, USB-C input, 60W charging, factory-calibrated color.",
        "Desk setups, office, creators, laptop docking.",
        "Useful add-on for mini desktops and laptops.",
        "27 inch 4K monitor with USB C, desk setup, creator, office, laptop docking, external display.",
    ),
    product(
        "PRD_018", "SW34-UW-144", "SwiftPanel 34 Ultrawide", "ViewPoint", "Computers", "Monitors", "monitor",
        599.99, 549.99, 4.5, "in_stock", True, True,
        "34-inch 3440x1440 ultrawide monitor, 144Hz refresh rate.",
        "Multitasking, immersive gaming, editing timelines, productivity.",
        "Good upsell monitor for desktop buyers.",
        "34 inch ultrawide monitor, 144Hz, multitasking, immersive gaming, productivity, creator timeline workspace.",
    ),
    product(
        "PRD_019", "GV27-240-IPS", "GameView 27 240Hz Monitor", "ViewPoint", "Computers", "Monitors", "monitor",
        329.99, 299.99, 4.4, "in_stock", True, True,
        "27-inch 1080p IPS gaming monitor, 240Hz refresh rate, 1ms response.",
        "Esports, PC gaming, secondary display.",
        "Gaming-focused monitor, not a primary compute device.",
        "27 inch gaming monitor, 240Hz, esports, PC gaming, desktop setup, fast response.",
    ),
    product(
        "PRD_020", "PT12-OLED-256", "PixelTab 12 Pro", "Google", "Computers", "Tablets", "tablet",
        799.99, 749.99, 4.3, "in_stock", True, True,
        "12-inch Android tablet, OLED display, 256GB storage, pen support.",
        "Tablet productivity, sketching, media, travel.",
        "Not a substitute for desktop software questions unless the workflow is tablet-friendly.",
        "Android tablet with OLED screen, pen support, travel, media, sketching, light productivity.",
    ),
    product(
        "PRD_021", "GST10-PLUS-256", "Galaxy Tab S10+", "Samsung", "Computers", "Tablets", "tablet",
        999.99, 899.99, 4.5, "in_stock", True, True,
        "12.4-inch Android tablet, AMOLED display, 256GB storage, keyboard support.",
        "Tablet productivity, note taking, media, DeX desk setup.",
        "Useful for mobile workflows, not broad desktop compatibility.",
        "Samsung Android tablet with AMOLED display, keyboard support, DeX productivity, note taking, travel, media.",
    ),
    product(
        "PRD_022", "IP16-128-BLK", "iPhone 16", "Apple", "Phones", "Smartphones", "phone",
        829.99, 799.99, 4.7, "in_stock", True, True,
        "128GB iPhone with A18 chip and USB-C.",
        "Mobile apps, photos, messaging, travel.",
        "Important category coverage, but not a desktop-class product recommendation.",
        "Apple smartphone with A18 chip, mobile apps, photos, messaging, travel, iOS.",
    ),
    product(
        "PRD_023", "GS25-256-NVY", "Galaxy S25", "Samsung", "Phones", "Smartphones", "phone",
        899.99, 849.99, 4.6, "in_stock", True, True,
        "256GB Android phone with Snapdragon flagship chip.",
        "Mobile apps, camera, messaging, travel, Android ecosystem.",
        "Strong phone option, but not relevant when the user needs a machine for desktop software.",
        "Samsung Android smartphone with flagship chip, mobile apps, camera, travel, Android ecosystem, productivity.",
    ),
    product(
        "PRD_024", "MW-BE11000-3PK", "MeshWave BE11000 Router 3-Pack", "NetLink", "Networking", "Routers", "router",
        699.99, 649.99, 4.4, "in_stock", True, True,
        "Tri-band Wi-Fi 7 mesh system with 10GbE uplink.",
        "Large homes, gaming setups, streaming, smart home.",
        "Broadens the catalog, but not a compute-device answer.",
        "Wi Fi 7 mesh router system, large home networking, gaming setup, streaming, smart home coverage.",
    ),
    product(
        "PRD_025", "HCAM-BAT-2K", "HomeCam Battery 2K", "Nestor", "Smart Home", "Cameras", "camera",
        179.99, 149.99, 4.1, "in_stock", True, True,
        "Battery-powered 2K smart security camera with cloud recording support.",
        "Home monitoring, porch coverage, smart alerts.",
        "Useful smart-home product that should not pollute machine recommendations.",
        "Battery smart home camera, home monitoring, porch, cloud recording, alerts, smart home.",
    ),
    product(
        "PRD_026", "VDB-4MP-WIFI", "VisionBell Video Doorbell", "Nestor", "Smart Home", "Doorbells", "doorbell",
        229.99, 199.99, 4.0, "in_stock", True, True,
        "4MP smart video doorbell with local and cloud clip storage.",
        "Front door monitoring, package alerts, smart-home setup.",
        "Smart-home category breadth, not a machine recommendation.",
        "Smart video doorbell, package alerts, front door monitoring, smart home, app notifications.",
    ),
    product(
        "PRD_027", "PRTR-COLOR-WF", "ProColor Photo Printer", "Canonix", "Office", "Printers", "printer",
        299.99, 269.99, 4.2, "in_stock", True, True,
        "Wireless all-in-one photo printer with scanner and duplex support.",
        "Home office, photo prints, family documents.",
        "Another broad-catalog item that should not confuse compute recommendations.",
        "Wireless photo printer, home office, scanning, duplex, family documents, creative prints.",
    ),
    product(
        "PRD_028", "WBC-1080P-WHT", "WorkBeam 1080p Webcam", "LogiTech", "Accessories", "Webcams", "webcam",
        89.99, 69.99, 4.3, "in_stock", True, True,
        "1080p webcam with dual microphones and privacy shutter.",
        "Video calls, streaming, office setup.",
        "Useful accessory, not a primary machine.",
        "1080p webcam for video calls, work from home, streaming, office desk setup, microphones.",
    ),
]

PRODUCT_NAME_BY_ID = {row["product_id"]: row["name"] for row in PRODUCTS}
STORE_NAME_BY_ID = {row["store_id"]: row["name"] for row in STORES}


STORE_INVENTORY = [
    inventory("INV_001", "STORE_001", "PRD_001", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_001"], 2, "pickup_today", 2, "Laptop bar L2"),
    inventory("INV_002", "STORE_001", "PRD_002", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_002"], 4, "pickup_today", 1, "Gaming wall G4"),
    inventory("INV_003", "STORE_001", "PRD_003", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_003"], 6, "pickup_today", 1, "Compact PC table C1"),
    inventory("INV_004", "STORE_001", "PRD_004", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_004"], 1, "pickup_tomorrow", 18, "Premium gaming L5"),
    inventory("INV_005", "STORE_001", "PRD_005", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_005"], 3, "pickup_today", 2, "Laptop bar L1"),
    inventory("INV_006", "STORE_001", "PRD_008", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_008"], 8, "pickup_today", 1, "Accessories A7"),
    inventory("INV_007", "STORE_001", "PRD_009", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_009"], 5, "pickup_today", 1, "Apple shop M1"),
    inventory("INV_008", "STORE_001", "PRD_010", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_010"], 4, "pickup_today", 2, "Apple shop L3"),
    inventory("INV_009", "STORE_001", "PRD_011", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_011"], 2, "pickup_today", 2, "Apple shop L4"),
    inventory("INV_010", "STORE_001", "PRD_012", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_012"], 3, "pickup_today", 2, "Laptop bar L4"),
    inventory("INV_011", "STORE_001", "PRD_013", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_013"], 2, "pickup_today", 3, "Gaming tower G8"),
    inventory("INV_012", "STORE_001", "PRD_014", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_014"], 1, "pickup_tomorrow", 20, "Creator desktop C5"),
    inventory("INV_013", "STORE_001", "PRD_015", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_015"], 5, "pickup_today", 2, "Education L6"),
    inventory("INV_014", "STORE_001", "PRD_016", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_016"], 3, "pickup_today", 2, "2-in-1 table T2"),
    inventory("INV_015", "STORE_001", "PRD_017", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_017"], 6, "pickup_today", 1, "Monitor wall D3"),
    inventory("INV_016", "STORE_001", "PRD_018", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_018"], 2, "pickup_today", 2, "Monitor wall D4"),
    inventory("INV_017", "STORE_001", "PRD_019", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_019"], 4, "pickup_today", 1, "Gaming display D6"),
    inventory("INV_018", "STORE_001", "PRD_024", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_024"], 4, "pickup_today", 2, "Networking N2"),
    inventory("INV_019", "STORE_001", "PRD_027", STORE_NAME_BY_ID["STORE_001"], PRODUCT_NAME_BY_ID["PRD_027"], 3, "pickup_today", 2, "Office O3"),
    inventory("INV_020", "STORE_002", "PRD_002", STORE_NAME_BY_ID["STORE_002"], PRODUCT_NAME_BY_ID["PRD_002"], 2, "pickup_today", 2, "Gaming wall G3"),
    inventory("INV_021", "STORE_002", "PRD_003", STORE_NAME_BY_ID["STORE_002"], PRODUCT_NAME_BY_ID["PRD_003"], 0, "sold_out", 72, "Compact PC table C1"),
    inventory("INV_022", "STORE_002", "PRD_004", STORE_NAME_BY_ID["STORE_002"], PRODUCT_NAME_BY_ID["PRD_004"], 2, "pickup_today", 3, "Gaming laptops L5"),
    inventory("INV_023", "STORE_002", "PRD_013", STORE_NAME_BY_ID["STORE_002"], PRODUCT_NAME_BY_ID["PRD_013"], 3, "pickup_today", 3, "Gaming tower G7"),
    inventory("INV_024", "STORE_002", "PRD_018", STORE_NAME_BY_ID["STORE_002"], PRODUCT_NAME_BY_ID["PRD_018"], 1, "pickup_today", 2, "Monitor wall D5"),
    inventory("INV_025", "STORE_002", "PRD_024", STORE_NAME_BY_ID["STORE_002"], PRODUCT_NAME_BY_ID["PRD_024"], 2, "pickup_today", 4, "Networking N2"),
    inventory("INV_026", "STORE_003", "PRD_004", STORE_NAME_BY_ID["STORE_003"], PRODUCT_NAME_BY_ID["PRD_004"], 3, "pickup_today", 3, "Premium gaming L3"),
    inventory("INV_027", "STORE_003", "PRD_009", STORE_NAME_BY_ID["STORE_003"], PRODUCT_NAME_BY_ID["PRD_009"], 2, "pickup_today", 2, "Apple shop M1"),
    inventory("INV_028", "STORE_003", "PRD_010", STORE_NAME_BY_ID["STORE_003"], PRODUCT_NAME_BY_ID["PRD_010"], 4, "pickup_today", 2, "Apple shop L2"),
    inventory("INV_029", "STORE_003", "PRD_011", STORE_NAME_BY_ID["STORE_003"], PRODUCT_NAME_BY_ID["PRD_011"], 1, "pickup_today", 3, "Apple shop L3"),
    inventory("INV_030", "STORE_003", "PRD_016", STORE_NAME_BY_ID["STORE_003"], PRODUCT_NAME_BY_ID["PRD_016"], 2, "pickup_today", 4, "2-in-1 table T1"),
    inventory("INV_031", "STORE_004", "PRD_006", STORE_NAME_BY_ID["STORE_004"], PRODUCT_NAME_BY_ID["PRD_006"], 5, "pickup_today", 4, "TV wall T2"),
    inventory("INV_032", "STORE_004", "PRD_011", STORE_NAME_BY_ID["STORE_004"], PRODUCT_NAME_BY_ID["PRD_011"], 2, "pickup_today", 2, "Apple shop L1"),
    inventory("INV_033", "STORE_004", "PRD_014", STORE_NAME_BY_ID["STORE_004"], PRODUCT_NAME_BY_ID["PRD_014"], 2, "pickup_today", 4, "Creator desktop C4"),
    inventory("INV_034", "STORE_004", "PRD_017", STORE_NAME_BY_ID["STORE_004"], PRODUCT_NAME_BY_ID["PRD_017"], 5, "pickup_today", 2, "Monitor wall D2"),
    inventory("INV_035", "STORE_004", "PRD_025", STORE_NAME_BY_ID["STORE_004"], PRODUCT_NAME_BY_ID["PRD_025"], 6, "pickup_today", 1, "Smart home S1"),
]

current_order_date = now - timedelta(days=5, hours=3)
current_promised_date = now - timedelta(days=1, hours=4)

ORDERS = [
    {
        "order_id": "ORD_EH_1001",
        "customer_id": DEMO_CUSTOMER["customer_id"],
        "status": "shipped_delayed",
        "fulfillment_type": "shipping",
        "store_id": None,
        "store_name": None,
        "order_total": 1829.98,
        "order_date": ts(current_order_date),
        "promised_date": ts(current_promised_date),
        "delivered_at": None,
        "tracking_number": "1Z999AA10123456784",
        "shipping_address": "1717 Wewatta St, Denver, CO 80202",
        "summary": "VoltEdge 16 Gaming Notebook and QuantumDock Thunderbolt hub",
    },
    {
        "order_id": "ORD_EH_1002",
        "customer_id": DEMO_CUSTOMER["customer_id"],
        "status": "completed",
        "fulfillment_type": "pickup",
        "store_id": "STORE_001",
        "store_name": "ElectroHub Cherry Creek",
        "order_total": 999.99,
        "order_date": ts(now - timedelta(days=28)),
        "promised_date": ts(now - timedelta(days=27, hours=20)),
        "delivered_at": ts(now - timedelta(days=27, hours=22)),
        "tracking_number": None,
        "shipping_address": None,
        "summary": "NovaBook 14 Creator",
    },
    {
        "order_id": "ORD_EH_1003",
        "customer_id": DEMO_CUSTOMER["customer_id"],
        "status": "completed",
        "fulfillment_type": "shipping",
        "store_id": None,
        "store_name": None,
        "order_total": 249.99,
        "order_date": ts(now - timedelta(days=71)),
        "promised_date": ts(now - timedelta(days=67)),
        "delivered_at": ts(now - timedelta(days=67, hours=2)),
        "tracking_number": "9400111899223847291000",
        "shipping_address": "1717 Wewatta St, Denver, CO 80202",
        "summary": "SoundKey 100 ANC Headphones",
    },
    {
        "order_id": "ORD_EH_2001",
        "customer_id": "CUST_EH_002",
        "status": "ready_for_pickup",
        "fulfillment_type": "pickup",
        "store_id": "STORE_002",
        "store_name": "ElectroHub Flatiron",
        "order_total": 1199.99,
        "order_date": ts(now - timedelta(hours=9)),
        "promised_date": ts(now + timedelta(hours=2)),
        "delivered_at": None,
        "tracking_number": None,
        "shipping_address": None,
        "summary": "PulseTower Mini RTX 4060",
    },
]

ORDER_ITEMS = [
    {
        "order_item_id": "ITEM_EH_001",
        "order_id": "ORD_EH_1001",
        "product_id": "PRD_004",
        "product_name": PRODUCT_NAME_BY_ID["PRD_004"],
        "quantity": 1,
        "unit_price": 1599.99,
        "fulfillment_status": "in_transit",
    },
    {
        "order_item_id": "ITEM_EH_002",
        "order_id": "ORD_EH_1001",
        "product_id": "PRD_008",
        "product_name": PRODUCT_NAME_BY_ID["PRD_008"],
        "quantity": 1,
        "unit_price": 229.99,
        "fulfillment_status": "in_transit",
    },
    {
        "order_item_id": "ITEM_EH_003",
        "order_id": "ORD_EH_1002",
        "product_id": "PRD_001",
        "product_name": PRODUCT_NAME_BY_ID["PRD_001"],
        "quantity": 1,
        "unit_price": 999.99,
        "fulfillment_status": "picked_up",
    },
    {
        "order_item_id": "ITEM_EH_004",
        "order_id": "ORD_EH_1003",
        "product_id": "PRD_007",
        "product_name": PRODUCT_NAME_BY_ID["PRD_007"],
        "quantity": 1,
        "unit_price": 249.99,
        "fulfillment_status": "delivered",
    },
    {
        "order_item_id": "ITEM_EH_005",
        "order_id": "ORD_EH_2001",
        "product_id": "PRD_002",
        "product_name": PRODUCT_NAME_BY_ID["PRD_002"],
        "quantity": 1,
        "unit_price": 1199.99,
        "fulfillment_status": "ready_for_pickup",
    },
]

SHIPMENTS = [
    {
        "shipment_id": "SHIP_EH_001",
        "order_id": "ORD_EH_1001",
        "carrier": "UPS",
        "tracking_number": "1Z999AA10123456784",
        "shipment_status": "delay_in_transit",
        "shipped_at": ts(now - timedelta(days=4, hours=18)),
        "estimated_delivery": ts(now + timedelta(days=1, hours=6)),
        "last_scan_at": ts(now - timedelta(hours=4)),
        "current_location": "Salt Lake City, UT sort facility",
        "delay_reason": "Weather delay after a missed outbound linehaul departure.",
    },
    {
        "shipment_id": "SHIP_EH_002",
        "order_id": "ORD_EH_1003",
        "carrier": "USPS",
        "tracking_number": "9400111899223847291000",
        "shipment_status": "delivered",
        "shipped_at": ts(now - timedelta(days=69)),
        "estimated_delivery": ts(now - timedelta(days=67)),
        "last_scan_at": ts(now - timedelta(days=67, hours=2)),
        "current_location": "Denver, CO",
        "delay_reason": None,
    },
]

SHIPMENT_EVENTS = [
    {
        "event_id": "SEVT_EH_001",
        "shipment_id": "SHIP_EH_001",
        "order_id": "ORD_EH_1001",
        "event_type": "label_created",
        "timestamp": ts(now - timedelta(days=5)),
        "location": "Louisville, KY",
        "description": "Shipping label created for order ORD_EH_1001.",
    },
    {
        "event_id": "SEVT_EH_002",
        "shipment_id": "SHIP_EH_001",
        "order_id": "ORD_EH_1001",
        "event_type": "picked_up",
        "timestamp": ts(now - timedelta(days=4, hours=18)),
        "location": "Louisville, KY",
        "description": "Carrier picked up the package from the ElectroHub distribution center.",
    },
    {
        "event_id": "SEVT_EH_003",
        "shipment_id": "SHIP_EH_001",
        "order_id": "ORD_EH_1001",
        "event_type": "arrival_scan",
        "timestamp": ts(now - timedelta(days=2, hours=20)),
        "location": "Salt Lake City, UT",
        "description": "Package arrived at the Salt Lake City sorting facility.",
    },
    {
        "event_id": "SEVT_EH_004",
        "shipment_id": "SHIP_EH_001",
        "order_id": "ORD_EH_1001",
        "event_type": "delay",
        "timestamp": ts(now - timedelta(hours=4)),
        "location": "Salt Lake City, UT",
        "description": "Weather delay recorded after the package missed its outbound trailer departure.",
    },
    {
        "event_id": "SEVT_EH_005",
        "shipment_id": "SHIP_EH_002",
        "order_id": "ORD_EH_1003",
        "event_type": "delivered",
        "timestamp": ts(now - timedelta(days=67, hours=2)),
        "location": "Denver, CO",
        "description": "Package delivered at front desk.",
    },
]

SUPPORT_CASES = [
    {
        "case_id": "CASE_EH_001",
        "customer_id": DEMO_CUSTOMER["customer_id"],
        "order_id": "ORD_EH_1001",
        "category": "shipment_delay",
        "status": "open",
        "opened_at": ts(now - timedelta(hours=3)),
        "summary": "Customer reports shipment not received by original promise date.",
        "resolution": None,
    },
    {
        "case_id": "CASE_EH_002",
        "customer_id": DEMO_CUSTOMER["customer_id"],
        "order_id": "ORD_EH_1002",
        "category": "pickup_question",
        "status": "resolved",
        "opened_at": ts(now - timedelta(days=28, hours=4)),
        "summary": "Asked whether curbside pickup was available for a laptop order.",
        "resolution": "Confirmed curbside pickup at ElectroHub Cherry Creek.",
    },
]

GUIDE_TEXT = [
    {
        "guide_id": "GUIDE_EH_001",
        "title": "How to Recommend Hardware for Unknown Apps or Games",
        "category": "buying_guide",
        "content": (
            "When a user names software that does not exist in the catalog, first infer the likely operating system, "
            "device class, portability needs, and performance tier. Then search for products by those generic traits rather "
            "than the literal software title. If the workload sounds like lightweight gaming or older desktop software, a "
            "mini desktop or mainstream Windows laptop is often enough."
        ),
    },
    {
        "guide_id": "GUIDE_EH_002",
        "title": "Mini Desktop vs Laptop vs Gaming Tower",
        "category": "buying_guide",
        "content": (
            "Mini desktops are ideal when the buyer wants a small footprint and already has a monitor. Laptops are best when "
            "portability matters. Gaming towers are best when the buyer needs maximum Windows performance, easier upgrades, or "
            "strong graphics headroom."
        ),
    },
    {
        "guide_id": "GUIDE_EH_003",
        "title": "Using Live Inventory for Same-Day Pickup",
        "category": "pickup_policy",
        "content": (
            "Product pages may show a general availability status, but store inventory is the source of truth for same-day pickup. "
            "Always verify quantity available and pickup ETA at the selected store before promising pickup today."
        ),
    },
    {
        "guide_id": "GUIDE_EH_004",
        "title": "Shipment Tracking and Delay Reviews",
        "category": "shipping_policy",
        "content": (
            "When a shipment is delayed, the latest carrier scan and revised ETA are the best current signal. Once the original "
            "promise date has passed, support can review the order while the shipment remains in transit."
        ),
    },
    {
        "guide_id": "GUIDE_EH_005",
        "title": "What 8GB, 16GB, and 32GB of Memory Usually Mean",
        "category": "buying_guide",
        "content": (
            "8GB is usually fine for web, office, and light school workloads. 16GB is the safer baseline for modern laptops and "
            "mixed productivity. 32GB is best when the buyer may multitask heavily, run creative apps, use virtual machines, or "
            "wants more headroom."
        ),
    },
]


def write_jsonl(output_dir: Path, filename: str, rows: list[dict[str, object]]) -> None:
    path = output_dir / filename
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  {path.name}: {len(rows)} records")


def update_env(key: str, value: str) -> None:
    env_path = ROOT / ".env"
    safe_value = f'"{value}"' if " " in value else value
    if not env_path.exists():
        env_path.write_text(f"{key}={safe_value}\n")
        return
    lines = env_path.read_text().splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[index] = f"{key}={safe_value}"
            break
    else:
        lines.append(f"{key}={safe_value}")
    env_path.write_text("\n".join(lines) + "\n")


def generate_demo_data(
    *,
    output_dir: Path | None = None,
    seed: int | None = None,
    update_env_file: bool = True,
) -> GeneratedDataset:
    del seed
    resolved_output_dir = output_dir or OUTPUT_DIR
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating embeddings for guides...")
    embeddings = embed([guide["content"] for guide in GUIDE_TEXT])
    guides = [{**guide, "content_embedding": embedding} for guide, embedding in zip(GUIDE_TEXT, embeddings)]

    print("Writing JSONL files:")
    write_jsonl(resolved_output_dir, "customers.jsonl", CUSTOMERS)
    write_jsonl(resolved_output_dir, "stores.jsonl", STORES)
    write_jsonl(resolved_output_dir, "products.jsonl", PRODUCTS)
    write_jsonl(resolved_output_dir, "store_inventory.jsonl", STORE_INVENTORY)
    write_jsonl(resolved_output_dir, "orders.jsonl", ORDERS)
    write_jsonl(resolved_output_dir, "order_items.jsonl", ORDER_ITEMS)
    write_jsonl(resolved_output_dir, "shipments.jsonl", SHIPMENTS)
    write_jsonl(resolved_output_dir, "shipment_events.jsonl", SHIPMENT_EVENTS)
    write_jsonl(resolved_output_dir, "support_cases.jsonl", SUPPORT_CASES)
    write_jsonl(resolved_output_dir, "guides.jsonl", guides)

    env_updates = {
        "DEMO_USER_ID": DEMO_CUSTOMER["customer_id"],
        "DEMO_USER_NAME": DEMO_CUSTOMER["name"],
        "DEMO_USER_EMAIL": DEMO_CUSTOMER["email"],
        "DEMO_USER_MEMBER_TIER": DEMO_CUSTOMER["member_tier"],
        "DEMO_USER_CITY": DEMO_CUSTOMER["city"],
        "DEMO_USER_STATE": DEMO_CUSTOMER["state"],
        "DEMO_USER_HOME_STORE_ID": DEMO_CUSTOMER["home_store_id"],
        "DEMO_USER_HOME_STORE_NAME": DEMO_CUSTOMER["home_store_name"],
    }
    if update_env_file:
        for key, value in env_updates.items():
            update_env(key, value)

    print(f"\nDemo user: {DEMO_CUSTOMER['name']} ({DEMO_CUSTOMER['customer_id']})")
    print(f"Home store: {DEMO_CUSTOMER['home_store_name']} ({DEMO_CUSTOMER['home_store_id']})")
    print("Done.")

    return GeneratedDataset(
        output_dir=str(resolved_output_dir),
        env_updates=env_updates,
        summary={
            "customers": len(CUSTOMERS),
            "stores": len(STORES),
            "products": len(PRODUCTS),
            "store_inventory": len(STORE_INVENTORY),
            "orders": len(ORDERS),
            "order_items": len(ORDER_ITEMS),
            "shipments": len(SHIPMENTS),
            "shipment_events": len(SHIPMENT_EVENTS),
            "support_cases": len(SUPPORT_CASES),
            "guides": len(GUIDE_TEXT),
        },
    )
