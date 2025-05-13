# Web Archiver & Monitor

Basit bir Python mikroservis mimarisiyle web sayfalarını izleyen ve değişiklikleri otomatik arşivleyen mikroservis uygulaması.

## İçindekiler

* [Özellikler](#özellikler)
* [Kurulum](#kurulum)
* [Kullanım](#kullanım)
* [Mimari](#mimari)
* [Katkıda Bulunma](#katkıda-bulunma)
* [Lisans](#lisans)

## Özellikler

* URL değişikliklerini düşük benzerlik eşiği ile tespit eder.
* Değişiklik olduğunda RabbitMQ kuyruğuna gönderir.
* Playwright ile tam sayfa snapshot (HTML + ekran görüntüsü) alır.
* `ARCHIVE_BASE_PATH` altında tarih-etiketli klasörlere kaydeder.

## Kurulum

1. Depoyu klonlayın:

   ```bash
   git clone https://github.com/mlatifkaya/web-archiver.git
   cd web-archiver
   ```
2. Gerekli Python paketlerini yükleyin:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. RabbitMQ sunucusunu kurun ve başlatın:

   * Resmi dokümantasyon: [https://www.rabbitmq.com/download.html](https://www.rabbitmq.com/download.html)
   * Alternatif olarak Docker ile:

     ```bash
     docker run -d --hostname my-rabbit --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
     ```

## Kullanım

1. Archiver (subscriber\_archiver.py) çalıştırın:

   ```bash
   python subscriber_archiver.py
   ```
2. URL izleyici (url\_monitor.py) çalıştırın:

   ```bash
   python url_monitor.py --url https://siteadi.com
   ```

> Not: RabbitMQ sunucunuzun `localhost:5672` ve varsayılan kimlik bilgileriyle çalıştığından emin olun.

## Mimari

* **Watcher**: URL’den içerik alır, `clean_html` ve hash hesaplama uygular.
* **Notifier**: Değişiklik algıladığında RabbitMQ’ya mesaj gönderir.
* **Archiver**: Kuyruktan URL alır, Playwright ile snapshot alır ve diske kaydeder.

## Katkıda Bulunma

1. Depoyu fork’layın
2. Yeni bir branch açın (`git checkout -b feature/my-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some feature'`)
4. Pushlayın (`git push origin feature/my-feature`)
5. Pull request açın

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.


