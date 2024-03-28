import os
import logging
import re
from tqdm import tqdm

# Loglama ayarları
logging.basicConfig(filename='recovery.log', level=logging.INFO)

# Okuma boyutu
size = 8192  

# Dosya imzaları
signatures = {
    'jpeg': (b'\xff\xd8\xff\xe0\x00\x10\x4a\x46', b'\xff\xd9', '.jpg'),
    'png': (b'\x89PNG\r\n\x1a\n', b'\x00\x00\x00\x00IEND\xaeB`\x82', '.png'),
    'gif': (b'GIF89a', b'\x00\x3b', '.gif'),
    'pdf': (b'%PDF-', b'%%EOF', '.pdf'),
    'bmp': (b'BM', b'\x00\x00', '.bmp'),
    'zip': (b'PK\x03\x04', b'PK\x05\x06', '.zip')
}

# Başlangıç imzaları için regex
start_regex = re.compile(b'|'.join(start for start, _, _ in signatures.values()))

# Sürücü harfini doğrulama
def validate_drive(drive_letter):
    if not drive_letter.isalpha() or len(drive_letter) != 1:
        raise ValueError("Geçersiz sürücü harfi")
    drive = f"\\\\.\\{drive_letter.upper()}:"
    if not os.path.exists(drive):
        raise FileNotFoundError(f"Disk {drive} mevcut değil veya erişilebilir değil")
    return drive

# Sürücüyü açma
def open_drive(drive):
    try:
        return open(drive, "rb")
    except Exception as e:
        logging.error(f"Disk açılamadı {drive}: {e}")
        raise

# Dosyaları kurtarma
def recover_files(fileD):
    offs = 0
    drec = False
    kurtarID = 0
    byte = fileD.read(size)
    pbar = tqdm(total=os.path.getsize(fileD.name))

    while byte:
        match = start_regex.search(byte)
        if match:
            for filetype, (start, end, extension) in signatures.items():
                if byte[match.start():match.start()+len(start)] == start:
                    drec = True
                    logging.info(f'{filetype.upper()} konumda bulundu: {str(hex(match.start()+(size*offs)))}')
                    try:
                        fileN = open(str(kurtarID) + extension, "wb")
                    except Exception as e:
                        logging.error(f"Çıktı dosyası açılamadı: {e}")
                        continue
                    fileN.write(byte[match.start():])
                    while drec:
                        byte = fileD.read(size)
                        bfind = byte.find(end)
                        if bfind >= 0:
                            fileN.write(byte[:bfind+len(end)])
                            fileD.seek((offs+1)*size)
                            logging.info(f'{filetype.upper()} yazildi: {str(kurtarID)}{extension}')
                            drec = False
                            kurtarID += 1
                            fileN.close()
                        else: 
                            fileN.write(byte)
        byte = fileD.read(size)
        offs += 1
        pbar.update(size)
    pbar.close()
    fileD.close()

# Ana fonksiyon
def main():
    drive_letter = input("Lütfen kullanmak istediğiniz sürücü harfini girin (F, E..): ")
    drive = validate_drive(drive_letter)
    fileD = open_drive(drive)
    recover_files(fileD)

# Ana fonksiyonu çağırma
if __name__ == "__main__":
    main()