"""Build the curated, source-linked product snapshot. No live stock claims."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'sales_agent/data'
HEADPHONES = 'https://electronics.sony.com/audio/headphones/c/all-headphones'
MONITORS = 'https://electronics.sony.com/tv-video/gaming-monitors/c/inzone-monitors'
CAMERAS = 'https://electronics.sony.com/imaging/compact-cameras/c/vlog-cameras'
AIRPODS = 'https://www.apple.com/shop/buy-airpods/airpods-5'
products = []

def add(id, name, category, price, source, specs, features, description, tradeoff, old=None, aliases=(), price_kind='snapshot'):
    products.append(dict(id=id, name=name, brand=name.split()[0], category=category,
        department={'headphones':'audio','earbuds':'audio','speakers':'audio','laptops':'computers','monitors':'computers',
                    'phones':'mobile','tablets':'mobile','cameras':'photography','tvs':'home theater','gaming':'gaming',
                    'wearables':'mobile','accessories':'computers','networking':'smart home','smart home':'smart home',
                    'appliances':'appliances'}[category],
        price=price, source_url=source, price_checked_at='2026-09-27', price_kind=price_kind,
        compare_at_price=old, specs=specs, features=features.split(','), description=description,
        tradeoff=tradeoff, stock=10, stock_source='local_demo', icon='', aliases=list(dict.fromkeys([*aliases,' '.join(name.split()[1:])])),
        image_note='Category illustration; see manufacturer for product photographs.'))

add('sony-wh1000xm5','Sony WH-1000XM5','headphones',299.99,'https://electronics.sony.com/audio/headphones/headband/p/wh1000xm5-s',{'Design':'Over-ear','Battery':'Up to 30 hours'},'wireless,noise cancelling,travel,music,long battery','Quiet your commute with wireless over-ear listening.','Over-ear headphones take more bag space than earbuds.',399.99,['WH 1000 XM5','WH1000XM5'])
add('google-pixel-9a','Google Pixel 9a','phones',499,'https://store.google.com/config/pixel_9a?hl=en-US',{'Storage':'128 GB','Network':'Unlocked'},'portable,home,work','An unlocked Android phone for everyday use.','Check your carrier compatibility before buying.',aliases=['Pixel 9a','Pixel nine a','Pixel9a'])
add('apple-airpods-5','Apple AirPods 5','earbuds',129,AIRPODS,{'Case':'USB-C charging','Listening':'Active noise cancellation'},'wireless,noise cancelling,portable,music','Small wireless earphones with a USB-C charging case.','Check device compatibility and the ear fit.',aliases=['AirPods 5','AirPods five'])
add('sonos-roam-2','Sonos Roam 2','speakers',179,'https://www.sonos.com/en-us/shop/roam-2-olive',{'Connectivity':'Bluetooth','Design':'Portable speaker'},'wireless,portable,home,music','A portable speaker for shared listening.','A speaker plays aloud; choose earphones for private listening.',aliases=['Roam 2'])
add('sony-whch530','Sony WH-CH530','headphones',69.99,HEADPHONES,{'Design':'On-ear','Color':'Coral'},'wireless,music,portable','An affordable on-ear option.','On-ear fit differs from full over-ear coverage.',aliases=['CH530','WH CH530'])
add('sony-ult-wear','Sony ULT WEAR','headphones',149.99,HEADPHONES,{'Design':'Over-ear','Color':'Black'},'wireless,noise cancelling,music,travel','Over-ear listening with a bass-oriented design.','Compare the sound tuning with your music preferences.',249.99,['ULT Wear'])
add('sony-whch730n','Sony WH-CH730N','headphones',179.99,HEADPHONES,{'Design':'Over-ear','Color':'White'},'wireless,noise cancelling,music','Wireless listening with noise cancellation.','Try the fit before long listening sessions.',aliases=['CH730N','WH CH730N'])
add('sony-wh1000xm6','Sony WH-1000XM6','headphones',459.99,HEADPHONES,{'Design':'Over-ear','Color':'Midnight blue'},'wireless,noise cancelling,travel,music','Premium over-ear headphones.','Costs more than the discounted XM5.',aliases=['WH 1000 XM6','WH1000XM6'])
add('sony-wf1000xm5','Sony WF-1000XM5','earbuds',279.99,'https://electronics.sony.com/audio/headphones/truly-wireless-earbuds/p/wf1000xm5-b',{'Design':'In-ear','Listening':'Noise cancellation'},'wireless,noise cancelling,music,portable','Noise-cancelling earphones in a compact form.','In-ear tips need a comfortable seal.',329.99,['WF 1000 XM5','WF1000XM5'])
add('sony-wf1000xm6','Sony WF-1000XM6','earbuds',329.99,HEADPHONES,{'Design':'In-ear','Color':'Black'},'wireless,noise cancelling,music,portable','Premium wireless earbuds.','More expensive than the discounted XM5 earbuds.',aliases=['WF 1000 XM6','WF1000XM6'])
add('sony-linkbuds-fit','Sony LinkBuds Fit','earbuds',229.99,HEADPHONES,{'Design':'Earbuds','Color':'Pink'},'wireless,portable,music','Compact wireless earbuds.','Fit varies by ear; check the return policy.',aliases=['LinkBuds Fit'])
add('sony-linkbuds-clip','Sony LinkBuds Clip','earbuds',229.99,HEADPHONES,{'Design':'Open-ear clip','Color':'Greige'},'wireless,portable,music','Clip-style listening with an open-ear design.','An open fit provides less passive isolation.',aliases=['LinkBuds Clip'])
add('apple-airpods-5-wireless','Apple AirPods 5 Wireless Case','earbuds',149,AIRPODS,{'Case':'Wireless charging','Listening':'Active noise cancellation'},'wireless,noise cancelling,portable,music','AirPods with a wireless charging case.','Costs more than the USB-C case version.',aliases=['AirPods wireless case'])
add('apple-airpods-pro-3','Apple AirPods Pro 3','earbuds',249,AIRPODS,{'Family':'AirPods Pro','Design':'In-ear'},'wireless,noise cancelling,portable,music','Apple’s in-ear Pro option.','Check device compatibility and tip fit.',aliases=['AirPods Pro 3','AirPods Pro three'])
add('apple-ipad-128','Apple iPad 128GB Wi-Fi','tablets',449,'https://www.apple.com/shop/buy-ipad/ipad',{'Storage':'128 GB','Connectivity':'Wi-Fi'},'portable,school,home','A tablet for browsing, reading and everyday tasks.','This Wi-Fi configuration has no cellular connection.',aliases=['iPad 128','iPad'])
add('macbook-air-m5-13','Apple MacBook Air 13 M5','laptops',1099,'https://www.apple.com/newsroom/2026/03/apple-introduces-the-new-macbook-air-with-m5/',{'Chip':'Apple M5','Memory / storage':'16 GB / 512 GB'},'portable,school,work,16gb ram','A 13-inch Mac laptop for everyday work.','Check that your required software supports macOS.',aliases=['MacBook Air 13','MacBook Air'],price_kind='launch_reference')
add('macbook-air-m5-15','Apple MacBook Air 15 M5','laptops',1299,'https://www.apple.com/newsroom/2026/03/apple-introduces-the-new-macbook-air-with-m5/',{'Chip':'Apple M5','Display':'15-inch'},'portable,school,work','A larger-screen MacBook Air.','The larger screen also takes more bag space.',aliases=['MacBook Air 15'],price_kind='launch_reference')
add('sony-inzone-m9-ii','Sony INZONE M9 II','monitors',749.99,MONITORS,{'Display':'27-inch 4K','Refresh rate':'160 Hz'},'4k,gaming,work','A 4K desktop display with a fast refresh rate.','Driving games at 4K requires suitable graphics hardware.',949.99,['INZONE M9 II','INZONE M9 2'])
add('sony-inzone-m10s','Sony INZONE M10S','monitors',899.99,MONITORS,{'Display':'27-inch QHD OLED','Refresh rate':'480 Hz'},'oled,gaming','A high-refresh OLED gaming monitor.','QHD has fewer pixels than 4K.',aliases=['INZONE M10S'])
add('sony-inzone-m10s-ii','Sony INZONE M10S II','monitors',1099.99,MONITORS,{'Display':'27-inch 1440p OLED','Refresh rate':'540 Hz'},'oled,gaming','A fast OLED display for competitive play.','High frame rates depend on the game and computer.',aliases=['INZONE M10S II','INZONE M10S 2'])
add('sony-zv1f','Sony ZV-1F','cameras',599.99,CAMERAS,{'Type':'Vlog camera'},'creator,portable','A compact starting point for video creation.','Compare lens flexibility with interchangeable-lens models.',aliases=['ZV1F','ZV 1F'])
add('sony-zv1-ii','Sony ZV-1 II','cameras',999.99,CAMERAS,{'Type':'Vlog camera'},'creator,portable','A compact camera for a video-focused setup.','Consider whether you need interchangeable lenses.',aliases=['ZV1 II','ZV 1 2'])
add('sony-zve10','Sony ZV-E10','cameras',799.99,CAMERAS,{'Sensor':'24 MP APS-C','Video':'4K 30p'},'creator,4k','An interchangeable-lens camera for making videos.','Budget for compatible lenses and accessories.',aliases=['ZVE10','ZV E10'])
add('sony-zve10-ii','Sony ZV-E10 II','cameras',1199.99,CAMERAS,{'Type':'Interchangeable-lens vlog camera'},'creator','A newer option in Sony’s E10 camera line.','Check the exact lens bundle before ordering.',aliases=['ZVE10 II','ZV E10 2'])

# Broad electronics-store assortment. Prices are reference prices captured for
# this demo; source links point to the relevant manufacturer storefronts.
SOURCES = {
 'apple':'https://www.apple.com/shop','samsung':'https://www.samsung.com/us/','google':'https://store.google.com/',
 'oneplus':'https://www.oneplus.com/us/store','motorola':'https://www.motorola.com/us/','nothing':'https://us.nothing.tech/',
 'microsoft':'https://www.microsoft.com/en-us/store/b/surface','dell':'https://www.dell.com/en-us/shop','lenovo':'https://www.lenovo.com/us/en/',
 'hp':'https://www.hp.com/us-en/shop/','asus':'https://www.asus.com/us/','acer':'https://store.acer.com/en-us/',
 'framework':'https://frame.work/','lg':'https://www.lg.com/us/','benq':'https://www.benq.com/en-us/','msi':'https://us.msi.com/',
 'bose':'https://www.bose.com/','sennheiser':'https://www.sennheiser-hearing.com/en-US/','beats':'https://www.beatsbydre.com/',
 'audiotechnica':'https://www.audio-technica.com/en-us/','jbl':'https://www.jbl.com/','jabra':'https://www.jabra.com/',
 'ultimateears':'https://www.ultimateears.com/','marshall':'https://www.marshall.com/us/en','sonos':'https://www.sonos.com/en-us/home',
 'sony':'https://electronics.sony.com/','tcl':'https://www.tcl.com/us/en','hisense':'https://www.hisense-usa.com/','roku':'https://www.roku.com/products/roku-tv',
 'canon':'https://www.usa.canon.com/shop/cameras','nikon':'https://www.nikonusa.com/cameras','fujifilm':'https://www.fujifilm-x.com/en-us/','gopro':'https://gopro.com/en/us/shop/cameras',
 'playstation':'https://direct.playstation.com/en-us/hardware/ps5','xbox':'https://www.xbox.com/en-US/consoles','nintendo':'https://www.nintendo.com/us/gaming-systems/switch/',
 'valve':'https://store.steampowered.com/steamdeck','meta':'https://www.meta.com/quest/','garmin':'https://www.garmin.com/en-US/c/wearables-smartwatches/',
 'fitbit':'https://store.google.com/category/watches_trackers','logitech':'https://www.logitech.com/en-us/products.html','anker':'https://www.anker.com/',
 'tp-link':'https://www.tp-link.com/us/home-networking/','netgear':'https://www.netgear.com/home/wifi/routers/','amazon':'https://www.amazon.com/echoshow',
 'ring':'https://ring.com/collections/video-doorbells','dyson':'https://www.dyson.com/vacuum-cleaners','irobot':'https://www.irobot.com/en_US/roomba.html',
 'ninja':'https://www.sharkninja.com/ninja-kitchen','breville':'https://www.breville.com/en-us/shop/espresso'
}

CATEGORY_COPY = {
 'phones':('A smartphone that combines {a} with {b} for everyday communication and apps.','Confirm carrier support, storage needs, and preferred mobile operating system.'),
 'tablets':('A tablet with {a} and {b} for portable browsing, media, and light work.','Keyboard, pen, and cellular capability may cost extra.'),
 'laptops':('A laptop pairing {a} with {b} for work, school, or creative tasks.','Confirm ports, operating-system compatibility, and sustained performance for your software.'),
 'monitors':('A desktop display with {a} and {b}.','Your computer must support the listed resolution and refresh rate.'),
 'headphones':('Over-ear listening with {a} and {b}.','Comfort, microphone quality, and sound tuning are personal preferences.'),
 'earbuds':('Compact earphones offering {a} and {b}.','A secure seal and comfortable ear-tip fit vary by listener.'),
 'speakers':('A wireless speaker with {a} and {b} for shared listening.','Room size and placement strongly affect bass and clarity.'),
 'tvs':('A television combining {a} with {b} for movies, sports, and games.','Measure the room and verify HDMI features before choosing a size.'),
 'cameras':('A camera built around {a} and {b} for photos and video.','Lenses, cards, batteries, and stabilization needs can raise the total cost.'),
 'gaming':('A gaming system with {a} and {b}.','Game library, subscriptions, storage, and display requirements differ by platform.'),
 'wearables':('A wearable with {a} and {b} for daily activity and notifications.','Battery life and health features vary with settings and phone compatibility.'),
 'accessories':('A practical accessory featuring {a} and {b}.','Check connector, operating-system, and device compatibility.'),
 'networking':('Home networking hardware with {a} and {b}.','Coverage depends on layout, interference, internet service, and device support.'),
 'smart home':('A connected-home device with {a} and {b}.','Some features require an account, compatible ecosystem, or subscription.'),
 'appliances':('A home appliance with {a} and {b}.','Consider counter or storage space, cleaning effort, and replacement-part costs.')
}

def add_reference(row):
    id,name,category,price,source_key,spec_a,spec_b,features=row
    key_a,value_a=spec_a.split('=',1);key_b,value_b=spec_b.split('=',1)
    description,tradeoff=CATEGORY_COPY[category]
    add(id,name,category,price,SOURCES[source_key],{key_a:value_a,key_b:value_b},features,
        description.format(a=value_a,b=value_b),tradeoff,price_kind='launch_reference')

REFERENCE_ROWS = [
 ('apple-iphone-16e','Apple iPhone 16e','phones',599,'apple','Storage=128 GB','Display=6.1-inch OLED','portable,work,home'),
 ('apple-iphone-16','Apple iPhone 16','phones',799,'apple','Storage=128 GB','Camera=Dual-camera system','portable,creator,work'),
 ('samsung-galaxy-s25','Samsung Galaxy S25','phones',799,'samsung','Storage=128 GB','Display=6.2-inch AMOLED','portable,work,creator'),
 ('samsung-galaxy-s25-ultra','Samsung Galaxy S25 Ultra','phones',1299,'samsung','Storage=256 GB','Pen=Built-in S Pen','portable,creator,work'),
 ('google-pixel-9','Google Pixel 9','phones',799,'google','Storage=128 GB','Camera=Dual rear camera','portable,creator,work'),
 ('oneplus-13','OnePlus 13','phones',899,'oneplus','Storage=256 GB','Battery=6,000 mAh','portable,long battery,work'),
 ('motorola-moto-g-power-2025','Motorola Moto G Power 2025','phones',299,'motorola','Storage=128 GB','Battery=5,000 mAh','portable,long battery,home'),
 ('nothing-phone-3a','Nothing Phone 3a','phones',379,'nothing','Storage=128 GB','Display=6.77-inch AMOLED','portable,home,work'),
 ('apple-ipad-pro-11-m4','Apple iPad Pro 11 M4','tablets',999,'apple','Chip=Apple M4','Display=11-inch OLED','portable,creator,work'),
 ('apple-ipad-air-11-m3','Apple iPad Air 11 M3','tablets',599,'apple','Chip=Apple M3','Storage=128 GB','portable,school,work'),
 ('samsung-galaxy-tab-s10-plus','Samsung Galaxy Tab S10+','tablets',999,'samsung','Display=12.4-inch AMOLED','Storage=256 GB','portable,creator,work'),
 ('google-pixel-tablet','Google Pixel Tablet','tablets',399,'google','Display=11-inch','Storage=128 GB','portable,home,school'),
 ('oneplus-pad-2','OnePlus Pad 2','tablets',549,'oneplus','Display=12.1-inch 144 Hz','Storage=256 GB','portable,school,work'),
 ('microsoft-surface-pro-11','Microsoft Surface Pro 11','tablets',999,'microsoft','Display=13-inch touchscreen','Memory=16 GB','portable,work,school'),
 ('dell-xps-13-9350','Dell XPS 13 9350','laptops',1399,'dell','Display=13.4-inch','Memory=16 GB','portable,work,16gb ram'),
 ('lenovo-yoga-7i-14','Lenovo Yoga 7i 14','laptops',899,'lenovo','Design=2-in-1 touchscreen','Memory=16 GB','portable,school,work,16gb ram'),
 ('lenovo-thinkpad-x1-carbon-gen-13','Lenovo ThinkPad X1 Carbon Gen 13','laptops',1699,'lenovo','Display=14-inch','Weight=Under 2.5 lb','portable,work,long battery'),
 ('hp-spectre-x360-14','HP Spectre x360 14','laptops',1499,'hp','Design=2-in-1 OLED','Memory=16 GB','portable,creator,work,16gb ram'),
 ('asus-zenbook-14-oled','ASUS Zenbook 14 OLED','laptops',999,'asus','Display=14-inch OLED','Memory=16 GB','portable,work,16gb ram'),
 ('asus-rog-zephyrus-g14','ASUS ROG Zephyrus G14','laptops',1599,'asus','Graphics=Dedicated RTX graphics','Display=14-inch 120 Hz OLED','gaming,creator,portable,dedicated graphics'),
 ('acer-swift-go-14','Acer Swift Go 14','laptops',799,'acer','Display=14-inch OLED','Memory=16 GB','portable,school,work,16gb ram'),
 ('microsoft-surface-laptop-7','Microsoft Surface Laptop 7','laptops',999,'microsoft','Display=13.8-inch touchscreen','Memory=16 GB','portable,work,long battery,16gb ram'),
 ('apple-macbook-pro-14-m4','Apple MacBook Pro 14 M4','laptops',1599,'apple','Chip=Apple M4','Memory=16 GB','creator,work,long battery,16gb ram'),
 ('framework-laptop-13','Framework Laptop 13','laptops',1099,'framework','Design=Repairable modular chassis','Memory=16 GB','work,school,portable,16gb ram'),
 ('dell-ultrasharp-u2725qe','Dell UltraSharp U2725QE','monitors',899,'dell','Display=27-inch 4K','Connection=Thunderbolt hub','4k,work,creator'),
 ('lg-ultragear-27gs95qe','LG UltraGear 27GS95QE','monitors',899,'lg','Display=27-inch OLED','Refresh=240 Hz','oled,gaming'),
 ('samsung-odyssey-oled-g8-32','Samsung Odyssey OLED G8 32','monitors',1299,'samsung','Display=32-inch 4K OLED','Refresh=240 Hz','4k,oled,gaming'),
 ('asus-proart-pa278cgv','ASUS ProArt PA278CGV','monitors',349,'asus','Display=27-inch QHD','Color=Factory calibrated','creator,work'),
 ('alienware-aw3225qf','Dell Alienware AW3225QF','monitors',1199,'dell','Display=32-inch 4K QD-OLED','Refresh=240 Hz','4k,oled,gaming'),
 ('acer-nitro-xv275k','Acer Nitro XV275K','monitors',599,'acer','Display=27-inch 4K','Refresh=160 Hz','4k,gaming,work'),
 ('benq-pd3225u','BenQ PD3225U','monitors',1099,'benq','Display=32-inch 4K','Color=P3 wide gamut','4k,creator,work'),
 ('msi-mag-271qpx','MSI MAG 271QPX QD-OLED','monitors',749,'msi','Display=27-inch QHD OLED','Refresh=360 Hz','oled,gaming'),
 ('bose-qc-ultra-headphones','Bose QuietComfort Ultra Headphones','headphones',429,'bose','Listening=Active noise cancellation','Battery=Up to 24 hours','wireless,noise cancelling,travel,music'),
 ('bose-quietcomfort-headphones','Bose QuietComfort Headphones','headphones',349,'bose','Listening=Active noise cancellation','Battery=Up to 24 hours','wireless,noise cancelling,travel,music'),
 ('apple-airpods-max-usbc','Apple AirPods Max USB-C','headphones',549,'apple','Listening=Active noise cancellation','Connection=USB-C','wireless,noise cancelling,music'),
 ('sennheiser-momentum-4','Sennheiser Momentum 4 Wireless','headphones',349,'sennheiser','Battery=Up to 60 hours','Listening=Adaptive noise cancellation','wireless,noise cancelling,long battery,music'),
 ('beats-studio-pro','Beats Studio Pro','headphones',349,'beats','Listening=Active noise cancellation','Connection=USB-C and Bluetooth','wireless,noise cancelling,music'),
 ('audio-technica-ath-m50xbt2','Audio-Technica ATH-M50xBT2','headphones',199,'audiotechnica','Design=Closed-back wireless','Battery=Up to 50 hours','wireless,long battery,studio,music'),
 ('apple-airpods-4','Apple AirPods 4','earbuds',129,'apple','Design=Open fit','Case=USB-C charging','wireless,portable,music'),
 ('apple-airpods-pro-2','Apple AirPods Pro 2','earbuds',249,'apple','Listening=Active noise cancellation','Case=MagSafe USB-C','wireless,noise cancelling,portable,music'),
 ('bose-qc-ultra-earbuds','Bose QuietComfort Ultra Earbuds','earbuds',299,'bose','Listening=Active noise cancellation','Audio=Immersive mode','wireless,noise cancelling,portable,music'),
 ('samsung-galaxy-buds3-pro','Samsung Galaxy Buds3 Pro','earbuds',249,'samsung','Listening=Active noise cancellation','Design=In-ear','wireless,noise cancelling,portable,music'),
 ('google-pixel-buds-pro-2','Google Pixel Buds Pro 2','earbuds',229,'google','Listening=Active noise cancellation','Design=In-ear stabilizer','wireless,noise cancelling,portable,music'),
 ('jabra-elite-8-active-gen-2','Jabra Elite 8 Active Gen 2','earbuds',229,'jabra','Durability=Workout-focused','Listening=Active noise cancellation','wireless,noise cancelling,water resistant,running'),
 ('jbl-flip-7','JBL Flip 7','speakers',149,'jbl','Design=Portable cylinder','Protection=Water and dust resistant','wireless,portable,water resistant,music'),
 ('jbl-charge-6','JBL Charge 6','speakers',199,'jbl','Battery=Up to 28 hours','Feature=Phone charging output','wireless,portable,long battery,music'),
 ('bose-soundlink-flex-2','Bose SoundLink Flex 2','speakers',149,'bose','Design=Portable Bluetooth','Protection=Water resistant','wireless,portable,water resistant,music'),
 ('ue-wonderboom-4','Ultimate Ears WONDERBOOM 4','speakers',99,'ultimateears','Design=Compact 360-degree','Protection=Waterproof and floating','wireless,portable,water resistant,music'),
 ('sonos-era-100','Sonos Era 100','speakers',249,'sonos','Connection=Wi-Fi and Bluetooth','Design=Room speaker','wireless,home,music'),
 ('marshall-emberton-iii','Marshall Emberton III','speakers',169,'marshall','Battery=Over 30 hours','Protection=Water resistant','wireless,portable,long battery,music'),
 ('lg-oled-c4-55','LG OLED C4 55','tvs',1499,'lg','Panel=55-inch OLED','Refresh=120 Hz','4k,oled,120hz,gaming,movies'),
 ('lg-oled-b4-55','LG OLED B4 55','tvs',1199,'lg','Panel=55-inch OLED','Refresh=120 Hz','4k,oled,120hz,gaming,movies'),
 ('samsung-s90d-55','Samsung S90D OLED 55','tvs',1599,'samsung','Panel=55-inch OLED','Refresh=144 Hz','4k,oled,144hz,gaming,movies'),
 ('samsung-qn90d-55','Samsung QN90D Neo QLED 55','tvs',1699,'samsung','Panel=55-inch Mini LED','Refresh=144 Hz','4k,144hz,gaming,movies,bright room'),
 ('sony-bravia-8-55','Sony BRAVIA 8 OLED 55','tvs',1799,'sony','Panel=55-inch OLED','Audio=Acoustic Surface','4k,oled,120hz,movies,gaming'),
 ('tcl-qm8-65','TCL QM8 65','tvs',1499,'tcl','Panel=65-inch Mini LED','Refresh=144 Hz','4k,144hz,bright room,gaming,movies'),
 ('hisense-u8n-65','Hisense U8N 65','tvs',1299,'hisense','Panel=65-inch Mini LED','Refresh=144 Hz','4k,144hz,bright room,gaming,movies'),
 ('roku-pro-series-65','Roku Pro Series 65','tvs',1199,'roku','Panel=65-inch Mini LED','Platform=Roku TV','4k,120hz,movies,home'),
 ('canon-eos-r50','Canon EOS R50','cameras',679,'canon','Sensor=24 MP APS-C','Video=4K 30p','creator,4k,portable'),
 ('canon-eos-r8','Canon EOS R8','cameras',1499,'canon','Sensor=24 MP full frame','Video=4K 60p','creator,4k'),
 ('nikon-z50-ii','Nikon Z50 II','cameras',909,'nikon','Sensor=21 MP APS-C','Video=4K 60p','creator,4k,portable'),
 ('nikon-z6-iii','Nikon Z6 III','cameras',2499,'nikon','Sensor=24 MP full frame','Stabilization=In-body','creator,4k'),
 ('fujifilm-xs20','Fujifilm X-S20','cameras',1299,'fujifilm','Sensor=26 MP APS-C','Stabilization=In-body','creator,4k,portable'),
 ('gopro-hero13-black','GoPro HERO13 Black','cameras',399,'gopro','Video=5.3K action video','Protection=Waterproof body','creator,portable,water resistant'),
 ('sony-playstation-5-slim','Sony PlayStation 5 Slim','gaming',499,'playstation','Output=4K gaming','Drive=Ultra HD Blu-ray','gaming,4k,home'),
 ('microsoft-xbox-series-x','Microsoft Xbox Series X','gaming',599,'xbox','Output=4K gaming','Storage=1 TB SSD','gaming,4k,1tb storage,home'),
 ('nintendo-switch-oled','Nintendo Switch OLED','gaming',349,'nintendo','Display=7-inch OLED','Modes=Handheld and docked','gaming,oled,portable,family'),
 ('valve-steam-deck-oled-512','Valve Steam Deck OLED 512GB','gaming',549,'valve','Display=7.4-inch OLED','Storage=512 GB','gaming,oled,portable'),
 ('asus-rog-ally-x','ASUS ROG Ally X','gaming',799,'asus','Display=7-inch 120 Hz','Storage=1 TB SSD','gaming,portable,1tb storage'),
 ('meta-quest-3-512','Meta Quest 3 512GB','gaming',499,'meta','Design=Standalone VR','Storage=512 GB','gaming,portable,home'),
 ('apple-watch-series-10','Apple Watch Series 10','wearables',399,'apple','Display=Always-on OLED','Size=42 mm','portable,work,running'),
 ('apple-watch-ultra-2','Apple Watch Ultra 2','wearables',799,'apple','Case=49 mm titanium','GPS=Dual frequency','portable,running,long battery'),
 ('samsung-galaxy-watch7','Samsung Galaxy Watch7','wearables',299,'samsung','Display=AMOLED','GPS=Dual frequency','portable,running,home'),
 ('google-pixel-watch-3','Google Pixel Watch 3','wearables',349,'google','Display=Actua AMOLED','Size=41 mm','portable,running,home'),
 ('garmin-forerunner-265','Garmin Forerunner 265','wearables',449,'garmin','Display=AMOLED','GPS=Multi-band','portable,running,long battery'),
 ('fitbit-charge-6','Fitbit Charge 6','wearables',159,'fitbit','Design=Fitness tracker','GPS=Built-in','portable,running,long battery'),
 ('logitech-mx-master-3s','Logitech MX Master 3S','accessories',99,'logitech','Type=Wireless ergonomic mouse','Connection=Bluetooth or receiver','wireless,work'),
 ('logitech-mx-keys-s','Logitech MX Keys S','accessories',109,'logitech','Type=Low-profile keyboard','Connection=Bluetooth or receiver','wireless,work'),
 ('samsung-t7-shield-2tb','Samsung T7 Shield 2TB','accessories',179,'samsung','Type=Portable SSD','Capacity=2 TB','portable,work'),
 ('anker-737-power-bank','Anker 737 Power Bank','accessories',149,'anker','Capacity=24,000 mAh','Output=140 W USB-C','portable,travel'),
 ('google-nest-wifi-pro','Google Nest Wifi Pro','networking',199,'google','Standard=Wi-Fi 6E','Coverage=Up to 2,200 sq ft','wireless,home,smart home'),
 ('amazon-eero-6-plus','Amazon eero 6+','networking',139,'amazon','Standard=Wi-Fi 6','Coverage=Up to 1,500 sq ft','wireless,home,smart home'),
 ('tp-link-deco-be63','TP-Link Deco BE63','networking',549,'tp-link','Standard=Wi-Fi 7 mesh','Pack=Three nodes','wireless,home,smart home'),
 ('netgear-nighthawk-rs300','NETGEAR Nighthawk RS300','networking',329,'netgear','Standard=Wi-Fi 7','Bands=Tri-band','wireless,home,smart home'),
 ('google-nest-doorbell-wired-2','Google Nest Doorbell Wired 2','smart home',179,'google','Video=HDR video','Power=Wired','smart home,security,home'),
 ('ring-battery-doorbell-pro','Ring Battery Doorbell Pro','smart home',229,'ring','Power=Rechargeable battery','Detection=3D motion','smart home,security,home'),
 ('amazon-echo-show-8-3','Amazon Echo Show 8 3rd Gen','smart home',149,'amazon','Display=8-inch touchscreen','Audio=Spatial audio','smart home,home,music'),
 ('google-nest-hub-max','Google Nest Hub Max','smart home',229,'google','Display=10-inch touchscreen','Camera=6.5 MP','smart home,home'),
 ('dyson-v15-detect','Dyson V15 Detect','appliances',749,'dyson','Type=Cordless stick vacuum','Feature=Laser dust illumination','home,pets,portable'),
 ('irobot-roomba-j7-plus','iRobot Roomba j7+','appliances',799,'irobot','Type=Robot vacuum','Dock=Self-emptying','home,pets,self emptying'),
 ('ninja-foodi-dualzone','Ninja Foodi 6-in-1 DualZone','appliances',199,'ninja','Capacity=8 qt','Baskets=Two cooking zones','home,dual zone'),
 ('breville-barista-express','Breville Barista Express','appliances',699,'breville','Type=Espresso machine','Grinder=Integrated burr grinder','home')
]

for row in REFERENCE_ROWS:
    add_reference(row)

if __name__ == '__main__':
    target = ROOT / 'catalog.json'
    fixture = ROOT / 'simulation_catalog.json'
    if not fixture.exists():
        fixture.write_text(target.read_text(encoding='utf-8'), encoding='utf-8')
    target.write_text(json.dumps(products, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f'Wrote {len(products)} sourced products; stock is synthetic.')
