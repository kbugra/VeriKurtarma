drive = "\\\\.\\E:"    
fileD = open(drive, "rb") 
size = 1024             # Her seferinde okunacak bayt sayısı
byte = fileD.read(size) # size kadar bayt oku
offs = 0                # Offset
drec = False            # Dosya bulundu mu?
rcvd = 0                # Kurtarılan dosya sayısı
while byte:
    found = byte.find(b'\xff\xd8\xff\xe0\x00\x10\x4a\x46') # JPG signature
    if found >= 0:
        drec = True
        print('==== Bu konumda JPG bulundu: ' + str(hex(found+(size*offs))) + ' ====') 
        # JPG dosyasını yazdıran kod bloğu
        fileN = open(str(rcvd) + '.jpg', "wb")
        fileN.write(byte[found:])
        while drec:
            byte = fileD.read(size)
            bfind = byte.find(b'\xff\xd9')
            if bfind >= 0:
                fileN.write(byte[:bfind+2])
                fileD.seek((offs+1)*size)
                print('==== JPG Yazıldı: ' + str(rcvd) + '.jpg ====\n')
                drec = False
                rcvd += 1
                fileN.close()
            else: fileN.write(byte)
    byte = fileD.read(size)
    offs += 1
fileD.close()