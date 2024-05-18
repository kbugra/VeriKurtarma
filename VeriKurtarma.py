import os
import logging
import re
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import threading

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
def recover_files(fileD, progress, log_text):
    offs = 0
    drec = False
    kurtarID = 0
    byte = fileD.read(size)
    total_size = os.path.getsize(fileD.name)
    progress['maximum'] = total_size

    while byte:
        match = start_regex.search(byte)
        if match:
            for filetype, (start, end, extension) in signatures.items():
                if byte[match.start():match.start()+len(start)] == start:
                    drec = True
                    logging.info(f'{filetype.upper()} konumda bulundu: {str(hex(match.start()+(size*offs)))}')
                    log_text.delete(1.0, END)
                    log_text.insert(END, read_logs())
                    try:
                        fileN = open(str(kurtarID) + extension, "wb")
                    except Exception as e:
                        logging.error(f"Çıktı dosyası açılamadı: {e}")
                        log_text.delete(1.0, END)
                        log_text.insert(END, read_logs())
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
                            log_text.delete(1.0, END)
                            log_text.insert(END, read_logs())
                        else: 
                            fileN.write(byte)
        byte = fileD.read(size)
        offs += 1
        progress['value'] = offs * size
    fileD.close()

# Log dosyasını okuma
def read_logs():
    with open('recovery.log', 'r') as f:
        return f.read()

# Ana fonksiyon
def main():
    def start_recovery():
        drive_letter = drive_letter_entry.get()
        try:
            drive = validate_drive(drive_letter)
            fileD = open_drive(drive)
            global recovery_thread
            recovery_thread = threading.Thread(target=recover_files, args=(fileD, progress, log_text))
            recovery_thread.daemon = True  # Make the thread a daemon thread
            recovery_thread.start()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def stop_recovery():
        if recovery_thread.is_alive():
            messagebox.showinfo("Info", "Recovery process will be stopped soon.")
            recovery_thread._stop()  # Stop the recovery thread

    root = Tk()
    root.title("File Recovery")

    Label(root, text="Drive Letter:").grid(row=0, column=0, padx=10, pady=10)
    drive_letter_entry = Entry(root)
    drive_letter_entry.grid(row=0, column=1, padx=10, pady=10)

    progress = ttk.Progressbar(root, length=200, mode='determinate')
    progress.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

    log_text = Text(root)
    log_text.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    Button(root, text="Start Recovery", command=start_recovery).grid(row=3, column=0, padx=10, pady=10)
    Button(root, text="Stop Recovery", command=stop_recovery).grid(row=3, column=1, padx=10, pady=10)  # Add "Stop Recovery" button

    root.mainloop()

# Ana fonksiyonu çağırma
if __name__ == "__main__":
    main()