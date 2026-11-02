import json
import random
from datetime import datetime, timedelta
from .connection import get_connection
from utils.auth import hash_password
from utils.image_catalog import get_deterministic_product_image, get_product_gallery_images

def generate_catalog():
    """Generates 750+ unique, realistic e-commerce products with INR prices, brands, specs, and verified images."""
    products = []
    sku_counter = 1000

    # Verified 500+ product image catalog dynamically resolved per category and subcategory
    category_definitions = [
        {
            "category": "Electronics",
            "subcategories": [
                {
                    "name": "Wireless Headphones",
                    "brands": ["Sony", "JBL", "boAt", "Sennheiser", "Bose", "Audio-Technica"],
                    "models": [
                        ("WH-1000XM5 Noise Cancelling Headphones", 29990, 34990, "Industry leading noise cancellation with Auto NC Optimizer, 30hr battery life, crystal clear hands-free calls."),
                        ("Tune 770NC Wireless Over-Ear NC", 5999, 7999, "Adaptive Noise Cancelling with Smart Ambient, up to 70H battery life and speed charge."),
                        ("Rockerz 550 Over-Ear Wireless", 1799, 4999, "50mm dynamic drivers, physical noise isolation, plush padded ear cushions."),
                        ("QuietComfort 45 Bluetooth Headphones", 24900, 29900, "World-class noise cancelling, high-fidelity audio, lightweight comfort and TriPort acoustic architecture."),
                        ("HD 450BT Wireless Noise Cancelling", 9990, 14990, "Great wireless sound with deep dynamic bass and high quality codec support including AAC and AptX."),
                        ("ATH-M50xBT2 Professional Monitor", 17500, 21000, "Proprietary 45 mm large-aperture drivers and dedicated amplifier deliver exceptional clarity."),
                        ("Bassheads 900 Wired Headphone", 799, 2490, "Super Extra Bass, PVC cable, featherlight compact foldable design."),
                        ("Live 660NC Wireless Over-Ear", 8999, 14999, "Signature Sound with 40mm drivers and active noise cancelling with Ambient Aware.")
                    ]
                },
                {
                    "name": "Earbuds & TWS",
                    "brands": ["Apple", "Samsung", "Sony", "OnePlus", "boAt", "Realme"],
                    "models": [
                        ("AirPods Pro (2nd Gen) with MagSafe Case (USB-C)", 20990, 24900, "Up to 2x more Active Noise Cancellation, Adaptive Audio, and Transparency mode."),
                        ("Galaxy Buds2 Pro Hi-Fi Sound", 12999, 19999, "24-bit Hi-Fi audio quality with 3 high SNR microphones eliminating ambient noise."),
                        ("WF-1000XM5 Truly Wireless Earbuds", 21990, 26990, "Specially designed Dynamic Driver X for wide frequency reproduction and deep bass."),
                        ("Nord Buds 2 with Active Noise Cancellation", 2499, 3299, "Up to 25dB Active Noise Cancellation, 12.4mm titanized dynamic drivers."),
                        ("Airdopes 141 True Wireless Earbuds", 1199, 4490, "42 hours total playback, ENx environmental noise cancellation technology, IPX4."),
                        ("Buds Air 5 Pro Dual Driver ANC", 4499, 6999, "50dB Active Noise Cancellation, 4000Hz ultra-wideband noise reduction, Hi-Res audio.")
                    ]
                },
                {
                    "name": "Smartwatches",
                    "brands": ["Apple", "Samsung", "Noise", "Fire-Boltt", "Amazfit", "Garmin"],
                    "models": [
                        ("Watch Series 9 GPS 45mm", 41990, 44900, "S9 SiP chip, double tap gesture, brightest display with edge-to-edge design."),
                        ("Galaxy Watch6 Classic Bluetooth 47mm", 32999, 40999, "Rotating bezel, advanced sleep coaching, ECG monitoring, Sapphire crystal glass."),
                        ("ColorFit Pro 4 Alpha AMOLED Display", 2999, 7999, "1.78 inch AMOLED display, gesture control, Tru Sync calling, 100 sports modes."),
                        ("Ninja Calling Pro Plus Smartwatch", 1499, 9999, "1.83 inch HD display, Bluetooth calling, AI voice assistant, 120 sports modes."),
                        ("GTR 4 Smart Fitness Watch", 16999, 23999, "Dual-band circular polarized GPS antenna, ultra-long 14-day battery life, BioTracker 4.0."),
                        ("Forerunner 265 Running GPS Smartwatch", 46990, 50490, "Colorful AMOLED touch display, training readiness metrics, multi-band GNSS tracking.")
                    ]
                },
                {
                    "name": "Bluetooth Speakers",
                    "brands": ["JBL", "Sony", "boAt", "Marshall", "Bose"],
                    "models": [
                        ("Flip 6 Portable Waterproof Bluetooth Speaker", 9999, 13999, "2-way speaker system engineered to deliver loud, crystal clear, powerful sound."),
                        ("SRS-XB100 Wireless Portable Speaker", 3990, 4990, "Sound Diffusion Processor, extra bass, IP67 waterproof and dustproof with strap."),
                        ("Stone 352 10W Bluetooth Speaker", 1499, 3490, "10W RMS stereo sound, IPX7 water resistance, 12 hours playtime, Type-C charging."),
                        ("Emberton II Portable Bluetooth Speaker", 14999, 19999, "30+ hours of portable playtime, True Stereophonic multi-directional sound."),
                        ("SoundLink Flex Bluetooth Portable Speaker", 12900, 15900, "PositionIQ technology detects orientation and optimizes audio output automatically.")
                    ]
                }
            ]
        },
        {
            "category": "Mobiles",
            "subcategories": [
                {
                    "name": "Smartphones",
                    "brands": ["Apple", "Samsung", "OnePlus", "Google", "Xiaomi", "Realme", "Motorola", "Nothing"],
                    "models": [
                        ("iPhone 15 (128 GB) - Blue", 65999, 79900, "Dynamic Island, 48MP main camera with 2x Telephoto, A16 Bionic chip, USB-C."),
                        ("iPhone 15 Pro Max (256 GB) - Natural Titanium", 148900, 159900, "A17 Pro chip, aerospace titanium design, 5x Optical Telephoto zoom camera."),
                        ("Galaxy S24 Ultra 5G (12GB RAM, 256GB)", 119999, 134999, "Galaxy AI capabilities, 200MP camera, Snapdragon 8 Gen 3 for Galaxy, S-Pen included."),
                        ("Galaxy S23 FE 5G (8GB RAM, 128GB)", 39999, 59999, "Pro-grade nightography camera, Corning Gorilla Glass 5, IP68 water resistance."),
                        ("OnePlus 12 5G (16GB RAM, 512GB)", 64999, 69999, "Snapdragon 8 Gen 3, Hasselblad Camera System, 5400mAh battery with 100W SUPERVOOC."),
                        ("OnePlus Nord CE4 5G (8GB RAM, 128GB)", 24999, 26999, "Qualcomm Snapdragon 7 Gen 3, 100W SUPERVOOC charging, 5500mAh battery."),
                        ("Pixel 8 Pro (128GB) - Obsidian", 89999, 106999, "Google Tensor G3 chip, fully upgraded pro cameras, Best Take and Audio Magic Eraser."),
                        ("Pixel 7a 5G (128GB) - Charcoal", 35999, 43999, "Google Tensor G2 chip, wireless charging, 64MP dual rear camera system."),
                        ("Redmi Note 13 Pro+ 5G (12GB RAM, 256GB)", 30999, 33999, "200MP camera with OIS, 3D curved AMOLED 120Hz display, 120W HyperCharge."),
                        ("Realme 12 Pro+ 5G (8GB RAM, 256GB)", 27999, 31999, "64MP Periscope Portrait camera with 3x optical zoom, Luxury watch design."),
                        ("Edge 50 Pro 5G (12GB RAM, 256GB)", 31999, 36999, "Pantone validated camera and display, 125W TurboPower charging, 50MP selfie."),
                        ("Nothing Phone (2) (12GB RAM, 256GB)", 36999, 49999, "Unique Glyph Interface, Snapdragon 8+ Gen 1, 50MP dual Sony sensor cameras.")
                    ]
                },
                {
                    "name": "Mobile Accessories",
                    "brands": ["Spigen", "Anker", "Apple", "Samsung", "Mi", "Ambrane"],
                    "models": [
                        ("Ultra Hybrid MagFit Case for iPhone 15", 1899, 2499, "Air Cushion Technology, magnetic ring compatible with MagSafe wireless charging."),
                        ("20W USB-C Power Adapter Fast Charger", 1599, 1900, "Fast and efficient charging for phone and tablet at home, in the office or on the go."),
                        ("20000mAh Power Bank with 22.5W Fast Charging", 1699, 2499, "Triple output ports, high density lithium polymer battery, two-way fast charging."),
                        ("Wireless Charger Pad 15W Qi-Certified", 999, 1999, "Ultra-slim fast wireless charging pad with LED indicator and temperature control."),
                        ("Tough Armor Back Cover for Galaxy S24", 1799, 2699, "Extreme dual-layer protection with kickstand and shock-absorbing air cushions.")
                    ]
                }
            ]
        },
        {
            "category": "Laptops",
            "subcategories": [
                {
                    "name": "Laptops",
                    "brands": ["Apple", "Dell", "HP", "Lenovo", "ASUS", "Acer"],
                    "models": [
                        ("MacBook Air 13-inch M2 (8GB Unified Memory, 256GB SSD)", 89990, 99900, "13.6-inch Liquid Retina display, 18 hours battery life, 1080p FaceTime HD camera."),
                        ("MacBook Pro 14-inch M3 Pro (18GB, 512GB SSD)", 189900, 199900, "Liquid Retina XDR display, extreme pro performance for coding, 3D rendering and video."),
                        ("Pavilion 15 13th Gen Intel Core i5 (16GB RAM, 512GB SSD)", 62990, 75990, "Intel Iris Xe Graphics, 15.6-inch FHD micro-edge display, Backlit keyboard, B&O Audio."),
                        ("Inspiron 3520 Laptop Intel Core i5 12th Gen (16GB, 512GB)", 48990, 61990, "120Hz 15.6-inch FHD anti-glare display, ExpressCharge battery, Windows 11 Home."),
                        ("IdeaPad Slim 3 12th Gen Intel Core i5 (16GB, 512GB SSD)", 51990, 68990, "15.6-inch FHD IPS display, rapid charge boost, privacy shutter webcam, Dolby Audio."),
                        ("VivoBook 15 Intel Core i3 12th Gen (8GB, 512GB SSD)", 36990, 49990, "180-degree lay-flat hinge, physical webcam shield, lightweight 1.7kg chassis."),
                        ("Aspire 5 Gaming Intel Core i5 13th Gen RTX 2050 (16GB)", 54990, 72990, "NVIDIA GeForce RTX 2050 4GB GPU, dual fans with copper thermal pipes, Wi-Fi 6E."),
                        ("Yoga Slim 7 Carbon Intel Core i7 13th Gen OLED (16GB, 1TB)", 104990, 132990, "Ultra-portable carbon fiber military grade chassis, 13.3-inch 2.5K 90Hz OLED display.")
                    ]
                },
                {
                    "name": "Monitors & Accessories",
                    "brands": ["Dell", "LG", "Samsung", "Logitech", "HP"],
                    "models": [
                        ("27-inch 4K UHD IPS Monitor with USB-C Hub", 26999, 36000, "99% sRGB color gamut, HDR400, AMD FreeSync, 65W power delivery over USB-C."),
                        ("UltraGear 24-inch 144Hz 1ms Gaming Monitor", 12499, 18000, "IPS 1ms response time, NVIDIA G-Sync compatible, AMD FreeSync Premium."),
                        ("MX Master 3S Wireless Performance Mouse", 8995, 10995, "Quiet clicks, 8K DPI any-surface tracking, MagSpeed electromagnetic scrolling."),
                        ("MX Keys S Advanced Wireless Illuminated Keyboard", 9995, 12995, "Smart illumination, spherical-dished keycaps, multi-device and multi-OS switching."),
                        ("C920 Pro HD Webcam 1080p/30fps", 6995, 8995, "Dual stereo audio mics, automatic HD light correction, premium glass lens.")
                    ]
                }
            ]
        },
        {
            "category": "Fashion",
            "subcategories": [
                {
                    "name": "Men's Apparel",
                    "brands": ["Levi's", "Allen Solly", "Van Heusen", "Peter England", "U.S. Polo Assn."],
                    "models": [
                        ("511 Slim Fit Stretch Denim Jeans", 2499, 3999, "Modern slim-cut jeans with room to move, durable premium stretch cotton blend."),
                        ("Regular Fit Solid Casual Cotton Shirt", 1299, 2199, "100% combed cotton, breathable weave, button-down collar, curved hem."),
                        ("Classic Polo T-Shirt with Embroidered Logo", 999, 1899, "Signature pique cotton knit polo, ribbed collar and cuffs, 2-button placket."),
                        ("Formal Slim Fit Poly-Viscose Trousers", 1499, 2599, "Wrinkle-resistant fabric, slant side pockets, double welt back pockets."),
                        ("Fleece Zip-Front Hooded Sweatshirt", 1799, 2999, "Ultra-soft brushed fleece interior, kangaroo pockets, drawcord adjustable hood.")
                    ]
                },
                {
                    "name": "Women's Apparel",
                    "brands": ["Biba", "W for Woman", "FabIndia", "Aurelia", "ONLY", "VERO MODA"],
                    "models": [
                        ("Printed Straight Cotton Kurta with Palazzo Set", 2299, 4599, "Pure cotton floral printed kurta with matching comfortable elasticated palazzo pants."),
                        ("Woven Banarasi Silk Blend Festive Saree", 2999, 7999, "Intricate zari border, contrasting pallu, comes with matching unstitched blouse piece."),
                        ("A-Line Floral Print Knee Length Summer Dress", 1499, 2799, "Lightweight breathable georgette fabric, sweetheart neckline with puffed sleeves."),
                        ("High-Rise Skinny Fit Clean Stretch Jeans", 1799, 3299, "Super stretch denim providing sculpted silhouette, five-pocket styling."),
                        ("Embroidered Anarkali Kurti with Dupatta", 3499, 6999, "Heavy embroidery work on yolk, flared silhouette, matching chanderi dupatta.")
                    ]
                }
            ]
        },
        {
            "category": "Footwear",
            "subcategories": [
                {
                    "name": "Sports & Running Shoes",
                    "brands": ["Nike", "Adidas", "Puma", "ASICS", "Skechers"],
                    "models": [
                        ("Revolution 6 Next Nature Road Running Shoes", 2995, 3995, "Plush foam midsole, breathable mesh upper made with at least 20% recycled material."),
                        ("Duramo Speed Running Shoes with Lightstrike", 3499, 6599, "Lightstrike cushioning for energized responsiveness, engineered mesh upper."),
                        ("Darter Pro Lightweight Running Shoes", 2499, 4999, "PROFOAM high-rebound EVA midsole, durable full-length rubber traction outsole."),
                        ("Gel-Kayano 30 Stability Running Shoes", 12999, 15999, "4D GUIDANCE SYSTEM for adaptive stability, PureGEL rearfoot cushioning technology."),
                        ("Go Walk 6 Slip-On Walking Shoes", 4499, 5999, "ULTRA GO cushioning, High-rebound Hyper Pillar Technology, Air-Cooled Goga Mat insole.")
                    ]
                },
                {
                    "name": "Casual & Formal Shoes",
                    "brands": ["Bata", "Clarks", "Red Tape", "Woodland", "Hush Puppies"],
                    "models": [
                        ("Derby Formal Genuine Leather Shoes", 2199, 3999, "Genuine leather upper, cushioned insole, non-slip TPR sole, formal lace-up design."),
                        ("Classic Suede Leather Chelsea Boots", 4999, 7999, "Elasticated side gussets, pull tabs, durable crepe outsole, comfortable textile lining."),
                        ("Casual Streetwear White Sneakers", 1599, 4499, "Synthetic leather upper, cushioned collar and tongue, perforated toe for breathability."),
                        ("Nubuck Leather Outdoor Trekking Shoes", 3799, 5295, "Sturdy rugged lug outsole, water-resistant nubuck leather, padded ankle support.")
                    ]
                }
            ]
        },
        {
            "category": "Home & Kitchen",
            "subcategories": [
                {
                    "name": "Kitchen Appliances",
                    "brands": ["Philips", "Prestige", "Bajaj", "Morphy Richards", "Havells"],
                    "models": [
                        ("Digital Air Fryer 4.1L Rapid Air Technology", 6999, 11995, "Fries with up to 90% less fat, 7 preset cooking programs, touch screen display."),
                        ("750W Mixer Grinder with 3 Stainless Steel Jars", 2999, 5495, "Heavy duty 750W copper motor, flow breakers, leak-proof lids, overload protection."),
                        ("Automatic Espresso & Cappuccino Coffee Maker 15 Bar", 8999, 14995, "15 bar high pressure pump, milk frother steam wand, removable water reservoir."),
                        ("Smart Induction Cooktop 2000W with Indian Menu", 2499, 4195, "Automatic voltage regulator, pre-set cooking menus, crystal glass plate."),
                        ("Electric Glass Kettle 1.8 Litre with LED Light", 1199, 2195, "Borosilicate glass body, blue LED illumination, auto shut-off, boil-dry protection.")
                    ]
                },
                {
                    "name": "Home Decor & Furnishing",
                    "brands": ["Spaces", "Bombay Dyeing", "Story@Home", "Wipro", "Philips"],
                    "models": [
                        ("100% Cotton 300 TC King Size Bedsheet with 2 Pillow Covers", 1499, 2999, "Super soft breathable long staple cotton, anti-fading reactive printing."),
                        ("Blackout Room Darkening Eyelet Curtains (Set of 2)", 1199, 2499, "Triple weave thermal insulated blackout fabric, reduces noise and saves energy."),
                        ("Smart LED Desk Lamp with Wireless Phone Charging", 1999, 3999, "3 color modes, dimmable brightness levels, 10W wireless charging base, USB port."),
                        ("Robotic Vacuum Cleaner with Smart LiDAR Mapping", 19990, 29990, "4000Pa powerful suction, mop and vacuum 2-in-1, app control and Alexa compatible.")
                    ]
                }
            ]
        },
        {
            "category": "Beauty",
            "subcategories": [
                {
                    "name": "Skincare",
                    "brands": ["Minimalist", "Plum", "Mamaearth", "The Derma Co", "Cetaphil"],
                    "models": [
                        ("10% Niacinamide Face Serum with Zinc 30ml", 599, 699, "Reduces acne marks, blemishes, balances sebum production and strengthens skin barrier."),
                        ("SPF 50 PA++++ Broad Spectrum Sunscreen Aquagel 50g", 399, 499, "Ultra-lightweight gel formula, non-greasy, no white cast, enriched with Hyaluronic Acid."),
                        ("Gentle Skin Cleanser for Sensitive Skin 250ml", 549, 630, "Hydrating non-foaming formula, soap-free, paraben-free, dermatologist recommended."),
                        ("2% Salicylic Acid Face Wash for Oil Control 100ml", 299, 399, "Unclogs pores, gently exfoliates dead skin cells and prevents recurring breakouts."),
                        ("Green Tea Renewed Clarity Night Gel 50ml", 499, 575, "Ultra-light hydration for oily and acne-prone skin with argan oil and green tea extract.")
                    ]
                },
                {
                    "name": "Haircare & Fragrances",
                    "brands": ["L'Oreal Paris", "Biotique", "Bella Vita", "Titan Skinn", "Park Avenue"],
                    "models": [
                        ("Extraordinary Clay Purifying Shampoo 640ml", 599, 899, "Deeply cleanses oily scalp while keeping ends hydrated and fresh for 72 hours."),
                        ("Raw Eau De Parfum for Men 100ml", 1995, 2495, "Crisp notes of citrus, violet leaves, patchouli and Gaiac wood. Long lasting."),
                        ("Sheer Eau De Parfum for Women 100ml", 1995, 2495, "Feminine notes of clementine, pink pepper, peony, cedarwood and vanilla."),
                        ("Red Onion Hair Oil with Black Seed Extract 200ml", 399, 599, "Stimulates hair growth, reduces hair fall, adds natural shine and silkiness.")
                    ]
                }
            ]
        },
        {
            "category": "Sports",
            "subcategories": [
                {
                    "name": "Cricket & Team Sports",
                    "brands": ["SS", "SG", "Cosco", "Nivia", "Yonex"],
                    "models": [
                        ("Kashmir Willow Cricket Bat Short Handle", 1899, 3299, "Crafted from selected Kashmir willow, thick edges, cane handle with rubber grip."),
                        ("Club Leather Cricket Ball (Pack of 2)", 699, 1200, "Four-piece alum tanned leather ball, water-proofed, lacquered finish."),
                        ("Storm Football Size 5 FIFA Standard", 799, 1399, "Rubber molded outer casing, polyester backing, butyl bladder for shape retention."),
                        ("Astrox 88D Play Graphite Badminton Racket", 2490, 3990, "Isometric head shape, Rotational Generator System, pre-strung with durable grip."),
                        ("Mavis 350 Nylon Shuttlecocks (Pack of 6)", 899, 1190, "Precision recovery performance, high durability, consistent flight trajectory.")
                    ]
                },
                {
                    "name": "Fitness & Gym",
                    "brands": ["Decathlon", "Boldfit", "Kobo", "AmazonBasics"],
                    "models": [
                        ("Anti-Skid TPE Yoga Mat 6mm with Carrying Strap", 899, 1999, "Eco-friendly non-toxic TPE material, dual texture grip, waterproof and lightweight."),
                        ("Adjustable Hex PVC Dumbbells Set 20kg with Rods", 1699, 3999, "Complete home gym package with weight plates, spinlock collars and connector bar."),
                        ("Fabric Resistance Loop Bands Set of 3", 499, 1299, "Non-slip elastic glute and hip workout bands for strength training and physical therapy."),
                        ("Stainless Steel Gym Shaker Bottle 750ml", 599, 1199, "Leak-proof flip cap, stainless steel blender whisk ball, BPA free.")
                    ]
                }
            ]
        },
        {
            "category": "Books",
            "subcategories": [
                {
                    "name": "Computer Science & Programming",
                    "brands": ["O'Reilly", "Pearson", "Packt", "No Starch Press"],
                    "models": [
                        ("Designing Data-Intensive Applications", 1499, 2199, "The big ideas behind reliable, scalable, and maintainable systems by Martin Kleppmann."),
                        ("Python Crash Course, 3rd Edition", 1299, 1899, "A hands-on, project-based introduction to programming with Python by Eric Matthes."),
                        ("Fluent Python: Clear, Concise, and Effective Programming", 1799, 2699, "Deep dive into Python 3 idioms, data models, metaclasses and asynchronous execution."),
                        ("Clean Code: A Handbook of Agile Software Craftsmanship", 799, 1299, "Noted software expert Robert C. Martin presents a revolutionary paradigm for clean code."),
                        ("Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow", 1899, 2799, "Practical concepts, intuition, and tools for building intelligent systems by Aurélien Géron."),
                        ("System Design Interview – An Insider's Guide", 1199, 1999, "Step-by-step framework to ace system design interviews by Alex Xu.")
                    ]
                },
                {
                    "name": "Business & Self Development",
                    "brands": ["Penguin", "HarperCollins", "Random House"],
                    "models": [
                        ("Atomic Habits: An Easy & Proven Way to Build Good Habits", 499, 799, "Tiny changes, remarkable results by James Clear. #1 New York Times Bestseller."),
                        ("The Psychology of Money: Timeless Lessons on Wealth", 399, 599, "Doing well with money isn't necessarily about what you know. It's about how you behave."),
                        ("Thinking, Fast and Slow", 499, 699, "Daniel Kahneman explains the two systems that drive the way we think and make choices."),
                        ("Zero to One: Notes on Startups, or How to Build the Future", 450, 650, "Peter Thiel reveals how to build companies that create new things and innovate."),
                        ("Deep Work: Rules for Focused Success in a Distracted World", 420, 699, "Cal Newport reveals why intense concentration leads to peak cognitive performance.")
                    ]
                }
            ]
        },
        {
            "category": "Gaming",
            "subcategories": [
                {
                    "name": "Gaming Peripherals",
                    "brands": ["Razer", "Logitech G", "Cosmic Byte", "Redragon", "HyperX"],
                    "models": [
                        ("DeathAdder Essential Gaming Mouse 6400 DPI", 1399, 2499, "Ergonomic form factor, 5 Hyperesponse buttons, multi-award winning sensor."),
                        ("G502 HERO High Performance RGB Gaming Mouse", 3995, 5495, "HERO 25K sensor, 11 customizable buttons, adjustable weight balance tuning."),
                        ("BlackWidow V3 Mechanical RGB Keyboard Green Switches", 7999, 12999, "Tactile and clicky Razer Green switches, transparent switch housing, Doubleshot ABS."),
                        ("CB-GK-16 Firefly RGB Mechanical Keyboard", 2199, 3999, "Blue Outemu switches, aluminum body, customizable rainbow backlighting modes."),
                        ("Cloud II Gaming Headset 7.1 Surround Sound", 6990, 9990, "Memory foam ear cushions, durable aluminum frame, detachable noise-cancelling mic.")
                    ]
                },
                {
                    "name": "Controllers & Gear",
                    "brands": ["Sony PlayStation", "Microsoft Xbox", "Ant Esports"],
                    "models": [
                        ("DualSense Wireless Controller (Midnight Black)", 5790, 6390, "Haptic feedback, dynamic adaptive triggers, built-in microphone for PS5 and PC."),
                        ("Xbox Wireless Controller (Robot White)", 5390, 5990, "Textured grip on triggers and bumpers, hybrid D-pad, share button, Bluetooth pairing."),
                        ("Ergonomic Racing Gaming Chair with Lumbar Support", 11999, 18999, "High density molded foam, 180-degree reclining backrest, 4D adjustable armrests.")
                    ]
                }
            ]
        },
        {
            "category": "Accessories",
            "subcategories": [
                {
                    "name": "Bags & Luggage",
                    "brands": ["Wildcraft", "American Tourister", "Skybags", "Safari"],
                    "models": [
                        ("45L Waterproof Trekking and Travel Rucksack", 2199, 3999, "Ergonomic padded back system, rain cover included, multi-compartment storage."),
                        ("30L Casual Laptop Backpack with Rain Cover", 1499, 2899, "Fits up to 15.6 inch laptops, air-mesh back padding, bottle holders, water resistant."),
                        ("Ivy 67 cm Medium Hard Sided Polycarbonate Trolley", 3299, 7500, "Scratch resistant polypropylene shell, 360-degree silent spinner wheels, TSA lock.")
                    ]
                },
                {
                    "name": "Wallets & Watches",
                    "brands": ["Titan", "Fastrack", "Casio", "Fossil", "Tommy Hilfiger"],
                    "models": [
                        ("Vintage Digital Gold Dial Watch", 3995, 4995, "Iconic retro square case, daily alarm, hourly time signal, auto calendar."),
                        ("Men's Brown Genuine Leather Bifold RFID Wallet", 899, 1999, "8 card slots, 2 currency compartments, RFID blocking layer against theft."),
                        ("Grant Chronograph Black Dial Leather Watch", 8495, 12995, "Roman numeral hour markers, genuine leather strap, stopwatch functionality.")
                    ]
                }
            ]
        }
    ]

    # Expand templates into 750+ unique realistic product variants
    colors = ["Midnight Black", "Arctic White", "Space Gray", "Navy Blue", "Crimson Red", "Forest Green", "Silver", "Champagne Gold", "Graphite", "Ocean Blue", "Rose Gold", "Titanium Grey"]
    editions = ["Standard Edition", "Pro Edition", "Special Edition", "2026 Refresh", "Ultra Edition", "Limited Edition", "Plus Edition", "Max Edition"]

    now = datetime.now()

    for cat_def in category_definitions:
        cat_name = cat_def["category"]

        for subcat_def in cat_def["subcategories"]:
            subcat_name = subcat_def["name"]
            models = subcat_def["models"]

            for model_name, base_price, base_orig, desc in models:
                # Add base model
                sku_counter += 1
                base_sku = f"SKU-{cat_name[:3].upper()}-{sku_counter}"
                img_url = get_deterministic_product_image(cat_name, subcat_name, base_sku)
                gallery_imgs = get_product_gallery_images(cat_name, subcat_name, img_url, base_sku)
                rating = round(random.uniform(4.0, 4.9), 1)
                reviews = random.randint(85, 3450)
                stock = random.randint(12, 95)
                # Ensure a few low stock for inventory alerts
                if sku_counter % 25 == 0:
                    stock = random.randint(2, 5)
                discount = int(round((base_orig - base_price) / base_orig * 100))

                specs = {
                    "Brand": model_name.split()[0] if model_name else "Brand",
                    "Category": cat_name,
                    "Subcategory": subcat_name,
                    "Warranty": "1 Year Manufacturer Warranty",
                    "Delivery": "Free 2-3 Day Delivery",
                    "Return Window": "7 Days Replacement / Return"
                }

                products.append({
                    "name": model_name,
                    "brand": model_name.split()[0],
                    "category": cat_name,
                    "subcategory": subcat_name,
                    "description": desc,
                    "price": float(base_price),
                    "original_price": float(base_orig),
                    "discount_percent": discount,
                    "stock": stock,
                    "sku": base_sku,
                    "rating": rating,
                    "review_count": reviews,
                    "image_url": img_url,
                    "gallery_images": json.dumps(gallery_imgs),
                    "specifications": json.dumps(specs),
                    "warranty": "1 Year Manufacturer Warranty",
                    "delivery_days": random.randint(2, 4),
                    "return_policy": "7 Days Replacement / Return",
                    "status": "active",
                    "created_at": (now - timedelta(days=random.randint(10, 180))).isoformat(timespec="seconds"),
                    "updated_at": now.isoformat(timespec="seconds")
                })

                # Generate 5 realistic color/edition variants to achieve 750+ catalogue size
                for var_idx in range(5):
                    sku_counter += 1
                    color = colors[(sku_counter + var_idx) % len(colors)]
                    edition = editions[(sku_counter + var_idx) % len(editions)]
                    v_name = f"{model_name} - {color} ({edition})"
                    v_sku = f"SKU-{cat_name[:3].upper()}-{sku_counter}"
                    v_img = get_deterministic_product_image(cat_name, subcat_name, f"{v_sku}-{color}", offset=var_idx + 1)
                    v_gallery = get_product_gallery_images(cat_name, subcat_name, v_img, v_sku)
                    
                    price_var = int(base_price * (1.0 + (var_idx * 0.04)))
                    orig_var = int(base_orig * (1.0 + (var_idx * 0.04)))
                    v_discount = int(round((orig_var - price_var) / orig_var * 100))
                    v_stock = random.randint(8, 85)
                    if sku_counter % 28 == 0:
                        v_stock = random.randint(1, 4)

                    v_specs = {
                        "Brand": model_name.split()[0],
                        "Color": color,
                        "Edition": edition,
                        "Category": cat_name,
                        "Subcategory": subcat_name,
                        "Warranty": "1 Year Manufacturer Warranty",
                        "Delivery": "Express Delivery Available"
                    }

                    products.append({
                        "name": v_name,
                        "brand": model_name.split()[0],
                        "category": cat_name,
                        "subcategory": subcat_name,
                        "description": f"{desc} Features sleek {color} finish and premium {edition} build.",
                        "price": float(price_var),
                        "original_price": float(orig_var),
                        "discount_percent": v_discount,
                        "stock": v_stock,
                        "sku": v_sku,
                        "rating": round(random.uniform(3.9, 4.9), 1),
                        "review_count": random.randint(45, 2100),
                        "image_url": v_img,
                        "gallery_images": json.dumps(v_gallery),
                        "specifications": json.dumps(v_specs),
                        "warranty": "1 Year Manufacturer Warranty",
                        "delivery_days": random.randint(2, 4),
                        "return_policy": "7 Days Replacement / Return",
                        "status": "active",
                        "created_at": (now - timedelta(days=random.randint(5, 120))).isoformat(timespec="seconds"),
                        "updated_at": now.isoformat(timespec="seconds")
                    })

    return products

def seed_database(force_reseed=False, wipe_products=False, wipe_customer_data=False):
    """Populates categories, products, coupons, demo users, orders idempotently without destroying customer records."""
    with get_connection() as conn:
        prod_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if prod_count > 100 and not force_reseed:
            return  # Already populated with rich catalogue

        # Only clear products if expressly requested or database has old <= 10 demo items
        should_wipe_products = (prod_count <= 10) or (force_reseed and wipe_products)
        if should_wipe_products:
            conn.execute("DELETE FROM products")
            conn.execute("DELETE FROM categories")

        # NEVER wipe customer transaction data unless expressly requested
        if wipe_customer_data:
            conn.execute("DELETE FROM order_items")
            conn.execute("DELETE FROM returns")
            conn.execute("DELETE FROM refunds")
            conn.execute("DELETE FROM reviews")
            conn.execute("DELETE FROM orders")
            conn.execute("DELETE FROM cart")
            conn.execute("DELETE FROM wishlist")
            conn.execute("DELETE FROM addresses")
            conn.execute("DELETE FROM notifications")

        now = datetime.now()

        # 1. Categories
        categories = [
            ("Electronics", "electronics", "🎧", "Headphones, Speakers, Earbuds & Audio Gear", 1),
            ("Mobiles", "mobiles", "📱", "Latest 5G Smartphones, Cases & Accessories", 2),
            ("Laptops", "laptops", "💻", "Laptops, PC Monitors, Keyboards & Mice", 3),
            ("Fashion", "fashion", "👕", "Men & Women Designer Apparel and Styles", 4),
            ("Footwear", "footwear", "👟", "Running Shoes, Sneakers, Casual & Formals", 5),
            ("Home & Kitchen", "home-kitchen", "☕", "Appliances, Cookware, Lighting & Decor", 6),
            ("Beauty", "beauty", "✨", "Skincare, Haircare, Grooming & Fragrances", 7),
            ("Sports", "sports", "⚽", "Fitness Gear, Cricket, Badminton & Equipment", 8),
            ("Books", "books", "📚", "Coding, AI, Business, Psychology & Bestsellers", 9),
            ("Gaming", "gaming", "🎮", "Gaming Peripherals, Controllers, Chairs & Gear", 10),
            ("Accessories", "accessories", "🎒", "Travel Bags, Leather Wallets & Watches", 11)
        ]
        conn.executemany("""
            INSERT OR REPLACE INTO categories (name, slug, icon, description, display_order)
            VALUES (?, ?, ?, ?, ?)
        """, categories)

        # 2. Products (if empty or wiped)
        if should_wipe_products or conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            catalog = generate_catalog()
            prod_tuples = [
                (
                    p["name"], p["brand"], p["category"], p["subcategory"], p["description"],
                    p["price"], p["original_price"], p["discount_percent"], p["stock"],
                    p["sku"], p["rating"], p["review_count"], p["image_url"], p.get("gallery_images", "[]"),
                    p["specifications"], p["warranty"], p["delivery_days"], p["return_policy"],
                    p["status"], p["created_at"], p["updated_at"]
                )
                for p in catalog
            ]
            conn.executemany("""
                INSERT INTO products (
                    name, brand, category, subcategory, description, price, original_price,
                    discount_percent, stock, sku, rating, review_count, image_url, gallery_images,
                    specifications, warranty, delivery_days, return_policy, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, prod_tuples)

        # 3. Coupons
        coupons = [
            ("WELCOME10", "percent", 10.0, 999.0, 500.0, "2027-12-31", 5000, 48, 1, now.isoformat()),
            ("SAVE200", "fixed", 200.0, 1999.0, 200.0, "2027-12-31", 3000, 112, 1, now.isoformat()),
            ("FESTIVE20", "percent", 20.0, 2499.0, 1000.0, "2027-12-31", 2000, 31, 1, now.isoformat()),
            ("NEWUSER15", "percent", 15.0, 1499.0, 600.0, "2027-12-31", 4000, 89, 1, now.isoformat()),
            ("MEGADEAL30", "percent", 30.0, 4999.0, 2000.0, "2027-12-31", 1000, 15, 1, now.isoformat())
        ]
        conn.executemany("""
            INSERT OR REPLACE INTO coupons (code, discount_type, discount_value, min_order_amount, max_discount, expiry_date, usage_limit, times_used, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, coupons)

        # 4. Users (Admin + Demo Customers)
        admin_pass = hash_password("Admin@123")
        cust_pass = hash_password("Customer@123")

        users = [
            (1, "Administrator", "admin@example.com", admin_pass, "+91 98765 43210", "E-Commerce HQ, Koramangala 4th Block, Bangalore", "admin", 1, now.isoformat()),
            (2, "Rahul Sharma", "rahul.sharma@example.com", cust_pass, "+91 98450 12345", "Flat 402, Green Glen Apartments, Bellandur, Bangalore, Karnataka - 560103", "customer", 1, now.isoformat()),
            (3, "Priya Patel", "priya.patel@example.com", cust_pass, "+91 97230 67890", "B-12, Shanti Kunj, Navrangpura, Ahmedabad, Gujarat - 380009", "customer", 1, now.isoformat())
        ]
        conn.executemany("""
            INSERT OR REPLACE INTO users (id, name, email, password, phone, address, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, users)

        # 5. Addresses for customers
        addresses = [
            (2, "Rahul Sharma", "+91 98450 12345", "Flat 402, Green Glen Apartments, Bellandur", "Bangalore", "Karnataka", "560103", 1, now.isoformat()),
            (2, "Rahul Sharma (Office)", "+91 98450 12345", "Tech Park Building 7, Outer Ring Road", "Bangalore", "Karnataka", "560103", 0, now.isoformat()),
            (3, "Priya Patel", "+91 97230 67890", "B-12, Shanti Kunj, Navrangpura", "Ahmedabad", "Gujarat", "380009", 1, now.isoformat())
        ]
        conn.executemany("""
            INSERT OR IGNORE INTO addresses (user_id, full_name, phone, street_address, city, state, postal_code, is_default, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, addresses)

        # 6. Demo Orders & Customer Activity (Seeded only if database is fresh)
        orders_exist = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        if orders_exist > 0:
            return  # Customer orders already populated; preserve existing activity

        p_rows = conn.execute("SELECT id, name, brand, price, image_url FROM products LIMIT 15").fetchall()
        if len(p_rows) < 5:
            return
        p1, p2, p3, p4, p5 = p_rows[0], p_rows[1], p_rows[2], p_rows[3], p_rows[4]

        # 6. Demo Orders
        # Order 1: Delivered (Eligible for Return)
        t_hist_1 = json.dumps([
            {"status": "Placed", "time": (now - timedelta(days=6)).strftime("%Y-%m-%d %H:%M"), "note": "Order placed successfully"},
            {"status": "Confirmed", "time": (now - timedelta(days=5, hours=20)).strftime("%Y-%m-%d %H:%M"), "note": "Payment verified"},
            {"status": "Packed", "time": (now - timedelta(days=5, hours=10)).strftime("%Y-%m-%d %H:%M"), "note": "Packed at Bangalore Fulfilment Center"},
            {"status": "Shipped", "time": (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M"), "note": "Handed over to BlueDart (AWB #BD982104)"},
            {"status": "Out for Delivery", "time": (now - timedelta(days=3, hours=5)).strftime("%Y-%m-%d %H:%M"), "note": "Courier out for delivery"},
            {"status": "Delivered", "time": (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"), "note": "Delivered to recipient with OTP"}
        ])
        subtotal_1 = float(p1["price"] + (p2["price"] * 2))
        del_date_1 = (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        cur = conn.execute("""
            INSERT INTO orders (order_number, user_id, subtotal, discount, coupon_code, delivery_fee, tax_amount, total, shipping_address, delivery_method, payment_method, payment_status, status, expected_delivery, delivery_date, tracking_history, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("ORD-2026-1001", 2, subtotal_1, 200.0, "SAVE200", 0.0, round(subtotal_1 * 0.18, 2), subtotal_1 - 200.0, "Flat 402, Green Glen Apartments, Bellandur, Bangalore - 560103", "Standard Express", "UPI (Google Pay)", "Paid", "Delivered", (now - timedelta(days=3)).strftime("%Y-%m-%d"), del_date_1, t_hist_1, (now - timedelta(days=6)).isoformat(), (now - timedelta(days=3)).isoformat()))
        ord1_id = cur.lastrowid
        
        cur_item1 = conn.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, brand, image_url, quantity, returned_quantity, price, total_price, has_return)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ord1_id, p1["id"], p1["name"], p1["brand"], p1["image_url"], 1, 1, p1["price"], p1["price"], 1))
        item1_id = cur_item1.lastrowid

        conn.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, brand, image_url, quantity, returned_quantity, price, total_price, has_return)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ord1_id, p2["id"], p2["name"], p2["brand"], p2["image_url"], 2, 0, p2["price"], p2["price"] * 2, 0))

        # Order 2: Shipped (In Transit)
        t_hist_2 = json.dumps([
            {"status": "Placed", "time": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), "note": "Order placed"},
            {"status": "Confirmed", "time": (now - timedelta(days=2, hours=4)).strftime("%Y-%m-%d %H:%M"), "note": "Payment confirmed"},
            {"status": "Packed", "time": (now - timedelta(days=1, hours=18)).strftime("%Y-%m-%d %H:%M"), "note": "Dispatched from Hub"},
            {"status": "Shipped", "time": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), "note": "In transit with Delhivery (AWB #DL554109)"}
        ])
        subtotal_2 = float(p3["price"])
        cur2 = conn.execute("""
            INSERT INTO orders (order_number, user_id, subtotal, discount, coupon_code, delivery_fee, tax_amount, total, shipping_address, delivery_method, payment_method, payment_status, status, expected_delivery, delivery_date, tracking_history, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("ORD-2026-1002", 2, subtotal_2, 0.0, None, 49.0, round(subtotal_2 * 0.18, 2), subtotal_2 + 49.0, "Flat 402, Green Glen Apartments, Bellandur, Bangalore - 560103", "Standard", "Credit Card (HDFC)", "Paid", "Shipped", (now + timedelta(days=2)).strftime("%Y-%m-%d"), None, t_hist_2, (now - timedelta(days=2)).isoformat(), (now - timedelta(days=1)).isoformat()))
        ord2_id = cur2.lastrowid
        conn.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, brand, image_url, quantity, returned_quantity, price, total_price, has_return)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ord2_id, p3["id"], p3["name"], p3["brand"], p3["image_url"], 1, 0, p3["price"], p3["price"], 0))

        # Order 3: Delivered with completed refund for demo user Priya Patel
        subtotal_3 = float(p4["price"])
        t_hist_3 = json.dumps([
            {"status": "Placed", "time": (now - timedelta(days=12)).strftime("%Y-%m-%d %H:%M"), "note": "Order placed"},
            {"status": "Delivered", "time": (now - timedelta(days=9)).strftime("%Y-%m-%d %H:%M"), "note": "Delivered"}
        ])
        del_date_3 = (now - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")
        cur3 = conn.execute("""
            INSERT INTO orders (order_number, user_id, subtotal, discount, coupon_code, delivery_fee, tax_amount, total, shipping_address, delivery_method, payment_method, payment_status, status, expected_delivery, delivery_date, tracking_history, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("ORD-2026-1003", 3, subtotal_3, 0.0, None, 0.0, round(subtotal_3 * 0.18, 2), subtotal_3, "B-12, Shanti Kunj, Navrangpura, Ahmedabad - 380009", "Standard", "Net Banking (SBI)", "Paid", "Delivered", (now - timedelta(days=9)).strftime("%Y-%m-%d"), del_date_3, t_hist_3, (now - timedelta(days=12)).isoformat(), (now - timedelta(days=9)).isoformat()))
        ord3_id = cur3.lastrowid
        cur_item3 = conn.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, brand, image_url, quantity, returned_quantity, price, total_price, has_return)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ord3_id, p4["id"], p4["name"], p4["brand"], p4["image_url"], 1, 1, p4["price"], p4["price"], 1))
        item3_id = cur_item3.lastrowid

        # 7. Demo Return Requests across multiple stages
        # Return 1: Rahul Sharma - Under Review / Pickup Scheduled
        ret_hist_1 = json.dumps([
            {"status": "Under Review", "time": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), "note": "Customer reported size / fit mismatch"},
            {"status": "Approved", "time": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), "note": "Return approved by seller"},
            {"status": "Pickup Scheduled", "time": (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"), "note": "Pickup scheduled with courier"}
        ])
        conn.execute("""
            INSERT INTO returns (return_number, order_id, order_item_id, product_id, user_id, quantity, reason, comments, refund_method, status, pickup_date, restocked, tracking_history, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
        """, ("RET-2026-5001", ord1_id, item1_id, p1["id"], 2, 1, "Size Issue", "The product dimensions were slightly larger than expected.", "UPI (Google Pay)", "Pickup Scheduled", (now + timedelta(days=1)).strftime("%Y-%m-%d"), ret_hist_1, (now - timedelta(days=2)).isoformat(), now.isoformat()))

        # Return 2: Priya Patel - Completed Refund
        ret_hist_2 = json.dumps([
            {"status": "Under Review", "time": (now - timedelta(days=8)).strftime("%Y-%m-%d %H:%M"), "note": "Customer requested return: Defective / Damaged"},
            {"status": "Approved", "time": (now - timedelta(days=6)).strftime("%Y-%m-%d %H:%M"), "note": "Return approved"},
            {"status": "Pickup Scheduled", "time": (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M"), "note": "Courier picked up parcel"},
            {"status": "Product Received", "time": (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M"), "note": "Item received at warehouse verification completed"},
            {"status": "Refund Initiated", "time": (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"), "note": "Bank payment gateway refund triggered"},
            {"status": "Refund Completed", "time": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), "note": "₹" + str(p4["price"]) + " credited to original payment source"}
        ])
        cur_ret2 = conn.execute("""
            INSERT INTO returns (return_number, order_id, order_item_id, product_id, user_id, quantity, reason, comments, refund_method, status, pickup_date, restocked, tracking_history, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
        """, ("RET-2026-5002", ord3_id, item3_id, p4["id"], 3, 1, "Defective", "Item had physical rattling inside the casing.", "Original Payment", "Refund Completed", (now - timedelta(days=5)).strftime("%Y-%m-%d"), ret_hist_2, (now - timedelta(days=8)).isoformat(), (now - timedelta(days=2)).isoformat()))
        ret2_id = cur_ret2.lastrowid

        # 8. Demo Refund Record
        conn.execute("""
            INSERT INTO refunds (refund_number, return_id, order_id, user_id, product_id, amount, method, status, transaction_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("REF-2026-9001", ret2_id, ord3_id, 3, p4["id"], p4["price"], "Original Payment (Net Banking)", "Completed", "TXN_REF_883920194", (now - timedelta(days=3)).isoformat(), (now - timedelta(days=2)).isoformat()))

        # 9. Demo Reviews
        reviews = [
            (p1["id"], 2, "Rahul Sharma", 5, "Outstanding sound and ANC!", "The sound quality is crisp and the active noise cancellation completely cuts out office chatter. Highly recommend!", 1, (now - timedelta(days=4)).isoformat(), now.isoformat()),
            (p2["id"], 2, "Rahul Sharma", 4, "Very solid build and good battery", "Great product overall. The delivery was fast and packaging was secure.", 1, (now - timedelta(days=3)).isoformat(), now.isoformat()),
            (p3["id"], 3, "Priya Patel", 5, "Premium experience", "Exceeded expectations in terms of speed, finish and battery longevity.", 1, (now - timedelta(days=10)).isoformat(), now.isoformat()),
            (p5["id"], 2, "Rahul Sharma", 5, "Best value in this segment", "Fantastic performance for the price. Works flawlessly out of the box.", 1, (now - timedelta(days=15)).isoformat(), now.isoformat())
        ]
        conn.executemany("""
            INSERT INTO reviews (product_id, user_id, user_name, rating, headline, comment, verified_purchase, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, reviews)

        # 10. Demo Notifications
        notifs = [
            (2, "Order Shipped! 🚚", "Your order #ORD-2026-1002 has been shipped with Delhivery. Expected arrival in 2 days.", "order", 0, "orders", (now - timedelta(days=1)).isoformat()),
            (2, "Return Pickup Scheduled 📦", "Pickup for return #RET-2026-5001 is scheduled for tomorrow with Shadowfax.", "return", 0, "returns", (now - timedelta(hours=6)).isoformat()),
            (2, "Exclusive Festival Offer! 🎉", "Use coupon code FESTIVE20 to get 20% OFF on all electronics and fashion.", "deal", 1, "deals", (now - timedelta(days=3)).isoformat()),
            (3, "Refund Completed ✅", "Refund of ₹" + str(p4["price"]) + " for order #ORD-2026-1003 has been credited to your bank account.", "refund", 0, "returns", (now - timedelta(days=2)).isoformat())
        ]
        conn.executemany("""
            INSERT INTO notifications (user_id, title, message, type, is_read, link_page, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, notifs)
