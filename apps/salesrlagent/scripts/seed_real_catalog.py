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
        department={'headphones':'audio','earbuds':'audio','speakers':'audio','laptops':'computers','monitors':'computers','phones':'mobile','tablets':'mobile','cameras':'photography'}[category],
        price=price, source_url=source, price_checked_at='2026-09-24', price_kind=price_kind,
        compare_at_price=old, specs=specs, features=features.split(','), description=description,
        tradeoff=tradeoff, stock=10, stock_source='local_demo', icon='', aliases=list(aliases),
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

if __name__ == '__main__':
    target = ROOT / 'catalog.json'
    fixture = ROOT / 'simulation_catalog.json'
    if not fixture.exists():
        fixture.write_text(target.read_text(encoding='utf-8'), encoding='utf-8')
    target.write_text(json.dumps(products, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f'Wrote {len(products)} sourced products; stock is synthetic.')
