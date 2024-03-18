import os
import time
import logging

# Set up logging
logging.basicConfig(filename='recovery.log', level=logging.INFO)

size = 4096  # Increase block size for better performance
offs = 0                
drec = False            
kurtarID = 0            

signatures = {
    'jpeg': (b'\xff\xd8\xff\xe0\x00\x10\x4a\x46', b'\xff\xd9', '.jpg'),
    'png': (b'\x89PNG\r\n\x1a\n', b'\x00\x00\x00\x00IEND\xaeB`\x82', '.png'),
    'gif': (b'GIF89a', b'\x00\x3b', '.gif'),
    'pdf': (b'%PDF-', b'%%EOF', '.pdf')
}

drive_letter = input("Lütfen kullanmak istediğiniz sürücü harfini girin (F, E..): ")
drive = f"\\\\.\\{drive_letter.upper()}:"    

# Check if the drive exists and is accessible
if not os.path.exists(drive):
    logging.error(f"Disk {drive} mevcut değil veya erişilemiyor.")
    print(f"Disk {drive} mevcut değil veya erişilemiyor.")
    exit(1)

try:
    fileD = open(drive, "rb") 
except Exception as e:
    logging.error(f"Disk acilamadi {drive}: {e}")
    print(f"Disk acilamadi {drive}: {e}")
    exit(1)

byte = fileD.read(size) 

while byte:
    for filetype, (start, end, extension) in signatures.items():
        found = byte.find(start)
        if found >= 0:
            drec = True
            print(f'==== {filetype.upper()} bu konumda bulundu: {str(hex(found+(size*offs)))} ====') 
            try:
                fileN = open(str(kurtarID) + extension, "wb")
            except Exception as e:
                logging.error(f"Cikti dosyasi acilamadi: {e}")
                print(f"Cikti dosyasi acilamadi: {e}")
                continue
            fileN.write(byte[found:])
            while drec:
                byte = fileD.read(size)
                bfind = byte.find(end)
                if bfind >= 0:
                    fileN.write(byte[:bfind+len(end)])
                    fileD.seek((offs+1)*size)
                    print(f'==== {filetype.upper()} buraya yazildi: {str(kurtarID)}{extension} ====\n')
                    drec = False
                    kurtarID += 1
                    fileN.close()
                else: 
                    fileN.write(byte)
    byte = fileD.read(size)
    offs += 1
    # Progress indication
    if offs % 100 == 0:
        print(f" {offs} kadar veri işlendi...")
fileD.close()